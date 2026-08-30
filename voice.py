import asyncio
import edge_tts
import threading
import queue
import subprocess

# ---------------------------------------------------------------------------
# edge_tts, but STREAMED straight into ffplay instead of:
#   generate full mp3 -> save to disk -> read file -> play
# This starts audio the moment the first chunk arrives instead of waiting
# for the whole sentence to finish generating/downloading. No temp files,
# no disk I/O at all.
#
# Requires ffmpeg (ffplay) installed and on PATH.
# ---------------------------------------------------------------------------

VOICE = "en-US-GuyNeural"
RATE = "+25%"

speech_queue = queue.Queue()
speaking_event = threading.Event()

_current_process = None
_current_process_lock = threading.Lock()


async def _generate_and_stream(text):
    global _current_process

    process = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-"],
        stdin=subprocess.PIPE,
    )
    with _current_process_lock:
        _current_process = process
    speaking_event.set()

    try:
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                try:
                    process.stdin.write(chunk["data"])
                except (BrokenPipeError, OSError):
                    break  # pipe closed because stop_speaking() killed it
        try:
            process.stdin.close()
        except Exception:
            pass
        process.wait()
    finally:
        with _current_process_lock:
            _current_process = None
        speaking_event.clear()



def _speaker():
    while True:
        text = speech_queue.get()
        try:
            asyncio.run(_generate_and_stream(text))
        except Exception as e:
            print("Voice Error:", e)
        speech_queue.task_done()


# Start ONE speaker thread only
threading.Thread(
    target=_speaker,
    daemon=True
).start()


def speak(text):
    speech_queue.put(text)


def is_speaking():
    """True while audio is actively playing."""
    return speaking_event.is_set()


def stop_speaking():
    """Immediately stop whatever is currently playing, and drop anything
    still queued up so it doesn't just start speaking again right after."""
    try:
        while True:
            speech_queue.get_nowait()
            speech_queue.task_done()
    except queue.Empty:
        pass

    with _current_process_lock:
        process = _current_process
    if process is not None:
        try:
            process.kill()
        except Exception:
            pass
    speaking_event.clear()
