"""
floating_button.py

A small, always-on-top, draggable "AI orb" button - styled like a glowing
arc-reactor / neural core, similar in spirit to Windows Copilot's floating
button or the Android Edge Panel handle. It is a completely independent
top-level widget, so it keeps floating above Chrome, VS Code, File
Explorer, etc. even while the main JarvisWindow is behind those apps.

- Single click  -> pop open a small quick-action menu (Mic / Transcript)
                   right next to the orb, WITHOUT opening the full GUI.
- Single click again (while the menu is open) -> close the quick menu.
- Double click  -> open/bring forward the full Jarvis window (this is the
                   "click twice" gesture to get the complete GUI).
- Drag          -> reposition anywhere on screen (snaps back into view if
                    dragged off-screen).
- close()       -> called by JGUI.py when Jarvis exits, so the button (and
                    its quick menu) never lingers after the app is gone.

This widget deliberately has no timers, no animations loop, and no heavy
painting, so it costs effectively nothing while idle.
"""

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QPen, QCursor
from PySide6.QtWidgets import (
    QWidget, QApplication, QPushButton, QVBoxLayout, QGraphicsDropShadowEffect
)

SIZE = 56
MARGIN_FROM_EDGE = 18
DRAG_THRESHOLD = 4  # pixels of movement before a press counts as a drag, not a click

MENU_BTN_SIZE = 42
MENU_WIDTH = 60


class OrbQuickMenu(QWidget):
    """Small floating popup with two quick-action buttons (mic + transcript)
    that appears next to the orb on a single click. It never touches the
    main JarvisWindow's layout - it only calls back into it."""

    def __init__(self, mic_callback, transcript_callback, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedWidth(MENU_WIDTH)

        card = QWidget(self)
        card.setObjectName("orbMenuCard")
        card.setStyleSheet("""
            #orbMenuCard {
                background-color: rgba(10, 12, 14, 235);
                border: 1px solid rgba(0, 200, 220, 130);
                border-radius: 16px;
            }
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(10)

        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor(0, 220, 255, 90))
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 0)
        card.setGraphicsEffect(shadow)

        btn_style = """
            QPushButton {
                background-color: rgba(10, 30, 34, 230);
                border: 1px solid rgba(0, 200, 220, 140);
                border-radius: %dpx;
                font-size: 16px;
                color: rgb(170, 240, 255);
            }
            QPushButton:hover {
                background-color: rgba(0, 60, 70, 230);
            }
        """ % (MENU_BTN_SIZE // 2)

        self.mic_btn = QPushButton("\U0001F399")  # microphone emoji
        self.mic_btn.setFixedSize(MENU_BTN_SIZE, MENU_BTN_SIZE)
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_btn.setToolTip("Toggle mic")
        self.mic_btn.setStyleSheet(btn_style)
        self.mic_btn.clicked.connect(self._on_mic)

        self.transcript_btn = QPushButton("\U0001F4AC")  # speech balloon emoji
        self.transcript_btn.setFixedSize(MENU_BTN_SIZE, MENU_BTN_SIZE)
        self.transcript_btn.setCursor(Qt.PointingHandCursor)
        self.transcript_btn.setToolTip("Toggle transcript")
        self.transcript_btn.setStyleSheet(btn_style)
        self.transcript_btn.clicked.connect(self._on_transcript)

        layout.addWidget(self.mic_btn)
        layout.addWidget(self.transcript_btn)
        self.adjustSize()

        self._mic_callback = mic_callback
        self._transcript_callback = transcript_callback

    def _on_mic(self):
        if self._mic_callback is not None:
            self._mic_callback()
        self.hide()

    def _on_transcript(self):
        if self._transcript_callback is not None:
            self._transcript_callback()
        self.hide()

    def position_near(self, orb_geometry):
        """Place the menu just to the left of the orb (or to the right if
        there isn't room), vertically centered on it, and keep it fully
        on-screen."""
        screen = QApplication.screenAt(orb_geometry.center()) or QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None

        self.adjustSize()
        menu_h = self.sizeHint().height()
        menu_w = self.sizeHint().width()

        x = orb_geometry.left() - menu_w - 10
        if avail is not None and x < avail.left():
            x = orb_geometry.right() + 10

        y = orb_geometry.center().y() - menu_h // 2
        if avail is not None:
            y = min(max(y, avail.top()), avail.bottom() - menu_h)

        self.move(x, y)


class FloatingJarvisButton(QWidget):
    def __init__(self, main_window):
        super().__init__(
            None,
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(SIZE, SIZE)
        self.setCursor(Qt.PointingHandCursor)

        self._main_window = main_window
        self._drag_offset = QPoint()
        self._dragging = False
        self._press_pos = QPoint()

        self._menu = OrbQuickMenu(self._handle_mic, self._handle_transcript)

        self._dock_to_right_edge()

    # ------------------------------------------------------------------
    def _handle_mic(self):
        if self._main_window is not None:
            self._main_window.voice_command()

    def _handle_transcript(self):
        if self._main_window is not None:
            self._main_window.toggle_transcript()

    # ------------------------------------------------------------------
    def _dock_to_right_edge(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            self.move(100, 100)
            return
        avail = screen.availableGeometry()
        x = avail.right() - SIZE - MARGIN_FROM_EDGE
        y = avail.top() + avail.height() // 2 - SIZE // 2
        self.move(x, y)

    def _keep_on_screen(self):
        screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        x = min(max(self.x(), avail.left()), avail.right() - SIZE)
        y = min(max(self.y(), avail.top()), avail.bottom() - SIZE)
        if (x, y) != (self.x(), self.y()):
            self.move(x, y)

    # ------------------------------------------------------------------
    def toggle_menu(self):
        if self._menu.isVisible():
            self._menu.hide()
        else:
            self._menu.position_near(self.geometry())
            self._menu.show()
            self._menu.raise_()

    def hide_menu(self):
        if self._menu is not None:
            self._menu.hide()

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        """Paint a glowing cyan AI-orb / arc-reactor style icon."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = SIZE / 2, SIZE / 2
        outer_radius = SIZE / 2 - 3

        # --- Outer ambient glow ---
        glow = QRadialGradient(cx, cy, outer_radius * 1.7)
        glow.setColorAt(0.0, QColor(0, 220, 255, 100))
        glow.setColorAt(1.0, QColor(0, 220, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(self.rect())

        # --- Outer housing ring (dark metal casing, like a reactor shell) ---
        housing_radius = outer_radius
        housing = QRadialGradient(cx, cy, housing_radius)
        housing.setColorAt(0.0, QColor(26, 34, 38, 235))
        housing.setColorAt(0.85, QColor(14, 20, 23, 235))
        housing.setColorAt(1.0, QColor(8, 12, 14, 235))
        painter.setBrush(housing)
        painter.setPen(QPen(QColor(0, 220, 255, 160), 1.4))
        painter.drawEllipse(
            int(cx - housing_radius), int(cy - housing_radius),
            int(housing_radius * 2), int(housing_radius * 2)
        )

        # --- Radial "teeth" segments around the ring, arc-reactor style ---
        painter.save()
        painter.translate(cx, cy)
        teeth = 10
        tooth_len = housing_radius * 0.32
        tooth_r_outer = housing_radius * 0.92
        for i in range(teeth):
            painter.save()
            painter.rotate(360.0 / teeth * i)
            painter.setPen(QPen(QColor(120, 230, 245, 180), 2.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(
                0, int(-(tooth_r_outer - tooth_len)),
                0, int(-tooth_r_outer)
            )
            painter.restore()
        painter.restore()

        # --- Thin inner ring ---
        inner_ring_radius = housing_radius * 0.55
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(150, 235, 255, 200), 1.6))
        painter.drawEllipse(
            int(cx - inner_ring_radius), int(cy - inner_ring_radius),
            int(inner_ring_radius * 2), int(inner_ring_radius * 2)
        )

        # --- Glowing core (bright cyan-white center, like an AI orb) ---
        core_radius = housing_radius * 0.38
        core = QRadialGradient(cx, cy, core_radius)
        core.setColorAt(0.0, QColor(235, 255, 255, 255))
        core.setColorAt(0.35, QColor(120, 235, 255, 255))
        core.setColorAt(1.0, QColor(0, 160, 190, 60))
        painter.setBrush(core)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            int(cx - core_radius), int(cy - core_radius),
            int(core_radius * 2), int(core_radius * 2)
        )

        painter.end()

    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._drag_offset = self._press_pos - self.pos()
            self._dragging = False

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            current = event.globalPosition().toPoint()
            if not self._dragging:
                moved = (current - self._press_pos).manhattanLength()
                if moved < DRAG_THRESHOLD:
                    return
                self._dragging = True
                self.hide_menu()
            self.move(current - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self._dragging:
            self._dragging = False
            self._keep_on_screen()
        else:
            # Single click -> quick-action menu (mic / transcript), NOT the
            # full GUI. Double-click (handled below) opens the full GUI.
            self.toggle_menu()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.hide_menu()
            self.toggle_main_window()

    # ------------------------------------------------------------------
    def bring_main_window_forward(self):
        if self._main_window is None:
            return
        if self._main_window.isMinimized():
            self._main_window.showNormal()
        if not self._main_window.isVisible():
            self._main_window.show()
        self._main_window.raise_()
        self._main_window.activateWindow()

    def toggle_main_window(self):
        if self._main_window is None:
            return
        if self._main_window.isVisible() and not self._main_window.isMinimized():
            self._main_window.hide()
        else:
            self.bring_main_window_forward()

    # ------------------------------------------------------------------
    def close(self):
        if getattr(self, "_menu", None) is not None:
            self._menu.close()
        return super().close()
