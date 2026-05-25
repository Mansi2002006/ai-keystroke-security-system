import json
import math
import os
import subprocess
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

try:
    import winsound
except ImportError:
    winsound = None

try:
    from PIL import Image, ImageEnhance, ImageOps, ImageTk
except ImportError:
    Image = None
    ImageEnhance = None
    ImageOps = None
    ImageTk = None

from backend_utils import (
    authenticate_registered_user,
    get_dashboard_stats,
    list_registered_users,
    log_auth_attempt,
)


TARGET_TEXT = "secure123"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 760
METRICS_FILE = os.path.join("models", "metrics.json")
BACKGROUND_CANDIDATES = [
    os.path.join("assets", "cyber_bg.png"),
    os.path.join("assets", "cyber_bg.jpg"),
    os.path.join("assets", "cyber_bg.jpeg"),
    r"C:\Users\DELL\Downloads\poster4.png",
    r"C:\Users\DELL\Downloads\poster3.png",
]


class KeystrokeDashboard:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Keystroke Dynamics Login")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg="#050913")

        self.press_times: dict[str, float] = {}
        self.hold_times: list[float] = []
        self.selected_user = tk.StringVar()
        self.theme_mode = tk.StringVar(value="Dark")

        self.theme_presets = {
            "Dark": {
                "root_bg": "#050913",
                "card_bg": "#0d1b2d",
                "card_border": "#35cfff",
                "card_shadow": "#07101d",
                "panel_bg": "#10233a",
                "panel_border": "#42c8ff",
                "text_primary": "#f7fbff",
                "text_secondary": "#c3dbef",
                "accent": "#58d4ff",
                "accent_2": "#7b5cff",
                "entry_bg": "#0a1526",
                "entry_fg": "#ffffff",
                "entry_border": "#ffd347",
                "progress_bg": "#17263a",
                "progress_fill": "#00E6FF",
                "login_bg": "#ffd347",
                "login_fg": "#10243d",
                "reset_bg": "#1ca8ff",
                "reset_fg": "#ffffff",
                "success": "#b8ff66",
                "denied": "#ff7575",
                "status": "#6fd7ff",
                "overlay": "#050913",
            },
            "Light": {
                "root_bg": "#d9e8f5",
                "card_bg": "#f8fbff",
                "card_border": "#2f8bff",
                "card_shadow": "#b9cfe3",
                "panel_bg": "#edf5fb",
                "panel_border": "#4fc8ff",
                "text_primary": "#10243d",
                "text_secondary": "#36526f",
                "accent": "#1883ff",
                "accent_2": "#6f5cff",
                "entry_bg": "#ffffff",
                "entry_fg": "#10243d",
                "entry_border": "#ffbf1f",
                "progress_bg": "#d6e4f2",
                "progress_fill": "#2f8bff",
                "login_bg": "#ffcf2c",
                "login_fg": "#10243d",
                "reset_bg": "#25a7ff",
                "reset_fg": "#ffffff",
                "success": "#259c34",
                "denied": "#cc334d",
                "status": "#1274cf",
                "overlay": "#edf5fb",
            },
        }

        self.background_photo = None
        self.background_canvas: tk.Canvas | None = None
        self.network_nodes: list[dict] = []
        self.network_lines: list[int] = []
        self.network_step = 0
        self.fake_angle = 0
        self.arc_angle = 0
        self.scanner_angle = 0
        self.scan_line_direction = 1
        self.scan_line_y = 118
        self.title_glow_index = 0
        self.current_result_color = self.theme_presets["Dark"]["text_primary"]
        self.last_auth_result = "Awaiting authentication"

        self.display_font_family = self.resolve_display_font()
        self.canvas_font_family = self.resolve_display_font(preferred_only=True)

        self.background_container = tk.Frame(self.root, bg=self.theme_presets["Dark"]["root_bg"])
        self.background_container.place(x=0, y=0, relwidth=1, relheight=1)

        self.build_background()
        self.build_title()
        self.build_dashboard()
        self.refresh_user_profiles()
        self.refresh_metrics_panel()
        self.apply_theme()
        self.animate_network_background()
        self.animate_scanner()
        self.animate_fake_glow()
        self.animate_rotating_arc()
        self.animate_title_glow()

    def play_success_sound(self) -> None:
        if winsound is None:
            return
        try:
            winsound.Beep(880, 180)
            winsound.Beep(1046, 220)
            winsound.Beep(1318, 260)
        except Exception:
            pass

    def play_denied_sound(self) -> None:
        if winsound is None:
            return
        try:
            winsound.Beep(440, 260)
            winsound.Beep(330, 320)
        except Exception:
            pass

    def show_custom_result_popup(self, granted: bool, username: str = "") -> None:
        theme = self.theme_presets[self.theme_mode.get()]
        popup = tk.Toplevel(self.root)
        popup.transient(self.root)
        popup.grab_set()
        popup.resizable(False, False)
        popup.title("Authentication Result")
        popup.configure(bg=theme["panel_bg"])

        width = 430
        height = 240
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        pos_x = root_x + max(0, (root_w - width) // 2)
        pos_y = root_y + max(0, (root_h - height) // 2)
        popup.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        accent = theme["success"] if granted else theme["denied"]
        title_text = "CONGRATULATIONS! 🎉" if granted else "ACCESS DENIED 🚫"
        body_text = (
            f"Congratulations {username}!\nAccess Granted"
            if granted
            else "Pattern mismatch detected.\nAccess Denied"
        )

        outer = tk.Frame(popup, bg=accent, padx=2, pady=2)
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        inner = tk.Frame(outer, bg=theme["card_bg"])
        inner.pack(fill="both", expand=True)

        icon_text = "🎊" if granted else "⚠"
        tk.Label(
            inner,
            text=icon_text,
            font=("Segoe UI Emoji", 26),
            fg=accent,
            bg=theme["card_bg"],
        ).pack(pady=(16, 8))

        tk.Label(
            inner,
            text=title_text,
            font=("Segoe UI", 20, "bold"),
            fg=accent,
            bg=theme["card_bg"],
        ).pack()

        tk.Label(
            inner,
            text=body_text,
            font=("Segoe UI", 13, "bold"),
            fg=theme["text_primary"],
            bg=theme["card_bg"],
            justify="center",
        ).pack(pady=(12, 16))

        button = tk.Button(
            inner,
            text="OK",
            command=popup.destroy,
            font=("Segoe UI", 12, "bold"),
            bg=theme["login_bg"] if granted else theme["reset_bg"],
            fg=theme["login_fg"] if granted else theme["reset_fg"],
            relief="flat",
            padx=22,
            pady=8,
        )
        button.pack(pady=(0, 18))
        button.focus_set()
        popup.bind("<Return>", lambda _event: popup.destroy())
        popup.bind("<Escape>", lambda _event: popup.destroy())

    def speak_message(self, message: str) -> None:
        def _run() -> None:
            safe_message = message.replace("'", "''")
            command = (
                "$voice = New-Object -ComObject SAPI.SpVoice; "
                "$selected = $null; "
                "foreach ($v in $voice.GetVoices()) { "
                "  if ($v.GetDescription() -match 'Zira|female|Female') { $selected = $v; break } "
                "}; "
                "if ($selected -ne $null) { $voice.Voice = $selected }; "
                "$voice.Volume = 100; "
                "$voice.Rate = -1; "
                f"$voice.Speak('{safe_message}')"
            )
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

        threading.Thread(target=_run, daemon=True).start()

    def is_trackable_key(self, event) -> bool:
        if event.keysym in {"BackSpace", "Delete"}:
            return False
        if not getattr(event, "char", ""):
            return False
        return event.char.isprintable() and not event.char.isspace()

    def sync_capture_state(self) -> None:
        typed_length = min(len(self.entry.get().strip()), len(TARGET_TEXT))
        if typed_length == 0:
            self.hold_times.clear()
            self.press_times.clear()
        elif len(self.hold_times) > typed_length:
            self.hold_times = self.hold_times[:typed_length]
        self.progress_label.config(text=f"Typing progress: {typed_length}/{len(TARGET_TEXT)}")
        width = int((typed_length / len(TARGET_TEXT)) * 300)
        self.progress_canvas.coords(self.progress_fill, 0, 0, width, 10)

    def resolve_display_font(self, preferred_only: bool = False) -> str:
        available_fonts = {font.lower(): font for font in tkfont.families(self.root)}
        for preferred in ["Segoe UI", "Orbitron", "Bahnschrift SemiBold", "Eurostile", "Agency FB", "Arial"]:
            if preferred.lower() in available_fonts:
                return available_fonts[preferred.lower()]
        return "Segoe UI"

    def discover_background_path(self) -> str | None:
        for candidate in BACKGROUND_CANDIDATES:
            if os.path.exists(candidate):
                return candidate
        return None

    def build_background(self) -> None:
        self.background_canvas = tk.Canvas(
            self.background_container,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=self.theme_presets["Dark"]["root_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.background_canvas.place(x=0, y=0)

        background_path = self.discover_background_path()
        if False and Image is not None and ImageOps is not None and ImageTk is not None and background_path:
            image = Image.open(background_path).convert("RGB")
            image = ImageOps.fit(
                image,
                (WINDOW_WIDTH, WINDOW_HEIGHT),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.45),
            )
            if ImageEnhance is not None:
                image = ImageEnhance.Brightness(image).enhance(0.74)
            self.background_photo = ImageTk.PhotoImage(image)
            self.background_canvas.create_image(0, 0, image=self.background_photo, anchor="nw")
        else:
            self.background_canvas.create_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, fill="#050913", outline="")

        self.background_canvas.create_rectangle(
            0,
            0,
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            fill="#050913",
            outline="",
        )
        self.background_canvas.create_oval(-140, 500, 440, 980, fill="#081427", outline="")
        self.background_canvas.create_oval(760, -150, 1400, 420, fill="#10092a", outline="")
        self.background_canvas.create_oval(900, 420, 1500, 980, fill="#09162d", outline="")
        self.background_canvas.create_oval(390, 210, 930, 720, fill="#061120", outline="")

        node_positions = [
            (80, 125), (145, 92), (225, 130), (300, 86), (380, 142),
            (905, 108), (990, 86), (1075, 130), (1160, 95), (1230, 150),
            (800, 585), (885, 540), (965, 595), (1040, 545), (1120, 610),
            (170, 610), (245, 560), (330, 625), (405, 575), (490, 645),
            (565, 320), (640, 280), (715, 340), (790, 290), (865, 350),
        ]
        edge_pairs = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (5, 6), (6, 7), (7, 8), (8, 9),
            (10, 11), (11, 12), (12, 13), (13, 14),
            (15, 16), (16, 17), (17, 18), (18, 19),
            (20, 21), (21, 22), (22, 23), (23, 24),
            (2, 20), (3, 21), (4, 22), (7, 22), (8, 23),
            (12, 23), (13, 24), (17, 20), (18, 21), (19, 22),
            (5, 21), (9, 24), (10, 24), (15, 20),
        ]
        node_colors = ["#1dd4ff", "#39a8ff", "#7f5cff", "#40f0c6", "#a65aff"]

        for start_index, end_index in edge_pairs:
            x1, y1 = node_positions[start_index]
            x2, y2 = node_positions[end_index]
            line = self.background_canvas.create_line(x1, y1, x2, y2, fill="#183452", width=2)
            self.network_lines.append(line)

        for index, (x, y) in enumerate(node_positions):
            glow = self.background_canvas.create_oval(x - 12, y - 12, x + 12, y + 12, outline="#143150", width=2)
            node = self.background_canvas.create_oval(
                x - 4,
                y - 4,
                x + 4,
                y + 4,
                fill=node_colors[index % len(node_colors)],
                outline="",
            )
            self.network_nodes.append(
                {
                    "glow": glow,
                    "node": node,
                    "base": node_colors[index % len(node_colors)],
                    "position": (x, y),
                }
            )

        self.background_canvas.create_line(210, 125, 320, 125, fill="#37c8ff", width=2)
        self.background_canvas.create_line(960, 125, 1070, 125, fill="#37c8ff", width=2)
        self.background_canvas.create_text(330, 125, text="•", fill="#dbefff", font=("Arial", 18, "bold"))
        self.background_canvas.create_text(950, 125, text="•", fill="#dbefff", font=("Arial", 18, "bold"))

    def build_title(self) -> None:
        self.title_outer = tk.Frame(self.root, bg="#57cfff", padx=1, pady=1)
        self.title_outer.place(x=120, y=42, width=1040, height=110)

        self.title_frame = tk.Frame(self.title_outer, bg="#163056")
        self.title_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.title_label = tk.Label(
            self.title_frame,
            text="AI-Based Secure Authentication System",
            font=(self.display_font_family, 30, "bold"),
            fg="#00E6FF",
            bg="#163056",
        )
        self.title_label.pack(pady=(14, 2))

        self.subtitle_label = tk.Label(
            self.title_frame,
            text="Advanced behavioral biometric login using keystroke dynamics",
            font=(self.display_font_family, 12),
            fg="#9fddff",
            bg="#163056",
        )
        self.subtitle_label.pack()

    def build_dashboard(self) -> None:
        self.main_outer = tk.Frame(self.root, bg="#56cfff", padx=1, pady=1)
        self.main_outer.place(x=85, y=188, width=1110, height=520)

        self.main_card = tk.Frame(self.main_outer, bg="#132845")
        self.main_card.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.left_panel = tk.Frame(self.main_card, bg="#132845")
        self.left_panel.place(x=40, y=40, width=620, height=455)

        self.right_panel = tk.Frame(self.main_card, bg="#10233d")
        self.right_panel.place(x=770, y=34, width=285, height=420)

        self.build_left_panel()
        self.build_right_panel()

    def build_left_panel(self) -> None:
        self.instruction_label = tk.Label(
            self.left_panel,
            text=f"Type this text exactly: {TARGET_TEXT}",
            font=("Segoe UI", 20, "bold"),
            fg="#f5fbff",
            bg="#132845",
        )
        self.instruction_label.pack(anchor="w")

        controls = tk.Frame(self.left_panel, bg="#132845")
        controls.pack(anchor="w", pady=(20, 10))

        self.profile_label = tk.Label(
            controls,
            text="User Profile",
            font=("Segoe UI", 13, "bold"),
            fg="#dcefff",
            bg="#132845",
        )
        self.profile_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.user_combo = ttk.Combobox(
            controls,
            textvariable=self.selected_user,
            state="readonly",
            width=16,
        )
        self.user_combo.grid(row=0, column=1, padx=(0, 12))

        self.refresh_button = tk.Button(
            controls,
            text="Refresh",
            command=self.refresh_user_profiles,
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=16,
            pady=6,
        )
        self.refresh_button.grid(row=0, column=2, padx=(0, 12))

        self.theme_combo = ttk.Combobox(
            controls,
            textvariable=self.theme_mode,
            values=["Dark", "Light"],
            state="readonly",
            width=10,
        )
        self.theme_combo.grid(row=0, column=3)
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)

        self.helper_label = tk.Label(
            self.left_panel,
            text="The AI model checks typing rhythm, key hold time, and behavior confidence.",
            font=("Segoe UI", 11),
            fg="#c5dbef",
            bg="#132845",
        )
        self.helper_label.pack(anchor="w", pady=(12, 18))

        self.entry_glow = tk.Frame(self.left_panel, bg="#ffd347", padx=3, pady=3)
        self.entry_glow.pack(anchor="w", pady=(0, 18))

        self.entry_outer = tk.Frame(self.entry_glow, bg="#214872")
        self.entry_outer.pack()

        self.entry = tk.Entry(
            self.entry_outer,
            font=("Segoe UI", 22, "bold"),
            width=22,
            bg="#0f1c2e",
            fg="white",
            insertbackground="white",
            bd=2,
            relief="solid",
            highlightthickness=2,
            insertwidth=3,
        )
        self.entry.pack(ipadx=12, ipady=11)
        self.entry.bind("<KeyPress>", self.on_key_press)
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.focus_set()

        self.progress_label = tk.Label(
            self.left_panel,
            text=f"Typing progress: 0/{len(TARGET_TEXT)}",
            font=("Segoe UI", 11),
            fg="#58d4ff",
            bg="#132845",
        )
        self.progress_label.pack(anchor="w", pady=(0, 6))

        self.progress_canvas = tk.Canvas(self.left_panel, width=300, height=10, highlightthickness=0, bd=0, bg="#1a2a3a")
        self.progress_canvas.pack(anchor="w", pady=(0, 28))
        self.progress_track = self.progress_canvas.create_rectangle(0, 0, 300, 10, fill="#1a2a3a", outline="")
        self.progress_fill = self.progress_canvas.create_rectangle(0, 0, 0, 10, fill="#00E6FF", outline="")

        button_row = tk.Frame(self.left_panel, bg="#132845")
        button_row.pack(anchor="w", pady=(8, 24))

        self.login_button = tk.Button(
            button_row,
            text="Login",
            command=self.authenticate_user,
            font=("Segoe UI", 18, "bold"),
            bg="#FFD54F",
            fg="black",
            activebackground="#FFC107",
            relief="flat",
            width=11,
            padx=20,
            pady=10,
        )
        self.login_button.pack(side="left", padx=(0, 14))

        self.reset_button = tk.Button(
            button_row,
            text="Reset",
            command=self.reset_form,
            font=("Segoe UI", 18),
            relief="flat",
            width=11,
            pady=10,
        )
        self.reset_button.pack(side="left")

        self.status_label = tk.Label(
            self.left_panel,
            text="System ready",
            font=("Segoe UI", 12, "italic"),
            fg="#74d8ff",
            bg="#132845",
        )
        self.status_label.pack(anchor="w", pady=(0, 16))

        self.result_label = tk.Label(
            self.left_panel,
            text="Awaiting authentication",
            font=("Segoe UI", 20, "bold"),
            fg="#f1faee",
            bg="#132845",
        )
        self.result_label.pack(anchor="w")

        self.confidence_label = tk.Label(
            self.left_panel,
            text="Confidence: 0.00%",
            font=("Segoe UI", 13),
            fg="#f2fbff",
            bg="#132845",
        )
        self.confidence_label.pack(anchor="w", pady=(12, 6))

        self.details_label = tk.Label(
            self.left_panel,
            text="Profile similarity: 0.00% | Best model: --",
            font=("Segoe UI", 11),
            fg="#b7d3e7",
            bg="#132845",
        )
        self.details_label.pack(anchor="w")

    def build_right_panel(self) -> None:
        self.scanner_canvas = tk.Canvas(
            self.right_panel,
            width=255,
            height=205,
            bg="#10233d",
            highlightthickness=0,
            bd=0,
        )
        self.scanner_canvas.pack(pady=(8, 12))

        self.outer_ring = self.scanner_canvas.create_oval(38, 25, 218, 205, outline="#52d8ff", width=3)
        self.middle_ring = self.scanner_canvas.create_oval(56, 43, 200, 187, outline="#7b5cff", width=2)
        self.inner_ring = self.scanner_canvas.create_oval(72, 59, 184, 171, outline="#29efba", width=2)
        self.arc_ring = self.scanner_canvas.create_arc(
            28, 15, 228, 215,
            start=0,
            extent=300,
            outline="#00E6FF",
            width=3,
            style="arc",
        )
        self.lock_body = self.scanner_canvas.create_rectangle(105, 100, 150, 142, outline="#ffffff", width=3)
        self.lock_arc = self.scanner_canvas.create_arc(110, 72, 145, 107, start=0, extent=180, style="arc", outline="#ffffff", width=3)
        self.keyhole_top = self.scanner_canvas.create_oval(124, 113, 131, 120, fill="#ffffff", outline="")
        self.keyhole_stem = self.scanner_canvas.create_rectangle(126, 119, 129, 130, fill="#ffffff", outline="")
        self.scan_line = self.scanner_canvas.create_line(56, 115, 200, 115, fill="#ffd347", width=4)
        self.orbit_dot = self.scanner_canvas.create_oval(213, 109, 224, 120, fill="#59d6ff", outline="")

        self.live_title = tk.Label(
            self.right_panel,
            text="Live Status",
            font=("Segoe UI", 18, "bold"),
            fg="#f7fbff",
            bg="#10233d",
        )
        self.live_title.pack(pady=(2, 12))

        self.live_items = {}
        for key, default in [
            ("Model loaded", "Yes"),
            ("Typing pattern scan", "Active"),
            ("Confidence score", "0.00%"),
            ("Best model name", "--"),
        ]:
            row = tk.Frame(self.right_panel, bg="#10233d")
            row.pack(anchor="w", pady=4, padx=24)
            label = tk.Label(row, text=f"{key}:", font=("Segoe UI", 11, "bold"), fg="#dcefff", bg="#10233d")
            label.pack(anchor="w")
            value = tk.Label(row, text=default, font=("Segoe UI", 11), fg="#00FFAA", bg="#10233d")
            value.pack(anchor="w")
            self.live_items[key] = value

    def on_theme_change(self, _event=None) -> None:
        self.apply_theme()

    def apply_theme(self) -> None:
        theme = self.theme_presets[self.theme_mode.get()]

        self.root.configure(bg=theme["root_bg"])
        self.title_outer.config(bg=theme["card_border"])
        self.title_frame.config(bg=theme["panel_bg"])
        self.title_label.config(bg=theme["panel_bg"], fg=theme["text_primary"])
        self.subtitle_label.config(bg=theme["panel_bg"], fg=theme["accent"])

        self.main_outer.config(bg=theme["card_border"])
        self.main_card.config(bg=theme["card_bg"])
        self.left_panel.config(bg=theme["card_bg"])
        self.right_panel.config(bg=theme["panel_bg"])

        for widget in [
            self.instruction_label,
            self.profile_label,
            self.helper_label,
            self.progress_label,
            self.status_label,
            self.result_label,
            self.confidence_label,
            self.details_label,
        ]:
            widget.configure(bg=theme["card_bg"])

        self.instruction_label.config(fg=theme["text_primary"])
        self.profile_label.config(fg=theme["text_secondary"])
        self.helper_label.config(fg=theme["text_secondary"])
        self.progress_label.config(fg=theme["accent"])
        self.status_label.config(fg=theme["status"])
        self.result_label.config(fg=self.current_result_color if self.current_result_color != theme["text_primary"] else theme["text_primary"])
        self.confidence_label.config(fg=theme["text_primary"])
        self.details_label.config(fg=theme["text_secondary"])

        self.entry_glow.config(bg=theme["entry_border"])
        self.entry_outer.config(bg=theme["panel_border"])
        self.entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["accent"])
        self.entry.config(highlightbackground=theme["entry_border"], highlightcolor=theme["entry_border"])

        self.progress_canvas.config(bg="#1a2a3a")
        self.progress_canvas.itemconfig(self.progress_track, fill=theme["progress_bg"])
        self.progress_canvas.itemconfig(self.progress_fill, fill=theme["progress_fill"])

        self.login_button.config(bg=theme["login_bg"], fg=theme["login_fg"], activebackground=theme["login_bg"])
        self.reset_button.config(bg=theme["reset_bg"], fg=theme["reset_fg"], activebackground=theme["reset_bg"])

        self.scanner_canvas.config(bg=theme["panel_bg"])
        self.scanner_canvas.itemconfig(self.outer_ring, outline="#4fd3ff")
        self.scanner_canvas.itemconfig(self.middle_ring, outline="#ab6cff")
        self.scanner_canvas.itemconfig(self.inner_ring, outline="#2aefba")
        self.scanner_canvas.itemconfig(self.scan_line, fill="#ffd347")
        self.scanner_canvas.itemconfig(self.orbit_dot, fill="#4fd3ff")

        self.live_title.config(bg=theme["panel_bg"], fg=theme["text_primary"])
        for child in self.right_panel.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(bg=theme["panel_bg"])
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, tk.Label):
                        if grandchild.cget("text").endswith(":"):
                            grandchild.config(bg=theme["panel_bg"], fg=theme["text_secondary"])
                        else:
                            grandchild.config(bg=theme["panel_bg"], fg=theme["accent"])

    def refresh_user_profiles(self) -> None:
        profiles = list_registered_users()
        self.user_combo["values"] = profiles
        if profiles:
            self.user_combo.current(0)
        else:
            self.user_combo.set("")

    def refresh_metrics_panel(self) -> None:
        best_model = "--"
        accuracy = 0.0
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, "r", encoding="utf-8") as file:
                    metrics = json.load(file)
                best_model = metrics.get("best_model", "--")
                accuracy = metrics.get("accuracy", 0.0) * 100
            except (OSError, json.JSONDecodeError):
                best_model = "--"
                accuracy = 0.0

        stats = get_dashboard_stats()
        self.live_items["Model loaded"].config(text="Yes" if os.path.exists(os.path.join("models", "model.pkl")) else "No")
        self.live_items["Typing pattern scan"].config(text="Active")
        self.live_items["Confidence score"].config(text="0.00%")
        self.live_items["Best model name"].config(text=f"{best_model} | {accuracy:.2f}%")
        self.details_label.config(
            text=f"Profile similarity: 0.00% | Best model: {best_model} | Users: {stats['total_users']}"
        )

    def on_key_press(self, event) -> None:
        if event.widget is not self.entry:
            return
        if event.keysym in {"BackSpace", "Delete"}:
            self.press_times.clear()
            self.hold_times.clear()
            self.root.after(10, self.sync_capture_state)
            return
        if not self.is_trackable_key(event):
            return
        self.press_times[event.keysym] = time.time()
        self.status_label.config(text="Capturing keystroke timing...")

    def on_key_release(self, event) -> None:
        if event.widget is not self.entry:
            return
        if event.keysym in {"BackSpace", "Delete"}:
            self.sync_capture_state()
            return
        if not self.is_trackable_key(event):
            return
        if event.keysym not in self.press_times:
            return
        hold_time = time.time() - self.press_times[event.keysym]
        self.hold_times.append(round(hold_time, 6))
        self.sync_capture_state()

    def update_progress(self) -> None:
        self.sync_capture_state()

    def reset_form(self) -> None:
        self.entry.delete(0, tk.END)
        self.press_times.clear()
        self.hold_times.clear()
        self.sync_capture_state()
        self.status_label.config(text="System ready")
        self.result_label.config(text="Awaiting authentication")
        self.current_result_color = self.theme_presets[self.theme_mode.get()]["text_primary"]
        self.result_label.config(fg=self.current_result_color)
        self.confidence_label.config(text="Confidence: 0.00%")
        best_model_text = self.live_items["Best model name"].cget("text").split("|")[0].strip()
        self.details_label.config(text=f"Profile similarity: 0.00% | Best model: {best_model_text}")
        self.live_items["Confidence score"].config(text="0.00%")
        self.entry.focus_set()

    def authenticate_user(self) -> None:
        model_path = os.path.join("models", "model.pkl")
        if not os.path.exists(model_path):
            messagebox.showerror("Model Missing", "Run train_model.py first to create the trained model.")
            return

        username = self.selected_user.get().strip()
        if not username:
            messagebox.showwarning("Missing User", "Please select a registered user profile.")
            return

        typed_text = self.entry.get().strip()
        self.sync_capture_state()
        if typed_text != TARGET_TEXT:
            self.show_result(
                granted=False,
                confidence=0.0,
                profile_similarity=0.0,
                best_model="Input validation",
                reason="Typed text mismatch",
            )
            messagebox.showwarning("Authentication Failed", "Type the exact text secure123 before clicking Login.")
            return

        if len(self.hold_times) < len(TARGET_TEXT):
            self.show_result(
                granted=False,
                confidence=0.0,
                profile_similarity=0.0,
                best_model="Input validation",
                reason=f"Incomplete typing sample ({len(self.hold_times)}/{len(TARGET_TEXT)})",
            )
            messagebox.showwarning(
                "Authentication Failed",
                "Typing sample is incomplete. Please type directly in the box once from start to finish.",
            )
            return

        self.status_label.config(text="Analyzing typing pattern...")
        self.result_label.config(text="Running AI verification...", fg=self.theme_presets[self.theme_mode.get()]["accent"])
        self.root.update_idletasks()

        sample = self.hold_times[: len(TARGET_TEXT)]
        try:
            result = authenticate_registered_user(username, sample, adaptive_learning=True)
        except Exception as exc:
            self.show_result(
                granted=False,
                confidence=0.0,
                profile_similarity=0.0,
                best_model="Backend error",
                reason="Authentication engine error",
            )
            messagebox.showerror("Authentication Error", f"The authentication engine failed:\n{exc}")
            return

        granted = result["prediction"] == 1
        log_auth_attempt(
            "Access Granted" if granted else "Access Denied",
            result["confidence"],
            result["genuine_probability"],
            result["best_model"],
            username=username,
        )
        self.show_result(
            granted=granted,
            confidence=result["confidence"] * 100,
            profile_similarity=result["profile_similarity"] * 100,
            best_model=result["best_model"],
            reason="User verified" if granted else "Pattern mismatch detected",
        )
        if granted:
            self.play_success_sound()
            self.speak_message(f"Congratulations {username}. Access granted.")
            self.show_custom_result_popup(True, username=username)
        else:
            self.play_denied_sound()
            self.speak_message("Warning. Access denied.")
            self.show_custom_result_popup(False, username=username)

        self.hold_times.clear()
        self.press_times.clear()

    def show_result(self, granted: bool, confidence: float, profile_similarity: float, best_model: str, reason: str) -> None:
        theme = self.theme_presets[self.theme_mode.get()]
        if granted:
            self.current_result_color = theme["success"]
            self.result_label.config(text=f"CONGRATULATIONS! ACCESS GRANTED 🎉 ({confidence:.2f}%)", fg=theme["success"])
            self.status_label.config(text="System ready")
        else:
            self.current_result_color = theme["denied"]
            self.result_label.config(text=f"ACCESS DENIED 🚫 ({confidence:.2f}%)", fg=theme["denied"])
            self.status_label.config(text=reason)

        self.confidence_label.config(text=f"Confidence: {confidence:.2f}%")
        self.details_label.config(text=f"Profile similarity: {profile_similarity:.2f}% | Best model: {best_model}")
        self.live_items["Confidence score"].config(text=f"{confidence:.2f}%")
        self.live_items["Best model name"].config(text=best_model)

    def animate_scanner(self) -> None:
        self.scanner_angle = (self.scanner_angle + 5) % 360
        radius = 90
        center_x = 128
        center_y = 115
        x = center_x + radius * math.cos(math.radians(self.scanner_angle))
        y = center_y + radius * math.sin(math.radians(self.scanner_angle))
        self.scanner_canvas.coords(self.orbit_dot, x - 5, y - 5, x + 5, y + 5)

        self.scan_line_y += 2 * self.scan_line_direction
        if self.scan_line_y >= 145:
            self.scan_line_direction = -1
        elif self.scan_line_y <= 88:
            self.scan_line_direction = 1
        self.scanner_canvas.coords(self.scan_line, 56, self.scan_line_y, 200, self.scan_line_y)

        pulse = (math.sin(math.radians(self.scanner_angle * 2)) + 1) / 2
        width = 2 + pulse
        self.scanner_canvas.itemconfig(self.outer_ring, width=width)
        self.scanner_canvas.itemconfig(self.middle_ring, width=1.5 + pulse * 0.7)

        self.root.after(55, self.animate_scanner)

    def animate_fake_glow(self) -> None:
        self.fake_angle = (self.fake_angle + 5) % 360
        pulse = (math.sin(math.radians(self.fake_angle)) + 1) / 2
        extra = 8 + (pulse * 10)
        self.scanner_canvas.delete("circle_glow")
        self.scanner_canvas.create_oval(
            38 - extra,
            25 - extra,
            218 + extra,
            205 + extra,
            outline="#00FFFF",
            width=2,
            tags="circle_glow",
        )
        self.scanner_canvas.tag_lower("circle_glow")
        self.root.after(100, self.animate_fake_glow)

    def animate_rotating_arc(self) -> None:
        self.arc_angle = (self.arc_angle + 10) % 360
        self.scanner_canvas.itemconfig(self.arc_ring, start=self.arc_angle)
        self.root.after(80, self.animate_rotating_arc)

    def animate_network_background(self) -> None:
        self.network_step = (self.network_step + 1) % len(self.network_nodes)
        active_nodes = {
            self.network_step,
            (self.network_step + 6) % len(self.network_nodes),
            (self.network_step + 13) % len(self.network_nodes),
        }
        for index, item in enumerate(self.network_nodes):
            if index in active_nodes:
                self.background_canvas.itemconfig(item["glow"], outline="#52d8ff", width=3)
                self.background_canvas.itemconfig(item["node"], fill="#effbff")
            else:
                self.background_canvas.itemconfig(item["glow"], outline="#173b67", width=2)
                self.background_canvas.itemconfig(item["node"], fill=item["base"])
        self.root.after(220, self.animate_network_background)

    def animate_title_glow(self) -> None:
        colors = ["#dff7ff", "#bfefff", "#ffffff", "#cfefff"]
        self.title_label.config(fg=colors[self.title_glow_index % len(colors)])
        self.title_glow_index += 1
        self.root.after(700, self.animate_title_glow)


def main() -> None:
    root = tk.Tk()
    KeystrokeDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
