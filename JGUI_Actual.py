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
from Jarvis import process_gui_command , startup_sequence
import sys
import math
import random
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
SILVER = QColor(235, 238, 242)
SILVER_DIM = QColor(150, 155, 165)
BG_DARK = QColor(0, 0, 0)
PANEL_BG = QColor(12, 12, 14, 180)

# kept as aliases so the rest of the file reads naturally
CYAN = SILVER
CYAN_DIM = SILVER_DIM


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
            c = QColor(255, 255, 255)
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

            c = QColor(255, 255, 255)
            c.setAlpha(max(0, min(255, alpha)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPointF(sx, sy), size, size)

            # tiny cross-flare on the brightest twinkles for a "star" sparkle
            if twinkle > 0.85 and depth_norm > 0.6:
                flare_c = QColor(255, 255, 255)
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


class StatBar(QWidget):
    """A small horizontal bar readout, e.g. CPU / NET / PWR."""
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.value = random.uniform(0.3, 0.9)
        self.setFixedHeight(34)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._jitter)
        self.timer.start(1200)

    def _jitter(self):
        self.value = max(0.1, min(0.97, self.value + random.uniform(-0.15, 0.15)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.setFont(QFont("Consolas", 8))
        p.setPen(QColor(185, 188, 195, 200))
        p.drawText(0, 12, f"{self.label_text}")
        p.drawText(0, 26, f"{int(self.value*100):02d}%")

        bar_x = 55
        bar_w = w - bar_x - 4
        bar_h = 6
        bar_y = h - 14

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(40, 40, 44, 160))
        p.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 2, 2)

        fill_w = int(bar_w * self.value)
        grad = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
        grad.setColorAt(0, QColor(160, 165, 175, 230))
        grad.setColorAt(1, QColor(245, 247, 250, 230))
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 2, 2)
        p.end()


class DigitalClock(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Consolas", 26, QFont.Bold))
        self.setStyleSheet("color: rgb(235,238,242); background: transparent;")
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
        self.status_label = HudLabel("● SYSTEMS ONLINE", size=11, color=QColor(200, 230, 200), bold=True)
        top_bar.addWidget(self.status_label)
        root.addLayout(top_bar)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(160,160,170,70); max-height:1px;")
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
        for name in ["CPU LOAD", "MEMORY", "NETWORK"]:
            left_panel.addWidget(StatBar(name))
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
        for name in ["POWER", "SIGNAL"]:
            right_panel.addWidget(StatBar(name))
        right_panel.addStretch()
        right_box = QFrame()
        right_box.setLayout(right_panel)
        right_box.setFixedWidth(220)
        middle.addWidget(right_box)

        root.addLayout(middle, stretch=1)

        # ---------------- Response / log area ----------------
        self.response_label = QLabel("Hello. I am online and ready to assist.")
        self.response_label.setFont(QFont("Consolas", 12))
        self.response_label.setStyleSheet("color: rgba(220,222,228,230); background: transparent;")
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
                border: 1px solid rgba(200, 202, 210, 120);
                border-radius: 8px;
                padding: 0 14px;
                color: rgb(230, 232, 238);
            }
            QLineEdit:focus {
                border: 1px solid rgba(245, 247, 250, 200);
            }
        """)
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(220, 222, 230, 160))
        glow.setBlurRadius(25)
        glow.setOffset(0, 0)
        self.input_field.setGraphicsEffect(glow)
        self.input_field.returnPressed.connect(self.handle_command)

        self.mic_btn = QPushButton("🎙")
        self.mic_btn.setFixedSize(44, 44)
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(28, 28, 30, 230);
                border: 1px solid rgba(200, 202, 210, 120);
                border-radius: 22px;
                font-size: 16px;
                color: rgb(230,232,238);
            }
            QPushButton:hover {
                background-color: rgba(50, 50, 54, 230);
            }
        """)
        self.mic_btn.clicked.connect(self.voice_command)
        self.voice_mode = False
        send_btn = QPushButton("SEND")
        send_btn.setFixedSize(80, 44)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(235, 238, 242, 230);
                border-radius: 8px;
                font-weight: bold;
                color: rgb(10,10,10);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 240);
            }
        """)
        send_btn.clicked.connect(self.handle_command)

        input_row.addWidget(self.input_field, stretch=1)
        input_row.addWidget(self.mic_btn)
        input_row.addWidget(send_btn)
        root.addLayout(input_row)

    # --------------------------------------------------------------------
    def toggle_listen(self):
        listening = not self.sphere.listening
        self.sphere.set_listening(listening)
        if listening:
            self.status_label.setText("● LISTENING...")
            self.status_label.setStyleSheet("color: rgb(255,180,110); background: transparent;")
        else:
            self.status_label.setText("● SYSTEMS ONLINE")
            self.status_label.setStyleSheet("color: rgb(245,245,245); background: transparent;")
    

    def voice_command(self):
        print("STEP 1")

        from Jarvis import takeCommand

        print("STEP 2")

        self.toggle_listen()

        print("STEP 3")

        text = takeCommand()

        print("STEP 4")

        self.toggle_listen()

        print("STEP 5")

        if text == "None":
            self.response_label.setText("Sorry, I didn't catch that.")
            return

        self.input_field.setText(text)

        print("STEP 6")

        self.handle_command()

        print("STEP 7")

    def handle_command(self):
        text = self.input_field.text().strip()

        if not text:
            return

        self.response_label.setText(f'You said: "{text}" — processing...')
        self.input_field.clear()

        self.worker = CommandWorker(text)
        self.worker.finished.connect(self.command_finished)
        self.worker.start()

    def command_finished(self, running):
        if not running:
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

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
