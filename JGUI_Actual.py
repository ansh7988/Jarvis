"""
JARVIS-style Desktop AI Assistant GUI
Built with PySide6

Features:
- Animated wireframe sphere "neural core" with a twinkling star layer
  (rotating, pulsing, silver/white glow on pure black)
- Top HUD with title + status line
- Side panels with fake system telemetry (digital clock, stats, bars)
- Bottom command input bar with a soft glow effect
- Silver-and-black sci-fi theme

Run:
    pip install PySide6
    python jarvis_gui.py
"""
from email.mime import text

from Jarvis import process_gui_command , startup_sequence, listen_for_stop_word, stop_speaking, is_speaking
import sys
import math
import random
import time
import subprocess
import psutil
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QPointF, Signal , QThread
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QLinearGradient, QRadialGradient 
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect
)

# ----------------------------------------------------------------------------
# Color palette — silver / white on black
# ----------------------------------------------------------------------------
SILVER = QColor(0, 229, 255)
SILVER_DIM = QColor(0, 150, 180)
BG_DARK = QColor(0, 0, 0)
PANEL_BG = QColor(12, 12, 14, 180)

# kept as aliases so the rest of the file reads naturally
CYAN = SILVER
CYAN_DIM = SILVER_DIM
CYAN_BRIGHT = QColor(170, 245, 255)


# ----------------------------------------------------------------------------
# Wireframe Sphere Widget — the "neural core"
# ----------------------------------------------------------------------------
class WireframeSphere(QWidget):
    """A rotating, pulsing wireframe sphere made of latitude/longitude rings,
    with an extra layer of independently-twinkling 'star' points scattered
    across the mesh, drawn each frame with QPainter. Silver/white on black."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.pulse = 0.0
        self.setMinimumSize(260, 260)

        # Pre-generate sphere vertices (lat/long grid) for the wireframe mesh
        self.points = []
        lat_steps = 16
        lon_steps = 24
        for i in range(lat_steps + 1):
            theta = math.pi * i / lat_steps  # 0..pi
            for j in range(lon_steps):
                phi = 2 * math.pi * j / lon_steps
                x = math.sin(theta) * math.cos(phi)
                y = math.cos(theta)
                z = math.sin(theta) * math.sin(phi)
                self.points.append((x, y, z))

        # Extra random "star" points scattered over the sphere surface,
        # each with its own twinkle phase/speed so they sparkle independently.
        self.stars = []
        num_stars = 260
        for _ in range(num_stars):
            # uniform point on sphere
            u = random.uniform(-1, 1)
            phi = random.uniform(0, 2 * math.pi)
            r = math.sqrt(max(0.0, 1 - u * u))
            x, y, z = r * math.cos(phi), u, r * math.sin(phi)
            self.stars.append({
                "pos": (x, y, z),
                "phase": random.uniform(0, 2 * math.pi),
                "speed": random.uniform(1.5, 4.0),
                "base_size": random.uniform(0.8, 2.4),
            })

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)

        self.listening = False
        self.t = 0.0

    def tick(self):
        self.angle_y += 0.010
        self.angle_x += 0.0035
        self.pulse += 0.06
        self.t += 0.033
        self.update()

    def set_listening(self, val: bool):
        self.listening = val

    def project(self, x, y, z, radius, cx, cy):
        # Rotate around Y then X
        cosy, siny = math.cos(self.angle_y), math.sin(self.angle_y)
        x1 = x * cosy - z * siny
        z1 = x * siny + z * cosy

        cosx, sinx = math.cos(self.angle_x), math.sin(self.angle_x)
        y1 = y * cosx - z1 * sinx
        z2 = y * sinx + z1 * cosx

        # simple perspective
        scale = 1.0 + z2 * 0.25
        sx = cx + x1 * radius * scale
        sy = cy + y1 * radius * scale
        return sx, sy, z2

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        base_radius = min(w, h) * 0.36

        pulse_amt = (math.sin(self.pulse) + 1) / 2  # 0..1
        radius = base_radius * (1.0 + (0.04 if not self.listening else 0.10) * pulse_amt)

        # --- Outer glow (soft white/silver halo, or warm accent when listening) ---
        glow_color = SILVER if not self.listening else QColor(255, 170, 90)
        glow = QRadialGradient(cx, cy, radius * 2.3)
        c1 = QColor(glow_color)
        c1.setAlpha(60)
        c2 = QColor(glow_color)
        c2.setAlpha(0)
        glow.setColorAt(0.0, c1)
        glow.setColorAt(1.0, c2)
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius * 2.3, radius * 2.3)

        # --- Project all wireframe points ---
        projected = []
        for (x, y, z) in self.points:
            sx, sy, sz = self.project(x, y, z, radius, cx, cy)
            projected.append((sx, sy, sz))

        # --- Draw latitude/longitude wireframe mesh (fine silver lines) ---
        lat_steps = 16
        lon_steps = 24
        line_color = QColor(glow_color)

        def idx(i, j):
            return i * lon_steps + (j % lon_steps)

        pen = QPen(line_color)
        for i in range(lat_steps + 1):
            for j in range(lon_steps):
                p1 = projected[idx(i, j)]
                p2 = projected[idx(i, j + 1)]
                depth = (p1[2] + p2[2]) / 2
                alpha = int(25 + 70 * ((depth + 1) / 2))
                width_f = 0.7 if depth < 0 else 1.1
                c = QColor(line_color)
                c.setAlpha(max(10, min(140, alpha)))
                pen.setColor(c)
                pen.setWidthF(width_f)
                painter.setPen(pen)
                painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1]))

                if i < lat_steps:
                    p3 = projected[idx(i + 1, j)]
                    depth2 = (p1[2] + p3[2]) / 2
                    alpha2 = int(25 + 70 * ((depth2 + 1) / 2))
                    c2 = QColor(line_color)
                    c2.setAlpha(max(10, min(140, alpha2)))
                    pen.setColor(c2)
                    painter.setPen(pen)
                    painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p3[0], p3[1]))

        # --- Wireframe vertex points (subtle, front-facing brighter) ---
        for (sx, sy, sz) in projected:
            depth_norm = (sz + 1) / 2
            if depth_norm < 0.5:
                continue
            alpha = int(70 + 100 * depth_norm)
            size = 0.9 + 1.1 * depth_norm
            c = QColor(CYAN_BRIGHT)
            c.setAlpha(min(220, alpha))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPointF(sx, sy), size, size)

        # --- Twinkling star layer: independent points scattered on the sphere,
        #     each pulsing brightness/size on its own phase for a sparkling look ---
        for star in self.stars:
            x, y, z = star["pos"]
            sx, sy, sz = self.project(x, y, z, radius, cx, cy)
            depth_norm = (sz + 1) / 2
            if depth_norm < 0.38:
                continue  # cull back-facing stars

            twinkle = (math.sin(self.t * star["speed"] + star["phase"]) + 1) / 2  # 0..1
            brightness = 0.35 + 0.65 * twinkle
            alpha = int(90 + 165 * depth_norm * brightness)
            size = star["base_size"] * (0.7 + 0.6 * brightness) * (0.7 + 0.5 * depth_norm)

            c = QColor(CYAN_BRIGHT)
            c.setAlpha(max(0, min(255, alpha)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPointF(sx, sy), size, size)

            # tiny cross-flare on the brightest twinkles for a "star" sparkle
            if twinkle > 0.85 and depth_norm > 0.6:
                flare_c = QColor(CYAN_BRIGHT)
                flare_c.setAlpha(int(alpha * 0.5))
                flare_pen = QPen(flare_c)
                flare_pen.setWidthF(0.6)
                painter.setPen(flare_pen)
                flare_len = size * 2.6
                painter.drawLine(QPointF(sx - flare_len, sy), QPointF(sx + flare_len, sy))
                painter.drawLine(QPointF(sx, sy - flare_len), QPointF(sx, sy + flare_len))
                painter.setPen(Qt.NoPen)

        # --- Core inner glow ---
        core = QRadialGradient(cx, cy, radius * 0.55)
        cc1 = QColor(glow_color)
        cc1.setAlpha(50)
        cc2 = QColor(glow_color)
        cc2.setAlpha(0)
        core.setColorAt(0.0, cc1)
        core.setColorAt(1.0, cc2)
        painter.setBrush(QBrush(core))
        painter.drawEllipse(QPointF(cx, cy), radius * 0.55, radius * 0.55)

        painter.end()


# ----------------------------------------------------------------------------
# Small HUD helper widgets
# ----------------------------------------------------------------------------
class HudLabel(QLabel):
    def __init__(self, text="", size=10, color=CYAN, bold=False, parent=None):
        super().__init__(text, parent)
        f = QFont("Consolas", size)
        f.setBold(bold)
        self.setFont(f)
        self.setStyleSheet(f"color: rgba({color.red()},{color.green()},{color.blue()},230); "
                            f"background: transparent; letter-spacing: 1px;")


def get_wifi_signal():
    """Best-effort Wi-Fi signal strength (0-100) via `netsh` on Windows.
    Returns None if unavailable (no Wi-Fi adapter, not on Windows, etc.)."""
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            stderr=subprocess.DEVNULL, timeout=1
        ).decode(errors="ignore")
        for line in output.splitlines():
            if "Signal" in line and ":" in line:
                pct = line.split(":", 1)[1].strip().replace("%", "")
                return int(pct)
    except Exception:
        return None
    return None


class StatBar(QWidget):
    """A small horizontal bar readout driven by live system stats
    (CPU load, memory, network throughput, battery, Wi-Fi signal)."""

    METRIC_LABELS = {
        "cpu": "CPU LOAD",
        "memory": "MEMORY",
        "network": "NETWORK",
        "battery": "POWER",
        "signal": "SIGNAL",
    }

    def __init__(self, metric, parent=None):
        super().__init__(parent)
        self._metric_key = metric
        self.label_text = self.METRIC_LABELS.get(metric, metric.upper())
        self.value = 0.0
        self.display_text = "--"
        self.setFixedHeight(34)

        if self._metric_key == "network":
            self._last_net = psutil.net_io_counters()
            self._last_time = time.time()

        if self._metric_key == "cpu":
            # First call always returns 0.0 - prime it so the first
            # real reading a moment later is accurate.
            psutil.cpu_percent(interval=None)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh)
        self.timer.start(1200)
        self._refresh()

    def _refresh(self):
        try:
            if self._metric_key == "cpu":
                pct = psutil.cpu_percent(interval=None)
                self.value = pct / 100.0
                self.display_text = f"{int(pct):02d}%"

            elif self._metric_key == "memory":
                pct = psutil.virtual_memory().percent
                self.value = pct / 100.0
                self.display_text = f"{int(pct):02d}%"

            elif self._metric_key == "network":
                now = psutil.net_io_counters()
                now_t = time.time()
                elapsed = max(0.001, now_t - self._last_time)
                delta_bytes = (now.bytes_sent - self._last_net.bytes_sent) + \
                              (now.bytes_recv - self._last_net.bytes_recv)
                bytes_per_sec = delta_bytes / elapsed
                self._last_net = now
                self._last_time = now_t

                # Bar fill: normalized against a 2 MB/s reference point
                pct = min(100.0, (bytes_per_sec / (2 * 1024 * 1024)) * 100.0)
                self.value = pct / 100.0

                if bytes_per_sec >= 1024 * 1024:
                    self.display_text = f"{bytes_per_sec / (1024 * 1024):.1f}MB/s"
                else:
                    self.display_text = f"{bytes_per_sec / 1024:.0f}KB/s"

            elif self._metric_key == "battery":
                battery = psutil.sensors_battery()
                if battery is None:
                    # Desktop / no battery sensor - always on AC power
                    self.value = 1.0
                    self.display_text = "AC"
                else:
                    pct = battery.percent
                    self.value = pct / 100.0
                    self.display_text = f"{int(pct):02d}%" + (" ⚡" if battery.power_plugged else "")

            elif self._metric_key == "signal":
                sig = get_wifi_signal()
                if sig is None:
                    self.value = 0.0
                    self.display_text = "N/A"
                else:
                    self.value = sig / 100.0
                    self.display_text = f"{sig:02d}%"

        except Exception:
            pass

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.setFont(QFont("Consolas", 8))
        p.setPen(QColor(90, 210, 230, 200))
        p.drawText(0, 12, f"{self.label_text}")
        p.drawText(0, 26, self.display_text)

        bar_x = 55
        bar_w = w - bar_x - 4
        bar_h = 6
        bar_y = h - 14

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(40, 40, 44, 160))
        p.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 2, 2)

        fill_w = int(bar_w * self.value)
        grad = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
        grad.setColorAt(0, QColor(0, 150, 175, 230))
        grad.setColorAt(1, QColor(120, 235, 255, 230))
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 2, 2)
        p.end()


class DigitalClock(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Consolas", 26, QFont.Bold))
        self.setStyleSheet("color: rgb(120,235,255); background: transparent;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh)
        self.timer.start(1000)
        self._refresh()

    def _refresh(self):
        now = datetime.now()
        self.setText(now.strftime("%H:%M:%S"))


# ----------------------------------------------------------------------------
# Main Window
# ----------------------------------------------------------------------------
class CommandWorker(QThread):
    finished = Signal(bool)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        from Jarvis import process_gui_command
        result = process_gui_command(self.command)
        self.finished.emit(result)

class VoiceWorker(QThread):
    command_received = Signal(str)
    listening = Signal(bool)

    def __init__(self):
        super().__init__()
        self.running = True
        self.paused = False

    def stop(self):
        self.running = False

    def pause_listening(self):
        self.paused = True

    def resume_listening(self):
        self.paused = False

    def run(self):
        from Jarvis import takeCommand

        while self.running:
            if self.paused:
                self.msleep(150)
                continue

            self.listening.emit(True)
            text = takeCommand()
            self.listening.emit(False)

            if not self.running:
                break

            if text != "None":
                # Pause immediately (in this thread, no race with the GUI
                # thread) so we don't start listening again before the
                # command we just recognized has been handled.
                self.paused = True
                self.command_received.emit(text)


class StopWordListener(QThread):
    """Runs for the whole session. It only actively listens while Jarvis
    is speaking (checked via is_speaking()) - the moment it hears
    "stop" or "stop jarvis", it cuts playback off immediately and clears
    anything queued to be spoken next, so Jarvis is instantly ready for
    the next command."""
    stopped = Signal()

    def __init__(self):
        super().__init__()
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            if is_speaking():
                if listen_for_stop_word(timeout=1, phrase_time_limit=2):
                    stop_speaking()
                    self.stopped.emit()
            else:
                self.msleep(150)

class JarvisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S")
        self.resize(1180, 720)
        self.setStyleSheet(f"background-color: rgb({BG_DARK.red()},{BG_DARK.green()},{BG_DARK.blue()});")

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(10)

        # ---------------- Top bar ----------------
        top_bar = QHBoxLayout()
        title = HudLabel("J.A.R.V.I.S", size=20, color=CYAN, bold=True)
        top_bar.addWidget(title)
        top_bar.addStretch()
        self.system_label = HudLabel("● SYSTEMS ONLINE", size=11, color=QColor(120, 255, 210), bold=True)
        top_bar.addWidget(self.system_label)
        root.addLayout(top_bar)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(0,200,220,70); max-height:1px;")
        root.addWidget(line)

        # ---------------- Middle area: left stats | sphere | right stats ----------------
        middle = QHBoxLayout()
        middle.setSpacing(16)

        # Left panel
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        self.clock = DigitalClock()
        left_panel.addWidget(self.clock)
        date_lbl = HudLabel(datetime.now().strftime("%a, %d %b %Y").upper(), size=10, color=CYAN_DIM)
        left_panel.addWidget(date_lbl)
        left_panel.addSpacing(10)
        for metric in ["cpu", "memory", "network"]:
            left_panel.addWidget(StatBar(metric))
        left_panel.addStretch()
        left_box = QFrame()
        left_box.setLayout(left_panel)
        left_box.setFixedWidth(220)
        middle.addWidget(left_box)

        # Center sphere
        self.sphere = WireframeSphere()
        middle.addWidget(self.sphere, stretch=1)

        # Right panel
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        right_panel.addWidget(HudLabel("ACTIVE PROCESSES", size=10, color=CYAN_DIM, bold=True))
        self.proc_labels = []
        for proc in ["voice_engine.py", "vision_core.dll", "nlp_router", "task_manager", "web_query"]:
            lbl = HudLabel(f"▸ {proc}", size=9, color=CYAN)
            right_panel.addWidget(lbl)
        right_panel.addSpacing(10)
        for metric in ["battery", "signal"]:
            right_panel.addWidget(StatBar(metric))
        right_panel.addStretch()
        right_box = QFrame()
        right_box.setLayout(right_panel)
        right_box.setFixedWidth(220)
        middle.addWidget(right_box)

        root.addLayout(middle, stretch=1)
        self.response_label = QLabel("")

        # ---------------- Response / log area ----------------
        self.response_label.setFont(QFont("Consolas", 12))
        self.response_label.setStyleSheet("color: rgba(150,235,255,230); background: transparent;")
        self.response_label.setWordWrap(True)
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.setFixedHeight(40)
        root.addWidget(self.response_label)

        # ---------------- Bottom input bar ----------------
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command, sir...")
        self.input_field.setFont(QFont("Consolas", 12))
        self.input_field.setFixedHeight(44)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(18, 18, 20, 220);
                border: 1px solid rgba(0, 200, 220, 140);
                border-radius: 8px;
                padding: 0 14px;
                color: rgb(170, 240, 255);
            }
            QLineEdit:focus {
                border: 1px solid rgba(120, 240, 255, 220);
            }
        """)
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(0, 220, 255, 160))
        glow.setBlurRadius(25)
        glow.setOffset(0, 0)
        self.input_field.setGraphicsEffect(glow)
        self.input_field.returnPressed.connect(self.handle_command)

        self.mic_btn = QPushButton("🎙")
        self.mic_btn.setFixedSize(44, 44)
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(10, 30, 34, 230);
                border: 1px solid rgba(0, 200, 220, 140);
                border-radius: 22px;
                font-size: 16px;
                color: rgb(170, 240, 255);
            }
            QPushButton:hover {
                background-color: rgba(0, 60, 70, 230);
            }
        """)
        self.mic_btn.clicked.connect(self.voice_command)
        self.voice_mode = False

        input_row.addWidget(self.input_field, stretch=1)
        input_row.addWidget(self.mic_btn)
        self.voice_label = HudLabel("READY", size=12, color=CYAN, bold=True)

        input_row.addStretch()
        input_row.addWidget(self.voice_label)
        input_row.addStretch()

        root.addLayout(input_row)

        # Voice worker is created fresh each time listening starts/stops
        # (a QThread cannot be restarted once it has finished running).
        self.voice_worker = None
        self.listening_active = False

        # Commands are queued and run one at a time. Keeping a reference
        # to each CommandWorker until it finishes prevents Qt from garbage
        # collecting (and force-destroying) a thread that's still running,
        # which is what was causing the app to lag and then crash when
        # several commands came in quickly.
        self._active_workers = []
        self._command_queue = []
        self._busy = False

        # Always-on background listener that can interrupt Jarvis mid-speech
        # when it hears "stop" / "stop jarvis" - independent of whether
        # continuous command listening is toggled on.
        self.stop_listener = StopWordListener()
        self.stop_listener.stopped.connect(self.on_jarvis_stopped)
        self.stop_listener.start()
    # --------------------------------------------------------------------
    def toggle_listen(self):
        listening = not self.sphere.listening
        self.sphere.set_listening(listening)

        if listening:
            self.voice_label.setText("● LISTENING...")
            self.voice_label.setStyleSheet(
                "color: rgb(255,180,110); background: transparent;"
            )
        else:
            self.voice_label.setText("READY")
            self.voice_label.setStyleSheet(
                "color: rgb(120,220,235); background: transparent;"
            )


    def update_listening_state(self, listening):
        self.sphere.set_listening(listening)

        if listening:
            self.voice_label.setText("● LISTENING...")
            self.voice_label.setStyleSheet(
                "color: rgb(255,180,110); background: transparent;"
            )
        else:
            self.voice_label.setText("READY")
            self.voice_label.setStyleSheet(
                "color: rgb(120,220,235); background: transparent;"
            )


    def voice_command_received(self, text):
        self.response_label.setText(f'You said: "{text}"')
        self.input_field.setText(text)
        self.handle_command()

    def voice_command(self):
        """Toggle the mic on/off. Listening happens on a background
        QThread (VoiceWorker) so the GUI never freezes while recording.
        The same worker thread is reused for the app's lifetime and is
        paused/resumed rather than destroyed and recreated, since
        destroying a QThread while it's still running crashes the app."""
        if self.listening_active:
            # Currently listening -> stop it for real (user turned it off)
            if self.voice_worker is not None:
                self.voice_worker.stop()
                self.voice_worker.wait(2000)
            self.listening_active = False
            self.mic_btn.setText("🎙")
            self.update_listening_state(False)
        else:
            if self.voice_worker is None or not self.voice_worker.isRunning():
                self.voice_worker = VoiceWorker()
                self.voice_worker.command_received.connect(self.voice_command_received)
                self.voice_worker.listening.connect(self.update_listening_state)
                self.voice_worker.start()
            else:
                self.voice_worker.resume_listening()
            self.listening_active = True
            self.mic_btn.setText("⏹")

    def handle_command(self):
        text = self.input_field.text().strip()

        if not text:
            return

        self.input_field.clear()
        self._command_queue.append(text)
        self._process_next_command()

    def _process_next_command(self):
        if self._busy or not self._command_queue:
            return

        text = self._command_queue.pop(0)
        self._busy = True
        self.response_label.setText(f'You said: "{text}" — processing...')

        # Pause continuous listening while this command runs, so it
        # doesn't compete for the microphone with commands that need to
        # listen again themselves (e.g. "write a note", "send email").
        # (For voice-triggered commands the worker has usually already
        # paused itself the instant it recognized the command.)
        self._resume_listening_after = False
        if self.listening_active and self.voice_worker is not None:
            self.voice_worker.pause_listening()
            self._resume_listening_after = True

        worker = CommandWorker(text)
        self._active_workers.append(worker)
        worker.finished.connect(lambda running, w=worker: self._on_command_worker_finished(w, running))
        worker.start()

    def _on_command_worker_finished(self, worker, running):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        self._busy = False

        if running and getattr(self, "_resume_listening_after", False):
            if self.voice_worker is not None and self.voice_worker.isRunning():
                self.voice_worker.resume_listening()
            self.listening_active = True
            self.mic_btn.setText("⏹")

        self.command_finished(running)
        if running:
            self._process_next_command()

    def on_jarvis_stopped(self):
        self.response_label.setText("Stopped. Ready for your next command, sir.")

    def command_finished(self, running):
        if not running:
            if self.voice_worker is not None:
                self.voice_worker.stop()
                self.voice_worker.wait(2000)
            if self.stop_listener is not None:
                self.stop_listener.stop()
                self.stop_listener.wait(2000)
            QApplication.quit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()
        else:
            super().keyPressEvent(event)

def main():
    import subprocess
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = JarvisWindow()

    from Jarvis import set_gui
    set_gui(window)

    window.showMaximized()

    # Start Jarvis AFTER the GUI appears
    QTimer.singleShot(500, startup_sequence)
    # QTimer.singleShot(6000,window.voice_command)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
