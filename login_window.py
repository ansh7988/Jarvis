"""
login_window.py

A standalone "JARVIS SECURITY" login screen built with CustomTkinter,
matching the black + glowing-cyan HUD theme used throughout the rest of
the Jarvis app (same cyan as JGUI.py's QColor(0, 220, 255) accents, same
Consolas font family, same dark-glass panel feel).

No authentication logic lives here on purpose - LoginWindow only owns the
UI. `on_unlock` is left as a stub with a single TODO marking exactly where
password verification should be wired in later. Everything else (reading
the password, toggling its visibility, updating the status label) is
already fully working.

Run directly to preview the window:
    python login_window.py
"""

import tkinter as tk
import customtkinter as ctk

from voice import speak
from voice import speak

# ---------------------------------------------------------------------------
# Theme tokens - kept in one place so the whole window stays consistent with
# the rest of Jarvis's black/cyan look.
# ---------------------------------------------------------------------------
BG_COLOR = "#05080a"          # near-black window background
PANEL_COLOR = "#0a1418"       # slightly-lifted card/entry background
BORDER_COLOR = "#0f2830"      # dim cyan border for idle inputs

CYAN = "#00dcff"              # primary glow accent (matches rgb(0,220,255))
CYAN_BRIGHT = "#aef4ff"       # near-white cyan for hot highlights / core
CYAN_DIM = "#0f6c80"          # muted cyan for secondary text / dim glow
TEXT_MAIN = "#eaf6f8"
TEXT_MUTED = "#7f97a3"

FONT_FAMILY = "Consolas"      # same family JGUI.py uses throughout

WINDOW_W, WINDOW_H = 500, 350
ORB_SIZE = 96


def _blend(hex_a, hex_b, t):
    """Linear-interpolate between two hex colors (t=0 -> a, t=1 -> b).
    Used to fake soft glow falloff on a plain Tk Canvas, which has no real
    alpha compositing - each "glow ring" is really just a solid color
    blended partway toward the background."""
    a = tuple(int(hex_a[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(hex_b[i:i + 2], 16) for i in (1, 3, 5))
    rgb = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return "#%02x%02x%02x" % rgb


class LoginWindow(ctk.CTk):
    """Self-contained JARVIS login screen. All UI lives in this class -
    construct it and call .mainloop() to show it."""

    def __init__(self):
        super().__init__(fg_color=BG_COLOR)

        ctk.set_appearance_mode("dark")

        self.title("Jarvis Security")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        self._password_visible = False

        self._center_on_screen()
        self._build_ui()

        # Enter triggers the same action as clicking the unlock button,
        # no matter which widget currently has focus.
        self.bind("<Return>", self._on_unlock_event)

    # ------------------------------------------------------------------
    def _center_on_screen(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - WINDOW_W) // 2
        y = (screen_h - WINDOW_H) // 2
        self.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = ctk.CTkFrame(self, fg_color=BG_COLOR)
        root.pack(fill="both", expand=True, padx=28, pady=(20, 18))

        self._build_orb(root)
        self._build_headings(root)
        self._build_password_row(root)
        self._build_unlock_button(root)
        self._build_status_label(root)

    # ------------------------------------------------------------------
    def _build_orb(self, parent):
        """Small glowing 'arc reactor' orb - concentric blended rings plus
        a segmented cyan ring and a bright core, all drawn on a plain
        Canvas so no image assets are needed."""
        canvas = tk.Canvas(
            parent, width=ORB_SIZE, height=ORB_SIZE,
            bg=BG_COLOR, highlightthickness=0, bd=0
        )
        canvas.pack(pady=(0, 6))

        cx = cy = ORB_SIZE / 2

        # Soft outer glow: several rings blended from the background color
        # up toward bright cyan as they shrink toward the center.
        glow_steps = 10
        max_r = ORB_SIZE / 2
        for i in range(glow_steps, 0, -1):
            r = max_r * (i / glow_steps)
            t = 1 - (i / glow_steps)  # 0 at the outer edge, 1 near center
            color = _blend(BG_COLOR, CYAN, t * 0.55)
            canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline="", fill=color
            )

        # Dark housing ring (like the arc-reactor casing).
        housing_r = max_r * 0.62
        canvas.create_oval(
            cx - housing_r, cy - housing_r, cx + housing_r, cy + housing_r,
            outline=CYAN, width=1, fill="#0a1518"
        )

        # Segmented tick ring.
        seg_r = housing_r - 4
        segments = 10
        for i in range(segments):
            start = (360 / segments) * i
            canvas.create_arc(
                cx - seg_r, cy - seg_r, cx + seg_r, cy + seg_r,
                start=start, extent=14, style="arc",
                outline=CYAN, width=2
            )

        # Bright pulsing-looking core (static, but blended white -> cyan).
        core_r = housing_r * 0.42
        for i in range(6, 0, -1):
            r = core_r * (i / 6)
            t = 1 - (i / 6)
            color = _blend(CYAN, CYAN_BRIGHT, t)
            canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline="", fill=color
            )

        self.orb_canvas = canvas

    # ------------------------------------------------------------------
    def _build_headings(self, parent):
        title = ctk.CTkLabel(
            parent,
            text="JARVIS SECURITY",
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color=CYAN_BRIGHT,
        )
        title.pack(pady=(0, 2))

        subtitle = ctk.CTkLabel(
            parent,
            text="Secure Authentication Required",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_MUTED,
        )
        subtitle.pack(pady=(0, 18))

    # ------------------------------------------------------------------
    def _build_password_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(pady=(0, 16))

        self.password_entry = ctk.CTkEntry(
            row,
            width=280, height=40,
            corner_radius=10,
            placeholder_text="Enter Password",
            show="*",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=PANEL_COLOR,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_MAIN,
        )
        self.password_entry.grid(row=0, column=0, padx=(0, 8))
        self.password_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.password_entry.bind("<FocusOut>", self._on_entry_focus_out)

        self.eye_button = ctk.CTkButton(
            row,
            text="\U0001F441",  # 👁
            width=40, height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=15),
            fg_color=PANEL_COLOR,
            hover_color=CYAN_DIM,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=CYAN,
            command=self._toggle_password_visibility,
        )
        self.eye_button.grid(row=0, column=1)

    def _on_entry_focus_in(self, _event=None):
        self.password_entry.configure(border_color=CYAN)

    def _on_entry_focus_out(self, _event=None):
        self.password_entry.configure(border_color=BORDER_COLOR)

    def _toggle_password_visibility(self):
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.password_entry.configure(show="")
            self.eye_button.configure(text="\U0001F576")  # 🕶 ("hidden" state icon)
        else:
            self.password_entry.configure(show="*")
            self.eye_button.configure(text="\U0001F441")  # 👁

    # ------------------------------------------------------------------
    def _build_unlock_button(self, parent):
        self.unlock_button = ctk.CTkButton(
            parent,
            text="UNLOCK JARVIS",
            width=280, height=42,
            corner_radius=12,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            fg_color=CYAN_DIM,
            hover_color=CYAN,
            text_color="#04191e",
            border_color=CYAN,
            border_width=1,
            command=self._on_unlock,
        )
        self.unlock_button.pack(pady=(2, 10))

    # ------------------------------------------------------------------
    def _build_status_label(self, parent):
        self.status_label = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=TEXT_MUTED,
        )
        self.status_label.pack(pady=(0, 0))

    # ------------------------------------------------------------------
    def set_status(self, message, success=None):
        """Public helper for whatever wires up auth later:
            self.set_status("Access Granted", success=True)
            self.set_status("Incorrect Password", success=False)
        success=None keeps the neutral/muted color."""
        if success is True:
            color = CYAN_BRIGHT
        elif success is False:
            color = "#ff6b6b"
        else:
            color = TEXT_MUTED
        self.status_label.configure(text=message, text_color=color)

    # ------------------------------------------------------------------
    def _on_unlock_event(self, _event=None):
        self._on_unlock()
    
    def _on_unlock(self):
        password = self.password_entry.get()

        if password == "PASSWORD":
            self.set_status("Access Granted", success=True)

            speak("Authentication successful. Welcome to Jarvis.")
            speak("Starting Jarvis.")

            self.after(2000, self.start_jarvis)

        else:
            self.set_status("Incorrect Password", success=False)
            speak("Incorrect password. Please try again.")

    def start_jarvis(self):
        import subprocess
        import sys

        subprocess.Popen(["py", "-3.12", "JGUI.py"])
        self.destroy()

if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
