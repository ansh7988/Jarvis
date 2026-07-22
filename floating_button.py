"""
floating_button.py

A small, always-on-top, draggable "arc reactor" orb - similar in spirit to
Windows Copilot's floating button or the Android Edge Panel handle. It is a
completely independent top-level widget, so it keeps floating above Chrome,
VS Code, File Explorer, etc. even while the main JarvisWindow is behind
those apps.

Interaction model:
- Single click  -> pop open a small "quick actions" menu right next to the
                    orb, with two round buttons: Mic and Transcript. Neither
                    of these opens the full JarvisWindow - they call
                    straight into JarvisWindow.voice_command() /
                    .toggle_transcript(), the same way the full GUI's own
                    mic / transcript buttons do.
- Double click  -> open (or bring forward) the full Jarvis window. If the
                    window is already visible and not minimized, this hides
                    it again - a normal toggle.
- Drag          -> reposition anywhere on screen (snaps back into view if
                    dragged off-screen). Any in-progress quick actions menu
                    is dismissed as soon as a drag starts.
- close()       -> called by JGUI.py when Jarvis exits, so neither the orb
                    nor its quick actions menu ever lingers after the app
                    is gone.

Single vs. double click is disambiguated manually with a short timer (the
length of QApplication.doubleClickInterval()) rather than relying on Qt's
mouseDoubleClickEvent, because a genuine double click still delivers a
single mouseReleaseEvent first - we need to hold that first click briefly
to see whether a second one follows before deciding which action to take.

This widget deliberately has no animation loop and no heavy painting, so it
costs effectively nothing while idle.
"""

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QWidget, QApplication, QPushButton, QVBoxLayout, QGraphicsDropShadowEffect
)

SIZE = 56
MARGIN_FROM_EDGE = 18
DRAG_THRESHOLD = 4  # pixels of movement before a press counts as a drag, not a click

ACTION_SIZE = 44
ACTION_GAP = 10


class QuickActionsMenu(QWidget):
    """Small floating popup with Mic / Transcript buttons, shown next to the
    orb on a single click. Talks directly to JarvisWindow - it never opens
    or needs the full GUI to be visible."""

    def __init__(self, main_window):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ACTION_GAP)

        self.mic_btn = self._make_action_button("\U0001F399", "Mic")
        self.transcript_btn = self._make_action_button("\U0001F4AC", "Transcript")
        self.cancel_btn = self._make_action_button(
            "\u2715", "Stop Jarvis", danger=True
        )

        self.mic_btn.clicked.connect(self._on_mic)
        self.transcript_btn.clicked.connect(self._on_transcript)
        self.cancel_btn.clicked.connect(self._on_cancel)

        layout.addWidget(self.mic_btn)
        layout.addWidget(self.transcript_btn)
        layout.addWidget(self.cancel_btn)

    def _make_action_button(self, glyph, tooltip, danger=False):
        btn = QPushButton(glyph)
        btn.setFixedSize(ACTION_SIZE, ACTION_SIZE)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)

        if danger:
            # Red-tinted variant for the stop/cancel button, so it reads as
            # distinct and a little "careful" compared to Mic/Transcript.
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(34, 12, 14, 235);
                    border: 1px solid rgba(230, 70, 80, 170);
                    border-radius: %dpx;
                    font-size: 16px;
                    color: rgb(255, 150, 150);
                }
                QPushButton:hover {
                    background-color: rgba(92, 20, 24, 235);
                    border: 1px solid rgba(255, 110, 110, 220);
                }
            """ % (ACTION_SIZE // 2))
            glow_color = QColor(255, 70, 70, 120)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(10, 30, 34, 235);
                    border: 1px solid rgba(0, 210, 230, 160);
                    border-radius: %dpx;
                    font-size: 17px;
                    color: rgb(170, 240, 255);
                }
                QPushButton:hover {
                    background-color: rgba(0, 80, 92, 235);
                    border: 1px solid rgba(120, 240, 255, 220);
                }
            """ % (ACTION_SIZE // 2))
            glow_color = QColor(0, 220, 255, 110)

        glow = QGraphicsDropShadowEffect()
        glow.setColor(glow_color)
        glow.setBlurRadius(20)
        glow.setOffset(0, 0)
        btn.setGraphicsEffect(glow)
        return btn

    # ------------------------------------------------------------------
    def _on_mic(self):
        self.hide()
        if self._main_window is not None and hasattr(self._main_window, "voice_command"):
            self._main_window.voice_command()

    def _on_transcript(self):
        self.hide()
        if self._main_window is not None and hasattr(self._main_window, "toggle_transcript"):
            self._main_window.toggle_transcript()

    def _on_cancel(self):
        """Stop the whole program - not just close this popup. Reuses
        JarvisWindow.command_finished(False), the same choke point voice
        commands like "exit" already use: it stops the background threads,
        closes the transcript panel and this orb, then quits the app. Falls
        back to a plain QApplication.quit() if that hook isn't there."""
        self.hide()
        if self._main_window is not None and hasattr(self._main_window, "command_finished"):
            self._main_window.command_finished(False)
        else:
            app = QApplication.instance()
            if app is not None:
                app.quit()

    # ------------------------------------------------------------------
    def reposition(self, anchor_rect):
        """anchor_rect: QRect (global coords) of the orb button this menu
        is attached to. Centers under/above the orb, flipping to whichever
        side actually has room on the current screen."""
        self.adjustSize()
        screen = QApplication.screenAt(anchor_rect.center()) or QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None

        x = anchor_rect.x() + (anchor_rect.width() - self.width()) // 2
        # Prefer opening upward (above the orb); flip below if no room.
        y = anchor_rect.y() - self.height() - ACTION_GAP
        if avail is not None:
            if y < avail.top():
                y = anchor_rect.bottom() + ACTION_GAP
            x = min(max(x, avail.left()), avail.right() - self.width())
        self.move(x, y)

    def close(self):
        self.hide()
        return super().close()


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

        self._quick_actions = QuickActionsMenu(main_window)

        # Manual single/double click disambiguation - see module docstring.
        self._pending_clicks = 0
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._handle_single_click)

        self._dock_to_right_edge()

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
    def paintEvent(self, event):
        """Paints a small glowing "arc reactor" orb - a dark housing, a
        segmented cyan turbine ring, and a bright core - instead of plain
        text, so the button reads as an AI/HUD icon at a glance."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = SIZE / 2, SIZE / 2
        outer_r = SIZE / 2 - 3

        # ---- Ambient outer glow ----
        glow = QRadialGradient(cx, cy, outer_r * 1.8)
        glow.setColorAt(0.0, QColor(0, 220, 255, 100))
        glow.setColorAt(1.0, QColor(0, 220, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(self.rect())

        # ---- Dark housing ----
        housing = QRadialGradient(cx, cy, outer_r)
        housing.setColorAt(0.0, QColor(20, 30, 34, 240))
        housing.setColorAt(1.0, QColor(6, 10, 12, 240))
        painter.setBrush(housing)
        painter.setPen(QPen(QColor(0, 220, 255, 150), 1.5))
        painter.drawEllipse(QPointF(cx, cy), outer_r, outer_r)

        # ---- Segmented turbine ring (arc-reactor blades) ----
        blade_r = outer_r - 6
        pen = QPen(QColor(120, 235, 255, 225))
        pen.setWidthF(4.0)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        segments = 8
        span_deg = 26
        blade_rect = QRectF(cx - blade_r, cy - blade_r, blade_r * 2, blade_r * 2)
        for i in range(segments):
            start_angle = int((360 / segments) * i * 16)
            painter.drawArc(blade_rect, start_angle, span_deg * 16)

        # ---- Bright glowing core ----
        core_r = outer_r * 0.42
        core = QRadialGradient(cx, cy, core_r)
        core.setColorAt(0.0, QColor(255, 255, 255, 255))
        core.setColorAt(0.35, QColor(150, 240, 255, 255))
        core.setColorAt(1.0, QColor(0, 180, 210, 50))
        painter.setPen(Qt.NoPen)
        painter.setBrush(core)
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)

        # ---- Center hot-spot ----
        painter.setBrush(QColor(255, 255, 255, 235))
        painter.drawEllipse(QPointF(cx, cy), core_r * 0.28, core_r * 0.28)

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
                # A drag is starting - don't leave a stale menu behind.
                self._quick_actions.hide()
            self.move(current - self._drag_offset)
            if self._quick_actions.isVisible():
                self._quick_actions.reposition(self.geometry())

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self._dragging:
            self._dragging = False
            self._keep_on_screen()
            return

        # Not a drag - queue this as a click and wait briefly to see if a
        # second one arrives (making it a double click).
        self._pending_clicks += 1
        if self._pending_clicks == 1:
            self._click_timer.start(QApplication.doubleClickInterval())
        else:
            self._click_timer.stop()
            self._pending_clicks = 0
            self._handle_double_click()

    # ------------------------------------------------------------------
    def _handle_single_click(self):
        self._pending_clicks = 0
        self.toggle_quick_actions()

    def _handle_double_click(self):
        self._quick_actions.hide()
        self.toggle_main_window()

    # ------------------------------------------------------------------
    def toggle_quick_actions(self):
        if self._quick_actions.isVisible():
            self._quick_actions.hide()
        else:
            self._quick_actions.reposition(self.geometry())
            self._quick_actions.show()
            self._quick_actions.raise_()

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
        self._click_timer.stop()
        if getattr(self, "_quick_actions", None) is not None:
            self._quick_actions.close()
        return super().close()
