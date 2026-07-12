import asyncio
import edge_tts
from playsound3 import playsound
import tempfile
import threading
import queue
import os

# CHANGED: Switched to Ryan (British Jarvis vibe). 
# Change back to "en-US-GuyNeural" if you prefer the David/American style.
VOICE = "en-US-GuyNeural" 

# Queue for speech
speech_queue = queue.Queue()

# --- Interrupt / "stop" support -------------------------------------------
# speaking_event is set for as long as audio is actively playing, so other
# parts of the app can check is_speaking() to know whether it's worth
# listening for a "stop" command right now.
speaking_event = threading.Event()
_current_sound = None
_current_sound_lock = threading.Lock()


async def _generate_and_play(text):
    global _current_sound

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        filename = f.name

    try:
        # FIXED: Changed rate from "-10%" to "+25%" for snappier speech
        communicate = edge_tts.Communicate(
            text,
            VOICE,
            rate="+20%" 
        )

        await communicate.save(filename)

        # Non-blocking playback so we can hold onto a handle and stop() it
        # mid-sentence if the user interrupts.
        sound = playsound(filename, block=False)
        with _current_sound_lock:
            _current_sound = sound
        speaking_event.set()

        while sound.is_alive():
            await asyncio.sleep(0.05)

    finally:
        with _current_sound_lock:
            _current_sound = None
        speaking_event.clear()
        try:
            os.remove(filename)
        except:
            pass


def _speaker():
    while True:
        text = speech_queue.get()

        try:
            asyncio.run(_generate_and_play(text))
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

    with _current_sound_lock:
        sound = _current_sound
    if sound is not None:
        try:
            sound.stop()
        except Exception:
            pass
