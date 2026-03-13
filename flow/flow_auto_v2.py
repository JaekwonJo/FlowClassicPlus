import json
import os
import time
import random
import threading
import queue
import re
import calendar
import traceback 
from pathlib import Path
from datetime import datetime, timedelta
import importlib 

# [CRITICAL] 윈도우/리눅스(WSL) 호환성 체크
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    pystray = None
    Image = None
    TRAY_AVAILABLE = False

# [Playwright 핵심 모듈]
from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)
try:
    from playwright_stealth import stealth_sync
except ImportError:
    try:
        from playwright_stealth import Stealth

        def stealth_sync(page):
            try:
                Stealth().apply_stealth_sync(page)
            except Exception:
                return None
    except ImportError:
        def stealth_sync(_page):
            return None

# [NEW] 인간 행동 엔진 탑재
try:
    import flow.human_behavior_v2 as hb
    importlib.reload(hb) 
    from flow.human_behavior_v2 import HumanActor
except ImportError:
    from flow.human_behavior_v2 import HumanActor

# --- 윈도우 절전 방지 ---
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

APP_VERSION = "2026-03-03 Ver.01"
APP_NAME = f"Flow Classic Plus - {APP_VERSION}"
CONFIG_FILE = "flow_config.json"
DEFAULT_CONFIG = {
    "prompts_file": "flow_prompts.txt",
    "prompts_separator": "|||",
    "interval_seconds": 180,
    "start_url": "https://labs.google/flow",
    "input_selector": "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [role='textbox'], [contenteditable='true']",
    "submit_selector": "button[type='submit']",
    "auto_open_new_project": True,
    "new_project_selector": "",
    "browser_headless": False,
    "browser_channel": "chrome",
    "browser_profile_dir": "flow_human_profile_pw",
    "input_area": None,  # 구버전 호환용(미사용)
    "submit_area": None,  # 구버전 호환용(미사용)
    "afk_area": None,  # 구버전 호환용(미사용)
    "afk_mode": False,
    "prompt_slots": [],
    "active_prompt_slot": 0,
    "sound_enabled": True,
    "project_profiles": [],
    "active_project_profile": 0,
    "pipeline_steps": [],
    "active_pipeline_step": 0,
    "relay_mode": False,
    "relay_count": 1,
    "relay_start_slot": None,
    "relay_end_slot": None,
    "relay_use_selection": False,
    "relay_selected_slots": [],
    "scheduled_start_enabled": False,
    "scheduled_start_at": "",
    "language_mode": "en",
    "input_mode": "typing", # typing, paste, mixed
    "typing_speed_profile": "x5",
    "prompt_mode_preset_enabled": True,
    "prompt_media_mode": "image",
    "prompt_orientation": "landscape",
    "prompt_variant_count": "x1",
    "prompt_reference_enabled": False,
    "prompt_reference_items": [],
    "prompt_reference_test_tag": "S999",
    "prompt_reference_search_input_selector": "",
    "prompt_reference_result_selector": "",
    "prompt_media_mode_selector": "",
    "prompt_orientation_selector": "",
    "prompt_variant_selector": "",
    "prompt_image_panel_selector": "",
    "prompt_video_panel_selector": "",
    "asset_prompt_mode_preset_enabled": True,
    "asset_prompt_media_mode": "video",
    "asset_prompt_orientation": "landscape",
    "asset_prompt_variant_count": "x1",
    "asset_prompt_media_mode_selector": "",
    "asset_prompt_orientation_selector": "",
    "asset_prompt_variant_selector": "",
    "asset_prompt_image_panel_selector": "",
    "asset_prompt_video_panel_selector": "",
    "asset_loop_enabled": False,
    "asset_loop_start": 1,
    "asset_loop_end": 1,
    "asset_loop_num_width": 3,
    "asset_loop_prefix": "S",
    "asset_loop_prompt_template": "{tag} : Naturally Seamless Loop animation.",
    "asset_use_prompt_slot": False,
    "asset_prompt_slot": 0,
    "asset_manual_selection": "",
    "asset_start_selector": "",
    "asset_search_button_selector": "",
    "asset_search_input_selector": "",
    "prompt_manual_selection": "",
    "download_mode": "video",  # video / image
    "download_video_quality": "1080P",
    "download_image_quality": "4K",
    "download_wait_seconds": 20,
    "download_search_input_selector": "",
    "download_video_filter_selector": "",
    "download_image_filter_selector": "",
    "download_video_card_selector": "",
    "download_image_card_selector": "",
    "download_video_more_selector": "",
    "download_image_more_selector": "",
    "download_video_menu_selector": "",
    "download_image_menu_selector": "",
    "download_video_quality_selector": "",
    "download_image_quality_selector": "",
    "download_output_dir": "",
    "download_human_slowdown": 1.35,
    "ui_window_width": 0,
    "ui_window_height": 0,
    "ui_zoom_percent": 100,
    "scale_lock_enabled": False,
    "browser_window_scale_percent": 100,
    "browser_zoom_percent": 100,
    "work_env_mode": "laptop",
    "display_mode_presets": {
        "laptop": {
            "browser_window_scale_percent": 100,
            "browser_zoom_percent": 100,
        },
        "desktop": {
            "browser_window_scale_percent": 70,
            "browser_zoom_percent": 100,
        },
    },
    "prompt_image_baseline_ready": False,
    "asset_image_baseline_ready": False,
    "current_media_state": "",
    "last_startup_preflight_ok": False,
    "last_startup_preflight_summary": "",
    "last_startup_preflight_at": "",
    "enter_submit_rate": 0.5,
    "work_break_every_count": 40,
    "work_break_minutes": 12,
    "work_break_random_ratio": 0.30,
    "use_ref_images": False,
    "ref_image_count": 1,
    "add_btn1_area": None,
    "add_btn2_area": None,
    "add_btn3_area": None,
    "add_btn4_area": None,
    "add_btn5_area": None,
    "ref_img1_area": None,
    "ref_img2_area": None,
    "ref_img3_area": None,
    "ref_img4_area": None,
    "ref_img5_area": None
}

PROMPT_MEDIA_LABELS = {"image": "이미지", "video": "영상"}
PROMPT_MEDIA_VALUES = {label: value for value, label in PROMPT_MEDIA_LABELS.items()}
PROMPT_ORIENTATION_LABELS = {"landscape": "가로", "portrait": "세로"}
PROMPT_ORIENTATION_VALUES = {label: value for value, label in PROMPT_ORIENTATION_LABELS.items()}

SLOT_FILE_REGEX = re.compile(r"^flow_prompts_slot_?(\d+)\.txt$", re.IGNORECASE)

# [TOOLTIP] 친절한 설명서 풍선 기능
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text: return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#F8F9FA", foreground="black", relief="solid", borderwidth=1,
                         font=("Malgun Gothic", 9, "normal"), padx=5, pady=3)
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw: tw.destroy()

# [ALARM] 휴식 종료 임박 알림
class CountdownAlert:
    def __init__(self, master, seconds=30, sound_enabled=True):
        self.root = tk.Toplevel(master)
        self.sound_enabled = sound_enabled
        self.root.title("알림")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.configure(bg="#F8F9FA")
        
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 350, 120
        x = sw - w - 20
        y = sh - h - 100
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        frame = tk.Frame(self.root, bg="#FFFFFF", highlightbackground="#007AFF", highlightthickness=3)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="⚡ 봇 출동 준비!", font=("Malgun Gothic", 12, "bold"), bg="#FFFFFF", fg="#007AFF").pack(pady=10)
        self.lbl_time = tk.Label(frame, text=f"{seconds}초 전", font=("Malgun Gothic", 20, "bold"), bg="#FFFFFF", fg="#DC3545")
        self.lbl_time.pack()

    def update_time(self, seconds):
        if not self.root.winfo_exists(): return
        self.lbl_time.config(text=f"{int(seconds)}초 전")
        if self.sound_enabled and WINSOUND_AVAILABLE and seconds <= 5:
            try: winsound.Beep(1000, 100)
            except: pass

    def close(self):
        try: self.root.destroy()
        except: pass

class CaptureOverlay:
    def __init__(self, master, callback, kind):
        self.master = master
        self.callback = callback
        self.kind = kind
        self.top = tk.Toplevel(master)
        self.top.attributes("-fullscreen", True)
        self.top.attributes("-alpha", 0.3)
        self.top.attributes("-topmost", True)
        self.top.configure(bg="black", cursor="cross")
        self.top.bind("<Button-1>", self.on_press)
        self.top.bind("<B1-Motion>", self.on_drag)
        self.top.bind("<ButtonRelease-1>", self.on_release)
        self.top.bind("<Escape>", lambda e: self.top.destroy())
        self.canvas = tk.Canvas(self.top, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.start_x = None
        self.start_y = None
        self.rect = None

    def on_press(self, event):
        self.start_x = self.top.winfo_pointerx() - self.top.winfo_rootx()
        self.start_y = self.top.winfo_pointery() - self.top.winfo_rooty()
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="#00FF00", width=4)

    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        if self.start_x is None: return
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        self.top.destroy()
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5: return
        self.callback(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

def load_config_from_file(path):
    if not path.exists(): return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        for k, v in DEFAULT_CONFIG.items():
            if k not in data: data[k] = v
        return data
    except: return DEFAULT_CONFIG.copy()

class LogWindow:
    def __init__(self, master, app=None):
        self.root = tk.Toplevel(master)
        self.app = app
        self.root.title("📜 시스템 로그 & 프롬프트 모니터")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(920, max(640, int(sw * 0.62)))
        h = min(760, max(480, int(sh * 0.72)))
        x = max((sw - w) // 2 + 20, 0)
        y = max((sh - h) // 2 + 20, 0)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(560, 420)
        self.root.configure(bg="#212529")
        
        # [NEW] 마법의 칸막이 (PanedWindow) 설치
        self.paned = ttk.Panedwindow(self.root, orient="vertical")
        self.paned.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. Prompt Preview Section
        self.frame_top = tk.Frame(self.paned, bg="#212529")
        self.paned.add(self.frame_top, weight=1) # 비중 설정

        # 상단 레이블과 새로고침 버튼을 담을 프레임
        top_f = tk.Frame(self.frame_top, bg="#212529")
        top_f.pack(fill="x", pady=(0, 5))

        lbl1 = tk.Label(top_f, text="📝 현재 로드된 프롬프트 (미리보기)", font=("Malgun Gothic", 11, "bold"), bg="#212529", fg="#FFC107")
        lbl1.pack(side="left")

        if self.app:
            btn_refresh = tk.Button(top_f, text="🔄 즉시 새로고침 (Reload)", command=self.app.on_reload,
                                     bg="#007AFF", fg="white", font=("Malgun Gothic", 9, "bold"), padx=10)
            btn_refresh.pack(side="right")
        
        self.text_preview = ScrolledText(self.frame_top, bg="#343A40", fg="#F8F9FA", 
                                         font=("Consolas", 11), insertbackground="white", borderwidth=1, relief="solid")
        self.text_preview.pack(fill="both", expand=True)

        # 2. System Log Section
        self.frame_bottom = tk.Frame(self.paned, bg="#212529")
        self.paned.add(self.frame_bottom, weight=2) # 로그 칸을 더 크게

        lbl2 = tk.Label(self.frame_bottom, text="💻 시스템 작동 로그", font=("Malgun Gothic", 11, "bold"), bg="#212529", fg="#20C997")
        lbl2.pack(anchor="w", pady=(10, 5))

        self.log_text = ScrolledText(self.frame_bottom, bg="black", fg="#00FF00", 
                                     font=("Consolas", 10), state="disabled", borderwidth=1, relief="solid")
        self.log_text.pack(fill="both", expand=True)
        
        btn_close = ttk.Button(self.root, text="창 닫기 (백그라운드 유지)", command=self.root.withdraw)
        btn_close.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)

    def log(self, msg):
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_text.config(state="normal")
            self.log_text.insert("end", f"[{ts}] {msg}\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        except: pass
    
    def set_preview(self, text):
        try:
            self.text_preview.delete("1.0", "end")
            self.text_preview.insert("1.0", text)
        except: pass
    
    def show(self):
        self.root.deiconify()
        self.root.lift()

class FlowVisionApp:

    def __init__(self):
        self.base = Path(__file__).resolve().parent
        self.cfg_path = self.base / CONFIG_FILE
        self.cfg = load_config_from_file(self.cfg_path)
        self._normalize_display_mode_config()
        self._normalize_generation_preset_config()
        self._normalize_media_panel_selector_cache()
        self.logs_dir = self.base.parent / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.running = False
        self.is_processing = False 
        self.prompts = []
        self.prompt_source_prompts = []
        self.prompt_run_numbers = None
        self.index = 0
        self.t_next = None
        self.scheduled_waiting = False
        self.scheduled_start_ts = None
        self.alert_window = None
        self.relay_progress = 0 
        self.playwright = None
        self.browser_context = None
        self.page = None
        self.action_log_path = None
        self.action_log_fp = None
        self.session_report_path = None
        self.task_queue = queue.Queue()
        self.worker_thread = None
        self.worker_stop_event = threading.Event()
        self.run_input_mode = None
        self.enter_only_submit = True
        self.asset_loop_items = []
        self.current_run_mode = None
        self.tray_icon = None
        self.tray_thread = None
        self.hidden_to_tray = False
        self._tray_warned_unavailable = False
        self.paused = False
        self.pause_remaining = None
        self.download_items = []
        self.download_index = 0
        self.download_session_log = []
        self.download_report_path = None
        self.completion_summary_path = None
        self.retry_error_log = []
        self.current_selection_summary = ""
        self.current_selection_input = ""
        self.home_window = None
        self.pipeline_window = None
        self.pipeline_runtime_active = False
        self.pipeline_run_order = []
        self.pipeline_run_position = -1
        self.pipeline_active_output_dir = ""
        self.prompt_image_baseline_ready = bool(self.cfg.get("prompt_image_baseline_ready", False))
        self.asset_image_baseline_ready = bool(self.cfg.get("asset_image_baseline_ready", False))
        current_media_state = str(self.cfg.get("current_media_state", "") or "").strip().lower()
        self.current_media_state = current_media_state if current_media_state in ("image", "video") else None
        self.preflight_running = False
        self.scale_control_buttons = []
        self.last_startup_preflight_ok = bool(self.cfg.get("last_startup_preflight_ok", False))
        self.last_startup_preflight_summary = str(self.cfg.get("last_startup_preflight_summary", "") or "").strip()
        self.last_startup_preflight_at = str(self.cfg.get("last_startup_preflight_at", "") or "").strip()

        self.actor = HumanActor(action_logger=self._action_log, status_callback=self._actor_status)
        self.actor.language_mode = self.cfg.get("language_mode", "en")
        self.actor.set_typing_speed_profile(self.cfg.get("typing_speed_profile", "x5"))
        self._apply_actor_break_settings(reset_batch=True)
        
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - 작업창")
        self._set_initial_window_size()
        
        # [NEW] Responsive Grid Weight
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.root.bind("<Configure>", self._on_root_configure)
        self.root.bind_all("<MouseWheel>", self._on_global_mousewheel, add="+")
        self.root.bind_all("<Button-4>", self._on_global_mousewheel, add="+")
        self.root.bind_all("<Button-5>", self._on_global_mousewheel, add="+")
        self._geometry_save_after = None
        
        # [NEW] Log Window Instance
        self.log_window = LogWindow(self.root, self)
        self.log_window.root.withdraw() # Start hidden
        
        try:
            icon_path = self.base.parent / "icon.ico"
            if icon_path.exists(): self.root.iconbitmap(str(icon_path))
        except: pass
        
        # [STYLE] Premium Cute + Readable Theme
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.font_ui_family = "Segoe UI"
        self.font_mono_family = "Consolas"
        self.base_font_sizes = {
            "title": 22,
            "subtitle": 12,
            "section": 14,
            "body": 12,
            "small": 11,
            "mono": 12,
            "mono_small": 11,
            "hud": 16,
            "action": 15,
        }
        self.font_title = tkfont.Font(family=self.font_ui_family, size=22, weight="bold")
        self.font_subtitle = tkfont.Font(family=self.font_ui_family, size=12)
        self.font_section = tkfont.Font(family=self.font_ui_family, size=14, weight="bold")
        self.font_body = tkfont.Font(family=self.font_ui_family, size=12)
        self.font_body_bold = tkfont.Font(family=self.font_ui_family, size=12, weight="bold")
        self.font_small = tkfont.Font(family=self.font_ui_family, size=11)
        self.font_mono = tkfont.Font(family=self.font_mono_family, size=12)
        self.font_mono_small = tkfont.Font(family=self.font_mono_family, size=11)

        self.color_bg = "#0E1728"
        self.color_card = "#182741"
        self.color_header = "#12203A"
        self.color_accent = "#59A8FF"
        self.color_success = "#59D98E"
        self.color_error = "#FF7575"
        self.color_info = "#8AD7FF"
        self.color_text = "#F7FAFF"
        self.color_text_sec = "#B8C6DD"
        self.color_input_bg = "#E6EDF7"
        self.color_input_fg = "#10203A"
        self.color_input_soft = "#D7E1F0"
        self.root.configure(bg=self.color_bg)
        self._apply_ui_zoom_fonts(force=True)
        self.root.option_add("*Font", self.font_body)
        self.root.option_add("*Label.Foreground", self.color_text)
        self.root.option_add("*Label.Background", self.color_bg)
        self.root.option_add("*Entry.Font", self.font_mono)
        self.root.option_add("*Text.Font", self.font_mono)
        self.root.option_add("*Checkbutton.Foreground", self.color_text)
        self.root.option_add("*Checkbutton.Background", self.color_bg)
        self.root.option_add("*Checkbutton.ActiveBackground", self.color_bg)
        self.root.option_add("*Checkbutton.ActiveForeground", self.color_text)
        self.root.option_add("*Checkbutton.SelectColor", self.color_bg)
        self.root.option_add("*Radiobutton.Foreground", self.color_text)
        self.root.option_add("*Radiobutton.Background", self.color_bg)
        
        self.style.configure("TFrame", background=self.color_bg)
        self.style.configure("Card.TFrame", background=self.color_card, relief="flat")
        self.style.configure("TLabelframe", background=self.color_bg, foreground=self.color_accent, borderwidth=2, relief="groove")
        self.style.configure("TLabelframe.Label", background=self.color_bg, foreground=self.color_accent, font=self.font_section)
        self.style.configure("TLabel", background=self.color_bg, foreground=self.color_text, font=self.font_body)
        self.style.configure("TCombobox", fieldbackground=self.color_input_bg, foreground=self.color_input_fg, padding=4)
        
        # Button Styles
        self.style.configure("TButton", background="#294162", foreground=self.color_text, borderwidth=1, font=self.font_body_bold, padding=6)
        self.style.map("TButton", background=[('active', '#37557D')], foreground=[('active', self.color_text)])
        
        # Progress Bar
        self.style.configure("Horizontal.TProgressbar", background=self.color_success, troughcolor="#1C2940", bordercolor="#2A3A56", thickness=20)
        
        # Big Action Button
        self.style.configure("Action.TButton", background=self.color_accent, foreground="white", font=(self.font_ui_family, 15, "bold"), padding=10)
        self.style.map("Action.TButton", background=[('active', '#1B78D0'), ('disabled', '#5A6982')])
        self.style.configure("ActionCompact.TButton", background=self.color_accent, foreground="white", font=(self.font_ui_family, 13, "bold"), padding=6)
        self.style.map("ActionCompact.TButton", background=[('active', '#1B78D0'), ('disabled', '#5A6982')])
        self.style.configure("ControlCompact.TButton", background="#294162", foreground=self.color_text, borderwidth=1, font=self.font_body_bold, padding=4)
        self.style.map("ControlCompact.TButton", background=[('active', '#37557D')], foreground=[('active', self.color_text)])

        self._ensure_prompt_slots()
        self._ensure_project_profiles()
        self._ensure_prompt_reference_items()
        self._ensure_pipeline_steps()
        self._build_ui()
        self.on_reload()
        self.root.after(1000, self._tick)

    def _set_initial_window_size(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        try:
            saved_w = int(self.cfg.get("ui_window_width", 0) or 0)
            saved_h = int(self.cfg.get("ui_window_height", 0) or 0)
        except Exception:
            saved_w = 0
            saved_h = 0
        if saved_w > 0 and saved_h > 0:
            w = min(sw - 40, max(860, saved_w))
            h = min(sh - 60, max(620, saved_h))
        elif sw <= 1600 or sh <= 900:
            w = min(1120, max(900, int(sw * 0.80)))
            h = min(840, max(660, int(sh * 0.84)))
        else:
            w = min(1220, max(980, int(sw * 0.74)))
            h = min(900, max(720, int(sh * 0.80)))
        x = max((sw - w) // 2, 0)
        y = max((sh - h) // 2, 0)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(860, 620)

    def _clamp_percent(self, value, default=100, minimum=50, maximum=150):
        try:
            pct = int(str(value).strip())
        except Exception:
            pct = int(default)
        return max(minimum, min(maximum, pct))

    def _effective_ui_scale(self):
        ui_zoom = self._clamp_percent(self.cfg.get("ui_zoom_percent", 100), default=100, minimum=50, maximum=150) / 100.0
        return max(0.50, min(1.50, ui_zoom))

    def _font_px(self, key):
        base = int(self.base_font_sizes.get(key, 12))
        return max(9, int(round(base * self._effective_ui_scale())))

    def _apply_ui_zoom_fonts(self, force=False):
        scale = self._effective_ui_scale()

        self.font_title.configure(size=self._font_px("title"))
        self.font_subtitle.configure(size=self._font_px("subtitle"))
        self.font_section.configure(size=self._font_px("section"))
        self.font_body.configure(size=self._font_px("body"))
        self.font_body_bold.configure(size=self._font_px("body"))
        self.font_small.configure(size=self._font_px("small"))
        self.font_mono.configure(size=self._font_px("mono"))
        self.font_mono_small.configure(size=self._font_px("mono_small"))

        action_size = max(12, self._font_px("action"))
        self.style.configure("TLabelframe.Label", background=self.color_bg, foreground=self.color_accent, font=self.font_section)
        self.style.configure("TLabel", background=self.color_bg, foreground=self.color_text, font=self.font_body)
        self.style.configure("TCombobox", fieldbackground=self.color_input_bg, foreground=self.color_input_fg, padding=max(4, int(4 * scale)))
        self.style.configure("TButton", background="#294162", foreground=self.color_text, borderwidth=1, font=self.font_body_bold, padding=max(5, int(6 * scale)))
        self.style.configure("Action.TButton", background=self.color_accent, foreground="white", font=(self.font_ui_family, action_size, "bold"), padding=max(8, int(10 * scale)))
        self.style.configure("ActionCompact.TButton", background=self.color_accent, foreground="white", font=(self.font_ui_family, max(11, action_size - 2), "bold"), padding=max(5, int(6 * scale)))
        self.style.configure("ControlCompact.TButton", background="#294162", foreground=self.color_text, borderwidth=1, font=(self.font_ui_family, max(10, self._font_px("body") - 1), "bold"), padding=max(3, int(4 * scale)))

    def _display_mode_labels(self):
        return {
            "laptop": "노트북 모드",
            "desktop": "데스크탑 모드",
        }

    def _display_mode_values(self):
        return {label: key for key, label in self._display_mode_labels().items()}

    def _default_display_mode_presets(self):
        return {
            "laptop": {
                "browser_window_scale_percent": 100,
                "browser_zoom_percent": 100,
            },
            "desktop": {
                "browser_window_scale_percent": 70,
                "browser_zoom_percent": 100,
            },
        }

    def _normalize_display_mode_config(self):
        raw_presets = self.cfg.get("display_mode_presets", {})
        if not isinstance(raw_presets, dict):
            raw_presets = {}
        defaults = self._default_display_mode_presets()
        normalized = {}
        for mode, default in defaults.items():
            current = raw_presets.get(mode, {})
            if not isinstance(current, dict):
                current = {}
            normalized[mode] = {
                "browser_window_scale_percent": self._clamp_percent(
                    current.get("browser_window_scale_percent", default["browser_window_scale_percent"]),
                    default=default["browser_window_scale_percent"],
                    minimum=50,
                    maximum=150,
                ),
                "browser_zoom_percent": self._clamp_percent(
                    current.get("browser_zoom_percent", default["browser_zoom_percent"]),
                    default=default["browser_zoom_percent"],
                    minimum=50,
                    maximum=150,
                ),
            }

        active_mode = str(self.cfg.get("work_env_mode", "laptop") or "laptop").strip().lower()
        if active_mode not in normalized:
            active_mode = "laptop"

        self.cfg["display_mode_presets"] = normalized
        self.cfg["work_env_mode"] = active_mode
        self.cfg["scale_lock_enabled"] = False
        self.cfg["relay_mode"] = False
        self.cfg["scheduled_start_enabled"] = False
        self.cfg["scheduled_start_at"] = ""

        active = normalized[active_mode]
        self.cfg["browser_window_scale_percent"] = active["browser_window_scale_percent"]
        self.cfg["browser_zoom_percent"] = active["browser_zoom_percent"]

    def _normalize_generation_preset_config(self):
        changed = False
        for key in ("prompt_mode_preset_enabled", "asset_prompt_mode_preset_enabled"):
            if self.cfg.get(key, True) is not True:
                self.cfg[key] = True
                changed = True
        if changed:
            self.save_config()

    def _normalize_media_panel_selector_cache(self):
        changed = False
        for profile in ("prompt", "asset"):
            image_key = self._panel_selector_key(profile, "image")
            video_key = self._panel_selector_key(profile, "video")
            image_sel = str(self.cfg.get(image_key, "") or "").strip()
            video_sel = str(self.cfg.get(video_key, "") or "").strip()
            if image_sel and video_sel and image_sel == video_sel:
                self.cfg[image_key] = ""
                self.cfg[video_key] = ""
                changed = True
        if changed:
            self.save_config()

    def _active_display_mode(self):
        mode = str(self.cfg.get("work_env_mode", "laptop") or "laptop").strip().lower()
        if mode not in self._default_display_mode_presets():
            mode = "laptop"
        return mode

    def _sync_active_display_mode_from_current_settings(self, mode=None, save=False):
        mode = str(mode or self._active_display_mode()).strip().lower()
        presets = self.cfg.get("display_mode_presets", {})
        if not isinstance(presets, dict):
            presets = {}
        defaults = self._default_display_mode_presets()
        normalized = {}
        for key, default in defaults.items():
            current = presets.get(key, {})
            if not isinstance(current, dict):
                current = {}
            normalized[key] = {
                "browser_window_scale_percent": self._clamp_percent(
                    current.get("browser_window_scale_percent", default["browser_window_scale_percent"]),
                    default=default["browser_window_scale_percent"],
                    minimum=50,
                    maximum=150,
                ),
                "browser_zoom_percent": self._clamp_percent(
                    current.get("browser_zoom_percent", default["browser_zoom_percent"]),
                    default=default["browser_zoom_percent"],
                    minimum=50,
                    maximum=150,
                ),
            }
        if mode not in normalized:
            mode = "laptop"
        normalized[mode] = {
            "browser_window_scale_percent": self._clamp_percent(self.cfg.get("browser_window_scale_percent", 100), default=100, minimum=50, maximum=150),
            "browser_zoom_percent": self._clamp_percent(self.cfg.get("browser_zoom_percent", 100), default=100, minimum=50, maximum=150),
        }
        self.cfg["display_mode_presets"] = normalized
        if save:
            self.save_config()

    def _display_mode_summary_text(self):
        presets = self.cfg.get("display_mode_presets", {}) or {}
        labels = self._display_mode_labels()
        parts = []
        for mode in ("laptop", "desktop"):
            preset = presets.get(mode, {}) or {}
            parts.append(
                f"{labels.get(mode, mode)} {preset.get('browser_window_scale_percent', 100)} / {preset.get('browser_zoom_percent', 100)}"
            )
        return " | ".join(parts)

    def _refresh_display_mode_ui(self):
        if hasattr(self, "display_mode_var"):
            self.display_mode_var.set(self._display_mode_labels().get(self._active_display_mode(), "노트북 모드"))
        if hasattr(self, "lbl_display_mode_state"):
            self.lbl_display_mode_state.config(
                text=f"현재 적용: {self._display_mode_labels().get(self._active_display_mode(), '노트북 모드')}",
                fg=self.color_success,
            )
        if hasattr(self, "lbl_display_mode_summary"):
            self.lbl_display_mode_summary.config(
                text=self._display_mode_summary_text(),
                fg=self.color_info,
            )

    def _apply_display_mode(self, mode=None, apply_browser_live=True, write_log=False):
        self._normalize_display_mode_config()
        mode = str(mode or self._active_display_mode()).strip().lower()
        presets = self.cfg.get("display_mode_presets", {}) or {}
        if mode not in presets:
            mode = "laptop"
        preset = presets.get(mode, {}) or {}
        self.cfg["work_env_mode"] = mode
        self.cfg["browser_window_scale_percent"] = self._clamp_percent(
            preset.get("browser_window_scale_percent", 100),
            default=100,
            minimum=50,
            maximum=150,
        )
        self.cfg["browser_zoom_percent"] = self._clamp_percent(
            preset.get("browser_zoom_percent", 100),
            default=100,
            minimum=50,
            maximum=150,
        )
        if hasattr(self, "browser_window_scale_var"):
            self.browser_window_scale_var.set(str(self.cfg["browser_window_scale_percent"]))
        if hasattr(self, "browser_zoom_var"):
            self.browser_zoom_var.set(str(self.cfg["browser_zoom_percent"]))
        if hasattr(self, "lbl_browser_window_scale_state"):
            self.lbl_browser_window_scale_state.config(text=f"{self.cfg['browser_window_scale_percent']}%")
        if hasattr(self, "lbl_browser_zoom_state"):
            self.lbl_browser_zoom_state.config(text=f"{self.cfg['browser_zoom_percent']}%")
        self.save_config()
        self._refresh_display_mode_ui()
        if self.page and apply_browser_live:
            self._apply_browser_window_scale_live()
            self._apply_browser_zoom()
        if write_log:
            self.log(
                f"💻 환경 모드 적용: {self._display_mode_labels().get(mode, mode)} | "
                f"작업창={self.cfg['browser_window_scale_percent']}% / 브라우저={self.cfg['browser_zoom_percent']}%"
            )

    def on_display_mode_change(self, event=None):
        label = str(self.display_mode_var.get() or "").strip() if hasattr(self, "display_mode_var") else ""
        mode = self._display_mode_values().get(label, self._active_display_mode())
        self._apply_display_mode(mode=mode, apply_browser_live=bool(self.page), write_log=True)

    def on_save_display_mode(self, mode):
        mode = str(mode or self._active_display_mode()).strip().lower()
        if mode not in self._default_display_mode_presets():
            mode = "laptop"
        self._sync_active_display_mode_from_current_settings(mode=mode, save=True)
        self._refresh_display_mode_ui()
        self.log(
            f"💾 환경 모드 저장: {self._display_mode_labels().get(mode, mode)} | "
            f"작업창={self.cfg.get('browser_window_scale_percent', 100)}% / 브라우저={self.cfg.get('browser_zoom_percent', 100)}%"
        )

    def _set_ui_zoom_percent(self, delta=0, absolute=None):
        current = self._clamp_percent(self.cfg.get("ui_zoom_percent", 100), default=100, minimum=50, maximum=150)
        target = self._clamp_percent(absolute if absolute is not None else current + delta, default=current, minimum=50, maximum=150)
        self.cfg["ui_zoom_percent"] = target
        self.save_config()
        self._apply_ui_zoom_fonts(force=True)
        if hasattr(self, "lbl_zoom_state"):
            self.lbl_zoom_state.config(text=f"{target}%")
        self._refresh_responsive_layout()
        self.log(f"🔎 UI 확대 비율 적용: {target}%")

    def _is_scale_locked(self):
        return False

    def _apply_locked_scale_settings(self, apply_browser_live=True, write_log=False):
        self._apply_display_mode(mode=self._active_display_mode(), apply_browser_live=apply_browser_live, write_log=write_log)

    def _refresh_scale_lock_ui(self):
        self._refresh_display_mode_ui()

    def on_toggle_scale_lock(self):
        self.cfg["scale_lock_enabled"] = False
        self.save_config()
        self._refresh_display_mode_ui()

    def _get_browser_work_area(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        safe_w = max(760, sw - 80)
        safe_h = max(620, sh - 140)
        return sw, sh, safe_w, safe_h

    def _apply_browser_window_scale_live(self):
        if not self.page:
            return
        try:
            win_w, win_h, viewport_w, viewport_h = self._compute_browser_window_size()
            cdp_owner = getattr(self.page, "context", None) or self.browser_context
            if cdp_owner and hasattr(cdp_owner, "new_cdp_session"):
                session = cdp_owner.new_cdp_session(self.page)
                info = session.send("Browser.getWindowForTarget")
                window_id = (info or {}).get("windowId")
                if window_id:
                    session.send(
                        "Browser.setWindowBounds",
                        {
                            "windowId": window_id,
                            "bounds": {
                                "left": 24,
                                "top": 24,
                                "width": win_w,
                                "height": win_h,
                            },
                        },
                    )
            try:
                self.page.set_viewport_size({"width": viewport_w, "height": viewport_h})
            except Exception:
                pass
            self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 브라우저 창 크기 적용: {self.cfg.get('browser_window_scale_percent', 100)}%")
        except Exception as e:
            self.log(f"⚠️ 봇 작업창 크기 실시간 적용 실패(계속 진행): {e}")

    def _set_browser_window_scale_percent(self, delta=0, absolute=None):
        current = self._clamp_percent(self.cfg.get("browser_window_scale_percent", 100), default=100, minimum=50, maximum=150)
        target = self._clamp_percent(absolute if absolute is not None else current + delta, default=current, minimum=50, maximum=150)
        self.cfg["browser_window_scale_percent"] = target
        if hasattr(self, "browser_window_scale_var"):
            self.browser_window_scale_var.set(str(target))
        if hasattr(self, "lbl_browser_window_scale_state"):
            self.lbl_browser_window_scale_state.config(text=f"{target}%")
        self._sync_active_display_mode_from_current_settings(save=False)
        self.save_config()
        self._refresh_display_mode_ui()
        self._apply_browser_window_scale_live()
        self.log(f"🪟 봇 작업창 크기 적용: {target}%")

    def _set_browser_zoom_percent(self, delta=0, absolute=None):
        current = self._clamp_percent(self.cfg.get("browser_zoom_percent", 100), default=100, minimum=50, maximum=150)
        target = self._clamp_percent(absolute if absolute is not None else current + delta, default=current, minimum=50, maximum=150)
        self.cfg["browser_zoom_percent"] = target
        if hasattr(self, "browser_zoom_var"):
            self.browser_zoom_var.set(str(target))
        if hasattr(self, "lbl_browser_zoom_state"):
            self.lbl_browser_zoom_state.config(text=f"{target}%")
        self._sync_active_display_mode_from_current_settings(save=False)
        self.save_config()
        self._refresh_display_mode_ui()
        self._apply_browser_zoom()
        self.log(f"🔎 브라우저 배율 적용: {target}%")

    def _prepare_page_for_selector_detection(self):
        if not self.page:
            return
        try:
            self._apply_browser_zoom()
        except Exception:
            pass
        try:
            self.page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass
        time.sleep(0.35)

    def _scroll_page_to_ratio(self, ratio):
        if not self.page:
            return
        try:
            ratio = max(0.0, min(1.0, float(ratio)))
        except Exception:
            ratio = 0.0
        try:
            self.page.evaluate(
                """(r) => {
                    const root = document.scrollingElement || document.documentElement || document.body;
                    if (!root) return;
                    const maxY = Math.max(0, root.scrollHeight - window.innerHeight);
                    root.scrollTo({ top: Math.round(maxY * r), behavior: "instant" });
                }""",
                ratio,
            )
        except Exception:
            try:
                self.page.evaluate("window.scrollTo(0, 0)")
            except Exception:
                pass
        time.sleep(0.18)

    def _resolve_best_locator_with_scroll(self, candidates, timeout_ms=1200, prefer_enabled=False, ratios=None):
        if ratios is None:
            ratios = (0.0, 0.18, 0.34, 0.52)
        for ratio in ratios:
            self._scroll_page_to_ratio(ratio)
            loc, sel = self._resolve_best_locator(
                candidates,
                timeout_ms=timeout_ms,
                prefer_enabled=prefer_enabled,
            )
            if loc is not None:
                return loc, sel
        return None, None

    def _draw_header_progress_bar(self, pct=0.0):
        if not hasattr(self, "header_progress_canvas"):
            return
        try:
            canvas = self.header_progress_canvas
            canvas.update_idletasks()
            width = max(int(canvas.winfo_width() or 0), 140)
            height = max(int(canvas.winfo_height() or 0), 18)
            pad = 2
            inner_w = max(width - (pad * 2), 1)
            pct = max(0.0, min(100.0, float(pct)))
            fill_w = pad + int(inner_w * (pct / 100.0))

            canvas.delete("all")
            canvas.create_rectangle(
                pad,
                pad,
                width - pad,
                height - pad,
                fill="#142236",
                outline="#2B3E5D",
                width=1,
            )
            for idx in range(1, 5):
                x = pad + int(inner_w * (idx / 5))
                canvas.create_line(x, pad + 2, x, height - pad - 2, fill="#23344F", width=1)
            if fill_w > pad:
                canvas.create_rectangle(
                    pad,
                    pad,
                    fill_w,
                    height - pad,
                    fill="#1E90FF",
                    outline="",
                )
                canvas.create_rectangle(
                    pad,
                    pad,
                    fill_w,
                    max(pad + 1, (height // 2) + 1),
                    fill="#81D8FF",
                    outline="",
                    stipple="gray25",
                )
                canvas.create_line(
                    fill_w,
                    pad + 1,
                    fill_w,
                    height - pad - 1,
                    fill="#EAF8FF",
                    width=2,
                )
            canvas.create_text(
                width // 2,
                height // 2,
                text=f"{pct:.1f}%",
                fill="#F4FAFF",
                font=(self.font_mono_family, max(9, self._font_px("mono_small")), "bold"),
            )
        except Exception:
            return

    def _resolve_scroll_canvas(self, widget):
        current = widget
        while current is not None:
            target = getattr(current, "_scroll_canvas_target", None)
            if target is not None:
                return target
            try:
                parent_name = current.winfo_parent()
            except Exception:
                parent_name = ""
            if not parent_name:
                break
            try:
                current = current.nametowidget(parent_name)
            except Exception:
                break
        return None

    def _on_global_mousewheel(self, event):
        try:
            widget = self.root.winfo_containing(event.x_root, event.y_root)
        except Exception:
            widget = getattr(event, "widget", None)
        canvas = self._resolve_scroll_canvas(widget)
        if canvas is None:
            return
        if getattr(event, "num", None) == 4:
            delta = -3
        elif getattr(event, "num", None) == 5:
            delta = 3
        else:
            raw = int(getattr(event, "delta", 0) or 0)
            if raw == 0:
                return
            steps = max(1, int(abs(raw) / 120)) if abs(raw) >= 120 else 1
            delta = (-steps * 3) if raw > 0 else (steps * 3)
        try:
            canvas.yview_scroll(delta, "units")
            return "break"
        except Exception:
            return

    def _refresh_responsive_layout(self):
        width = max(int(self.root.winfo_width() or 0), 1)
        height = max(int(self.root.winfo_height() or 0), 1)
        compact = width < 1040
        narrow = width < 930
        layout_key = (compact, narrow, height < 720, self._clamp_percent(self.cfg.get("ui_zoom_percent", 100), default=100))
        if getattr(self, "_last_layout_key", None) == layout_key:
            return
        self._last_layout_key = layout_key
        if hasattr(self, "left_container"):
            target_width = 560
            if compact:
                target_width = 500
            if narrow:
                target_width = 420
            self.left_container.config(width=target_width)
        if hasattr(self, "body_pane") and hasattr(self, "left_container") and hasattr(self, "right_panel"):
            total_w = max(int(self.body_pane.winfo_width() or 0), 0)
            left_min = 320 if narrow else 360
            right_min = 240 if narrow else (280 if compact else 320)
            try:
                self.body_pane.paneconfigure(self.left_container, minsize=left_min)
                self.body_pane.paneconfigure(self.right_panel, minsize=right_min)
            except Exception:
                pass
            if total_w > (left_min + right_min):
                desired_left = target_width if hasattr(self, "left_container") else int(total_w * 0.60)
                desired_left = min(desired_left, total_w - right_min)
                desired_left = max(left_min, desired_left)
                try:
                    self.body_pane.sashpos(0, desired_left)
                except Exception:
                    pass
        if hasattr(self, "btn_log") and hasattr(self, "btn_refresh_big"):
            pad_y = 4 if compact else 6
            self.btn_log.config(font=self.font_body_bold, padx=10 if compact else 14, pady=pad_y)
            self.btn_refresh_big.config(font=self.font_body_bold, padx=10 if compact else 14, pady=pad_y)
        action_style = "ActionCompact.TButton" if compact else "Action.TButton"
        control_style = "ControlCompact.TButton" if compact else "TButton"
        btn_text_map = {
            "btn_start_prompt": "▶ 프롬프트 시작" if compact else "▶ 프롬프트 자동화 시작",
            "btn_start_asset": "▶ S반복 시작" if compact else "▶ S반복 자동화 시작",
            "btn_start_download": "▶ 다운로드 시작" if compact else "▶ 다운로드 자동화 시작",
            "btn_pause": "⏸ 일시정지",
            "btn_resume": "▶ 재개",
            "btn_stop": "⏹ 완전중지" if compact else "⏹ 완전중지(브라우저 종료)",
        }
        for btn_name in ("btn_start_prompt", "btn_start_asset", "btn_start_download"):
            if hasattr(self, btn_name):
                try:
                    getattr(self, btn_name).config(style=action_style, text=btn_text_map[btn_name])
                except Exception:
                    pass
        for btn_name in ("btn_pause", "btn_resume", "btn_stop"):
            if hasattr(self, btn_name):
                try:
                    getattr(self, btn_name).config(style=control_style, text=btn_text_map[btn_name])
                except Exception:
                    pass
        if hasattr(self, "lbl_header_progress"):
            self.lbl_header_progress.config(font=(self.font_mono_family, max(12, self._font_px("mono")), "bold"))
        if hasattr(self, "lbl_main_status"):
            self.lbl_main_status.config(font=(self.font_ui_family, max(15, self._font_px("hud")), "bold"))
        if hasattr(self, "header_progress_canvas"):
            bar_height = 16 if compact else 18
            if narrow:
                bar_height = 14
            self.header_progress_canvas.config(height=bar_height)
            pct = float(self.progress_var.get()) if hasattr(self, "progress_var") else 0.0
            self._draw_header_progress_bar(pct)
        if hasattr(self, "lbl_prog_text"):
            self.lbl_prog_text.config(font=(self.font_mono_family, max(12, self._font_px("mono")), "bold"))
        if hasattr(self, "lbl_eta"):
            self.lbl_eta.config(font=self.font_body)
        if hasattr(self, "lbl_nav_status"):
            self.lbl_nav_status.config(font=(self.font_mono_family, max(11, self._font_px("mono_small")), "bold"))
        if hasattr(self, "ent_jump"):
            self.ent_jump.config(font=self.font_mono)
        if hasattr(self, "btn_go_home"):
            self.btn_go_home.config(style="TButton")
        if hasattr(self, "lbl_prompt_preset_selector"):
            self.lbl_prompt_preset_selector.config(wraplength=max(360, width - 620))
        if hasattr(self, "lbl_asset_prompt_preset_selector"):
            self.lbl_asset_prompt_preset_selector.config(wraplength=max(360, width - 620))
        right_wrap = max(180, min(520, width - 760))
        if hasattr(self, "lbl_hud_trait"):
            self.lbl_hud_trait.config(wraplength=right_wrap)
        if hasattr(self, "btn_toggle_hud"):
            self.btn_toggle_hud.config(width=6 if compact else 8)

    def _persist_window_geometry(self):
        try:
            if str(self.root.state()) != "normal":
                return
            w = int(self.root.winfo_width())
            h = int(self.root.winfo_height())
            if w >= 860 and h >= 620:
                self.cfg["ui_window_width"] = w
                self.cfg["ui_window_height"] = h
                self.save_config()
        except Exception:
            pass

    def _on_root_configure(self, _event=None):
        try:
            if self._geometry_save_after:
                self.root.after_cancel(self._geometry_save_after)
        except Exception:
            pass
        try:
            self._geometry_save_after = self.root.after(500, self._persist_window_geometry)
        except Exception:
            self._persist_window_geometry()
        try:
            if getattr(self, "_responsive_after", None):
                self.root.after_cancel(self._responsive_after)
        except Exception:
            pass
        try:
            self._responsive_after = self.root.after(120, self._refresh_responsive_layout)
        except Exception:
            self._refresh_responsive_layout()

    def _compute_browser_window_size(self):
        sw, sh, safe_w, safe_h = self._get_browser_work_area()
        browser_scale = self._clamp_percent(self.cfg.get("browser_window_scale_percent", 100), default=100, minimum=50, maximum=150) / 100.0
        if sw <= 1600 or sh <= 900:
            win_w = max(680, int(safe_w * 0.76 * browser_scale))
            win_h = max(560, int(safe_h * 0.88 * browser_scale))
        else:
            win_w = max(760, int(safe_w * 0.72 * browser_scale))
            win_h = max(620, int(safe_h * 0.90 * browser_scale))
        win_w = min(win_w, safe_w)
        win_h = min(win_h, safe_h)
        viewport_w = max(640, win_w - 32)
        viewport_h = max(420, win_h - 136)
        return win_w, win_h, viewport_w, viewport_h

    def _apply_browser_zoom(self):
        if not self.page:
            return
        zoom_pct = self._clamp_percent(self.cfg.get("browser_zoom_percent", 100), default=100, minimum=50, maximum=150)
        zoom_value = f"{zoom_pct}%"
        script = f"""
        (() => {{
            const applyZoom = () => {{
                try {{
                    document.documentElement.style.zoom = "{zoom_value}";
                    if (document.body) {{
                        document.body.style.zoom = "{zoom_value}";
                    }}
                }} catch (_e) {{}}
            }};
            applyZoom();
            document.addEventListener('DOMContentLoaded', applyZoom, {{ once: true }});
            window.addEventListener('load', applyZoom, {{ once: true }});
            setTimeout(applyZoom, 350);
            setTimeout(applyZoom, 900);
        }})();
        """
        try:
            self.page.evaluate(script)
            self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 브라우저 페이지 배율 적용: {zoom_pct}%")
        except Exception as e:
            self.log(f"⚠️ 브라우저 배율 적용 실패(계속 진행): {e}")

    def _init_body_sash(self):
        try:
            self.root.update_idletasks()
            total_w = self.body_pane.winfo_width()
            if total_w > 0:
                # 왼쪽(설정) 비중을 조금 더 크게 유지
                self.body_pane.sashpos(0, int(total_w * 0.64))
        except:
            pass

    def play_sound(self, category):
        if not self.cfg.get("sound_enabled", True) or not WINSOUND_AVAILABLE: return 
        try:
            if category == "start": winsound.MessageBeep(winsound.MB_OK)
            elif category == "success": winsound.Beep(800, 200)
            elif category == "finish": winsound.MessageBeep(winsound.MB_ICONHAND)
        except: pass

    def save_config(self):
        try: self.cfg_path.write_text(json.dumps(self.cfg, indent=4, ensure_ascii=False), encoding='utf-8')
        except: pass

    def _actor_status(self, text):
        self.root.after(0, lambda: self.update_status_label(text, self.color_info))

    def _action_log(self, msg):
        if not self.action_log_fp:
            return
        try:
            self.action_log_fp.write(f"{msg}\n")
            self.action_log_fp.flush()
        except Exception:
            pass

    def _open_action_log(self, prefix="action_trace"):
        if self.action_log_fp:
            return
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prefix = str(prefix or "action_trace").strip() or "action_trace"
        self.action_log_path = self.logs_dir / f"{safe_prefix}_{stamp}.log"
        self.action_log_fp = self.action_log_path.open("a", encoding="utf-8")
        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 액션 로그 파일 생성: {self.action_log_path}")
        self.log(f"🧾 행동 로그 저장 시작: {self.action_log_path.name}")

    def _close_action_log(self):
        if not self.action_log_fp:
            return
        try:
            self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 액션 로그 종료")
            self.action_log_fp.close()
        except Exception:
            pass
        finally:
            self.action_log_fp = None

    def _resolve_profile_dir(self):
        profile_dir = (self.cfg.get("browser_profile_dir") or "flow_human_profile_pw").strip()
        profile_path = self.base / profile_dir
        profile_path.mkdir(parents=True, exist_ok=True)
        return profile_path

    def _pick_primary_browser_page(self):
        if not self.browser_context:
            return None
        pages = []
        try:
            pages = [p for p in self.browser_context.pages if p and (not p.is_closed())]
        except Exception:
            pages = []
        if not pages:
            return None

        start_url = (self.cfg.get("start_url") or "").strip()
        internal_prefixes = ("about:blank", "chrome://newtab", "edge://newtab", "chrome://new-tab-page", "edge://new-tab-page")

        def _page_url(page):
            try:
                return str(page.url or "").strip()
            except Exception:
                return ""

        preferred = None
        if start_url:
            for page in pages:
                if start_url and start_url in _page_url(page):
                    preferred = page
                    break
        if preferred is None:
            for page in pages:
                url = _page_url(page)
                if not url or any(url.startswith(prefix) for prefix in internal_prefixes):
                    continue
                preferred = page
                break
        if preferred is None:
            preferred = pages[0]

        for page in pages:
            if page == preferred:
                continue
            try:
                page.close()
            except Exception:
                pass
        return preferred

    def _ensure_browser_session(self):
        if self.page and not self.page.is_closed():
            return
        if self.playwright is None:
            self.playwright = sync_playwright().start()
        if self.browser_context:
            try:
                self.browser_context.close()
            except Exception:
                pass
            self.browser_context = None

        profile_path = self._resolve_profile_dir()
        # Windows에서 남아있는 profile lock 파일이 있으면 launch가 즉시 죽는 경우가 있어 정리
        for lock_name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            try:
                p = profile_path / lock_name
                if p.exists():
                    p.unlink()
            except Exception:
                pass

        channel = (self.cfg.get("browser_channel") or "chrome").strip() or None
        headless = bool(self.cfg.get("browser_headless", False))
        win_w, win_h, viewport_w, viewport_h = self._compute_browser_window_size()

        def _launch_with(_profile_path, _channel):
            return self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(_profile_path),
                channel=_channel,
                headless=headless,
                viewport={"width": viewport_w, "height": viewport_h},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--window-position=24,24",
                    f"--window-size={win_w},{win_h}",
                ],
            )

        try:
            self.browser_context = _launch_with(profile_path, channel)
        except Exception as e1:
            # 1차 폴백: 채널 미지정(Playwright Chromium)
            self.log(f"⚠️ 브라우저 실행 1차 실패, Chromium 폴백 시도: {e1}")
            try:
                self.browser_context = _launch_with(profile_path, None)
            except Exception as e2:
                # 2차 폴백: 임시 프로필 디렉토리
                runtime_profile = self.base / f"flow_human_profile_pw_runtime_{int(time.time())}"
                runtime_profile.mkdir(parents=True, exist_ok=True)
                self.log(f"⚠️ 브라우저 실행 2차 실패, 임시 프로필 폴백 시도: {e2}")
                self.browser_context = _launch_with(runtime_profile, None)

        self.page = self._pick_primary_browser_page()
        if self.page is None:
            self.page = self.browser_context.new_page()

        try:
            stealth_sync(self.page)
        except Exception as e:
            self.log(f"⚠️ stealth 적용 실패(계속 진행): {e}")

        self.actor.set_page(self.page)
        zoom_pct = self._clamp_percent(self.cfg.get("browser_zoom_percent", 100), default=100, minimum=50, maximum=150)
        zoom_value = f"{zoom_pct}%"
        try:
            self.browser_context.add_init_script(
                """
                (() => {
                    const apply = () => {
                        try {
                            document.documentElement.style.zoom = "__ZOOM__";
                            if (document.body) document.body.style.zoom = "__ZOOM__";
                        } catch (_e) {}
                    };
                    apply();
                    document.addEventListener('DOMContentLoaded', apply);
                    window.addEventListener('load', apply);
                })();
                """.replace("__ZOOM__", zoom_value)
            )
        except Exception:
            pass
        self._apply_browser_zoom()
        self.log("🌐 Playwright 브라우저 세션 연결 완료")
        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 브라우저 세션 생성")

    def _shutdown_browser(self):
        try:
            if self.browser_context:
                self.browser_context.close()
        except Exception:
            pass
        self.browser_context = None
        self.page = None

        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        self.playwright = None

    def on_open_bot_work_window(self):
        try:
            self.on_option_toggle()
            self._ensure_browser_session()
            self.actor.set_page(self.page)
            start_url = (self.cfg.get("start_url") or "").strip()
            if not start_url:
                raise RuntimeError("시작 URL을 먼저 입력해주세요.")
            current_url = (self.page.url or "").strip() if self.page else ""
            if (not current_url) or (start_url not in current_url):
                self.log(f"🌐 봇 작업창 이동: {start_url}")
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(random.uniform(1.0, 2.0))
            self._apply_browser_zoom()
            try:
                self.page.bring_to_front()
            except Exception:
                pass
            self.refresh_detected_media_state(ensure_session=False)
            self.log("🤖 봇 작업창 열기 완료 - 이 창에서 Image 기본값을 맞춰주세요.")
            self.update_status_label("🤖 봇 작업창 열림", self.color_success)
        except Exception as e:
            self.log(f"❌ 봇 작업창 열기 실패: {e}")
            self.update_status_label("❌ 봇 작업창 열기 실패", self.color_error)

    def _set_detected_media_state_ui(self, state=None, detail="", error=False):
        if state == "image":
            text = "현재 감지 생성 기본값: 이미지"
            color = self.color_success
        elif state == "video":
            text = "현재 감지 생성 기본값: 동영상"
            color = self.color_accent
        elif error:
            text = f"현재 감지 생성 기본값: 확인 실패{f' | {detail}' if detail else ''}"
            color = self.color_error
        else:
            suffix = f" | {detail}" if detail else ""
            text = f"현재 감지 생성 기본값: 확인 필요{suffix}"
            color = self.color_text_sec

        if hasattr(self, "lbl_detected_media_state"):
            self.lbl_detected_media_state.config(text=text, fg=color)

    def _read_detected_media_state(self, input_locator=None, profile="prompt"):
        if not self.page:
            return None, "브라우저 없음"
        if input_locator is None:
            input_selector = (self.cfg.get("input_selector") or "").strip()
            if input_selector:
                try:
                    input_locator, _ = self._resolve_prompt_input_locator(input_selector, timeout_ms=1800)
                except Exception:
                    input_locator = None
        _loc, desc, state = self._resolve_current_media_panel_button(input_locator=input_locator, profile=profile)
        return state, desc or ""

    def refresh_detected_media_state(self, ensure_session=True, input_locator=None, profile="prompt", write_log=False):
        try:
            if ensure_session:
                self.on_option_toggle()
                self._ensure_browser_session()
                self.actor.set_page(self.page)
            if not self.page:
                self._set_detected_media_state_ui(None, "브라우저 없음")
                return None
            state, desc = self._read_detected_media_state(input_locator=input_locator, profile=profile)
            self._set_detected_media_state_ui(state, desc or "")
            if write_log:
                self.log(f"👁 현재 감지 상태: {state or '미확인'}{f' | {desc}' if desc else ''}")
            return state
        except Exception as e:
            self._set_detected_media_state_ui(None, str(e), error=True)
            return None

    def on_refresh_detected_media_state(self):
        self.refresh_detected_media_state(ensure_session=True, write_log=True)

    def _set_startup_preflight_ui(self, passed=None, detail="", checked_at=""):
        if not hasattr(self, "lbl_startup_preflight"):
            return
        checked_at = str(checked_at or "").strip()
        detail = str(detail or "").strip()
        if len(detail) > 72:
            detail = detail[:69] + "..."
        time_prefix = f"[{checked_at}] " if checked_at else ""
        if passed is True:
            text = f"{time_prefix}시작 전 자동 점검: 합격"
            if detail:
                text += f" | {detail}"
            color = self.color_success
        elif passed is False:
            text = f"{time_prefix}시작 전 자동 점검: 불합격"
            if detail:
                text += f" | {detail}"
            color = self.color_error
        else:
            text = f"{time_prefix}시작 전 자동 점검: 아직 안 함"
            if detail:
                text += f" | {detail}"
            color = self.color_text_sec
        self.lbl_startup_preflight.config(text=text, fg=color)

    def _format_startup_preflight_message(self, results):
        lines = []
        for name, ok, detail in results or []:
            status = "합격" if ok else "실패"
            line = f"- {name}: {status}"
            if detail:
                line += f" | {detail}"
            lines.append(line)
        return "\n".join(lines) if lines else "- 자동 점검 결과가 없습니다."

    def _startup_preflight_check_prompt_selectors(self):
        self._ensure_browser_session()
        self.actor.set_page(self.page)
        start_url = (self.cfg.get("start_url") or "").strip()
        input_selector = (self.cfg.get("input_selector") or "").strip()
        submit_selector = (self.cfg.get("submit_selector") or "").strip()

        def _check_once():
            try:
                input_loc, _ = self._resolve_prompt_input_locator(input_selector, timeout_ms=2200)
                input_ok_local = input_loc is not None
            except Exception:
                input_ok_local = False
                input_loc = None
            try:
                submit_loc, _ = self._resolve_best_locator(
                    self._normalize_candidate_list(submit_selector) or self._submit_candidates(),
                    near_locator=input_loc if input_ok_local else None,
                    timeout_ms=2200,
                )
                submit_ok_local = submit_loc is not None
            except Exception:
                submit_ok_local = False
            return input_ok_local, submit_ok_local

        input_ok, submit_ok = _check_once()
        if not (input_ok and submit_ok):
            if start_url:
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
            self._try_open_new_project_if_needed(
                input_selector or "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [contenteditable='true'], [role='textbox']"
            )
            for _ in range(6):
                time.sleep(0.7)
                input_ok, submit_ok = _check_once()
                if input_ok and submit_ok:
                    break
        ok = input_ok and submit_ok
        return ok, f"입력={'OK' if input_ok else 'FAIL'} / 제출={'OK' if submit_ok else 'FAIL'}"

    def _startup_preflight_detect_media_state(self, profile="prompt"):
        profile = "asset" if str(profile).strip().lower() == "asset" else "prompt"
        self._ensure_browser_session()
        self.actor.set_page(self.page)
        start_url = (self.cfg.get("start_url") or "").strip()
        if start_url:
            if start_url not in (self.page.url or ""):
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(1.0, 2.0))

        input_hint = (self.cfg.get("input_selector") or "").strip() or "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [contenteditable='true'], [role='textbox']"
        self._try_open_new_project_if_needed(input_hint)
        input_locator, _ = self._resolve_prompt_input_locator(input_hint, timeout_ms=2200)

        detected_state = self.refresh_detected_media_state(
            ensure_session=False,
            input_locator=input_locator,
            profile=profile,
            write_log=True,
        )
        if detected_state not in ("image", "video"):
            return False, "현재 상태 감지 실패", None, input_locator

        return True, f"현재={detected_state}", detected_state, input_locator

    def _startup_preflight_check_media_switch(self, profile="prompt", detected_state=None, input_locator=None):
        if detected_state not in ("image", "video") or input_locator is None:
            ok, detail, detected, input_locator = self._startup_preflight_detect_media_state(profile=profile)
            if not ok:
                return False, detail
            detected_state = detected
        if detected_state not in ("image", "video"):
            return False, "현재 상태 감지 실패"

        target_state = "video" if detected_state == "image" else "image"
        self.current_media_state = detected_state
        first_ok = self._switch_media_state(target_state, input_locator=input_locator, profile=profile)
        second_ok = self._switch_media_state(detected_state, input_locator=input_locator, profile=profile)
        ok = bool(first_ok and second_ok)
        return ok, (
            f"현재={detected_state} / "
            f"{detected_state}→{target_state}={'OK' if first_ok else 'FAIL'} / "
            f"{target_state}→{detected_state}={'OK' if second_ok else 'FAIL'}"
        )

    def _startup_preflight_prepare_asset_video_state(self):
        ok, detail, detected_state, input_locator = self._startup_preflight_detect_media_state("asset")
        if not ok:
            return False, detail
        if detected_state == "video":
            return True, "현재=video / 유지=OK"

        switch_ok = self._switch_media_state("video", input_locator=input_locator, profile="asset")
        verified_state = self.refresh_detected_media_state(
            ensure_session=False,
            input_locator=input_locator,
            profile="asset",
            write_log=True,
        )
        ok = bool(switch_ok and verified_state == "video")
        return ok, f"현재={detected_state} / {detected_state}→video={'OK' if ok else 'FAIL'}"

    def _startup_preflight_check_asset_selectors(self):
        self._ensure_browser_session()
        self.actor.set_page(self.page)
        start_url = (self.cfg.get("start_url") or "").strip()
        if start_url and start_url not in (self.page.url or ""):
            self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(random.uniform(0.8, 1.6))
        video_ready_ok, video_ready_detail = self._startup_preflight_prepare_asset_video_state()
        if not video_ready_ok:
            return False, f"{video_ready_detail} / 에셋 전 준비 실패"
        self._prepare_page_for_selector_detection()
        self._ensure_asset_workspace_visible(timeout_sec=4)
        self._open_asset_search_surface_for_detection()

        start_candidates = self._normalize_candidate_list(self.cfg.get("asset_start_selector", "")) or self._asset_start_button_candidates()
        search_candidates = self._normalize_candidate_list(self.cfg.get("asset_search_button_selector", "")) or self._asset_search_button_candidates()
        input_candidates = self._normalize_candidate_list(self.cfg.get("asset_search_input_selector", "")) or self._asset_search_input_candidates()

        start_loc, _ = self._resolve_best_locator_with_scroll(start_candidates, timeout_ms=2200, prefer_enabled=False)
        search_loc, _ = self._resolve_best_locator_with_scroll(
            search_candidates + ["text=에셋 검색", "text=Asset search"],
            timeout_ms=2200,
            prefer_enabled=False,
            ratios=(0.0, 0.12, 0.24, 0.36, 0.50),
        )
        if start_loc is None:
            start_loc, _ = self._resolve_text_locator_any_frame(["시작", "Start"], timeout_ms=1000)
        if search_loc is None:
            search_loc, _ = self._resolve_text_locator_any_frame(["에셋 검색", "Asset search", "Search assets"], timeout_ms=1200)

        input_loc, _ = self._resolve_best_locator_with_scroll(
            input_candidates,
            timeout_ms=1800,
            prefer_enabled=False,
            ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
        )
        if (input_loc is None) and (search_loc is not None):
            try:
                search_loc.click(timeout=2000)
            except Exception:
                pass
            self.actor.random_action_delay("자동 점검 검색 입력칸 확인 대기", 0.3, 1.0)
            input_loc, _ = self._resolve_best_locator_with_scroll(
                input_candidates,
                timeout_ms=2200,
                prefer_enabled=False,
                ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
            )

        start_ok = start_loc is not None
        input_ok = input_loc is not None
        ok = bool(start_ok and input_ok)
        return ok, (
            f"{video_ready_detail} / "
            f"시작={'OK' if start_ok else 'FAIL'} / 검색입력={'OK' if input_ok else 'FAIL'}"
        )

    def _startup_preflight_check_download(self, mode):
        mode = "image" if mode == "image" else "video"
        self._ensure_browser_session()
        self.actor.set_page(self.page)
        start_url = (self.cfg.get("start_url") or "").strip()
        if start_url and start_url not in (self.page.url or ""):
            self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(random.uniform(0.8, 1.4))

        items = self._build_download_items()
        if not items:
            return False, "다운로드 태그 없음"
        tag = items[0]
        quality = self._download_quality(mode)
        result = self._run_single_download_flow(mode=mode, tag=tag, quality=quality, dry_run=True, wait_sec=25)
        self._apply_download_used_selectors(mode, result.get("used", {}))
        self.save_config()
        used = result.get("used", {})
        ok = bool(used.get("search_input") and used.get("card") and used.get("more") and used.get("menu") and used.get("quality"))
        return ok, (
            f"태그={tag} / 검색={used.get('search_input') or 'FAIL'} / 카드={used.get('card') or 'FAIL'} / "
            f"더보기={used.get('more') or 'FAIL'} / 다운로드={used.get('menu') or 'FAIL'} / 품질={used.get('quality') or 'FAIL'}"
        )

    def _run_startup_preflight_suite(self, interactive=True):
        if self.preflight_running:
            return False, [("자동 점검", False, "이미 실행 중입니다.")]

        opened_here = False
        results = []
        self.preflight_running = True
        checked_at = datetime.now().strftime("%H:%M:%S")
        try:
            self.on_option_toggle()
            if not self.action_log_fp:
                self._open_action_log("startup_preflight")
                opened_here = True
            self.update_status_label("🛡 시작 전 자동 점검 중...", self.color_info)
            self._apply_display_mode(mode=self._active_display_mode(), apply_browser_live=True, write_log=True)

            prompt_detect_ok, prompt_detect_detail, prompt_detected_state, prompt_input_locator = self._startup_preflight_detect_media_state("prompt")
            results.append(("현재 상태 감지", bool(prompt_detect_ok), str(prompt_detect_detail or "").strip()))
            self.log(f"🛡 자동 점검 | 현재 상태 감지 | {'OK' if prompt_detect_ok else 'FAIL'} | {prompt_detect_detail}")

            checks = [
                ("이미지/동영상 전환", lambda: self._startup_preflight_check_media_switch("prompt", detected_state=prompt_detected_state, input_locator=prompt_input_locator)),
                ("S 에셋 확인", self._startup_preflight_check_asset_selectors),
                ("이미지 다운로드", lambda: self._startup_preflight_check_download("image")),
                ("영상 다운로드", lambda: self._startup_preflight_check_download("video")),
            ]

            for name, fn in checks:
                self.update_status_label(f"🛡 자동 점검 중... {name}", self.color_info)
                try:
                    ok, detail = fn()
                except Exception as e:
                    ok, detail = False, str(e)
                results.append((name, bool(ok), str(detail or "").strip()))
                self.log(f"🛡 자동 점검 | {name} | {'OK' if ok else 'FAIL'} | {detail}")

            passed = all(ok for _, ok, _ in results)
            summary = ", ".join(f"{name}={'OK' if ok else 'FAIL'}" for name, ok, _ in results)
            self.last_startup_preflight_ok = passed
            self.last_startup_preflight_summary = summary
            self.last_startup_preflight_at = checked_at
            self.cfg["last_startup_preflight_ok"] = passed
            self.cfg["last_startup_preflight_summary"] = summary
            self.cfg["last_startup_preflight_at"] = checked_at
            self.save_config()
            self._set_startup_preflight_ui(passed, summary, checked_at)
            self.update_status_label("✅ 시작 전 자동 점검 합격" if passed else "❌ 시작 전 자동 점검 실패", self.color_success if passed else self.color_error)
            if interactive:
                if passed:
                    messagebox.showinfo("시작 전 자동 점검", "아래 항목이 모두 합격했습니다.\n\n" + self._format_startup_preflight_message(results))
                else:
                    messagebox.showwarning("시작 전 자동 점검 실패", "아래 항목을 먼저 확인해주세요.\n\n" + self._format_startup_preflight_message(results))
            return passed, results
        finally:
            self.preflight_running = False
            if opened_here:
                self._close_action_log()

    def on_run_startup_preflight(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 시작 전 자동 점검을 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self._run_startup_preflight_suite(interactive=True)

    def _ensure_worker_thread(self):
        if self.worker_thread and self.worker_thread.is_alive():
            return
        self.worker_stop_event.clear()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.log("🧵 자동화 작업 스레드 시작")

    def _stop_worker_thread(self):
        self.worker_stop_event.set()
        try:
            self.task_queue.put_nowait("shutdown_and_stop")
        except Exception:
            pass
        if self.worker_thread and self.worker_thread.is_alive():
            try:
                self.worker_thread.join(timeout=2.0)
            except Exception:
                pass
        self.worker_thread = None
        # 남은 큐를 비워 다음 시작 시 중복 실행 방지
        try:
            while True:
                self.task_queue.get_nowait()
        except queue.Empty:
            pass

    def _worker_loop(self):
        while not self.worker_stop_event.is_set():
            try:
                cmd = self.task_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if cmd == "stop":
                break
            if cmd == "shutdown_and_stop":
                try:
                    self._shutdown_browser()
                except Exception:
                    pass
                break
            if cmd == "run":
                try:
                    self._run_task()
                except Exception as e:
                    self.log(f"❌ 작업 스레드 예외: {e}")

    def _ensure_prompt_slots(self):
        changed = False
        if "prompt_slots" not in self.cfg or not self.cfg["prompt_slots"]:
            self.cfg["prompt_slots"] = [{"name": "기본 슬롯", "file": "flow_prompts.txt"}]
            self.cfg["active_prompt_slot"] = 0
            changed = True

        active = self._clamp_slot_index(self.cfg.get("active_prompt_slot", 0))
        if self.cfg.get("active_prompt_slot") != active:
            self.cfg["active_prompt_slot"] = active
            changed = True

        expected_file = self.cfg["prompt_slots"][active]["file"]
        if self.cfg.get("prompts_file") != expected_file:
            self.cfg["prompts_file"] = expected_file
            changed = True

        for key in ("relay_start_slot", "relay_end_slot"):
            val = self.cfg.get(key)
            if val is not None:
                clamped = self._clamp_slot_index(val, active)
                if val != clamped:
                    self.cfg[key] = clamped
                    changed = True

        selected_before = self.cfg.get("relay_selected_slots", [])
        selected_after = self._normalize_relay_selected_slots(selected_before)
        if selected_before != selected_after:
            self.cfg["relay_selected_slots"] = selected_after
            changed = True

        if changed:
            self.save_config()

    def _default_project_profile(self):
        return {
            "project_name": "기본 프로젝트",
            "url": str(self.cfg.get("start_url", "https://labs.google/flow") or "https://labs.google/flow").strip(),
        }

    def _clamp_project_profile_index(self, idx, default=0):
        profiles = self.cfg.get("project_profiles", [])
        if not profiles:
            return 0
        try:
            idx = int(idx)
        except (TypeError, ValueError):
            idx = default
        return max(0, min(len(profiles) - 1, idx))

    def _make_unique_project_profile_name(self, base_name):
        base_name = str(base_name or "").strip() or "프로젝트"
        existing = {str(item.get("project_name", "")).strip() for item in self.cfg.get("project_profiles", [])}
        if base_name not in existing:
            return base_name
        suffix = 2
        while True:
            candidate = f"{base_name} ({suffix})"
            if candidate not in existing:
                return candidate
            suffix += 1

    def _ensure_project_profiles(self):
        changed = False
        raw_profiles = self.cfg.get("project_profiles", [])
        normalized = []
        if isinstance(raw_profiles, list):
            for item in raw_profiles:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("project_name", "") or item.get("name", "") or "").strip()
                url = str(item.get("url", "") or "").strip()
                if not name:
                    name = self._make_unique_project_profile_name("프로젝트")
                normalized.append({
                    "project_name": name,
                    "url": url,
                })
        if not normalized:
            normalized = [self._default_project_profile()]
            changed = True
        if raw_profiles != normalized:
            self.cfg["project_profiles"] = normalized
            changed = True
        active = self._clamp_project_profile_index(self.cfg.get("active_project_profile", 0))
        if self.cfg.get("active_project_profile") != active:
            self.cfg["active_project_profile"] = active
            changed = True
        if changed:
            self.save_config()

    def _normalize_prompt_reference_item(self, item):
        if not isinstance(item, dict):
            item = {}
        name = str(item.get("name", "") or "").strip()
        asset_tag = self._normalize_reference_asset_tag(item.get("asset_tag", ""))
        scene_spec = str(item.get("scene_spec", "") or "").strip()
        return {
            "name": name,
            "asset_tag": asset_tag,
            "scene_spec": scene_spec,
        }

    def _ensure_prompt_reference_items(self):
        raw_items = self.cfg.get("prompt_reference_items", [])
        normalized = []
        if isinstance(raw_items, list):
            for item in raw_items:
                normalized.append(self._normalize_prompt_reference_item(item))
        if raw_items != normalized:
            self.cfg["prompt_reference_items"] = normalized
            self.save_config()

    def _normalize_reference_asset_tag(self, value):
        raw = str(value or "").strip().upper()
        if not raw:
            return ""
        prefix = (self.cfg.get("asset_loop_prefix") or "S").strip().upper() or "S"
        if raw.isdigit():
            return f"{prefix}{raw.zfill(self._asset_pad_width())}"
        m = re.match(rf"^\s*{re.escape(prefix)}\s*0*([0-9]+)\s*$", raw, re.IGNORECASE)
        if m:
            return f"{prefix}{str(int(m.group(1))).zfill(self._asset_pad_width())}"
        return raw

    def _prompt_reference_scene_upper_bound(self):
        return max(1, len(getattr(self, "prompt_source_prompts", []) or []))

    def _prompt_reference_matches_for_scene(self, scene_no):
        matches = []
        try:
            target = int(scene_no or 0)
        except Exception:
            target = 0
        if target < 1 or not self.cfg.get("prompt_reference_enabled"):
            return matches
        for item in self.cfg.get("prompt_reference_items", []) or []:
            normalized = self._normalize_prompt_reference_item(item)
            asset_tag = normalized.get("asset_tag", "")
            if not asset_tag:
                continue
            info = self._parse_manual_number_spec(
                normalized.get("scene_spec", ""),
                upper_bound=self._prompt_reference_scene_upper_bound(),
            )
            if target in set(info.get("numbers", []) or []):
                matches.append(normalized)
        return matches

    def _prompt_reference_summary_text(self):
        items = [self._normalize_prompt_reference_item(x) for x in (self.cfg.get("prompt_reference_items", []) or [])]
        usable = [x for x in items if x.get("asset_tag") and x.get("scene_spec")]
        if not usable:
            return "레퍼런스 첨부 비사용"
        return f"활성 {len(usable)}개 | 장면 시작 전에 @로 첨부"

    def _refresh_prompt_reference_ui(self):
        if hasattr(self, "prompt_reference_enabled_var"):
            self.prompt_reference_enabled_var.set(bool(self.cfg.get("prompt_reference_enabled", False)))
        if hasattr(self, "lbl_prompt_reference_status"):
            self.lbl_prompt_reference_status.config(
                text=self._prompt_reference_summary_text(),
                fg=self.color_info if self.cfg.get("prompt_reference_enabled") else self.color_text_sec,
            )
        if not hasattr(self, "prompt_reference_rows_frame"):
            return
        for child in self.prompt_reference_rows_frame.winfo_children():
            child.destroy()
        self.prompt_reference_row_vars = []
        items = list(self.cfg.get("prompt_reference_items", []) or [])
        if not items:
            hint = tk.Label(
                self.prompt_reference_rows_frame,
                text="아직 레퍼런스가 없습니다. `+ 레퍼런스 추가`로 한 줄씩 만들 수 있습니다.",
                bg=self.color_bg,
                fg=self.color_text_sec,
                font=self.font_small,
            )
            hint.pack(anchor="w", pady=(2, 4))
            return
        for idx, item in enumerate(items):
            row = tk.Frame(self.prompt_reference_rows_frame, bg=self.color_bg)
            row.pack(fill="x", pady=(0, 6))
            item = self._normalize_prompt_reference_item(item)
            name_var = tk.StringVar(value=item.get("name", ""))
            tag_var = tk.StringVar(value=item.get("asset_tag", ""))
            spec_var = tk.StringVar(value=item.get("scene_spec", ""))
            tk.Label(row, text=f"레퍼런스 {idx + 1}", bg=self.color_bg, font=self.font_small).pack(side="left")
            tk.Label(row, text="이름", bg=self.color_bg, font=self.font_small).pack(side="left", padx=(10, 4))
            name_entry = tk.Entry(row, textvariable=name_var, width=10, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_small)
            name_entry.pack(side="left", padx=(0, 6), ipady=2)
            tk.Label(row, text="참조 번호", bg=self.color_bg, font=self.font_small).pack(side="left", padx=(4, 4))
            tag_entry = tk.Entry(row, textvariable=tag_var, width=9, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_mono_small)
            tag_entry.pack(side="left", padx=(0, 6), ipady=2)
            tk.Label(row, text="장면 번호", bg=self.color_bg, font=self.font_small).pack(side="left", padx=(4, 4))
            spec_entry = tk.Entry(row, textvariable=spec_var, width=24, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_mono_small)
            spec_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=2)
            ttk.Button(row, text="삭제", command=lambda i=idx: self.on_delete_prompt_reference_item(i), style="ControlCompact.TButton").pack(side="left")
            for widget in (name_entry, tag_entry, spec_entry):
                widget.bind("<FocusOut>", self.on_option_toggle)
                widget.bind("<Return>", self.on_option_toggle)
                widget.bind("<KeyRelease>", self.on_option_toggle)
            self.prompt_reference_row_vars.append({
                "name": name_var,
                "asset_tag": tag_var,
                "scene_spec": spec_var,
            })

    def _project_profile_preview(self, item):
        return str(item.get("project_name", "") or "").strip() or "이름 없음"

    def _sync_project_profile_ui(self):
        if not hasattr(self, "project_profile_listbox"):
            return
        profiles = self.cfg.get("project_profiles", [])
        self.project_profile_listbox.delete(0, "end")
        for item in profiles:
            self.project_profile_listbox.insert("end", self._project_profile_preview(item))
        active = self._clamp_project_profile_index(self.cfg.get("active_project_profile", 0))
        if profiles:
            self.project_profile_listbox.selection_clear(0, "end")
            self.project_profile_listbox.selection_set(active)
            self.project_profile_listbox.activate(active)
            self.project_profile_listbox.see(active)
            profile = profiles[active]
        else:
            profile = {"project_name": "", "url": ""}

        if hasattr(self, "pipeline_profile_name_var"):
            self.pipeline_profile_name_var.set(str(profile.get("project_name", "") or ""))
        if hasattr(self, "pipeline_profile_url_var"):
            self.pipeline_profile_url_var.set(str(profile.get("url", "") or ""))
        if hasattr(self, "lbl_pipeline_profile_status"):
            count = len(profiles)
            status = f"저장된 프로젝트 {count}개"
            if count:
                status += f" | 현재 선택: {self._project_profile_preview(profile)}"
            self.lbl_pipeline_profile_status.config(text=status)

    def _save_pipeline_profile_fields(self):
        if not hasattr(self, "pipeline_profile_name_var"):
            return
        profiles = self.cfg.get("project_profiles", [])
        if not profiles:
            return
        active = self._clamp_project_profile_index(self.cfg.get("active_project_profile", 0))
        profile = profiles[active]
        name = str(self.pipeline_profile_name_var.get() or "").strip() or "프로젝트"
        url = str(self.pipeline_profile_url_var.get() or "").strip()
        changed = False
        if profile.get("project_name") != name:
            profile["project_name"] = name
            changed = True
        if profile.get("url") != url:
            profile["url"] = url
            changed = True
        if changed:
            self.save_config()
            self._sync_project_profile_ui()

    def on_pipeline_profile_select(self, event=None):
        if not hasattr(self, "project_profile_listbox"):
            return
        try:
            selection = self.project_profile_listbox.curselection()
            if not selection:
                return
            idx = int(selection[0])
        except Exception:
            return
        self.cfg["active_project_profile"] = self._clamp_project_profile_index(idx)
        self.save_config()
        self._sync_project_profile_ui()

    def on_add_project_profile(self):
        base_name = simpledialog.askstring("프로젝트 추가", "새 프로젝트 이름을 입력하세요:", parent=self.pipeline_window)
        if base_name is None:
            return
        name = self._make_unique_project_profile_name(base_name)
        profiles = self.cfg.get("project_profiles", [])
        profiles.append({"project_name": name, "url": ""})
        self.cfg["active_project_profile"] = len(profiles) - 1
        self.save_config()
        self._sync_project_profile_ui()
        self.log(f"📁 프로젝트 추가: {name}")

    def on_rename_project_profile(self):
        profiles = self.cfg.get("project_profiles", [])
        if not profiles:
            return
        active = self._clamp_project_profile_index(self.cfg.get("active_project_profile", 0))
        current_name = str(profiles[active].get("project_name", "") or "").strip() or "프로젝트"
        new_name = simpledialog.askstring("이름 변경", "새 프로젝트 이름을 입력하세요:", initialvalue=current_name, parent=self.pipeline_window)
        if new_name is None:
            return
        new_name = self._make_unique_project_profile_name(new_name)
        profiles[active]["project_name"] = new_name
        self.save_config()
        self._sync_project_profile_ui()
        self.log(f"✏️ 프로젝트 이름 변경: {current_name} -> {new_name}")

    def on_delete_project_profile(self):
        profiles = self.cfg.get("project_profiles", [])
        if len(profiles) <= 1:
            messagebox.showwarning("삭제 불가", "프로젝트는 최소 1개 이상 있어야 합니다.", parent=self.pipeline_window)
            return
        active = self._clamp_project_profile_index(self.cfg.get("active_project_profile", 0))
        name = str(profiles[active].get("project_name", "") or "").strip() or "프로젝트"
        if not messagebox.askyesno("삭제 확인", f"'{name}' 프로젝트를 삭제할까요?", parent=self.pipeline_window):
            return
        profiles.pop(active)
        self.cfg["active_project_profile"] = self._clamp_project_profile_index(active, default=0)
        for step in self.cfg.get("pipeline_steps", []) or []:
            try:
                idx = int(step.get("project_profile", 0))
            except Exception:
                idx = 0
            if idx > active:
                step["project_profile"] = idx - 1
            elif idx == active:
                step["project_profile"] = min(active, max(len(profiles) - 1, 0))
        self.save_config()
        self._sync_project_profile_ui()
        self._sync_pipeline_step_ui()
        self.log(f"🗑 프로젝트 삭제: {name}")

    def on_save_project_profile_detail(self, event=None):
        self._save_pipeline_profile_fields()
        if hasattr(self, "lbl_pipeline_profile_status"):
            self.lbl_pipeline_profile_status.config(
                text=f"저장 완료 | 현재 선택: {self._project_profile_preview(self.cfg['project_profiles'][self._clamp_project_profile_index(self.cfg.get('active_project_profile', 0))])}"
            )
        self._sync_pipeline_step_ui()

    def _pipeline_type_labels(self):
        return {
            "prompt": "프롬프트 자동화",
            "asset": "S반복 자동화",
            "download": "다운로드 자동화",
        }

    def _pipeline_type_values(self):
        return {v: k for k, v in self._pipeline_type_labels().items()}

    def _pipeline_mode_labels(self):
        return {"image": "이미지", "video": "동영상"}

    def _pipeline_mode_values(self):
        return {v: k for k, v in self._pipeline_mode_labels().items()}

    def _pipeline_download_quality_options(self, mode="video"):
        mode = "image" if str(mode or "").strip().lower() == "image" else "video"
        if mode == "image":
            return ("1K", "2K", "4K")
        return ("1080P", "720P", "4K")

    def _normalize_pipeline_quality(self, quality, mode="video"):
        quality = str(quality or "").strip().upper()
        allowed = self._pipeline_download_quality_options(mode)
        if quality in allowed:
            return quality
        if mode == "image":
            return "4K"
        return "1080P"

    def _prompt_slot_names(self):
        return [str(slot.get("name", "") or f"슬롯 {idx+1}") for idx, slot in enumerate(self.cfg.get("prompt_slots", []) or [])]

    def _load_prompts_from_file_name(self, file_name):
        file_name = str(file_name or "").strip()
        if not file_name:
            return []
        path = self.base / file_name
        if not path.exists():
            return []
        try:
            raw = path.read_text(encoding="utf-8")
        except Exception:
            return []
        sep = self.cfg.get("prompts_separator", "|||")
        return [part.strip() for part in raw.split(sep) if part.strip()]

    def _pipeline_prompt_slot_summary(self, slot_idx):
        slots = self.cfg.get("prompt_slots", []) or []
        if not slots:
            return "프롬프트 파일이 없습니다."
        slot_idx = self._clamp_slot_index(slot_idx)
        slot = slots[slot_idx]
        file_name = str(slot.get("file", "") or "").strip()
        prompts = self._load_prompts_from_file_name(file_name)
        if not file_name:
            return "프롬프트 파일 연결이 없습니다."
        if not prompts:
            return f"{file_name} | 프롬프트 없음"
        return f"{file_name} | 총 {len(prompts)}개 | 1~{len(prompts)}"

    def _asset_prompt_slot_data(self):
        slots = self.cfg.get("prompt_slots", []) or []
        if not slots:
            return {
                "slot_name": "",
                "file_name": "",
                "entries": [],
                "tagged_prompts": {},
                "common_prompt": "",
                "mode": "empty",
            }
        slot_idx = self._clamp_slot_index(self.cfg.get("asset_prompt_slot", 0))
        slot = slots[slot_idx]
        slot_name = str(slot.get("name", "") or f"슬롯 {slot_idx + 1}")
        file_name = str(slot.get("file", "") or "").strip()
        entries = self._load_prompts_from_file_name(file_name)
        prefix = (self.cfg.get("asset_loop_prefix") or "S").strip() or "S"
        tag_pattern = re.compile(rf"^\s*({re.escape(prefix)}\d+)\s*::\s*(.*)\s*$", re.IGNORECASE | re.DOTALL)
        tagged_prompts = {}
        common_prompt = ""
        for entry in entries:
            raw_text = str(entry or "").strip()
            if not raw_text:
                continue
            match = tag_pattern.match(raw_text)
            if match:
                tag = match.group(1).strip().upper()
                body = match.group(2).strip()
                if body:
                    tagged_prompts[tag] = body
                continue
            if not common_prompt:
                common_prompt = raw_text
        mode = "tagged" if tagged_prompts else ("sequential" if entries else "empty")
        return {
            "slot_name": slot_name,
            "file_name": file_name,
            "entries": entries,
            "tagged_prompts": tagged_prompts,
            "common_prompt": common_prompt,
            "mode": mode,
        }

    def _asset_prompt_slot_summary(self):
        if not self.cfg.get("asset_use_prompt_slot"):
            return "공통 프롬프트 템플릿 사용"
        data = self._asset_prompt_slot_data()
        if not data.get("slot_name"):
            return "개별 프롬프트 파일이 없습니다."
        slot_name = data.get("slot_name", "")
        file_name = data.get("file_name", "")
        if not file_name:
            return f"{slot_name} | 파일 연결 없음"
        entries = list(data.get("entries", []) or [])
        if not entries:
            return f"{slot_name} | {file_name} | 프롬프트 없음"
        if data.get("mode") == "tagged":
            tagged_count = len(data.get("tagged_prompts", {}) or {})
            has_common = bool(data.get("common_prompt"))
            common_text = " + 공통 fallback" if has_common else ""
            return f"{slot_name} | {file_name} | 태그형 {tagged_count}개{common_text}"
        return f"{slot_name} | {file_name} | 총 {len(entries)}개 | S001=1번, S002=2번..."

    def _refresh_asset_prompt_slot_controls(self):
        slot_names = self._prompt_slot_names()
        self.cfg["asset_prompt_slot"] = self._clamp_slot_index(self.cfg.get("asset_prompt_slot", 0))
        if hasattr(self, "combo_asset_prompt_slot"):
            self.combo_asset_prompt_slot["values"] = slot_names
            if slot_names:
                self.combo_asset_prompt_slot.current(self._clamp_slot_index(self.cfg.get("asset_prompt_slot", 0)))
        if hasattr(self, "lbl_asset_prompt_source_status"):
            self.lbl_asset_prompt_source_status.config(
                text=self._asset_prompt_slot_summary(),
                fg=self.color_info if self.cfg.get("asset_use_prompt_slot") else self.color_text_sec,
            )

    def _pipeline_active_step(self):
        steps = self.cfg.get("pipeline_steps", []) or []
        if not steps:
            return None, None
        active = self._clamp_pipeline_step_index(self.cfg.get("active_pipeline_step", 0))
        return steps[active], active

    def _refresh_pipeline_step_editor_state(self):
        step, _active = self._pipeline_active_step()
        step_type = self._pipeline_type_values().get(
            str(self.pipeline_step_type_var.get() or "").strip(),
            str((step or {}).get("type", "prompt") or "prompt").strip().lower(),
        ) if hasattr(self, "pipeline_step_type_var") else str((step or {}).get("type", "prompt") or "prompt").strip().lower()
        download_mode = self._pipeline_mode_values().get(
            str(self.pipeline_step_download_mode_var.get() or "").strip(),
            str((step or {}).get("download_mode", "video") or "video").strip().lower(),
        ) if hasattr(self, "pipeline_step_download_mode_var") else str((step or {}).get("download_mode", "video") or "video").strip().lower()
        if step_type not in {"prompt", "asset", "download"}:
            step_type = "prompt"
        if download_mode not in {"image", "video"}:
            download_mode = "video"

        if step_type == "prompt":
            fixed_mode = "image"
        elif step_type == "asset":
            fixed_mode = "video"
        else:
            fixed_mode = "image" if download_mode == "image" else "video"

        if hasattr(self, "pipeline_step_media_mode_var"):
            self.pipeline_step_media_mode_var.set(self._pipeline_mode_labels().get(fixed_mode, "이미지"))
        if hasattr(self, "combo_pipeline_media_mode"):
            self.combo_pipeline_media_mode.config(state="disabled")

        prompt_enabled = (step_type == "prompt")
        if hasattr(self, "combo_pipeline_prompt_slot"):
            self.combo_pipeline_prompt_slot.config(state="readonly" if prompt_enabled else "disabled")
        if hasattr(self, "lbl_pipeline_prompt_slot"):
            self.lbl_pipeline_prompt_slot.config(fg=self.color_text if prompt_enabled else self.color_text_sec)
        if hasattr(self, "lbl_pipeline_prompt_range"):
            if prompt_enabled:
                slot_idx = 0
                if hasattr(self, "combo_pipeline_prompt_slot") and self.combo_pipeline_prompt_slot.current() >= 0:
                    slot_idx = self.combo_pipeline_prompt_slot.current()
                elif step is not None:
                    slot_idx = self._clamp_slot_index(step.get("prompt_slot", self.cfg.get("active_prompt_slot", 0)))
                self.lbl_pipeline_prompt_range.config(text=self._pipeline_prompt_slot_summary(slot_idx), fg=self.color_info)
            else:
                self.lbl_pipeline_prompt_range.config(text="프롬프트 자동화를 선택하면 파일과 범위가 표시됩니다.", fg=self.color_text_sec)

        if hasattr(self, "combo_pipeline_download_mode"):
            self.combo_pipeline_download_mode.config(state="readonly")
        if hasattr(self, "combo_pipeline_quality"):
            values = self._pipeline_download_quality_options(download_mode)
            self.combo_pipeline_quality["values"] = values
            current_quality = str(self.pipeline_step_quality_var.get() or "").strip()
            normalized_quality = self._normalize_pipeline_quality(current_quality, download_mode)
            self.pipeline_step_quality_var.set(normalized_quality)
            self.combo_pipeline_quality.config(state="readonly")
        if hasattr(self, "lbl_pipeline_quality"):
            self.lbl_pipeline_quality.config(fg=self.color_text)

        if hasattr(self, "entry_pipeline_output_dir"):
            self.entry_pipeline_output_dir.config(state="readonly")
        if hasattr(self, "btn_pipeline_output_dir"):
            self.btn_pipeline_output_dir.config(state="normal")
        if hasattr(self, "lbl_pipeline_output_dir"):
            self.lbl_pipeline_output_dir.config(fg=self.color_text)

    def _default_pipeline_step(self, step_no=1):
        return {
            "name": f"{step_no}번 작업",
            "type": "prompt",
            "project_profile": 0,
            "prompt_slot": self._clamp_slot_index(self.cfg.get("active_prompt_slot", 0)),
            "start": 1,
            "end": 1,
            "manual_selection": "",
            "interval_seconds": int(self.cfg.get("interval_seconds", 180) or 180),
            "media_mode": "image",
            "download_mode": "video",
            "quality": "1080P",
            "output_dir": "",
        }

    def _clamp_pipeline_step_index(self, idx, default=0):
        steps = self.cfg.get("pipeline_steps", [])
        if not steps:
            return 0
        try:
            idx = int(idx)
        except (TypeError, ValueError):
            idx = default
        return max(0, min(len(steps) - 1, idx))

    def _pipeline_profile_names(self):
        return [self._project_profile_preview(item) for item in self.cfg.get("project_profiles", [])]

    def _make_unique_pipeline_step_name(self, base_name):
        base_name = str(base_name or "").strip() or "작업"
        existing = {str(item.get("name", "")).strip() for item in self.cfg.get("pipeline_steps", [])}
        if base_name not in existing:
            return base_name
        suffix = 2
        while True:
            candidate = f"{base_name} ({suffix})"
            if candidate not in existing:
                return candidate
            suffix += 1

    def _ensure_pipeline_steps(self):
        changed = False
        raw_steps = self.cfg.get("pipeline_steps", [])
        normalized = []
        if isinstance(raw_steps, list):
            for idx, item in enumerate(raw_steps, start=1):
                if not isinstance(item, dict):
                    continue
                step_type = str(item.get("type", "prompt") or "prompt").strip().lower()
                if step_type not in {"prompt", "asset", "download"}:
                    step_type = "prompt"
                media_mode = str(item.get("media_mode", "image") or "image").strip().lower()
                if media_mode not in {"image", "video"}:
                    media_mode = "image"
                download_mode = str(item.get("download_mode", "video") or "video").strip().lower()
                if download_mode not in {"image", "video"}:
                    download_mode = "video"
                try:
                    project_profile = self._clamp_project_profile_index(item.get("project_profile", 0))
                except Exception:
                    project_profile = 0
                try:
                    start = max(1, int(item.get("start", 1)))
                except Exception:
                    start = 1
                try:
                    end = max(1, int(item.get("end", start)))
                except Exception:
                    end = start
                if start > end:
                    start, end = end, start
                try:
                    interval_seconds = max(1, int(item.get("interval_seconds", self.cfg.get("interval_seconds", 180) or 180)))
                except Exception:
                    interval_seconds = int(self.cfg.get("interval_seconds", 180) or 180)
                normalized.append({
                    "name": str(item.get("name", "") or f"{idx}번 작업").strip() or f"{idx}번 작업",
                    "type": step_type,
                    "project_profile": project_profile,
                    "prompt_slot": self._clamp_slot_index(item.get("prompt_slot", self.cfg.get("active_prompt_slot", 0))),
                    "start": start,
                    "end": end,
                    "manual_selection": str(item.get("manual_selection", "") or "").strip(),
                    "interval_seconds": interval_seconds,
                    "media_mode": "image" if step_type == "prompt" else ("video" if step_type == "asset" else media_mode),
                    "download_mode": download_mode,
                    "quality": self._normalize_pipeline_quality(item.get("quality", "1080P"), download_mode),
                    "output_dir": str(item.get("output_dir", "") or "").strip(),
                })
        if not normalized:
            normalized = [self._default_pipeline_step(1)]
            changed = True
        if raw_steps != normalized:
            self.cfg["pipeline_steps"] = normalized
            changed = True
        active = self._clamp_pipeline_step_index(self.cfg.get("active_pipeline_step", 0))
        if self.cfg.get("active_pipeline_step") != active:
            self.cfg["active_pipeline_step"] = active
            changed = True
        if changed:
            self.save_config()

    def _pipeline_step_preview(self, step, idx):
        type_label = self._pipeline_type_labels().get(step.get("type", "prompt"), "프롬프트 자동화")
        return f"{idx+1}. {step.get('name', f'{idx+1}번 작업')} | {type_label}"

    def _sync_pipeline_step_ui(self):
        if not hasattr(self, "pipeline_step_listbox"):
            return
        steps = self.cfg.get("pipeline_steps", [])
        self.pipeline_step_listbox.delete(0, "end")
        for idx, step in enumerate(steps):
            self.pipeline_step_listbox.insert("end", self._pipeline_step_preview(step, idx))
        active = self._clamp_pipeline_step_index(self.cfg.get("active_pipeline_step", 0))
        profiles = self._pipeline_profile_names()
        if hasattr(self, "combo_pipeline_project_profile"):
            self.combo_pipeline_project_profile["values"] = profiles
        if steps:
            self.pipeline_step_listbox.selection_clear(0, "end")
            self.pipeline_step_listbox.selection_set(active)
            self.pipeline_step_listbox.activate(active)
            self.pipeline_step_listbox.see(active)
            step = steps[active]
        else:
            step = self._default_pipeline_step(1)
        if hasattr(self, "pipeline_step_name_var"):
            self.pipeline_step_name_var.set(str(step.get("name", "") or ""))
        if hasattr(self, "pipeline_step_type_var"):
            self.pipeline_step_type_var.set(self._pipeline_type_labels().get(step.get("type", "prompt"), "프롬프트 자동화"))
        if hasattr(self, "combo_pipeline_prompt_slot"):
            slot_names = self._prompt_slot_names()
            self.combo_pipeline_prompt_slot["values"] = slot_names
            if slot_names:
                self.combo_pipeline_prompt_slot.current(self._clamp_slot_index(step.get("prompt_slot", self.cfg.get("active_prompt_slot", 0))))
        if hasattr(self, "pipeline_step_start_var"):
            self.pipeline_step_start_var.set(str(step.get("start", 1)))
        if hasattr(self, "pipeline_step_end_var"):
            self.pipeline_step_end_var.set(str(step.get("end", 1)))
        if hasattr(self, "pipeline_step_manual_var"):
            self.pipeline_step_manual_var.set(str(step.get("manual_selection", "") or ""))
        if hasattr(self, "pipeline_step_interval_var"):
            self.pipeline_step_interval_var.set(str(step.get("interval_seconds", self.cfg.get("interval_seconds", 180) or 180)))
        if hasattr(self, "pipeline_step_media_mode_var"):
            self.pipeline_step_media_mode_var.set(self._pipeline_mode_labels().get(step.get("media_mode", "image"), "이미지"))
        if hasattr(self, "pipeline_step_download_mode_var"):
            self.pipeline_step_download_mode_var.set(self._pipeline_mode_labels().get(step.get("download_mode", "video"), "동영상"))
        if hasattr(self, "pipeline_step_quality_var"):
            self.pipeline_step_quality_var.set(str(step.get("quality", "1080P") or "1080P"))
        if hasattr(self, "pipeline_step_output_dir_var"):
            self.pipeline_step_output_dir_var.set(str(step.get("output_dir", "") or ""))
        if hasattr(self, "combo_pipeline_project_profile") and profiles:
            profile_idx = self._clamp_project_profile_index(step.get("project_profile", 0))
            self.combo_pipeline_project_profile.current(profile_idx)
        self._refresh_pipeline_step_editor_state()
        if hasattr(self, "lbl_pipeline_step_status"):
            self.lbl_pipeline_step_status.config(text=f"저장된 작업 단계 {len(steps)}개")

    def _save_pipeline_step_fields(self, event=None):
        if not hasattr(self, "pipeline_step_name_var"):
            return
        steps = self.cfg.get("pipeline_steps", [])
        if not steps:
            return
        active = self._clamp_pipeline_step_index(self.cfg.get("active_pipeline_step", 0))
        step = steps[active]
        type_value = self._pipeline_type_values().get(str(self.pipeline_step_type_var.get() or "").strip(), "prompt")
        download_mode = self._pipeline_mode_values().get(str(self.pipeline_step_download_mode_var.get() or "").strip(), "video")
        prompt_slot_idx = self._clamp_slot_index(step.get("prompt_slot", self.cfg.get("active_prompt_slot", 0)))
        if hasattr(self, "combo_pipeline_prompt_slot") and self.combo_pipeline_prompt_slot.current() >= 0:
            prompt_slot_idx = self.combo_pipeline_prompt_slot.current()
        try:
            start = max(1, int(str(self.pipeline_step_start_var.get() or "1").strip()))
        except Exception:
            start = 1
        try:
            end = max(1, int(str(self.pipeline_step_end_var.get() or start).strip()))
        except Exception:
            end = start
        if start > end:
            start, end = end, start
        try:
            interval_seconds = max(1, int(str(self.pipeline_step_interval_var.get() or self.cfg.get("interval_seconds", 180)).strip()))
        except Exception:
            interval_seconds = int(self.cfg.get("interval_seconds", 180) or 180)
        profile_idx = 0
        if hasattr(self, "combo_pipeline_project_profile") and self.combo_pipeline_project_profile.current() >= 0:
            profile_idx = self.combo_pipeline_project_profile.current()
        media_mode = "image" if type_value == "prompt" else ("video" if type_value == "asset" else ("image" if download_mode == "image" else "video"))
        step["name"] = str(self.pipeline_step_name_var.get() or "").strip() or f"{active+1}번 작업"
        step["type"] = type_value
        step["project_profile"] = self._clamp_project_profile_index(profile_idx)
        step["prompt_slot"] = prompt_slot_idx
        step["start"] = start
        step["end"] = end
        step["manual_selection"] = str(self.pipeline_step_manual_var.get() or "").strip()
        step["interval_seconds"] = interval_seconds
        step["media_mode"] = media_mode
        step["download_mode"] = download_mode
        step["quality"] = self._normalize_pipeline_quality(self.pipeline_step_quality_var.get(), download_mode)
        step["output_dir"] = str(self.pipeline_step_output_dir_var.get() or "").strip() if type_value == "download" else str(step.get("output_dir", "") or "").strip()
        self.save_config()
        self._sync_pipeline_step_ui()
        if hasattr(self, "lbl_pipeline_step_status"):
            self.lbl_pipeline_step_status.config(text=f"저장 완료 | 현재 단계: {step['name']}")

    def on_pipeline_step_type_change(self, event=None):
        self._refresh_pipeline_step_editor_state()
        self._save_pipeline_step_fields()

    def on_pipeline_step_download_mode_change(self, event=None):
        self._refresh_pipeline_step_editor_state()
        self._save_pipeline_step_fields()

    def on_pipeline_step_prompt_slot_change(self, event=None):
        self._refresh_pipeline_step_editor_state()
        self._save_pipeline_step_fields()

    def on_pick_pipeline_output_dir(self):
        self._save_pipeline_step_fields()
        step, _active = self._pipeline_active_step()
        initial = ""
        if step is not None:
            initial = str(step.get("output_dir", "") or "").strip()
        if not initial:
            initial = str(self.cfg.get("download_output_dir", "") or "").strip()
        if not initial:
            initial = str(self._resolve_download_output_dir())
        try:
            initial_path = Path(initial).expanduser()
        except Exception:
            initial_path = Path.home()
        if not initial_path.exists():
            initial_path = self._resolve_download_output_dir()
        if not initial_path.exists():
            initial_path = Path.home()
        picked = filedialog.askdirectory(
            parent=self.pipeline_window,
            initialdir=str(initial_path),
            mustexist=False,
            title="이어달리기 저장 폴더 선택",
        )
        if not picked:
            return
        self.pipeline_step_output_dir_var.set(picked)
        self._save_pipeline_step_fields()

    def on_pipeline_step_select(self, event=None):
        if not hasattr(self, "pipeline_step_listbox"):
            return
        try:
            selection = self.pipeline_step_listbox.curselection()
            if not selection:
                return
            idx = int(selection[0])
        except Exception:
            return
        self.cfg["active_pipeline_step"] = self._clamp_pipeline_step_index(idx)
        self.save_config()
        self._sync_pipeline_step_ui()

    def on_add_pipeline_step(self):
        steps = self.cfg.get("pipeline_steps", [])
        steps.append(self._default_pipeline_step(len(steps) + 1))
        self.cfg["active_pipeline_step"] = len(steps) - 1
        self.save_config()
        self._sync_pipeline_step_ui()
        self.log(f"🧩 이어달리기 작업 추가: {len(steps)}번 작업")

    def on_duplicate_pipeline_step(self):
        steps = self.cfg.get("pipeline_steps", [])
        if not steps:
            return
        active = self._clamp_pipeline_step_index(self.cfg.get("active_pipeline_step", 0))
        copied = dict(steps[active])
        copied["name"] = self._make_unique_pipeline_step_name(str(copied.get("name", "") or f"{active+1}번 작업 복사"))
        steps.insert(active + 1, copied)
        self.cfg["active_pipeline_step"] = active + 1
        self.save_config()
        self._sync_pipeline_step_ui()
        self.log(f"📄 이어달리기 작업 복제: {copied['name']}")

    def on_delete_pipeline_step(self):
        steps = self.cfg.get("pipeline_steps", [])
        if len(steps) <= 1:
            messagebox.showwarning("삭제 불가", "작업 단계는 최소 1개 이상 있어야 합니다.", parent=self.pipeline_window)
            return
        active = self._clamp_pipeline_step_index(self.cfg.get("active_pipeline_step", 0))
        name = str(steps[active].get("name", "") or f"{active+1}번 작업")
        if not messagebox.askyesno("삭제 확인", f"'{name}' 작업을 삭제할까요?", parent=self.pipeline_window):
            return
        steps.pop(active)
        self.cfg["active_pipeline_step"] = self._clamp_pipeline_step_index(active, default=0)
        self.save_config()
        self._sync_pipeline_step_ui()
        self.log(f"🗑 이어달리기 작업 삭제: {name}")

    def on_move_pipeline_step(self, direction):
        steps = self.cfg.get("pipeline_steps", [])
        if len(steps) <= 1:
            return
        active = self._clamp_pipeline_step_index(self.cfg.get("active_pipeline_step", 0))
        target = active + int(direction)
        if not (0 <= target < len(steps)):
            return
        steps[active], steps[target] = steps[target], steps[active]
        self.cfg["active_pipeline_step"] = target
        self.save_config()
        self._sync_pipeline_step_ui()

    def _pipeline_prompt_selection_text(self, step):
        raw = str(step.get("manual_selection", "") or "").strip()
        if raw:
            return raw
        start = max(1, int(step.get("start", 1) or 1))
        end = max(1, int(step.get("end", start) or start))
        if start > end:
            start, end = end, start
        return f"{start}-{end}"

    def _focus_work_target(self, target):
        try:
            if hasattr(self, "_set_asset_open"):
                self._set_asset_open(target == "asset")
            if hasattr(self, "_set_dl_open"):
                self._set_dl_open(target == "download")
            if hasattr(self, "_set_relay_open"):
                self._set_relay_open(False)
            if hasattr(self, "_set_sched_open"):
                self._set_sched_open(False)
            if hasattr(self, "left_canvas"):
                if target == "prompt":
                    self.left_canvas.yview_moveto(0.0)
                elif target == "asset":
                    self.left_canvas.yview_moveto(0.30)
                elif target == "download":
                    self.left_canvas.yview_moveto(0.52)
                else:
                    self.left_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _apply_pipeline_step_to_work_config(self, step_index=None, open_root=True):
        self.on_save_project_profile_detail()
        self._save_pipeline_step_fields()
        steps = self.cfg.get("pipeline_steps", [])
        if not steps:
            return None
        active = self._clamp_pipeline_step_index(
            self.cfg.get("active_pipeline_step", 0) if step_index is None else step_index
        )
        step = steps[active]
        profiles = self.cfg.get("project_profiles", [])
        profile_idx = self._clamp_project_profile_index(step.get("project_profile", 0))
        profile = profiles[profile_idx] if profiles else self._default_project_profile()
        target = str(step.get("type", "prompt") or "prompt").strip().lower()
        if open_root:
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass
        if hasattr(self, "start_url_var"):
            self.start_url_var.set(str(profile.get("url", "") or ""))
        if hasattr(self, "entry_interval"):
            try:
                self.entry_interval.delete(0, "end")
                self.entry_interval.insert(0, str(step.get("interval_seconds", self.cfg.get("interval_seconds", 180) or 180)))
            except Exception:
                pass
        prompt_selection = self._pipeline_prompt_selection_text(step)
        self.cfg["start_url"] = str(profile.get("url", "") or "").strip()
        self.cfg["interval_seconds"] = int(step.get("interval_seconds", self.cfg.get("interval_seconds", 180) or 180) or 180)
        self.cfg["pipeline_last_project_name"] = str(profile.get("project_name", "") or "").strip()
        self.cfg["asset_loop_start"] = max(1, int(step.get("start", 1) or 1))
        self.cfg["asset_loop_end"] = max(1, int(step.get("end", self.cfg["asset_loop_start"]) or self.cfg["asset_loop_start"]))
        self.pipeline_active_output_dir = ""
        if target == "prompt":
            self._set_run_mode("prompt")
            self.cfg["asset_loop_enabled"] = False
            if hasattr(self, "asset_loop_var"):
                self.asset_loop_var.set(False)
            self.cfg["prompt_manual_selection"] = prompt_selection
            if hasattr(self, "prompt_manual_selection_var"):
                self.prompt_manual_selection_var.set(prompt_selection)
            prompt_slot_idx = self._clamp_slot_index(step.get("prompt_slot", self.cfg.get("active_prompt_slot", 0)))
            self.cfg["active_prompt_slot"] = prompt_slot_idx
            prompt_slots = self.cfg.get("prompt_slots", []) or []
            if prompt_slots:
                self.cfg["prompts_file"] = str(prompt_slots[prompt_slot_idx].get("file", self.cfg.get("prompts_file", "flow_prompts.txt")) or self.cfg.get("prompts_file", "flow_prompts.txt"))
                if hasattr(self, "combo_slots"):
                    try:
                        self.combo_slots.current(prompt_slot_idx)
                    except Exception:
                        pass
            self.cfg["prompt_media_mode"] = "image"
            if hasattr(self, "prompt_media_mode_var"):
                self.prompt_media_mode_var.set(PROMPT_MEDIA_LABELS.get(self.cfg["prompt_media_mode"], "이미지"))
            target_key = "prompt"
        elif target == "asset":
            self._set_run_mode("asset")
            self.cfg["asset_loop_enabled"] = True
            if hasattr(self, "asset_loop_var"):
                self.asset_loop_var.set(True)
            manual_text = str(step.get("manual_selection", "") or "").strip()
            self.cfg["asset_manual_selection"] = manual_text
            if hasattr(self, "asset_manual_selection_var"):
                self.asset_manual_selection_var.set(manual_text)
            if hasattr(self, "asset_loop_start_var"):
                self.asset_loop_start_var.set(self._format_asset_number_text(self.cfg["asset_loop_start"]))
            if hasattr(self, "asset_loop_end_var"):
                self.asset_loop_end_var.set(self._format_asset_number_text(self.cfg["asset_loop_end"]))
            self.cfg["asset_prompt_media_mode"] = "video"
            if hasattr(self, "asset_prompt_media_mode_var"):
                self.asset_prompt_media_mode_var.set(PROMPT_MEDIA_LABELS.get(self.cfg["asset_prompt_media_mode"], "영상"))
            target_key = "asset"
        else:
            self._set_run_mode("download")
            self.cfg["asset_loop_enabled"] = False
            if hasattr(self, "asset_loop_var"):
                self.asset_loop_var.set(False)
            manual_text = str(step.get("manual_selection", "") or "").strip()
            self.cfg["asset_manual_selection"] = manual_text
            if hasattr(self, "asset_manual_selection_var"):
                self.asset_manual_selection_var.set(manual_text)
            if hasattr(self, "asset_loop_start_var"):
                self.asset_loop_start_var.set(self._format_asset_number_text(self.cfg["asset_loop_start"]))
            if hasattr(self, "asset_loop_end_var"):
                self.asset_loop_end_var.set(self._format_asset_number_text(self.cfg["asset_loop_end"]))
            self.cfg["download_mode"] = str(step.get("download_mode", "video") or "video")
            if hasattr(self, "download_mode_var"):
                self.download_mode_var.set(self.cfg["download_mode"])
            quality = str(step.get("quality", "1080P") or "1080P").strip() or "1080P"
            if self.cfg["download_mode"] == "video":
                self.cfg["download_video_quality"] = quality
                if hasattr(self, "download_video_quality_var"):
                    self.download_video_quality_var.set(quality)
            else:
                self.cfg["download_image_quality"] = quality
                if hasattr(self, "download_image_quality_var"):
                    self.download_image_quality_var.set(quality)
            self.cfg["download_output_dir"] = str(step.get("output_dir", "") or "").strip()
            self.pipeline_active_output_dir = self.cfg["download_output_dir"]
            if hasattr(self, "download_output_dir_var"):
                self.download_output_dir_var.set(self.cfg["download_output_dir"])
            target_key = "download"
            self.log(f"📁 이어달리기 다운로드 저장 폴더 적용: {self.cfg['download_output_dir'] or str(self._resolve_download_output_dir())}")
        self.on_option_toggle()
        self.save_config()
        if target_key != "download":
            self.on_reload()
        self._focus_work_target(target_key)
        self.log(
            f"🔗 이어달리기 작업 적용: {step.get('name', f'{active+1}번 작업')} | "
            f"{self._pipeline_type_labels().get(target, target)} | 프로젝트={profile.get('project_name', '-') or '-'}"
        )
        if hasattr(self, "lbl_pipeline_runtime_status"):
            self.lbl_pipeline_runtime_status.config(
                text=f"적용 완료 | {step.get('name', f'{active+1}번 작업')} | 프로젝트={profile.get('project_name', '-') or '-'}"
            )
        return step

    def on_apply_pipeline_step_to_work(self):
        step = self._apply_pipeline_step_to_work_config(open_root=True)
        if step is None:
            messagebox.showwarning("안내", "적용할 이어달리기 작업이 없습니다.", parent=self.pipeline_window)
            return

    def on_open_pipeline_bot_work_window(self):
        step = self._apply_pipeline_step_to_work_config(open_root=False)
        if step is None:
            messagebox.showwarning("안내", "먼저 이어달리기 작업을 하나 선택해주세요.", parent=self.pipeline_window)
            return
        self.on_open_bot_work_window()

    def _clear_pipeline_runtime(self, cancelled=False):
        self.pipeline_runtime_active = False
        self.pipeline_run_order = []
        self.pipeline_run_position = -1
        self.pipeline_active_output_dir = ""
        if hasattr(self, "btn_pipeline_start"):
            self.btn_pipeline_start.config(state="normal")
        if hasattr(self, "lbl_pipeline_runtime_status"):
            self.lbl_pipeline_runtime_status.config(
                text="이어달리기 중지됨" if cancelled else "이어달리기 대기 중"
            )

    def _run_pipeline_step_at(self, position):
        if not self.pipeline_runtime_active:
            return
        if not (0 <= position < len(self.pipeline_run_order)):
            self._clear_pipeline_runtime(cancelled=False)
            return
        self.pipeline_run_position = position
        step_index = self.pipeline_run_order[position]
        step = self._apply_pipeline_step_to_work_config(step_index=step_index, open_root=True)
        if step is None:
            self._clear_pipeline_runtime(cancelled=True)
            return
        step_name = str(step.get("name", "") or f"{position+1}번 작업")
        if hasattr(self, "lbl_pipeline_runtime_status"):
            self.lbl_pipeline_runtime_status.config(
                text=f"실행 중 {position+1}/{len(self.pipeline_run_order)} | {step_name}"
            )
        target = str(step.get("type", "prompt") or "prompt").strip().lower()
        runner = self.on_start_prompt
        if target == "asset":
            runner = self.on_start_asset
        elif target == "download":
            runner = self.on_start_download
        self.root.after(250, lambda cb=runner, name=step_name, step=step: self._launch_pipeline_step_runner(cb, name, step))

    def _prepare_pipeline_step_runtime(self, step):
        if not isinstance(step, dict):
            return
        target = str(step.get("type", "prompt") or "prompt").strip().lower()
        if target != "asset":
            return
        try:
            self._ensure_browser_session()
            self.actor.set_page(self.page)
            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url and start_url not in (self.page.url or ""):
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(random.uniform(0.8, 1.8))
            input_selector = (self.cfg.get("input_selector") or "").strip()
            preset_input_locator = None
            if input_selector:
                try:
                    preset_input_locator, _ = self._resolve_prompt_input_locator(input_selector, timeout_ms=2200)
                except Exception:
                    preset_input_locator = None
            self.refresh_detected_media_state(
                ensure_session=False,
                input_locator=preset_input_locator,
                profile="asset",
                write_log=True,
            )
            self.update_status_label("🎛️ 이어달리기 동영상 모드 맞추는 중...", self.color_info)
            self._apply_prompt_generation_preset(input_locator=preset_input_locator, profile="asset")
            self.log("🏃 이어달리기 사전준비 완료: 이미지→동영상 전환 확인")
        except Exception as e:
            self.log(f"⚠️ 이어달리기 S자동화 사전준비 실패(실행은 계속): {e}")

    def _launch_pipeline_step_runner(self, runner, step_name, step=None):
        self._prepare_pipeline_step_runtime(step)
        runner()
        self.root.after(250, lambda: self._check_pipeline_step_started(step_name))

    def _check_pipeline_step_started(self, step_name):
        if not self.pipeline_runtime_active:
            return
        if self.running or self.is_processing or self.paused:
            return
        self._clear_pipeline_runtime(cancelled=True)
        messagebox.showwarning("이어달리기 중단", f"'{step_name}' 작업이 시작되지 않았습니다.\n설정값이나 기본값 확인 문구를 먼저 확인해주세요.", parent=self.pipeline_window)

    def on_start_pipeline_run(self):
        if self.pipeline_runtime_active:
            messagebox.showwarning("안내", "이어달리기가 이미 실행 중입니다.", parent=self.pipeline_window)
            return
        if self.running or self.is_processing or self.paused:
            messagebox.showwarning("안내", "기존 자동화가 실행 중입니다. 먼저 완료 또는 중지 후 시작해주세요.", parent=self.pipeline_window)
            return
        self.on_save_project_profile_detail()
        self._save_pipeline_step_fields()
        steps = self.cfg.get("pipeline_steps", [])
        if not steps:
            messagebox.showwarning("안내", "이어달리기 작업이 없습니다.", parent=self.pipeline_window)
            return
        self.pipeline_runtime_active = True
        self.pipeline_run_order = list(range(len(steps)))
        self.pipeline_run_position = -1
        if hasattr(self, "btn_pipeline_start"):
            self.btn_pipeline_start.config(state="disabled")
        if hasattr(self, "lbl_pipeline_runtime_status"):
            self.lbl_pipeline_runtime_status.config(text=f"이어달리기 시작 준비 | 총 {len(steps)}개 작업")
        self.log(f"🏃 이어달리기 시작 | 총 {len(steps)}개 작업")
        self._run_pipeline_step_at(0)

    def _clamp_slot_index(self, idx, default=0):
        slots = self.cfg.get("prompt_slots", [])
        if not slots:
            return 0
        try:
            idx = int(idx)
        except (TypeError, ValueError):
            idx = default
        return max(0, min(len(slots) - 1, idx))

    def _get_effective_relay_range(self):
        slots = self.cfg.get("prompt_slots", [])
        if not slots:
            return 0, 0
        active = self._clamp_slot_index(self.cfg.get("active_prompt_slot", 0))
        start = self.cfg.get("relay_start_slot")
        end = self.cfg.get("relay_end_slot")

        if start is None or end is None:
            try:
                count = max(1, int(self.cfg.get("relay_count", 1)))
            except (TypeError, ValueError):
                count = 1
            start = active
            end = min(len(slots) - 1, start + count - 1)
        else:
            start = self._clamp_slot_index(start, active)
            end = self._clamp_slot_index(end, active)
            if start > end:
                start, end = end, start
        return start, end

    def _normalize_relay_selected_slots(self, selected):
        slots = self.cfg.get("prompt_slots", [])
        total = len(slots)
        if total <= 0:
            return []
        if not isinstance(selected, (list, tuple)):
            return []
        seen = set()
        out = []
        for raw in selected:
            try:
                idx = int(raw)
            except (TypeError, ValueError):
                continue
            if 0 <= idx < total and idx not in seen:
                out.append(idx)
                seen.add(idx)
        out.sort()
        return out

    def _get_effective_relay_sequence(self):
        slots = self.cfg.get("prompt_slots", [])
        if not slots:
            return []
        if self.cfg.get("relay_use_selection"):
            selected = self._normalize_relay_selected_slots(self.cfg.get("relay_selected_slots", []))
            if selected:
                return selected
        start, end = self._get_effective_relay_range()
        return list(range(start, end + 1))

    def _sync_relay_range_controls(self):
        if not hasattr(self, "combo_relay_start") or not hasattr(self, "combo_relay_end"):
            return
        slots = [s["name"] for s in self.cfg.get("prompt_slots", [])]
        self.combo_relay_start["values"] = slots
        self.combo_relay_end["values"] = slots
        if not slots:
            return
        start, end = self._get_effective_relay_range()
        self.combo_relay_start.current(start)
        self.combo_relay_end.current(end)
        self._sync_relay_selection_label()

    def _sync_relay_selection_label(self):
        if not hasattr(self, "lbl_relay_pick"):
            return
        selected = self._normalize_relay_selected_slots(self.cfg.get("relay_selected_slots", []))
        slot_names = [self.cfg["prompt_slots"][i]["name"] for i in selected]
        mode_txt = "체크사용" if self.cfg.get("relay_use_selection") else "체크미사용"
        if slot_names:
            preview = ", ".join(slot_names[:2])
            if len(slot_names) > 2:
                preview += f" 외 {len(slot_names) - 2}개"
            txt = f"{mode_txt} | {preview}"
        else:
            txt = f"{mode_txt} | 선택 없음(범위 실행)"
        self.lbl_relay_pick.config(text=txt)

    def _make_unique_slot_name(self, base_name):
        existing = {s.get("name", "") for s in self.cfg.get("prompt_slots", [])}
        if base_name not in existing:
            return base_name
        suffix = 2
        while True:
            candidate = f"{base_name} ({suffix})"
            if candidate not in existing:
                return candidate
            suffix += 1

    def _asset_pad_width(self):
        try:
            return max(3, int(self.cfg.get("asset_loop_num_width", 3) or 3))
        except Exception:
            return 3

    def _format_asset_number_text(self, value):
        try:
            num = max(1, int(str(value).strip()))
        except Exception:
            num = 1
        return str(num).zfill(self._asset_pad_width())

    def _parse_manual_number_spec(self, raw_text, upper_bound=None, max_items=500):
        raw = str(raw_text or "").strip()
        if not raw:
            return {
                "raw": "",
                "numbers": [],
                "invalid_tokens": [],
                "out_of_range": [],
                "truncated": False,
            }

        numbers = []
        invalid_tokens = []
        out_of_range = []
        seen = set()
        truncated = False

        for token in [x.strip() for x in raw.split(",") if x.strip()]:
            if "-" in token:
                parts = [p.strip() for p in token.split("-", 1)]
                if len(parts) != 2 or (not parts[0].isdigit()) or (not parts[1].isdigit()):
                    invalid_tokens.append(token)
                    continue
                start_num = int(parts[0])
                end_num = int(parts[1])
                if start_num > end_num:
                    start_num, end_num = end_num, start_num
                values = range(start_num, end_num + 1)
            else:
                if not token.isdigit():
                    invalid_tokens.append(token)
                    continue
                values = [int(token)]

            for value in values:
                if value < 1:
                    invalid_tokens.append(token)
                    continue
                if upper_bound is not None and value > upper_bound:
                    out_of_range.append(value)
                    continue
                if value in seen:
                    continue
                numbers.append(value)
                seen.add(value)
                if len(numbers) >= max_items:
                    truncated = True
                    break
            if truncated:
                break

        return {
            "raw": raw,
            "numbers": numbers,
            "invalid_tokens": invalid_tokens,
            "out_of_range": out_of_range,
            "truncated": truncated,
        }

    def _format_manual_selection_preview(self, numbers, prefix="", pad_width=3, max_preview=8):
        if not numbers:
            return "전체 실행"
        preview_items = []
        for num in numbers[:max_preview]:
            label = str(num).zfill(pad_width)
            preview_items.append(f"{prefix}{label}" if prefix else label)
        preview = ", ".join(preview_items)
        if len(numbers) > max_preview:
            preview += f" 외 {len(numbers) - max_preview}개"
        return f"{len(numbers)}개 선택: {preview}"

    def _compress_numbers_to_spec(self, numbers, pad_width=0):
        cleaned = []
        seen = set()
        for raw in numbers or []:
            try:
                value = int(raw)
            except Exception:
                continue
            if value < 1 or value in seen:
                continue
            seen.add(value)
            cleaned.append(value)
        cleaned.sort()
        if not cleaned:
            return ""

        def _fmt(value):
            text = str(value)
            return text.zfill(pad_width) if pad_width > 0 else text

        parts = []
        start = cleaned[0]
        prev = cleaned[0]
        for value in cleaned[1:]:
            if value == prev + 1:
                prev = value
                continue
            if start == prev:
                parts.append(_fmt(start))
            else:
                parts.append(f"{_fmt(start)}-{_fmt(prev)}")
            start = prev = value
        if start == prev:
            parts.append(_fmt(start))
        else:
            parts.append(f"{_fmt(start)}-{_fmt(prev)}")
        return ",".join(parts)

    def _latest_log_files(self, pattern):
        try:
            return sorted(self.logs_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        except Exception:
            return []

    def _extract_numbers_from_retry_errors(self, retry_errors, expect_prefix=None):
        numbers = []
        seen = set()
        for item in retry_errors or []:
            text = str(item or "").strip()
            if not text:
                continue
            head = text.split("|", 1)[0].strip()
            if expect_prefix:
                m = re.match(rf"^\s*{re.escape(expect_prefix)}\s*0*([0-9]+)\s*$", head, re.IGNORECASE)
            else:
                m = re.match(r"^\s*0*([0-9]+)\s*$", head)
            if not m:
                continue
            value = int(m.group(1))
            if value < 1 or value in seen:
                continue
            seen.add(value)
            numbers.append(value)
        return numbers

    def _load_recent_failed_prompt_numbers(self):
        for path in self._latest_log_files("session_report_*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            numbers = []
            seen = set()
            for entry in payload.get("entries", []) or []:
                if str(entry.get("status", "")).strip().lower() != "failed":
                    continue
                try:
                    value = int(entry.get("source_no"))
                except Exception:
                    continue
                if value >= 1 and value not in seen:
                    seen.add(value)
                    numbers.append(value)
            if not numbers:
                numbers = self._extract_numbers_from_retry_errors(payload.get("retry_errors", []), expect_prefix=None)
            if numbers:
                return numbers, path.name
        return [], ""

    def _load_recent_failed_asset_numbers(self):
        prefix = (self.cfg.get("asset_loop_prefix") or "S").strip() or "S"
        for path in self._latest_log_files("download_report_*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            numbers = []
            seen = set()
            for tag in payload.get("failed_tags", []) or []:
                m = re.match(rf"^\s*{re.escape(prefix)}\s*0*([0-9]+)\s*$", str(tag).strip(), re.IGNORECASE)
                if not m:
                    continue
                value = int(m.group(1))
                if value >= 1 and value not in seen:
                    seen.add(value)
                    numbers.append(value)
            if not numbers:
                numbers = self._extract_numbers_from_retry_errors(payload.get("retry_errors", []), expect_prefix=prefix)
            if numbers:
                return numbers, path.name

        for path in self._latest_log_files("session_report_*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            numbers = []
            seen = set()
            for entry in payload.get("entries", []) or []:
                if str(entry.get("status", "")).strip().lower() != "failed":
                    continue
                tag = str(entry.get("tag", "") or "").strip()
                m = re.match(rf"^\s*{re.escape(prefix)}\s*0*([0-9]+)\s*$", tag, re.IGNORECASE)
                if not m:
                    continue
                value = int(m.group(1))
                if value >= 1 and value not in seen:
                    seen.add(value)
                    numbers.append(value)
            if not numbers:
                numbers = self._extract_numbers_from_retry_errors(payload.get("retry_errors", []), expect_prefix=prefix)
            if numbers:
                return numbers, path.name
        return [], ""

    def _build_prompt_run_numbers(self):
        source = list(getattr(self, "prompt_source_prompts", []) or [])
        upper_bound = len(source)
        raw = str(self.cfg.get("prompt_manual_selection", "") or "").strip()
        info = self._parse_manual_number_spec(raw, upper_bound=upper_bound)
        if not raw:
            return list(range(1, upper_bound + 1)), info
        return info.get("numbers", []), info

    def _refresh_prompt_run_sequence(self, update_preview=False):
        source = self._load_prompt_source_prompts(update_preview=update_preview)
        numbers = list(self.prompt_run_numbers or [])
        if not numbers:
            self.prompts = list(source)
            return
        filtered = []
        valid_numbers = []
        for num in numbers:
            idx = num - 1
            if 0 <= idx < len(source):
                filtered.append(source[idx])
                valid_numbers.append(num)
        self.prompt_run_numbers = valid_numbers
        self.prompts = filtered

    def _resolve_asset_number_plan(self):
        raw = str(self.cfg.get("asset_manual_selection", "") or "").strip()
        info = self._parse_manual_number_spec(raw, upper_bound=None)
        if raw and info.get("numbers"):
            return info

        try:
            start_num = int(self.cfg.get("asset_loop_start", 1))
        except (TypeError, ValueError):
            start_num = 1
        try:
            end_num = int(self.cfg.get("asset_loop_end", 1))
        except (TypeError, ValueError):
            end_num = start_num
        start_num = max(1, start_num)
        end_num = max(1, end_num)
        if start_num > end_num:
            start_num, end_num = end_num, start_num
        return {
            "raw": raw,
            "numbers": list(range(start_num, end_num + 1)),
            "invalid_tokens": info.get("invalid_tokens", []),
            "out_of_range": [],
            "truncated": False,
        }

    def _refresh_manual_selection_labels(self):
        prompt_info = self._parse_manual_number_spec(
            str(self.cfg.get("prompt_manual_selection", "") or "").strip(),
            upper_bound=len(getattr(self, "prompt_source_prompts", []) or []),
        )
        if hasattr(self, "lbl_prompt_manual_status"):
            if prompt_info.get("invalid_tokens"):
                self.lbl_prompt_manual_status.config(
                    text=f"형식 확인: {', '.join(prompt_info['invalid_tokens'][:3])}",
                    fg=self.color_error,
                )
            elif prompt_info.get("raw"):
                self.lbl_prompt_manual_status.config(
                    text=self._format_manual_selection_preview(prompt_info.get("numbers", []), prefix="", pad_width=3),
                    fg=self.color_info,
                )
            else:
                self.lbl_prompt_manual_status.config(text="전체 프롬프트 실행", fg=self.color_text_sec)

        asset_info = self._resolve_asset_number_plan()
        if hasattr(self, "lbl_asset_manual_status"):
            raw = str(self.cfg.get("asset_manual_selection", "") or "").strip()
            if raw and asset_info.get("invalid_tokens"):
                self.lbl_asset_manual_status.config(
                    text=f"형식 확인: {', '.join(asset_info['invalid_tokens'][:3])}",
                    fg=self.color_error,
                )
            elif raw:
                self.lbl_asset_manual_status.config(
                    text=self._format_manual_selection_preview(
                        asset_info.get("numbers", []),
                        prefix=(self.cfg.get("asset_loop_prefix") or "S").strip() or "S",
                        pad_width=self._asset_pad_width(),
                    ),
                    fg=self.color_info,
                )
            else:
                self.lbl_asset_manual_status.config(text="비워두면 시작~끝 범위 실행", fg=self.color_text_sec)
        self._refresh_asset_prompt_slot_controls()

    def _load_prompt_source_prompts(self, update_preview=True):
        path = self.base / self.cfg["prompts_file"]
        if not path.exists():
            path.write_text("", encoding="utf-8")
        raw = path.read_text(encoding="utf-8")
        if update_preview and hasattr(self, "log_window"):
            self.log_window.set_preview(raw)
        sep = self.cfg.get("prompts_separator", "|||")
        self.prompt_source_prompts = [p.strip() for p in raw.split(sep) if p.strip()]
        self._refresh_manual_selection_labels()
        return list(self.prompt_source_prompts)

    def _sync_asset_range_display(self):
        if hasattr(self, "asset_loop_start_var"):
            self.asset_loop_start_var.set(self._format_asset_number_text(self.cfg.get("asset_loop_start", 1)))
        if hasattr(self, "asset_loop_end_var"):
            self.asset_loop_end_var.set(self._format_asset_number_text(self.cfg.get("asset_loop_end", self.cfg.get("asset_loop_start", 1))))

    def _build_asset_loop_items(self):
        if not self.cfg.get("asset_loop_enabled", False):
            self.asset_prompt_missing_numbers = []
            return []
        plan = self._resolve_asset_number_plan()
        numbers = list(plan.get("numbers", []) or [])
        if not numbers:
            self.asset_prompt_missing_numbers = []
            return []

        prefix = (self.cfg.get("asset_loop_prefix") or "S").strip() or "S"
        try:
            pad_width = int(self.cfg.get("asset_loop_num_width", 0))
        except (TypeError, ValueError):
            pad_width = 0
        pad_width = max(3, pad_width)
        template = (self.cfg.get("asset_loop_prompt_template") or "{tag} : Naturally Seamless Loop animation.").strip()
        if "{tag}" not in template:
            template = "{tag} : " + template
        use_prompt_slot = bool(self.cfg.get("asset_use_prompt_slot"))
        slot_data = {"mode": "empty", "entries": [], "tagged_prompts": {}, "common_prompt": ""}
        if use_prompt_slot:
            slot_data = self._asset_prompt_slot_data()
            slot_prompts = list(slot_data.get("entries", []) or [])
        else:
            slot_prompts = []

        max_items = 500
        items = []
        missing_numbers = []
        for n in numbers:
            if len(items) >= max_items:
                break
            num_txt = str(n).zfill(pad_width)
            tag = f"{prefix}{num_txt}"
            if use_prompt_slot:
                if slot_data.get("mode") == "tagged":
                    prompt = str((slot_data.get("tagged_prompts", {}) or {}).get(tag.upper(), "") or "").strip()
                    if not prompt:
                        prompt = str(slot_data.get("common_prompt", "") or "").strip()
                else:
                    prompt_idx = n - 1
                    if 0 <= prompt_idx < len(slot_prompts):
                        prompt = str(slot_prompts[prompt_idx] or "").strip()
                    else:
                        missing_numbers.append(n)
                        continue
                if not prompt:
                    missing_numbers.append(n)
                    continue
            else:
                prompt = template.replace("{tag}", tag).strip()
            items.append({"tag": tag, "prompt": prompt, "number": n})
        self.asset_prompt_missing_numbers = missing_numbers
        return items

    def _build_download_items(self):
        plan = self._resolve_asset_number_plan()
        numbers = list(plan.get("numbers", []) or [])
        if not numbers:
            return []

        prefix = (self.cfg.get("asset_loop_prefix") or "S").strip() or "S"
        try:
            pad_width = int(self.cfg.get("asset_loop_num_width", 0))
        except (TypeError, ValueError):
            pad_width = 0
        pad_width = max(3, pad_width)

        items = []
        max_items = 500
        for n in numbers:
            if len(items) >= max_items:
                break
            tag = f"{prefix}{str(n).zfill(pad_width)}"
            items.append(tag)
        return items

    def _download_mode(self):
        mode = str(self.cfg.get("download_mode", "video") or "video").strip().lower()
        return "image" if mode == "image" else "video"

    def _download_quality(self, mode=None):
        mode = mode or self._download_mode()
        if mode == "image":
            val = str(self.cfg.get("download_image_quality", "4K") or "4K").strip().upper()
            return val if val in ("1K", "2K", "4K") else "4K"
        val = str(self.cfg.get("download_video_quality", "1080P") or "1080P").strip().upper()
        return val if val in ("720P", "1080P", "4K") else "1080P"

    def _download_action_delay(self, label, min_s, max_s):
        try:
            slow = float(self.cfg.get("download_human_slowdown", 1.35))
        except Exception:
            slow = 1.35
        slow = max(1.0, min(2.5, slow))
        self.actor.random_action_delay(label, min_s * slow, max_s * slow)

    def _download_expect_timeout_sec(self, mode, quality, is_test=False):
        mode = "image" if mode == "image" else "video"
        quality = str(quality or "").strip().upper()
        if mode == "video":
            if quality in ("1080P", "4K"):
                return 300 if is_test else 240
            return 75 if is_test else 60
        # image
        if quality == "4K":
            return 180 if is_test else 120
        return 90 if is_test else 70

    def _profile_download_default_dir(self):
        try:
            pref = self._resolve_profile_dir() / "Default" / "Preferences"
            if not pref.exists():
                return None
            data = json.loads(pref.read_text(encoding="utf-8", errors="ignore"))
            for key in (
                ("savefile", "default_directory"),
                ("download", "default_directory"),
            ):
                val = (((data or {}).get(key[0]) or {}).get(key[1]) or "").strip()
                if val:
                    return Path(val)
        except Exception:
            return None
        return None

    def _resolve_download_output_dir(self):
        pipeline_output = str(getattr(self, "pipeline_active_output_dir", "") or "").strip()
        if pipeline_output:
            p = Path(pipeline_output).expanduser()
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            return p
        configured = str(self.cfg.get("download_output_dir", "") or "").strip()
        if configured:
            p = Path(configured).expanduser()
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            return p
        prof = self._profile_download_default_dir()
        if prof is not None:
            try:
                prof.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            return prof
        fallback = Path.home() / "Downloads"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return fallback

    def _next_available_path(self, path_obj):
        if not path_obj.exists():
            return path_obj
        stem = path_obj.stem
        suffix = path_obj.suffix
        parent = path_obj.parent
        n = 1
        while n <= 9999:
            cand = parent / f"{stem} ({n}){suffix}"
            if not cand.exists():
                return cand
            n += 1
        return parent / f"{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"

    def _download_search_input_candidates(self):
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get("download_search_input_selector", "")))
        cands.extend([
            "input[placeholder*='검색' i]",
            "input[aria-label*='검색' i]",
            "input[placeholder*='search' i]",
            "input[aria-label*='search' i]",
            "input[type='search']",
            "[role='searchbox']",
            "[role='textbox'][aria-label*='검색' i]",
            "[role='textbox'][aria-label*='search' i]",
            "[contenteditable='true'][aria-label*='검색' i]",
            "[contenteditable='true'][aria-label*='search' i]",
            "input[type='text']",
        ])
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _download_search_toggle_candidates(self):
        return [
            "button:has-text('search')",
            "[role='button']:has-text('search')",
            "button[aria-label*='검색' i]",
            "[role='button'][aria-label*='검색' i]",
            "button[aria-label*='search' i]",
            "[role='button'][aria-label*='search' i]",
            "button[title*='search' i]",
        ]

    def _download_filter_candidates(self, mode):
        key = "download_image_filter_selector" if mode == "image" else "download_video_filter_selector"
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get(key, "")))
        if mode == "image":
            cands.extend([
                "button:has-text('image')",
                "[role='button']:has-text('image')",
                "button:has-text('View images')",
                "[role='button']:has-text('View images')",
                "button:has-text('이미지')",
                "[role='button']:has-text('이미지')",
                "button[aria-label*='이미지' i]",
                "[role='button'][aria-label*='이미지' i]",
                "button:has-text('Image')",
                "[role='button']:has-text('Image')",
                "button[aria-label*='image' i]",
            ])
        else:
            cands.extend([
                "button:has-text('videocam')",
                "[role='button']:has-text('videocam')",
                "button:has-text('View videos')",
                "[role='button']:has-text('View videos')",
                "button:has-text('영상')",
                "[role='button']:has-text('영상')",
                "button[aria-label*='영상' i]",
                "[role='button'][aria-label*='영상' i]",
                "button:has-text('Video')",
                "[role='button']:has-text('Video')",
                "button[aria-label*='video' i]",
            ])
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _resolve_download_filter_button(self, mode, timeout_sec=4):
        if not self.page:
            return None, None
        mode = "image" if mode == "image" else "video"
        end_ts = time.time() + max(1, timeout_sec)
        viewport_h = 900
        try:
            vp = self.page.viewport_size or {}
            viewport_h = int(vp.get("height", 900))
        except Exception:
            pass

        while time.time() < end_ts:
            best = None
            best_sel = None
            best_score = float("-inf")
            for sel in self._download_filter_candidates(mode):
                try:
                    loc = self.page.locator(sel)
                    total = min(loc.count(), 20)
                except Exception:
                    continue
                for i in range(total):
                    cand = loc.nth(i)
                    try:
                        if not cand.is_visible(timeout=500):
                            continue
                        box = cand.bounding_box()
                    except Exception:
                        continue
                    if not box:
                        continue
                    # 좌측 사이드 필터 아이콘 영역만 허용
                    if box["x"] > 130:
                        continue
                    if box["y"] < 60 or box["y"] > (viewport_h * 0.55):
                        continue
                    score = 1000.0 - (box["x"] * 1.8) - (abs((box["y"] + box["height"] / 2.0) - 170.0) * 0.5)
                    meta = self._locator_meta_text(cand)
                    if mode == "video":
                        if ("videocam" in meta) or ("view videos" in meta) or ("video" in meta) or ("영상" in meta):
                            score += 300.0
                        if "동영상 x" in meta:
                            score -= 1200.0
                    else:
                        if ("image" in meta) or ("view images" in meta) or ("이미지" in meta):
                            score += 300.0
                    if score > best_score:
                        best_score = score
                        best = cand
                        best_sel = sel
            if best is not None:
                return best, best_sel
            time.sleep(0.2)
        return None, None

    def _download_card_candidates(self, mode):
        key = "download_image_card_selector" if mode == "image" else "download_video_card_selector"
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get(key, "")))
        cands.extend([
            "article",
            "[role='listitem']",
            "li",
            "div[class*='card' i]",
            "div[class*='tile' i]",
            "div[data-testid*='card' i]",
            "div[data-testid*='result' i]",
        ])
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _download_more_candidates(self, mode):
        key = "download_image_more_selector" if mode == "image" else "download_video_more_selector"
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get(key, "")))
        cands.extend([
            "button[aria-label*='더보기' i]",
            "[role='button'][aria-label*='더보기' i]",
            "button[aria-label*='more' i]",
            "[role='button'][aria-label*='more' i]",
            "button[title*='more' i]",
            "button:has-text('...')",
            "button:has-text('⋮')",
        ])
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _download_menu_candidates(self, mode):
        key = "download_image_menu_selector" if mode == "image" else "download_video_menu_selector"
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get(key, "")))
        cands.extend([
            "button:has-text('다운로드')",
            "[role='menuitem']:has-text('다운로드')",
            "[role='button']:has-text('다운로드')",
            "text=다운로드",
            "button:has-text('Download')",
            "[role='menuitem']:has-text('Download')",
            "text=Download",
        ])
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _download_quality_candidates(self, mode, quality):
        key = "download_image_quality_selector" if mode == "image" else "download_video_quality_selector"
        quality = str(quality or "").strip().upper()
        cands = []
        # 요청 품질 기반 selector를 우선 사용해 품질 오클릭을 방지
        if quality:
            cands.extend([
                f"button:has-text('{quality}')",
                f"[role='menuitem']:has-text('{quality}')",
                f"[role='option']:has-text('{quality}')",
                f"text={quality}",
            ])
        saved = self._normalize_candidate_list(self.cfg.get(key, ""))
        for s in saved:
            su = s.upper()
            # 저장된 selector에 다른 품질이 박혀있으면 제외
            if any(q in su for q in ("720P", "1080P", "4K", "2K", "1K")) and (quality not in su):
                continue
            cands.append(s)
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _resolve_download_search_input(self, timeout_sec=8):
        if not self.page:
            return None, None

        end_ts = time.time() + max(1, timeout_sec)
        best_loc = None
        best_sel = None
        best_score = float("-inf")
        viewport_w = 1600
        viewport_h = 900
        try:
            vp = self.page.viewport_size or {}
            viewport_w = int(vp.get("width", 1600))
            viewport_h = int(vp.get("height", 900))
        except Exception:
            pass

        positive_keys = ("search", "검색", "media", "all media")
        negative_keys = ("project", "title", "이름", "rename", "name", "prompt", "프롬프트", "무엇을 만들고")
        toggled = False
        min_x = max(90, int(viewport_w * 0.12))
        max_y = max(190, int(viewport_h * 0.42))

        while time.time() < end_ts:
            for sel in self._download_search_input_candidates():
                try:
                    loc = self.page.locator(sel)
                    total = min(loc.count(), 20)
                except Exception:
                    continue
                for i in range(total):
                    cand = loc.nth(i)
                    try:
                        if not cand.is_visible(timeout=600):
                            continue
                        box = cand.bounding_box()
                    except Exception:
                        continue
                    if not box:
                        continue
                    if box["width"] < 100 or box["height"] < 20:
                        continue
                    # 작은 창에서는 검색바가 조금 더 아래/왼쪽에 나올 수 있어 허용 범위를 넓힌다.
                    if box["y"] > max_y:
                        continue
                    if box["x"] < min_x:
                        continue
                    score = 0.0
                    meta = self._locator_meta_text(cand)
                    if any(k in meta for k in positive_keys):
                        score += 450.0
                    if any(k in meta for k in negative_keys):
                        score -= 800.0
                    if box["width"] >= 280:
                        score += 220.0
                    elif box["width"] >= 180:
                        score += 80.0
                    else:
                        score -= 300.0
                    if box["y"] <= max(160, viewport_h * 0.22):
                        score += 120.0
                    else:
                        score -= 220.0
                    cx = box["x"] + box["width"] / 2.0
                    center_bias = abs(cx - (viewport_w / 2.0))
                    score -= center_bias * 0.25
                    if box["x"] < viewport_w * 0.18:
                        score -= 180.0
                    if score > best_score:
                        best_score = score
                        best_loc = cand
                        best_sel = sel
            if best_loc is not None and best_score >= -40:
                return best_loc, best_sel
            if (not toggled) and (time.time() + 0.8 < end_ts):
                toggle_loc, _ = self._resolve_best_locator(
                    self._download_search_toggle_candidates(),
                    timeout_ms=900,
                    prefer_enabled=False,
                )
                if toggle_loc is not None:
                    try:
                        self._click_with_actor_fallback(toggle_loc, "검색 아이콘")
                        self.actor.random_action_delay("검색바 표시 대기", 0.2, 0.8)
                        toggled = True
                        focus_loc, focus_sel = self._resolve_focused_download_search_input()
                        if focus_loc is not None:
                            return focus_loc, focus_sel
                    except Exception:
                        pass
            time.sleep(0.25)
        return best_loc, best_sel

    def _resolve_focused_download_search_input(self):
        if not self.page:
            return None, None
        try:
            focus_loc = self.page.locator(":focus").first
            if focus_loc.count() <= 0:
                return None, None
            if not focus_loc.is_visible(timeout=400):
                return None, None
            box = focus_loc.bounding_box()
            if (not box) or box["width"] < 80 or box["height"] < 18:
                return None, None
            meta = self._locator_meta_text(focus_loc)
            negative_keys = ("project", "title", "이름", "rename", "name", "prompt", "프롬프트", "무엇을 만들고")
            if any(k in meta for k in negative_keys):
                return None, None
            return focus_loc, ":focus"
        except Exception:
            return None, None

    def _direct_fill_download_search_via_dom(self, search_text):
        if (not self.page) or (not search_text):
            return False, "page/text 없음", ""
        try:
            result = self.page.evaluate(
                """(payload) => {
                    const text = String(payload.text || "").trim();
                    if (!text) return {ok:false, reason:"empty-text", selector:""};

                    const positiveKeys = ["search", "검색", "media", "all media", "find"];
                    const negativeKeys = ["project", "title", "이름", "rename", "name", "prompt", "프롬프트", "무엇을 만들고"];

                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width < 10 || r.height < 10) return false;
                        const st = window.getComputedStyle(el);
                        return st && st.display !== "none" && st.visibility !== "hidden" && st.opacity !== "0";
                    };

                    const metaText = (el) => {
                        const a = (k) => (el.getAttribute(k) || "");
                        return [
                            el.tagName || "",
                            el.id || "",
                            el.className || "",
                            a("type"),
                            a("role"),
                            a("name"),
                            a("placeholder"),
                            a("aria-label"),
                            a("title"),
                            (el.innerText || ""),
                        ].join(" ").toLowerCase();
                    };

                    const selectorHint = (el) => {
                        const a = (k) => (el.getAttribute(k) || "").trim();
                        const tag = (el.tagName || "input").toLowerCase();
                        if (el.id) return `${tag}[id='${el.id.replace(/'/g, "\\'")}']`;
                        if (a("aria-label")) return `${tag}[aria-label*='${a("aria-label").replace(/'/g, "\\'")}']`;
                        if (a("placeholder")) return `${tag}[placeholder*='${a("placeholder").replace(/'/g, "\\'")}']`;
                        if (a("name")) return `${tag}[name='${a("name").replace(/'/g, "\\'")}']`;
                        if (a("type")) return `${tag}[type='${a("type").replace(/'/g, "\\'")}']`;
                        if (a("role")) return `[role='${a("role").replace(/'/g, "\\'")}']`;
                        return "dom-search-fallback";
                    };

                    const roots = [];
                    const q = [document];
                    while (q.length) {
                        const root = q.shift();
                        roots.push(root);
                        const hostNodes = root.querySelectorAll ? root.querySelectorAll("*") : [];
                        for (const h of hostNodes) {
                            if (h && h.shadowRoot) q.push(h.shadowRoot);
                        }
                    }

                    let best = null;
                    let bestScore = -1e9;
                    for (const root of roots) {
                        const nodes = root.querySelectorAll
                            ? root.querySelectorAll("input, textarea, [contenteditable='true'], [role='searchbox'], [role='textbox']")
                            : [];
                        for (const el of nodes) {
                            if (!isVisible(el)) continue;
                            const r = el.getBoundingClientRect();
                            const meta = metaText(el);
                            let score = 0;
                            if (el === document.activeElement) score += 700;
                            if (positiveKeys.some(k => meta.includes(k))) score += 450;
                            if (negativeKeys.some(k => meta.includes(k))) score -= 1000;
                            if ((el.getAttribute("type") || "").toLowerCase() === "search") score += 280;
                            if ((el.getAttribute("role") || "").toLowerCase() === "searchbox") score += 280;
                            if (r.width >= 220) score += 180;
                            else if (r.width >= 140) score += 70;
                            else score -= 240;
                            if (r.y <= Math.max(220, window.innerHeight * 0.48)) score += 120;
                            else score -= 220;
                            if (r.x >= Math.max(40, window.innerWidth * 0.08)) score += 60;
                            if (score > bestScore) {
                                best = el;
                                bestScore = score;
                            }
                        }
                    }

                    if (!best) return {ok:false, reason:"no-candidate", selector:""};

                    best.focus();
                    if (best.isContentEditable) {
                        best.textContent = "";
                        best.dispatchEvent(new InputEvent("input", {bubbles:true, data:""}));
                        best.textContent = text;
                        best.dispatchEvent(new InputEvent("input", {bubbles:true, data:text}));
                    } else {
                        best.value = "";
                        best.dispatchEvent(new Event("input", {bubbles:true}));
                        best.value = text;
                        best.dispatchEvent(new Event("input", {bubbles:true}));
                        best.dispatchEvent(new Event("change", {bubbles:true}));
                    }
                    return {ok:true, reason:"", selector:selectorHint(best)};
                }""",
                {"text": search_text},
            ) or {}
        except Exception as e:
            return False, str(e), ""
        return bool(result.get("ok")), str(result.get("reason", "")), str(result.get("selector", ""))

    def _find_first_media_tile_box(self):
        if not self.page:
            return None
        try:
            return self.page.evaluate(
                """() => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width < 160 || r.height < 90) return false;
                        const st = window.getComputedStyle(el);
                        if (!st) return false;
                        return st.display !== 'none' && st.visibility !== 'hidden' && st.opacity !== '0';
                    };
                    const candidates = Array.from(document.querySelectorAll("video, img, canvas"));
                    const boxes = [];
                    for (const el of candidates) {
                        if (!isVisible(el)) continue;
                        const r = el.getBoundingClientRect();
                        if (r.top < 70) continue;
                        boxes.push({x:r.left, y:r.top, width:r.width, height:r.height});
                    }
                    boxes.sort((a,b) => (a.y - b.y) || (a.x - b.x));
                    return boxes.length ? boxes[0] : null;
                }"""
            )
        except Exception:
            return None

    def _resolve_more_button_near_box(self, box):
        if (not self.page) or (not box):
            return None, None
        try:
            loc = self.page.locator("button, [role='button']")
            total = min(loc.count(), 250)
        except Exception:
            return None, None
        right_top_x = float(box["x"]) + float(box["width"]) - 18.0
        right_top_y = float(box["y"]) + 18.0
        best = None
        best_score = float("inf")
        for i in range(total):
            cand = loc.nth(i)
            try:
                if not cand.is_visible(timeout=500):
                    continue
                b = cand.bounding_box()
            except Exception:
                continue
            if not b:
                continue
            if b["x"] < box["x"] - 24 or b["x"] > (box["x"] + box["width"] + 24):
                continue
            if b["y"] < box["y"] - 30 or b["y"] > (box["y"] + min(140, box["height"] * 0.45)):
                continue
            if b["width"] > 110 or b["height"] > 70:
                continue
            cx = b["x"] + b["width"] / 2.0
            cy = b["y"] + b["height"] / 2.0
            score = abs(cx - right_top_x) + abs(cy - right_top_y)
            try:
                meta = cand.evaluate("""(el)=>((el.getAttribute('aria-label')||'')+' '+(el.getAttribute('title')||'')+' '+(el.innerText||'')).toLowerCase()""")
            except Exception:
                meta = ""
            if any(x in meta for x in ("더보기", "more", "menu", "...", "⋮", "︙")):
                score -= 220.0
            if score < best_score:
                best_score = score
                best = cand
        return (best, "") if best is not None else (None, None)

    def _asset_start_button_candidates(self):
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get("asset_start_selector", "")))
        cands.extend([
            "button:has-text('시작')",
            "[role='button']:has-text('시작')",
            "button:has-text('Start')",
            "[role='button']:has-text('Start')",
        ])
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _resolve_asset_sidebar_button(self, timeout_sec=4):
        if not self.page:
            return None, None
        end_ts = time.time() + max(1, timeout_sec)
        viewport_w = 1600
        viewport_h = 900
        try:
            vp = self.page.viewport_size or {}
            viewport_w = int(vp.get("width", 1600))
            viewport_h = int(vp.get("height", 900))
        except Exception:
            pass

        positive_keys = ("image", "이미지", "photo", "사진", "gallery", "asset", "에셋", "media", "reference")
        negative_keys = ("video", "동영상", "설정", "setting", "menu", "download", "다운로드")

        while time.time() < end_ts:
            best = None
            best_sel = None
            best_score = float("-inf")
            candidates = [
                "button, [role='button']",
                "[aria-label*='image' i]",
                "[title*='image' i]",
                "[aria-label*='이미지' i]",
                "[title*='이미지' i]",
                "[aria-label*='asset' i]",
                "[title*='asset' i]",
                "[aria-label*='에셋' i]",
                "[title*='에셋' i]",
            ]
            for sel in candidates:
                try:
                    loc = self.page.locator(sel)
                    total = min(loc.count(), 60)
                except Exception:
                    continue
                for i in range(total):
                    cand = loc.nth(i)
                    try:
                        if not cand.is_visible(timeout=400):
                            continue
                        box = cand.bounding_box()
                    except Exception:
                        continue
                    if not box:
                        continue
                    if box["x"] > max(120, viewport_w * 0.12):
                        continue
                    if box["y"] < 90 or box["y"] > (viewport_h * 0.68):
                        continue
                    if box["width"] < 20 or box["height"] < 20 or box["width"] > 90 or box["height"] > 90:
                        continue
                    score = 0.0
                    meta = self._locator_meta_text(cand)
                    if any(k in meta for k in positive_keys):
                        score += 900.0
                    if any(k in meta for k in negative_keys):
                        score -= 900.0
                    score -= abs((box["x"] + box["width"] / 2.0) - 34.0) * 2.0
                    score -= abs((box["y"] + box["height"] / 2.0) - (viewport_h * 0.30)) * 0.8
                    if score > best_score:
                        best_score = score
                        best = cand
                        best_sel = sel
            if best is not None:
                return best, best_sel
            time.sleep(0.2)
        return None, None

    def _ensure_asset_workspace_visible(self, timeout_sec=4):
        if not self.page:
            return False
        start_loc, _ = self._resolve_best_locator_with_scroll(
            self._asset_start_button_candidates(),
            timeout_ms=1200,
            prefer_enabled=False,
            ratios=(0.0, 0.10, 0.18),
        )
        if start_loc is not None:
            return True
        start_loc, _ = self._resolve_text_locator_any_frame(["시작", "Start"], timeout_ms=900)
        if start_loc is not None:
            return True

        side_loc, side_sel = self._resolve_asset_sidebar_button(timeout_sec=timeout_sec)
        if side_loc is None:
            self.log("ℹ️ 좌측 이미지/에셋 아이콘 미탐지")
            return False
        if not self._click_with_actor_fallback(side_loc, "좌측 이미지/에셋 아이콘"):
            self.log("ℹ️ 좌측 이미지/에셋 아이콘 클릭 실패")
            return False
        self.log(f"🖼️ 좌측 이미지/에셋 아이콘 클릭: {side_sel or '위치기반 탐색'}")
        self.actor.random_action_delay("에셋 작업영역 표시 대기", 0.5, 1.3)
        start_loc, _ = self._resolve_best_locator_with_scroll(
            self._asset_start_button_candidates(),
            timeout_ms=1600,
            prefer_enabled=False,
            ratios=(0.0, 0.10, 0.18),
        )
        if start_loc is not None:
            return True
        start_loc, _ = self._resolve_text_locator_any_frame(["시작", "Start"], timeout_ms=1000)
        return start_loc is not None

    def _open_asset_search_surface_for_detection(self):
        if not self.page:
            return False
        input_loc, _ = self._resolve_best_locator_with_scroll(
            self._asset_search_input_candidates(),
            timeout_ms=1200,
            prefer_enabled=False,
            ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
        )
        if input_loc is not None:
            return True

        start_loc, start_sel = self._resolve_best_locator_with_scroll(
            self._asset_start_button_candidates(),
            timeout_ms=1800,
            prefer_enabled=False,
            ratios=(0.0, 0.10, 0.18),
        )
        if start_loc is None:
            start_loc, start_sel = self._resolve_text_locator_any_frame(["시작", "Start"], timeout_ms=1000)
            if start_loc is None:
                return False
        if not self._click_with_actor_fallback(start_loc, "시작 버튼"):
            self.log("ℹ️ 자동탐색용 시작 버튼 클릭 실패")
            return False
        self.log(f"🟢 자동탐색용 시작 클릭: {start_sel or '텍스트 탐색'}")
        self.actor.random_action_delay("에셋 검색창 표시 대기", 0.5, 1.4)
        input_loc, _ = self._resolve_best_locator_with_scroll(
            self._asset_search_input_candidates(),
            timeout_ms=1800,
            prefer_enabled=False,
            ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
        )
        return input_loc is not None

    def _asset_search_button_candidates(self):
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get("asset_search_button_selector", "")))
        cands.extend([
            "button:has-text('에셋 검색')",
            "[role='button']:has-text('에셋 검색')",
            "button:has-text('Asset search')",
            "[role='button']:has-text('Asset search')",
            "button:has-text('Search assets')",
            "[role='button']:has-text('Search assets')",
        ])
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _asset_search_input_candidates(self):
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get("asset_search_input_selector", "")))
        cands.extend([
            "input[placeholder*='에셋 검색' i]",
            "input[aria-label*='에셋 검색' i]",
            "textarea[placeholder*='에셋 검색' i]",
            "textarea[aria-label*='에셋 검색' i]",
            "input[placeholder*='asset' i]",
            "input[aria-label*='asset' i]",
            "textarea[placeholder*='asset' i]",
            "textarea[aria-label*='asset' i]",
            "input[placeholder*='검색' i]",
            "input[aria-label*='검색' i]",
            "textarea[placeholder*='검색' i]",
            "textarea[aria-label*='검색' i]",
            "[role='textbox'][aria-label*='에셋' i]",
            "[role='textbox'][aria-label*='asset' i]",
            "[contenteditable='true'][aria-label*='에셋' i]",
            "[contenteditable='true'][aria-label*='asset' i]",
            "input[type='search']",
            "[role='searchbox']",
        ])
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _wait_best_locator(self, candidates, timeout_sec=8, prefer_enabled=True):
        end_ts = time.time() + max(1, timeout_sec)
        while time.time() < end_ts:
            loc, sel = self._resolve_best_locator(
                candidates,
                timeout_ms=900,
                prefer_enabled=prefer_enabled,
            )
            if loc is not None:
                return loc, sel
            time.sleep(0.25)
        return None, None

    def _click_with_actor_fallback(self, locator, label):
        if locator is None:
            return False
        try:
            self.actor.move_to_locator(locator, label=label)
            self.actor.smart_click(label=f"{label} 클릭")
            return True
        except Exception:
            pass
        try:
            locator.click(timeout=2500)
            return True
        except Exception:
            return False

    def _resolve_text_locator_any_frame(self, texts, timeout_ms=1200):
        if not self.page:
            return None, None
        if isinstance(texts, str):
            texts = [texts]
        texts = [t for t in texts if isinstance(t, str) and t.strip()]
        if not texts:
            return None, None

        frames = []
        try:
            frames = list(self.page.frames)
        except Exception:
            frames = [self.page.main_frame]
        if self.page.main_frame not in frames:
            frames.insert(0, self.page.main_frame)

        for fr in frames:
            for txt in texts:
                try:
                    loc = fr.get_by_text(txt, exact=False).first
                    if loc.count() <= 0:
                        continue
                    if not loc.is_visible(timeout=timeout_ms):
                        continue
                    return loc, f"text:{txt}"
                except Exception:
                    continue
        return None, None

    def _direct_fill_asset_search_via_dom(self, asset_tag):
        if (not self.page) or (not asset_tag):
            return False, "page/tag 없음"
        try:
            result = self.page.evaluate(
                """(payload) => {
                    const tag = String(payload.tag || "").trim();
                    if (!tag) return {ok:false, reason:"empty-tag"};

                    const searchKeys = ["asset", "search", "에셋", "검색"];
                    const promptKeys = ["무엇을 만들고 싶으신가요", "prompt", "프롬프트", "message", "메시지"];

                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width < 10 || r.height < 10) return false;
                        const st = window.getComputedStyle(el);
                        return st && st.display !== "none" && st.visibility !== "hidden" && st.opacity !== "0";
                    };

                    const metaText = (el) => {
                        const a = (k) => (el.getAttribute(k) || "");
                        return [
                            el.tagName || "",
                            el.id || "",
                            el.className || "",
                            a("name"),
                            a("placeholder"),
                            a("aria-label"),
                            a("title"),
                            (el.innerText || ""),
                        ].join(" ").toLowerCase();
                    };

                    const roots = [];
                    const q = [document];
                    while (q.length) {
                        const root = q.shift();
                        roots.push(root);
                        const hostNodes = root.querySelectorAll ? root.querySelectorAll("*") : [];
                        for (const h of hostNodes) {
                            if (h && h.shadowRoot) q.push(h.shadowRoot);
                        }
                    }

                    let best = null;
                    let bestScore = -1e9;
                    for (const root of roots) {
                        const nodes = root.querySelectorAll ? root.querySelectorAll("input, textarea, [contenteditable='true'], [role='searchbox'], [role='textbox']") : [];
                        for (const el of nodes) {
                            if (!isVisible(el)) continue;
                            const meta = metaText(el);
                            const r = el.getBoundingClientRect();
                            let score = 0;

                            const hasSearch = searchKeys.some(k => meta.includes(k));
                            const hasPrompt = promptKeys.some(k => meta.includes(k));
                            if (hasSearch) score += 450;
                            if (hasPrompt) score -= 700;

                            if ((el.tagName || "").toLowerCase() === "input") score += 80;
                            if ((el.getAttribute("type") || "").toLowerCase() === "search") score += 260;
                            if (r.width > 120 && r.width < 700) score += 70;
                            if (r.y > 0 && r.y < window.innerHeight * 0.9) score += 30;

                            if (score > bestScore) {
                                bestScore = score;
                                best = el;
                            }
                        }
                    }

                    if (!best || bestScore < 120) {
                        return {ok:false, reason:"search-input-not-found"};
                    }

                    best.focus();
                    try {
                        if ("value" in best) {
                            best.value = "";
                            best.dispatchEvent(new Event("input", {bubbles:true}));
                            best.value = tag;
                            best.dispatchEvent(new Event("input", {bubbles:true}));
                            best.dispatchEvent(new Event("change", {bubbles:true}));
                        } else {
                            best.textContent = "";
                            best.dispatchEvent(new InputEvent("input", {bubbles:true, data:""}));
                            best.textContent = tag;
                            best.dispatchEvent(new InputEvent("input", {bubbles:true, data:tag}));
                        }
                        return {ok:true, reason:"dom-filled"};
                    } catch (e) {
                        return {ok:false, reason:String(e)};
                    }
                }""",
                {"tag": asset_tag},
            )
            ok = bool(result and result.get("ok"))
            reason = (result or {}).get("reason", "")
            return ok, reason
        except Exception as e:
            return False, str(e)

    def _run_asset_loop_prestep(self, asset_tag):
        if (not self.page) or (not asset_tag):
            return

        self._prepare_page_for_selector_detection()
        self._ensure_asset_workspace_visible(timeout_sec=4)
        self.log(f"🔁 S반복 사전단계 시작: {asset_tag}")
        start_locator, start_selector = self._resolve_best_locator_with_scroll(
            self._asset_start_button_candidates(),
            timeout_ms=2000,
            prefer_enabled=False,
        )
        if start_locator is not None:
            if self._click_with_actor_fallback(start_locator, "시작 버튼"):
                self.log(f"🟢 Step1 시작 클릭: {start_selector or '텍스트 탐색'}")
                self.actor.random_action_delay("시작 클릭 후 대기", 0.5, 1.6)
        else:
            start_locator, start_selector = self._resolve_text_locator_any_frame(["시작", "Start"], timeout_ms=1000)
            if start_locator is not None and self._click_with_actor_fallback(start_locator, "시작 버튼"):
                self.log(f"🟢 Step1 시작 클릭(문구탐색): {start_selector}")
                self.actor.random_action_delay("시작 클릭 후 대기", 0.5, 1.6)
            else:
                self.log("ℹ️ Step1 시작 버튼 미탐지(현재 화면 유지)")

        # 2-0) 에셋 검색 버튼 없이 바로 검색 입력칸이 열리는 UI 대응
        direct_input, _ = self._resolve_best_locator_with_scroll(
            self._asset_search_input_candidates(),
            timeout_ms=1600,
            prefer_enabled=False,
            ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
        )
        if direct_input is not None:
            try:
                direct_input.click(timeout=1200)
            except Exception:
                pass
            try:
                self.page.keyboard.press("Control+A")
                self.page.keyboard.press("Backspace")
            except Exception:
                pass
            try:
                direct_input.fill(asset_tag)
            except Exception:
                try:
                    direct_input.type(asset_tag, delay=random.randint(25, 70))
                except Exception:
                    direct_input = None
            if direct_input is not None:
                self.page.keyboard.press("Enter")
                self.log(f"✅ Step2 에셋 검색 입력 완료(직접입력): {asset_tag}")
                self.actor.random_action_delay("에셋 검색 Enter 후 대기", 0.2, 1.0)
                return

        search_candidates = self._asset_search_button_candidates() + [
            "text=에셋 검색",
            "text=Asset search",
            "text=Search assets",
            "[aria-label*='에셋' i][aria-label*='검색' i]",
            "[title*='에셋' i][title*='검색' i]",
            "[aria-label*='asset' i][aria-label*='search' i]",
            "[title*='asset' i][title*='search' i]",
        ]
        search_locator, search_selector = self._resolve_best_locator_with_scroll(
            search_candidates,
            timeout_ms=2200,
            prefer_enabled=False,
            ratios=(0.0, 0.12, 0.24, 0.36, 0.50),
        )
        if search_locator is None:
            search_locator, search_selector = self._resolve_text_locator_any_frame(
                ["에셋 검색", "Asset search", "Search assets"],
                timeout_ms=1200,
            )
        if search_locator is not None:
            if not self._click_with_actor_fallback(search_locator, "에셋 검색 버튼"):
                self.log("ℹ️ Step2 에셋 검색 클릭 실패, 입력칸 직접 탐색으로 전환")
            else:
                self.log(f"🔎 Step2 에셋 검색 클릭: {search_selector or '텍스트 탐색'}")
                self.actor.random_action_delay("에셋 검색 클릭 후 대기", 0.4, 1.6)

        search_input, _ = self._resolve_best_locator_with_scroll(
            self._asset_search_input_candidates(),
            timeout_ms=2200,
            prefer_enabled=False,
            ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
        )
        if search_input is None:
            # 클릭 후 포커스가 검색칸으로 이미 이동했을 수 있어 키보드 직접 입력 1회 폴백
            try:
                self.page.keyboard.press("Control+A")
                self.page.keyboard.press("Backspace")
                self.page.keyboard.insert_text(asset_tag)
                self.page.keyboard.press("Enter")
                self.log(f"✅ Step2 에셋 검색 입력 완료(포커스 폴백): {asset_tag}")
                self.actor.random_action_delay("에셋 검색 Enter 후 대기", 0.3, 1.0)
                return
            except Exception:
                ok_dom, reason_dom = self._direct_fill_asset_search_via_dom(asset_tag)
                if ok_dom:
                    self.page.keyboard.press("Enter")
                    self.log(f"✅ Step2 에셋 검색 입력 완료(DOM 폴백): {asset_tag}")
                    self.actor.random_action_delay("에셋 검색 Enter 후 대기", 0.3, 1.0)
                    return
                raise RuntimeError(f"Step2 실패: 에셋 검색 입력창을 찾지 못했습니다. (dom={reason_dom})")

        try:
            search_input.click(timeout=1500)
        except Exception:
            pass
        try:
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
        except Exception:
            pass
        try:
            search_input.fill(asset_tag)
        except Exception:
            try:
                search_input.type(asset_tag, delay=random.randint(25, 70))
            except Exception:
                raise RuntimeError("에셋 검색 입력에 실패했습니다.")

        self.actor.random_action_delay("에셋 검색어 입력 후 대기", 0.1, 0.5)
        self.page.keyboard.press("Enter")
        self.log(f"✅ Step2 에셋 검색 입력 완료: {asset_tag}")
        self.actor.random_action_delay("에셋 검색 Enter 후 대기", 0.2, 1.0)

    def _prompt_reference_search_input_candidates(self):
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get("prompt_reference_search_input_selector", "")))
        cands.extend(self._normalize_candidate_list(self.cfg.get("asset_search_input_selector", "")))
        cands.extend(self._asset_search_input_candidates())
        cands.extend([
            "input",
            "textarea",
            "[role='searchbox']",
            "[role='textbox']",
            "[contenteditable='true']",
            "[contenteditable='plaintext-only']",
        ])
        return list(dict.fromkeys([x for x in cands if x]))

    def _resolve_prompt_reference_search_overlay_input(self, timeout_sec=2.0):
        if not self.page:
            return None, None
        end_ts = time.time() + max(1.0, timeout_sec)
        best_dump = []
        dumped = False
        while time.time() < end_ts:
            best = None
            best_sel = None
            best_score = float("-inf")
            dump_rows = []
            selectors = self._prompt_reference_search_input_candidates()
            for sel in selectors:
                try:
                    loc = self.page.locator(sel)
                    total = min(loc.count(), 40)
                except Exception:
                    continue
                for idx in range(total):
                    cand = loc.nth(idx)
                    try:
                        if not cand.is_visible(timeout=250):
                            continue
                        box = cand.bounding_box()
                    except Exception:
                        continue
                    if not box:
                        continue
                    meta = self._locator_meta_text(cand)
                    width = float(box["width"] or 0.0)
                    height = float(box["height"] or 0.0)
                    x = float(box["x"] or 0.0)
                    y = float(box["y"] or 0.0)
                    cx = x + width / 2.0
                    score = 0.0
                    if width < 120 or height < 20:
                        score -= 800.0
                    if y < 8.0:
                        score -= 120.0
                    if y <= 180.0:
                        score += 720.0
                    elif y <= 260.0:
                        score += 260.0
                    else:
                        score -= 1600.0
                    if 220.0 <= width <= 980.0:
                        score += 220.0
                    elif width > 1200.0:
                        score -= 400.0
                    score -= abs(cx - 420.0) * 0.22
                    if any(k in meta for k in ("검색", "search", "asset", "에셋", "recent", "최근")):
                        score += 520.0
                    if any(k in meta for k in ("무엇을 만들", "prompt", "프롬프트", "message", "메시지")):
                        score -= 1800.0
                    if any(k in meta for k in ("nano banana", "veo", "video", "동영상", "이미지", "x1", "x2", "x3", "x4")):
                        score -= 1200.0
                    dump_rows.append((score, sel, meta[:100], box))
                    if score > best_score:
                        best = cand
                        best_sel = self._locator_selector_hint(cand) or sel
                        best_score = score
            if dump_rows:
                best_dump = sorted(dump_rows, key=lambda x: x[0], reverse=True)[:12]
            if best is not None and best_score > 150.0:
                if not dumped and best_dump:
                    self.log("🧩 레퍼런스 검색창 후보 덤프")
                    for idx, row in enumerate(best_dump, start=1):
                        box = row[3] or {}
                        self.log(
                            f"   {idx:02d}. score={row[0]:.1f} sel={row[1]} meta='{row[2]}' "
                            f"box=({float(box.get('x') or 0.0):.1f}, {float(box.get('y') or 0.0):.1f}, "
                            f"{float(box.get('width') or 0.0):.1f}, {float(box.get('height') or 0.0):.1f})"
                        )
                return best, best_sel
            time.sleep(0.12)
        if best_dump:
            self.log("🧩 레퍼런스 검색창 후보 덤프(실패)")
            for idx, row in enumerate(best_dump, start=1):
                box = row[3] or {}
                self.log(
                    f"   {idx:02d}. score={row[0]:.1f} sel={row[1]} meta='{row[2]}' "
                    f"box=({float(box.get('x') or 0.0):.1f}, {float(box.get('y') or 0.0):.1f}, "
                    f"{float(box.get('width') or 0.0):.1f}, {float(box.get('height') or 0.0):.1f})"
                )
        return None, None

    def _open_prompt_reference_search_via_keyboard(self, input_locator, timeout_sec=2.2):
        if (not self.page) or input_locator is None:
            raise RuntimeError("프롬프트 입력창이 없어 @ 레퍼런스 호출을 할 수 없습니다.")
        try:
            input_locator.focus(timeout=1200)
        except Exception:
            pass
        deadline = time.time() + max(1.0, timeout_sec)
        last_error = "search-input-not-found"
        trigger_methods = (
            "page_type_at",
            "locator_type_at",
            "page_shift2",
            "locator_shift2",
            "js_dispatch",
        )
        while time.time() < deadline:
            for method in trigger_methods:
                before_text = self._read_input_text(input_locator)
                try:
                    if method == "page_type_at":
                        self.page.keyboard.type("@")
                        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 레퍼런스 @ 트리거 입력: page type('@')")
                    elif method == "locator_type_at":
                        input_locator.type("@", delay=random.randint(30, 80), timeout=1200)
                        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 레퍼런스 @ 트리거 입력: locator type('@')")
                    elif method == "page_shift2":
                        self.page.keyboard.down("Shift")
                        self.page.keyboard.press("2")
                        self.page.keyboard.up("Shift")
                        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 레퍼런스 @ 트리거 입력: page Shift+2")
                    elif method == "locator_shift2":
                        input_locator.press("Shift+2", timeout=1200)
                        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 레퍼런스 @ 트리거 입력: locator Shift+2")
                    else:
                        self.page.evaluate(
                            """() => {
                                const el = document.activeElement;
                                if (!el) return false;
                                const fireKey = (type) => el.dispatchEvent(new KeyboardEvent(type, {
                                    key: "@",
                                    code: "Digit2",
                                    shiftKey: true,
                                    bubbles: true,
                                    cancelable: true,
                                }));
                                fireKey("keydown");
                                try {
                                    if ("value" in el) {
                                        const start = el.selectionStart ?? String(el.value || "").length;
                                        const end = el.selectionEnd ?? start;
                                        const next = String(el.value || "").slice(0, start) + "@" + String(el.value || "").slice(end);
                                        el.value = next;
                                        if (el.setSelectionRange) el.setSelectionRange(start + 1, start + 1);
                                    } else if (el.isContentEditable) {
                                        document.execCommand("insertText", false, "@");
                                    }
                                } catch (e) {}
                                el.dispatchEvent(new InputEvent("input", {bubbles:true, data:"@", inputType:"insertText"}));
                                fireKey("keyup");
                                return true;
                            }"""
                        )
                        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 레퍼런스 @ 트리거 입력: js dispatch")
                except Exception as e:
                    last_error = str(e)
                self.actor.random_action_delay("레퍼런스 검색창 표시 대기", 0.25, 0.7)
                after_text = self._read_input_text(input_locator)
                typed_at = after_text.endswith("@") or (after_text.count("@") > before_text.count("@"))
                search_input, search_sel = self._resolve_prompt_reference_search_overlay_input(timeout_sec=0.9)
                if search_input is not None and typed_at:
                    self.log(f"🔡 레퍼런스 @ 호출 성공: {method} -> {search_sel or '자동 탐색'}")
                    return search_input, search_sel or ""
                # 검색창이 안 뜨거나, @ 없이 상단 입력칸만 잘못 잡힌 경우 입력 흔적 정리 후 다음 방법 재시도
                try:
                    input_locator.focus(timeout=800)
                    current_text = self._read_input_text(input_locator)
                    extra_count = max(0, len(current_text) - len(before_text))
                    if extra_count > 0 and current_text.startswith(before_text):
                        for _ in range(extra_count):
                            self.page.keyboard.press("Backspace")
                    elif current_text.endswith("@"):
                        self.page.keyboard.press("Backspace")
                except Exception:
                    pass
                time.sleep(0.10)
        raise RuntimeError(f"@ 레퍼런스 검색창 호출 실패 ({last_error})")

    def _resolve_prompt_reference_result(self, search_input=None, timeout_sec=3):
        if not self.page:
            return None, None, None
        try:
            search_box = search_input.bounding_box() if search_input is not None else None
        except Exception:
            search_box = None

        stored = self._normalize_candidate_list(self.cfg.get("prompt_reference_result_selector", ""))
        generic = [
            "button:has(img)",
            "[role='button']:has(img)",
            "div[role='button']:has(img)",
            "li:has(img)",
            "a:has(img)",
            "button:has(canvas)",
            "[role='button']:has(canvas)",
            "div[role='button']:has(canvas)",
            "li:has(canvas)",
            "a:has(canvas)",
        ]
        candidates = list(dict.fromkeys([x for x in (stored + generic) if x]))
        end_ts = time.time() + max(1, timeout_sec)
        while time.time() < end_ts:
            best = None
            best_sel = None
            best_score = float("-inf")
            for sel in candidates:
                try:
                    loc = self.page.locator(sel)
                    total = min(loc.count(), 40)
                except Exception:
                    continue
                for i in range(total):
                    cand = loc.nth(i)
                    try:
                        if not cand.is_visible(timeout=350):
                            continue
                        box = cand.bounding_box()
                    except Exception:
                        continue
                    if not box:
                        continue
                    if box["width"] < 28 or box["height"] < 28:
                        continue
                    if box["width"] > 220 or box["height"] > 220:
                        continue
                    if search_box:
                        if box["y"] < (search_box["y"] + search_box["height"] + 12):
                            continue
                        if box["x"] > (search_box["x"] + search_box["width"] * 0.42):
                            continue
                    meta = self._locator_meta_text(cand)
                    score = 0.0
                    score += max(0.0, 240.0 - box["y"])
                    score -= box["x"] * 0.35
                    score -= abs(box["width"] - 96.0) * 0.4
                    score -= abs(box["height"] - 96.0) * 0.4
                    if any(k in meta for k in ("recent", "최근 사용", "검색", "search", "menu", "설정")):
                        score -= 900.0
                    if any(k in meta for k in ("image", "이미지", "asset", "에셋", "reference", "참조")):
                        score += 120.0
                    if score > best_score:
                        best = cand
                        best_sel = self._locator_selector_hint(cand) or sel
                        best_score = score
            if best is not None and best_score > -300:
                try:
                    return best, best_sel, best.bounding_box()
                except Exception:
                    return best, best_sel, None

            try:
                result = self.page.evaluate(
                    """(payload) => {
                        const searchBox = payload && payload.searchBox ? payload.searchBox : null;
                        const isVisible = (el) => {
                            if (!el) return false;
                            const r = el.getBoundingClientRect();
                            if (!r || r.width < 28 || r.height < 28) return false;
                            const st = window.getComputedStyle(el);
                            if (!st) return false;
                            return st.display !== "none" && st.visibility !== "hidden" && st.opacity !== "0";
                        };
                        const selectorHint = (el) => {
                            if (!el) return "";
                            const esc = (value) => String(value || "").replace(/\\/g, "\\\\").replace(/"/g, '\\"');
                            const tag = (el.tagName || "").toLowerCase();
                            if (el.id) return `#${el.id}`;
                            const aria = el.getAttribute("aria-label") || "";
                            if (aria) return `${tag || "*"}[aria-label="${esc(aria)}"]`;
                            const title = el.getAttribute("title") || "";
                            if (title) return `${tag || "*"}[title="${esc(title)}"]`;
                            const cls = String(el.className || "").trim().split(/\\s+/).filter(Boolean).slice(0, 2);
                            if (tag && cls.length) return `${tag}.${cls.join(".")}`;
                            return tag || "*";
                        };
                        let best = null;
                        let bestScore = -1e9;
                        for (const el of Array.from(document.querySelectorAll("img, canvas, video"))) {
                            if (!isVisible(el)) continue;
                            const r = el.getBoundingClientRect();
                            if (r.top < 70) continue;
                            if (r.width > 180 || r.height > 180) continue;
                            if (searchBox) {
                                if (r.top < (searchBox.y + searchBox.height + 12)) continue;
                                if (r.left > (searchBox.x + searchBox.width * 0.42)) continue;
                            } else if (r.left > window.innerWidth * 0.42) {
                                continue;
                            }
                            let score = 0;
                            score += Math.max(0, 240 - r.top);
                            score -= r.left * 0.35;
                            score -= Math.abs(r.width - 96) * 0.4;
                            score -= Math.abs(r.height - 96) * 0.4;
                            if (score > bestScore) {
                                best = el;
                                bestScore = score;
                            }
                        }
                        if (!best) return null;
                        const box = best.getBoundingClientRect();
                        return {
                            selector: selectorHint(best),
                            box: {x: box.x, y: box.y, width: box.width, height: box.height},
                        };
                    }""",
                    {"searchBox": search_box},
                )
            except Exception:
                result = None
            if result and result.get("box"):
                box = result.get("box") or {}
                return None, str(result.get("selector") or "위치기반 결과"), box
            time.sleep(0.18)
        return None, None, None

    def _fill_prompt_reference_search_input(self, search_input, asset_tag):
        if not self.page:
            return None, None
        used_selector = None
        if search_input is not None:
            try:
                search_input.click(timeout=1200)
            except Exception:
                pass
            try:
                self.page.keyboard.press("Control+A")
                self.page.keyboard.press("Backspace")
            except Exception:
                pass
            try:
                search_input.fill(asset_tag)
                used_selector = self._locator_selector_hint(search_input)
            except Exception:
                try:
                    search_input.type(asset_tag, delay=random.randint(25, 70))
                    used_selector = self._locator_selector_hint(search_input)
                except Exception:
                    search_input = None
        if search_input is None:
            ok_dom, reason_dom = self._direct_fill_asset_search_via_dom(asset_tag)
            if not ok_dom:
                raise RuntimeError(f"레퍼런스 검색창을 찾지 못했습니다. ({reason_dom})")
            used_selector = used_selector or "DOM 직접입력"
        self.log(f"🔎 레퍼런스 검색 입력: {asset_tag} ({used_selector or '직접입력'})")
        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 레퍼런스 검색 입력: {asset_tag} ({used_selector or '직접입력'})")
        return search_input, used_selector

    def _resolve_prompt_reference_sort_button(self, search_input=None, timeout_sec=1.6):
        if not self.page:
            return None, None
        try:
            search_box = search_input.bounding_box() if search_input is not None else None
        except Exception:
            search_box = None

        labels = ("최근 사용", "가장 많이 사용", "최신순", "오래된 순")
        end_ts = time.time() + max(1.0, timeout_sec)
        while time.time() < end_ts:
            best = None
            best_sel = None
            best_score = float("-inf")
            for sel in ("button", "[role='button']", "div[role='button']"):
                try:
                    loc = self.page.locator(sel)
                    total = min(loc.count(), 40)
                except Exception:
                    continue
                for idx in range(total):
                    cand = loc.nth(idx)
                    try:
                        if not cand.is_visible(timeout=250):
                            continue
                        box = cand.bounding_box()
                    except Exception:
                        continue
                    if not box:
                        continue
                    meta = self._locator_meta_text(cand)
                    if not any(label in meta for label in labels):
                        continue
                    score = 0.0
                    if search_box:
                        score -= abs(float(box["y"]) - float(search_box["y"])) * 1.2
                        score -= abs((float(box["x"]) + float(box["width"]) * 0.5) - (float(search_box["x"]) + float(search_box["width"]) + 70.0)) * 0.18
                        if float(box["x"]) < float(search_box["x"]) + float(search_box["width"]) - 40.0:
                            score -= 600.0
                    score += 240.0
                    if "최근 사용" in meta:
                        score += 120.0
                    if score > best_score:
                        best = cand
                        best_sel = self._locator_selector_hint(cand) or sel
                        best_score = score
            if best is not None and best_score > -300.0:
                return best, best_sel or ""
            time.sleep(0.10)
        return None, None

    def _resolve_prompt_reference_oldest_option(self, timeout_sec=1.6):
        if not self.page:
            return None, None
        end_ts = time.time() + max(1.0, timeout_sec)
        while time.time() < end_ts:
            for sel in (
                "button",
                "[role='button']",
                "div[role='button']",
                "[role='menuitem']",
                "li",
            ):
                try:
                    loc = self.page.locator(sel)
                    total = min(loc.count(), 50)
                except Exception:
                    continue
                for idx in range(total):
                    cand = loc.nth(idx)
                    try:
                        if not cand.is_visible(timeout=250):
                            continue
                        box = cand.bounding_box()
                    except Exception:
                        continue
                    if not box:
                        continue
                    meta = self._locator_meta_text(cand)
                    if "오래된 순" not in meta:
                        continue
                    return cand, self._locator_selector_hint(cand) or sel
            time.sleep(0.10)
        return None, None

    def _set_prompt_reference_sort_oldest(self, search_input=None):
        if not self.page:
            return search_input
        sort_button, sort_sel = self._resolve_prompt_reference_sort_button(search_input=search_input, timeout_sec=1.5)
        if sort_button is None:
            self.log("⚠️ 레퍼런스 정렬 버튼을 찾지 못해 기본 정렬로 계속합니다.")
            return search_input
        try:
            sort_button.click(timeout=1200)
        except Exception:
            if not self._click_with_actor_fallback(sort_button, "레퍼런스 정렬 버튼"):
                self.log("⚠️ 레퍼런스 정렬 버튼 클릭에 실패해 기본 정렬로 계속합니다.")
                return search_input
        self.log(f"↕️ 레퍼런스 정렬 버튼 클릭: {sort_sel or '자동 탐색'}")
        self.actor.random_action_delay("레퍼런스 정렬 메뉴 표시 대기", 0.08, 0.18)
        oldest_button, oldest_sel = self._resolve_prompt_reference_oldest_option(timeout_sec=1.4)
        if oldest_button is None:
            self.log("⚠️ `오래된 순` 항목을 찾지 못해 기본 정렬로 계속합니다.")
            return search_input
        try:
            oldest_button.click(timeout=1200)
        except Exception:
            if not self._click_with_actor_fallback(oldest_button, "레퍼런스 오래된 순"):
                self.log("⚠️ `오래된 순` 클릭에 실패해 기본 정렬로 계속합니다.")
                return search_input
        self.log(f"↕️ 레퍼런스 정렬 선택: 오래된 순 ({oldest_sel or '자동 탐색'})")
        self.actor.random_action_delay("레퍼런스 정렬 반영 대기", 0.10, 0.22)
        refreshed_input, refreshed_sel = self._resolve_prompt_reference_search_overlay_input(timeout_sec=1.2)
        if refreshed_input is not None:
            try:
                refreshed_input.click(timeout=1200)
            except Exception:
                pass
            self.log(f"🔎 레퍼런스 검색창 재확인: {refreshed_sel or '자동 탐색'}")
            return refreshed_input
        return search_input

    def _click_prompt_reference_first_result(self, search_input=None, asset_tag="", timeout_sec=3):
        end_ts = time.time() + max(1, timeout_sec)
        last_selector = None
        while time.time() < end_ts:
            result_loc, result_sel, result_box = self._resolve_prompt_reference_result(search_input=search_input, timeout_sec=1)
            last_selector = result_sel or last_selector
            if result_loc is not None:
                if self._click_with_actor_fallback(result_loc, "레퍼런스 첫 결과"):
                    self.log(f"🖼️ 레퍼런스 첫 결과 클릭: {result_sel or '자동 탐색'}")
                    self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 레퍼런스 첫 결과 클릭: {result_sel or '자동 탐색'}")
                    return True, result_sel or ""
            elif result_box:
                try:
                    cx = float(result_box["x"]) + float(result_box["width"]) * 0.5
                    cy = float(result_box["y"]) + float(result_box["height"]) * 0.5
                    self.page.mouse.move(cx, cy, steps=8)
                    self.actor.random_action_delay("레퍼런스 첫 결과 클릭 전 대기", 0.12, 0.38)
                    self.page.mouse.click(cx, cy, delay=random.randint(30, 90))
                    self.log(f"🖼️ 레퍼런스 첫 결과 클릭: {result_sel or '위치기반 결과'}")
                    self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 레퍼런스 첫 결과 클릭: {result_sel or '위치기반 결과'}")
                    return True, result_sel or ""
                except Exception:
                    pass
            time.sleep(0.18)
        if asset_tag:
            self.log(f"⚠️ 레퍼런스 첫 결과를 클릭하지 못했습니다: {asset_tag}")
        return False, last_selector or ""

    def _attach_prompt_reference_asset(self, input_locator, asset_tag):
        if (not self.page) or input_locator is None or (not asset_tag):
            return input_locator
        self.log(f"🔖 레퍼런스 첨부 시작: {asset_tag}")
        search_input, search_sel = self._open_prompt_reference_search_via_keyboard(input_locator, timeout_sec=2.4)
        search_input = self._set_prompt_reference_sort_oldest(search_input=search_input)
        search_input, search_sel = self._fill_prompt_reference_search_input(search_input, asset_tag)
        if search_sel:
            self.cfg["prompt_reference_search_input_selector"] = search_sel
        self.actor.random_action_delay("레퍼런스 Enter 전 대기", 0.04, 0.10)
        self.page.keyboard.press("Enter")
        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 레퍼런스 Enter 선택: {asset_tag}")
        self.actor.random_action_delay("레퍼런스 Enter 반영 대기", 0.08, 0.18)
        self.log(f"✅ 레퍼런스 첨부 요청 완료: {asset_tag}")
        self.actor.random_action_delay("레퍼런스 첨부 반영 대기", 0.04, 0.10)
        # 실제 화면에서는 Enter만으로 첨부가 끝나도, 남아 있지 않은 검색창을
        # 오탐해서 첫 결과를 다시 클릭하는 경우가 있었다.
        # inline 레퍼런스 본체 실행에서는 Enter 뒤 추가 클릭을 하지 않는다.
        self.log("🧭 레퍼런스 첨부 후 입력창 복귀: Enter만 사용")
        return input_locator

    def _split_prompt_inline_reference_parts(self, prompt_text):
        text = str(prompt_text or "")
        pattern = re.compile(r"@(S?\d{3,4})\b", re.IGNORECASE)
        parts = []
        cursor = 0
        for match in pattern.finditer(text):
            if match.start() > cursor:
                parts.append({"type": "text", "value": text[cursor:match.start()]})
            asset_tag = self._normalize_reference_asset_tag(match.group(1))
            parts.append({"type": "reference", "value": asset_tag, "raw": match.group(0)})
            cursor = match.end()
        if cursor < len(text):
            parts.append({"type": "text", "value": text[cursor:]})
        return parts

    def _type_prompt_inline_text_chunk(self, chunk, input_locator):
        text = str(chunk or "")
        if (not text) or (not self.page) or input_locator is None:
            return
        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] inline 텍스트 직선 입력 시작 (len={len(text)})")
        fatigue = self.actor.get_fatigue_factor() if hasattr(self, "actor") else 1.0
        typing_speed = getattr(self.actor, "typing_speed_factor", 1.0) if hasattr(self, "actor") else 1.0
        for ch in text:
            try:
                if ch == "\n":
                    self.page.keyboard.press("Shift+Enter")
                else:
                    self.page.keyboard.type(ch)
            except Exception:
                self.page.keyboard.insert_text(ch)
            if ch in [" ", "\n"]:
                base_min, base_max = 0.015, 0.06
            elif ch in [".", ",", "!", "?", ":", ";", ")", "(", "]", "["]:
                base_min, base_max = 0.02, 0.09
            else:
                base_min, base_max = 0.025, 0.11
            speed = max(0.45, min(typing_speed * random.uniform(0.7, 1.3), 8.0))
            fatigue_slow = 1.0 + max(0.0, (1.0 - fatigue)) * 0.45
            delay = random.uniform(base_min, base_max) * (1.0 / speed) * fatigue_slow
            time.sleep(max(0.004, min(delay, 0.18)))
        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] inline 텍스트 직선 입력 완료")

    def _type_prompt_with_inline_references(self, prompt_text, input_locator, input_mode="typing"):
        parts = self._split_prompt_inline_reference_parts(prompt_text)
        if not any(part.get("type") == "reference" for part in parts):
            self.actor.type_text(prompt_text, input_locator=input_locator, mode=input_mode)
            return input_locator
        ref_count = sum(1 for part in parts if part.get("type") == "reference")
        self.log(f"🔖 프롬프트 inline 레퍼런스 감지: {ref_count}개")
        keep_focus_only = False
        total_parts = len(parts)
        for idx, part in enumerate(parts):
            if part.get("type") == "text":
                chunk = str(part.get("value", "") or "")
                if chunk:
                    if keep_focus_only:
                        next_has_reference = any(
                            later.get("type") == "reference"
                            for later in parts[idx + 1 :]
                        )
                        if next_has_reference:
                            # 다음 레퍼런스가 남아 있으면 칩이 선택되지 않게 단순 입력만 한다.
                            self._type_prompt_inline_text_chunk(chunk, input_locator)
                        else:
                            # 마지막 레퍼런스 뒤 본문은 앞부분만 보호 입력하고,
                            # 그 뒤부터는 다시 사람처럼 오타/멈칫이 들어가도록 복귀한다.
                            protected_len = min(len(chunk), 18)
                            protected_chunk = chunk[:protected_len]
                            remaining_chunk = chunk[protected_len:]
                            if protected_chunk:
                                self._type_prompt_inline_text_chunk(protected_chunk, input_locator)
                            if remaining_chunk:
                                self.actor.type_text(remaining_chunk, input_locator=None, mode=input_mode)
                    else:
                        self.actor.type_text(chunk, input_locator=input_locator, mode=input_mode)
                    keep_focus_only = True
                continue
            asset_tag = str(part.get("value", "") or "").strip()
            if not asset_tag:
                continue
            self.update_status_label(f"🖼️ inline 레퍼런스 첨부 중... ({asset_tag})", self.color_info)
            input_locator = self._attach_prompt_reference_asset(input_locator, asset_tag)
            keep_focus_only = True
        return input_locator

    def _apply_download_used_selectors(self, mode, used):
        if not isinstance(used, dict):
            return
        mapping = {
            "search_input": ("download_search_input_selector", None),
            "filter": ("download_image_filter_selector" if mode == "image" else "download_video_filter_selector", None),
            "card": ("download_image_card_selector" if mode == "image" else "download_video_card_selector", None),
            "more": ("download_image_more_selector" if mode == "image" else "download_video_more_selector", None),
            "menu": ("download_image_menu_selector" if mode == "image" else "download_video_menu_selector", None),
            "quality": ("download_image_quality_selector" if mode == "image" else "download_video_quality_selector", None),
        }
        var_mapping = {
            "download_search_input_selector": "download_search_input_selector_var",
            "download_image_filter_selector": "download_image_filter_selector_var",
            "download_video_filter_selector": "download_video_filter_selector_var",
            "download_image_card_selector": "download_image_card_selector_var",
            "download_video_card_selector": "download_video_card_selector_var",
            "download_image_more_selector": "download_image_more_selector_var",
            "download_video_more_selector": "download_video_more_selector_var",
            "download_image_menu_selector": "download_image_menu_selector_var",
            "download_video_menu_selector": "download_video_menu_selector_var",
            "download_image_quality_selector": "download_image_quality_selector_var",
            "download_video_quality_selector": "download_video_quality_selector_var",
        }
        for k, raw in used.items():
            cfg_key = mapping.get(k, (None, None))[0]
            val = str(raw or "").strip()
            if not cfg_key or not val:
                continue
            self.cfg[cfg_key] = val
            var_name = var_mapping.get(cfg_key)
            if var_name and hasattr(self, var_name):
                try:
                    getattr(self, var_name).set(val)
                except Exception:
                    pass

    def _click_download_filter(self, mode, used):
        filter_loc, filter_sel = self._resolve_download_filter_button(mode, timeout_sec=5)
        if filter_loc is None:
            # 필터 버튼을 못 찾아도 현재 화면이 이미 해당 필터일 수 있어 실패로 보지 않는다.
            self.log(f"ℹ️ {'이미지' if mode == 'image' else '영상'} 필터 버튼 미탐지(현재 화면 유지)")
            return False
        used["filter"] = filter_sel or ""
        self._download_action_delay("필터 클릭 전 안정화", 0.2, 0.7)
        self._click_with_actor_fallback(filter_loc, f"{'이미지' if mode == 'image' else '영상'} 필터")
        self._download_action_delay("필터 적용 대기", 0.2, 0.9)
        return True

    def _resolve_more_button_from_card(self, card_loc, mode):
        # 카드 내부에서 우상단 작은 버튼(더보기)을 우선 추정한다.
        if card_loc is None:
            return None, None
        try:
            card_box = card_loc.bounding_box()
        except Exception:
            card_box = None
        if not card_box:
            return None, None

        try:
            inner = card_loc.locator("button, [role='button']")
            total = min(inner.count(), 30)
        except Exception:
            total = 0
            inner = None

        best = None
        best_score = float("inf")
        for i in range(total):
            cand = inner.nth(i)
            try:
                if not cand.is_visible(timeout=800):
                    continue
                box = cand.bounding_box()
            except Exception:
                continue
            if not box:
                continue
            if box["width"] < 12 or box["height"] < 12:
                continue
            cx = box["x"] + box["width"] / 2.0
            cy = box["y"] + box["height"] / 2.0
            right_top_x = card_box["x"] + card_box["width"] - 28.0
            right_top_y = card_box["y"] + 20.0
            score = abs(cx - right_top_x) + abs(cy - right_top_y)
            try:
                meta = cand.evaluate("""(el)=>((el.getAttribute('aria-label')||'')+' '+(el.innerText||'')).toLowerCase()""")
            except Exception:
                meta = ""
            if any(x in meta for x in ("더보기", "more", "menu", "...", "⋮")):
                score -= 250.0
            if score < best_score:
                best_score = score
                best = cand
        if best is not None:
            key = "download_image_more_selector" if mode == "image" else "download_video_more_selector"
            return best, self.cfg.get(key, "")
        return None, None

    def _apply_vertical_quality_path_if_needed(self, mode, quality, quality_loc):
        # 이미지 4K 메뉴는 대각선 이동 시 서브메뉴가 닫히는 경우가 있어
        # 1K 위치에서 같은 X축으로 수직 이동해 4K를 누르는 경로를 우선 적용한다.
        if (not self.page) or mode != "image" or str(quality).upper() != "4K" or quality_loc is None:
            return
        try:
            one_loc, _ = self._resolve_best_locator(
                self._download_quality_candidates("image", "1K"),
                timeout_ms=800,
                prefer_enabled=False,
            )
            if one_loc is None:
                return
            b1 = one_loc.bounding_box()
            b4 = quality_loc.bounding_box()
            if (not b1) or (not b4):
                return
            x = float(b4["x"]) + float(b4["width"]) * 0.5
            y1 = float(b1["y"]) + float(b1["height"]) * 0.5
            y4 = float(b4["y"]) + float(b4["height"]) * 0.5
            self.page.mouse.move(x, y1, steps=7)
            self.page.mouse.move(x, y4, steps=14)
            self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 4K 수직 이동 경로 적용")
        except Exception:
            return

    def _run_single_download_flow(self, mode, tag, quality, dry_run=False, wait_sec=60, is_test=False):
        if not self.page:
            raise RuntimeError("브라우저 페이지가 없습니다.")
        mode = "image" if mode == "image" else "video"
        quality = self._download_quality(mode) if not quality else str(quality).strip().upper()
        wait_sec = max(3, min(120, int(wait_sec)))
        used = {"search_input": "", "filter": "", "card": "", "more": "", "menu": "", "quality": ""}

        self._click_download_filter(mode, used)

        search_loc, search_sel = self._resolve_download_search_input(timeout_sec=8)
        if search_loc is None:
            ok_dom, reason_dom, sel_dom = self._direct_fill_download_search_via_dom(tag)
            if not ok_dom:
                raise RuntimeError(f"검색 입력칸을 찾지 못했습니다. (dom={reason_dom})")
            used["search_input"] = sel_dom or "dom-search-fallback"
            self.log(f"✅ 다운로드 검색 입력 완료(DOM 폴백): {tag}")
            self.page.keyboard.press("Enter")
            self._download_action_delay("검색 결과 반영 대기", 0.4, 1.2)
        else:
            used["search_input"] = search_sel or ""
            try:
                search_loc.click(timeout=1500)
            except Exception:
                pass
            try:
                self.page.keyboard.press("Control+A")
                self.page.keyboard.press("Backspace")
            except Exception:
                pass
            try:
                search_loc.fill(tag)
            except Exception:
                try:
                    search_loc.type(tag, delay=random.randint(20, 60))
                except Exception:
                    ok_dom, reason_dom, sel_dom = self._direct_fill_download_search_via_dom(tag)
                    if not ok_dom:
                        raise RuntimeError(f"검색어 입력 실패: {reason_dom}")
                    used["search_input"] = sel_dom or used["search_input"] or "dom-search-fallback"
                    self.log(f"✅ 다운로드 검색 입력 완료(DOM 폴백): {tag}")
            self.page.keyboard.press("Enter")
            self._download_action_delay("검색 결과 반영 대기", 0.4, 1.2)

        deadline = time.time() + wait_sec
        card_loc = None
        card_sel = None
        more_loc = None
        more_sel = None
        while time.time() < deadline:
            card_loc, card_sel = self._resolve_best_locator(
                self._download_card_candidates(mode),
                timeout_ms=1100,
                prefer_enabled=False,
            )
            if card_loc is not None:
                used["card"] = card_sel or ""
                try:
                    self.actor.move_to_locator(card_loc, label=f"결과 카드({tag})")
                except Exception:
                    try:
                        card_loc.hover(timeout=1000)
                    except Exception:
                        pass
                more_loc, more_sel = self._resolve_best_locator(
                    self._download_more_candidates(mode),
                    near_locator=card_loc,
                    timeout_ms=1000,
                    prefer_enabled=False,
                )
                if more_loc is None:
                    more_loc, more_sel = self._resolve_more_button_from_card(card_loc, mode)
                if more_loc is None:
                    try:
                        box = card_loc.bounding_box()
                    except Exception:
                        box = None
                    more_loc, more_sel = self._resolve_more_button_near_box(box)
            if more_loc is None:
                tile_box = self._find_first_media_tile_box()
                if tile_box:
                    try:
                        self.page.mouse.move(
                            float(tile_box["x"]) + float(tile_box["width"]) * 0.5,
                            float(tile_box["y"]) + float(tile_box["height"]) * 0.45,
                            steps=8,
                        )
                    except Exception:
                        pass
                    more_loc, more_sel = self._resolve_more_button_near_box(tile_box)
            if more_loc is not None:
                used["more"] = more_sel or ""
                break
            time.sleep(0.5)

        if more_loc is None:
            raise RuntimeError(f"더보기 버튼을 찾지 못했습니다. (대기 {wait_sec}초)")

        self._download_action_delay("더보기 클릭 전 안정화", 0.25, 0.9)
        if not self._click_with_actor_fallback(more_loc, "더보기 버튼"):
            raise RuntimeError("더보기 버튼 클릭 실패")

        menu_loc, menu_sel = self._wait_best_locator(
            self._download_menu_candidates(mode),
            timeout_sec=7,
            prefer_enabled=False,
        )
        if menu_loc is None:
            menu_loc, menu_sel = self._resolve_text_locator_any_frame(["다운로드", "Download"], timeout_ms=1000)
        if menu_loc is None:
            # 더보기 메뉴가 짧게 닫힌 경우 1회 재시도
            try:
                self._click_with_actor_fallback(more_loc, "더보기 버튼(재시도)")
                self.actor.random_action_delay("다운로드 메뉴 재표시 대기", 0.2, 0.7)
            except Exception:
                pass
            menu_loc, menu_sel = self._wait_best_locator(
                self._download_menu_candidates(mode),
                timeout_sec=4,
                prefer_enabled=False,
            )
            if menu_loc is None:
                menu_loc, menu_sel = self._resolve_text_locator_any_frame(["다운로드", "Download"], timeout_ms=1000)
        if menu_loc is None:
            raise RuntimeError("다운로드 메뉴를 찾지 못했습니다.")
        used["menu"] = menu_sel or ""

        try:
            self.actor.move_to_locator(menu_loc, label="다운로드 메뉴")
        except Exception:
            try:
                menu_loc.hover(timeout=1200)
            except Exception:
                pass
        self._download_action_delay("품질 목록 표시 대기", 0.15, 0.6)

        quality_loc, quality_sel = self._wait_best_locator(
            self._download_quality_candidates(mode, quality),
            timeout_sec=7,
            prefer_enabled=False,
        )
        if quality_loc is None:
            quality_loc, quality_sel = self._resolve_text_locator_any_frame([quality], timeout_ms=1000)
        if quality_loc is None:
            raise RuntimeError(f"{quality} 품질 항목을 찾지 못했습니다.")
        used["quality"] = quality_sel or ""
        quality_meta = self._locator_meta_text(quality_loc)
        self.log(
            f"🎚️ 품질 선택 시도 | 요청: {quality} | selector: {quality_sel or '-'} | 후보: {(quality_meta or '')[:80]}"
        )
        # 방어적으로 요청 품질이 보이지 않으면 텍스트 기반 재탐색 1회
        if quality and (quality.lower() not in (quality_meta or "")):
            retry_loc, retry_sel = self._resolve_text_locator_any_frame([quality], timeout_ms=1200)
            if retry_loc is not None:
                quality_loc, quality_sel = retry_loc, retry_sel
                used["quality"] = quality_sel or used["quality"]
                self.log(f"🎚️ 품질 재탐색 적용: {quality_sel or quality}")

        if dry_run:
            return {"used": used, "file": None}

        dl_timeout_sec = self._download_expect_timeout_sec(mode, quality, is_test=is_test)
        self.log(f"⏱️ 다운로드 시작 대기 타임아웃: {dl_timeout_sec}초 ({mode}/{quality})")
        dl = None
        last_err = None
        for attempt in range(2):
            try:
                if attempt > 0:
                    self.log(f"♻️ 품질 클릭 재시도 {attempt+1}/2")
                    if not self._click_with_actor_fallback(more_loc, "더보기 버튼(품질 재시도)"):
                        raise RuntimeError("더보기 버튼 재열기 실패")
                    menu_loc_retry, _ = self._wait_best_locator(
                        self._download_menu_candidates(mode),
                        timeout_sec=4,
                        prefer_enabled=False,
                    )
                    if menu_loc_retry is None:
                        menu_loc_retry, _ = self._resolve_text_locator_any_frame(["다운로드", "Download"], timeout_ms=1000)
                    if menu_loc_retry is None:
                        raise RuntimeError("다운로드 메뉴 재탐색 실패")
                    try:
                        self.actor.move_to_locator(menu_loc_retry, label="다운로드 메뉴(재시도)")
                    except Exception:
                        try:
                            menu_loc_retry.hover(timeout=900)
                        except Exception:
                            pass
                    self._download_action_delay("품질 목록 재표시 대기", 0.12, 0.45)
                    quality_loc, quality_sel = self._wait_best_locator(
                        self._download_quality_candidates(mode, quality),
                        timeout_sec=4,
                        prefer_enabled=False,
                    )
                    if quality_loc is None:
                        quality_loc, quality_sel = self._resolve_text_locator_any_frame([quality], timeout_ms=1000)
                    if quality_loc is None:
                        raise RuntimeError(f"{quality} 품질 항목 재탐색 실패")
                    used["quality"] = quality_sel or used["quality"]

                self._download_action_delay("품질 클릭 전 안정화", 0.2, 0.8)
                self._apply_vertical_quality_path_if_needed(mode, quality, quality_loc)
                with self.page.expect_download(timeout=int(dl_timeout_sec * 1000)) as dl_info:
                    quality_loc.click(timeout=2500, force=True)
                dl = dl_info.value
                break
            except Exception as e:
                last_err = e
                if attempt == 0:
                    self._download_action_delay("품질 재시도 전 대기", 0.18, 0.55)
                else:
                    raise RuntimeError(f"다운로드 시작 실패: {e}")

        if dl is None:
            raise RuntimeError(f"다운로드 시작 실패: {last_err}")

        file_name = dl.suggested_filename or ""
        out_dir = self._resolve_download_output_dir()
        safe_name = file_name.strip() if file_name else ""
        ext = Path(safe_name).suffix if safe_name else ""
        if not ext:
            ext = ".mp4" if mode == "video" else ".png"
        safe_name = f"{tag}{ext}"
        target = self._next_available_path(out_dir / safe_name)
        dl.save_as(str(target))
        file_path = str(target)
        self.log(f"💾 다운로드 저장 경로: {file_path}")

        return {"used": used, "file": target.name, "path": file_path}

    def _parse_schedule_datetime(self, raw_text):
        txt = (raw_text or "").strip()
        if not txt:
            return None
        fmts = (
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
        )
        for fmt in fmts:
            try:
                return datetime.strptime(txt, fmt)
            except ValueError:
                continue
        return None

    def _show_completion_popup(self):
        run_mode = self.current_run_mode
        try:
            if run_mode == "download":
                self.save_download_report()
            else:
                self.save_session_report()
        except Exception:
            pass
        payload = self._build_completion_payload(run_mode)
        try:
            self._save_completion_summary(payload)
        except Exception as e:
            self.log(f"⚠️ 완료 요약 저장 실패: {e}")

        if self.pipeline_runtime_active:
            has_next = (self.pipeline_run_position + 1) < len(self.pipeline_run_order)

            if has_next:
                def _advance_ui():
                    self.on_stop(pipeline_transition=True)
                    self.update_status_label("🏃 다음 이어달리기 작업 준비 중...", self.color_info)
                    self.root.after(500, lambda: self._run_pipeline_step_at(self.pipeline_run_position + 1))
                self.root.after(0, _advance_ui)
                return

            def _done_pipeline_ui():
                self.on_stop(pipeline_transition=True)
                self._clear_pipeline_runtime(cancelled=False)
                self.play_sound("finish")
                self.update_status_label("🎉 이어달리기 전체 완료!", self.color_success)
                messagebox.showinfo("이어달리기 완료", self._format_completion_popup_text(payload))

            self.root.after(0, _done_pipeline_ui)
            return

        def _done_ui():
            self.on_stop()
            self.play_sound("finish")
            self.update_status_label("🎉 전체 완료!", self.color_success)
            messagebox.showinfo("작업 완료", self._format_completion_popup_text(payload))
        self.root.after(0, _done_ui)

    def _build_completion_payload(self, run_mode=None):
        mode = run_mode or self.current_run_mode or "prompt"
        started_at = getattr(self, "session_start_time", None)
        ended_at = datetime.now()
        retry_errors = list(getattr(self, "retry_error_log", []) or [])
        if mode == "download":
            entries = list(getattr(self, "download_session_log", []) or [])
            failed = [x for x in entries if x.get("status") != "success"]
            success = len(entries) - len(failed)
            return {
                "run_mode": "download",
                "title": "다운로드 자동화",
                "started_at": started_at,
                "ended_at": ended_at,
                "total": len(entries),
                "success": success,
                "failed": len(failed),
                "failed_tags": [x.get("tag", "") for x in failed if x.get("tag")],
                "prompt_file": "",
                "output_dir": str(self._resolve_download_output_dir()),
                "action_log_path": str(self.action_log_path) if self.action_log_path else "",
                "report_path": str(self.download_report_path) if self.download_report_path else "",
                "selection_summary": self.current_selection_summary,
                "selection_input": self.current_selection_input,
                "failed_details": [f"{x.get('tag', '')} | {(x.get('error') or '').strip()}" for x in failed],
                "retry_errors": retry_errors,
            }
        entries = list(getattr(self, "session_log", []) or [])
        failed_entries = [x for x in entries if x.get("status") == "failed"]
        success_entries = [x for x in entries if x.get("status") != "failed"]
        return {
            "run_mode": mode,
            "title": "S자동화" if mode == "asset" else "프롬프트 자동화",
            "started_at": started_at,
            "ended_at": ended_at,
            "total": len(entries),
            "success": len(success_entries),
            "failed": len(failed_entries),
            "failed_tags": [x.get("tag", "") or str(x.get("source_no", "")) for x in failed_entries if x.get("tag") or x.get("source_no")],
            "prompt_file": str(self.cfg.get("prompts_file", "") or ""),
            "output_dir": "",
            "action_log_path": str(self.action_log_path) if self.action_log_path else "",
            "report_path": str(self.session_report_path) if self.session_report_path else "",
            "selection_summary": self.current_selection_summary,
            "selection_input": self.current_selection_input,
            "failed_details": [
                f"{x.get('tag') or x.get('source_no') or '-'} | {(x.get('error') or '').strip()}"
                for x in failed_entries
            ],
            "retry_errors": retry_errors,
        }

    def _format_completion_popup_text(self, payload):
        started_at = payload.get("started_at")
        ended_at = payload.get("ended_at")
        try:
            duration_sec = max(0, int((ended_at - started_at).total_seconds())) if started_at and ended_at else 0
        except Exception:
            duration_sec = 0
        mm, ss = divmod(duration_sec, 60)
        hh, mm = divmod(mm, 60)
        duration_text = f"{hh:02d}:{mm:02d}:{ss:02d}"
        lines = [
            f"작업 종류: {payload.get('title', '자동화')}",
            f"시작: {started_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(started_at, 'strftime') else '-'}",
            f"종료: {ended_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(ended_at, 'strftime') else '-'}",
            f"총 소요 시간: {duration_text}",
            f"총 작업 수: {payload.get('total', 0)}",
            f"성공: {payload.get('success', 0)}",
            f"실패: {payload.get('failed', 0)}",
        ]
        if payload.get("selection_summary"):
            lines.append(f"실행 대상: {payload.get('selection_summary')}")
        if payload.get("selection_input"):
            lines.append(f"입력 원본: {payload.get('selection_input')}")
        if payload.get("prompt_file"):
            lines.append(f"프롬프트 파일: {payload.get('prompt_file')}")
        if payload.get("output_dir"):
            lines.append(f"저장 폴더: {payload.get('output_dir')}")
        failed_tags = payload.get("failed_tags", []) or []
        if failed_tags:
            preview = ", ".join(failed_tags[:8])
            if len(failed_tags) > 8:
                preview += f" 외 {len(failed_tags) - 8}개"
            lines.append(f"실패 항목: {preview}")
        failed_details = payload.get("failed_details", []) or []
        if failed_details:
            lines.append("")
            lines.append("[실패 상세]")
            for detail in failed_details[:12]:
                lines.append(f"- {detail}")
            if len(failed_details) > 12:
                lines.append(f"- 외 {len(failed_details) - 12}개는 요약 파일 참고")
        retry_errors = payload.get("retry_errors", []) or []
        if retry_errors:
            lines.append("")
            lines.append(f"[재시도 오류 기록] {len(retry_errors)}회")
            for detail in retry_errors[:12]:
                lines.append(f"- {detail}")
            if len(retry_errors) > 12:
                lines.append(f"- 외 {len(retry_errors) - 12}회는 요약 파일 참고")
        if payload.get("action_log_path"):
            lines.append(f"행동 로그: {payload.get('action_log_path')}")
        if payload.get("report_path"):
            lines.append(f"리포트: {payload.get('report_path')}")
        if getattr(self, "completion_summary_path", None):
            lines.append(f"완료 요약: {self.completion_summary_path}")
        return "\n".join(lines)

    def _save_completion_summary(self, payload):
        stamp_base = getattr(self, "session_start_time", datetime.now())
        stamp = stamp_base.strftime("%Y%m%d_%H%M%S") if hasattr(stamp_base, "strftime") else datetime.now().strftime("%Y%m%d_%H%M%S")
        self.completion_summary_path = self.logs_dir / f"completion_summary_{stamp}.txt"
        text = self._format_completion_popup_text(payload)
        self.completion_summary_path.write_text(text, encoding="utf-8")
        self.log(f"🧾 완료 요약 저장: {self.completion_summary_path.name}")

    def update_status_label(self, text, color):
        if color == "white": color = self.color_text
        self.lbl_main_status.config(text=text, fg=color)
        if hasattr(self, "lbl_hud_state"):
            self.lbl_hud_state.config(text=f"상태: {text}", fg=color)

    def _create_collapsible_section(self, parent, title, opened=False):
        title_key = str(title or "")
        head_bg = self.color_card
        head_fg = self.color_accent
        if "프롬프트 자동화 전용 생성 옵션" in title_key:
            head_bg = "#16304F"
            head_fg = "#8AD7FF"
        elif "S001~S###" in title_key:
            head_bg = "#1D3048"
            head_fg = "#7CD9FF"
        elif "다운로드 자동화" in title_key:
            head_bg = "#1E3156"
            head_fg = "#8FD8FF"
        elif "이어달리기" in title_key:
            head_bg = "#24324B"
            head_fg = "#B8C6DD"

        wrap = tk.Frame(parent, bg=self.color_bg, highlightbackground=head_fg, highlightthickness=1)
        wrap.pack(fill="x", pady=(6, 6))

        head = tk.Frame(wrap, bg=head_bg)
        head.pack(fill="x")

        state = {"open": bool(opened)}
        body = tk.Frame(wrap, bg=self.color_bg)

        btn = tk.Button(
            head,
            text="",
            anchor="w",
            relief="flat",
            borderwidth=0,
            bg=head_bg,
            activebackground=head_bg,
            fg=head_fg,
            font=self.font_section,
            cursor="hand2",
            padx=8,
            pady=10,
        )
        btn.pack(fill="x")

        def _refresh():
            arrow = "▾" if state["open"] else "▸"
            btn.config(text=f"{arrow} {title}")
            if state["open"]:
                body.pack(fill="x", padx=8, pady=(2, 8))
            else:
                body.pack_forget()

        def _set_open(flag):
            state["open"] = bool(flag)
            _refresh()

        btn.config(command=lambda: _set_open(not state["open"]))
        _refresh()
        return body, _set_open

    def _set_mini_hud_collapsed(self, collapsed):
        if not hasattr(self, "mini_hud_body"):
            return
        self.mini_hud_collapsed = bool(collapsed)
        if self.mini_hud_collapsed:
            self.mini_hud_body.pack_forget()
            if hasattr(self, "btn_toggle_hud"):
                self.btn_toggle_hud.config(text="펼치기")
        else:
            self.mini_hud_body.pack(fill="x", pady=(4, 0))
            if hasattr(self, "btn_toggle_hud"):
                self.btn_toggle_hud.config(text="접기")

    def _toggle_mini_hud(self):
        self._set_mini_hud_collapsed(not getattr(self, "mini_hud_collapsed", False))

    def on_typing_speed_scale_change(self):
        try:
            level = int(self.typing_speed_scale_var.get())
        except Exception:
            level = 5
        level = max(1, min(20, level))
        if hasattr(self, "typing_speed_profile_var"):
            self.typing_speed_profile_var.set(f"x{level}")
        if hasattr(self, "lbl_typing_speed_value"):
            self.lbl_typing_speed_value.config(text=f"x{level}")
        self.on_option_toggle()

    def _preset_cfg_key(self, profile, suffix):
        profile = "asset" if str(profile).strip().lower() == "asset" else "prompt"
        if profile == "asset":
            return f"asset_prompt_{suffix}"
        return f"prompt_{suffix}"

    def _panel_selector_key(self, profile, state):
        profile = "asset" if str(profile).strip().lower() == "asset" else "prompt"
        state = "video" if str(state).strip().lower() == "video" else "image"
        prefix = "asset_prompt" if profile == "asset" else "prompt"
        return f"{prefix}_{state}_panel_selector"

    def _preset_selector_summary(self, profile="prompt"):
        image_panel = str(self.cfg.get(self._panel_selector_key(profile, "image"), "") or "").strip() or "-"
        video_panel = str(self.cfg.get(self._panel_selector_key(profile, "video"), "") or "").strip() or "-"
        prefix = "S자동화" if profile == "asset" else "프롬프트"
        return f"{prefix} 저장된 selector | 이미지 패널: {image_panel} | 동영상 패널: {video_panel}"

    def _refresh_prompt_preset_selector_label(self):
        if hasattr(self, "lbl_prompt_preset_selector"):
            self.lbl_prompt_preset_selector.config(text=self._preset_selector_summary("prompt"))
        if hasattr(self, "lbl_asset_prompt_preset_selector"):
            self.lbl_asset_prompt_preset_selector.config(text=self._preset_selector_summary("asset"))

    def _refresh_manual_baseline_labels(self):
        if hasattr(self, "lbl_prompt_baseline_ready"):
            self.lbl_prompt_baseline_ready.config(
                text="기본값 이미지 확인됨" if self.prompt_image_baseline_ready else "기본값 이미지 확인 필요",
                fg=self.color_success if self.prompt_image_baseline_ready else self.color_error,
            )
        if hasattr(self, "lbl_asset_baseline_ready"):
            self.lbl_asset_baseline_ready.config(
                text="기본값 동영상 확인됨" if self.asset_image_baseline_ready else "기본값 동영상 확인 필요",
                fg=self.color_success if self.asset_image_baseline_ready else self.color_error,
            )

    def on_mark_prompt_image_baseline_ready(self):
        self.prompt_image_baseline_ready = True
        self.current_media_state = "image"
        self.cfg["prompt_image_baseline_ready"] = True
        self.cfg["current_media_state"] = "image"
        self.save_config()
        self._refresh_manual_baseline_labels()
        self.log("✅ 프롬프트 자동화 기본값 이미지 확인 완료")

    def on_reset_prompt_image_baseline_ready(self):
        self.prompt_image_baseline_ready = False
        self.cfg["prompt_image_baseline_ready"] = False
        self.save_config()
        self._refresh_manual_baseline_labels()
        self.log("ℹ️ 프롬프트 자동화 기본값 이미지 확인 해제")

    def on_mark_asset_image_baseline_ready(self):
        self.asset_image_baseline_ready = True
        self.current_media_state = "video"
        self.cfg["asset_image_baseline_ready"] = True
        self.cfg["current_media_state"] = "video"
        self.save_config()
        self._refresh_manual_baseline_labels()
        self.log("✅ S자동화 기본값 동영상 확인 완료")

    def on_reset_asset_image_baseline_ready(self):
        self.asset_image_baseline_ready = False
        self.cfg["asset_image_baseline_ready"] = False
        self.save_config()
        self._refresh_manual_baseline_labels()
        self.log("ℹ️ S자동화 기본값 동영상 확인 해제")

    def _build_ui(self):
        # 1. Header (High Visibility)
        header = tk.Frame(self.root, bg=self.color_header, height=64, highlightbackground="#24324B", highlightthickness=1)
        header.grid(row=0, column=0, sticky="ew")
        self.header = header
        
        title_f = tk.Frame(header, bg=self.color_header)
        title_f.pack(side="left", padx=16, pady=8)
        tk.Label(title_f, text="Flow Classic Plus", font=self.font_title, bg=self.color_header, fg=self.color_text).pack(anchor="w")
        tk.Label(title_f, text="클래식 개선판", font=self.font_subtitle, bg=self.color_header, fg=self.color_text_sec).pack(anchor="w")

        center_f = tk.Frame(header, bg=self.color_header)
        center_f.pack(side="left", fill="both", expand=True, padx=12, pady=8)
        header_progress_card = tk.Frame(center_f, bg="#18283D", highlightbackground="#304663", highlightthickness=1)
        header_progress_card.pack(fill="x", expand=True, padx=(0, 8))
        tk.Label(header_progress_card, text="진행 상황", font=self.font_small, bg="#18283D", fg=self.color_text_sec).pack(anchor="center", pady=(6, 0))
        self.lbl_header_progress = tk.Label(header_progress_card, text="0 / 0 (0.0%)", font=(self.font_mono_family, 13, "bold"), bg="#18283D", fg=self.color_accent)
        self.lbl_header_progress.pack(anchor="center", pady=(0, 3))
        self.header_progress_canvas = tk.Canvas(header_progress_card, height=18, bg="#18283D", highlightthickness=0, bd=0)
        self.header_progress_canvas.pack(fill="x", padx=12, pady=(0, 8))
        self.root.after(120, self._draw_header_progress_bar)

        right_f = tk.Frame(header, bg=self.color_header)
        right_f.pack(side="right", padx=14, pady=10)
        status_f = tk.Frame(right_f, bg=self.color_header)
        status_f.pack(side="left", padx=(0, 10))
        tk.Label(status_f, text="현재 상태", font=self.font_small, bg=self.color_header, fg=self.color_text_sec).pack(anchor="e")
        self.lbl_main_status = tk.Label(status_f, text="준비 완료", font=(self.font_ui_family, 16, "bold"), bg=self.color_header, fg=self.color_success)
        self.lbl_main_status.pack(anchor="e")
        self.btn_go_pipeline = ttk.Button(right_f, text="🏃 이어달리기", command=self.show_pipeline_window)
        self.btn_go_pipeline.pack(side="left", padx=(0, 6))
        self.btn_go_home = ttk.Button(right_f, text="🏠 메인 메뉴", command=self.show_home_menu)
        self.btn_go_home.pack(side="left")

        # 2. Body
        mid_frame = tk.Frame(self.root, bg=self.color_bg, pady=6)
        mid_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(6, 2))
        self.mid_frame = mid_frame

        self.body_pane = ttk.Panedwindow(mid_frame, orient="horizontal")
        self.body_pane.pack(fill="both", expand=True)

        # --- Left: Settings (Scrollable) ---
        self.left_container = tk.Frame(self.body_pane, bg=self.color_bg, width=520)
        self.left_container.pack_propagate(False) # 고정 너비 유지

        canvas = tk.Canvas(self.left_container, bg=self.color_bg, highlightthickness=0)
        self.left_canvas = canvas
        scrollbar = ttk.Scrollbar(self.left_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.color_bg)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(canvas_window, width=max(e.width - 2, 240)))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 마우스 휠 지원
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        left_card = ttk.LabelFrame(scrollable_frame, text=" ⚙️ 기본 설정 ", padding=12)
        left_card.pack(fill="x", padx=4, pady=4)
        canvas._scroll_canvas_target = canvas
        scrollable_frame._scroll_canvas_target = canvas
        
        # Playwright Target Settings
        tk.Label(left_card, text="1. 브라우저 대상 설정 (필수)", font=self.font_section, fg=self.color_text).pack(anchor="w", pady=(0, 5))

        tk.Label(left_card, text="시작 URL", bg=self.color_bg, font=self.font_small).pack(anchor="w")
        self.start_url_var = tk.StringVar(value=self.cfg.get("start_url", "https://labs.google/flow"))
        self.entry_start_url = tk.Entry(left_card, textvariable=self.start_url_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_mono)
        self.entry_start_url.pack(fill="x", ipady=4, pady=(2, 8))
        self.entry_start_url.bind("<FocusOut>", self.on_option_toggle)

        browser_scale_f = tk.Frame(left_card, bg=self.color_bg)
        browser_scale_f.pack(fill="x", pady=(0, 8))
        tk.Label(browser_scale_f, text="봇 작업창 크기", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.browser_window_scale_var = tk.StringVar(value=str(self._clamp_percent(self.cfg.get("browser_window_scale_percent", 100), default=100, minimum=50, maximum=150)))
        btn_browser_scale_minus = ttk.Button(browser_scale_f, text="-", width=3, command=lambda: self._set_browser_window_scale_percent(delta=-10))
        btn_browser_scale_minus.pack(side="left", padx=(6, 4))
        self.scale_control_buttons.append(btn_browser_scale_minus)
        self.lbl_browser_window_scale_state = tk.Label(browser_scale_f, text=f"{self._clamp_percent(self.cfg.get('browser_window_scale_percent', 100), default=100)}%", bg=self.color_bg, fg=self.color_info, font=self.font_small, width=6)
        self.lbl_browser_window_scale_state.pack(side="left", padx=(0, 6))
        btn_browser_scale_plus = ttk.Button(browser_scale_f, text="+", width=3, command=lambda: self._set_browser_window_scale_percent(delta=10))
        btn_browser_scale_plus.pack(side="left", padx=(0, 14))
        self.scale_control_buttons.append(btn_browser_scale_plus)

        tk.Label(browser_scale_f, text="브라우저 배율", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.browser_zoom_var = tk.StringVar(value=str(self._clamp_percent(self.cfg.get("browser_zoom_percent", 100), default=100, minimum=50, maximum=150)))
        btn_browser_zoom_minus = ttk.Button(browser_scale_f, text="-", width=3, command=lambda: self._set_browser_zoom_percent(delta=-10))
        btn_browser_zoom_minus.pack(side="left", padx=(6, 4))
        self.scale_control_buttons.append(btn_browser_zoom_minus)
        self.lbl_browser_zoom_state = tk.Label(browser_scale_f, text=f"{self._clamp_percent(self.cfg.get('browser_zoom_percent', 100), default=100)}%", bg=self.color_bg, fg=self.color_info, font=self.font_small, width=6)
        self.lbl_browser_zoom_state.pack(side="left", padx=(0, 6))
        btn_browser_zoom_plus = ttk.Button(browser_scale_f, text="+", width=3, command=lambda: self._set_browser_zoom_percent(delta=10))
        btn_browser_zoom_plus.pack(side="left")
        self.scale_control_buttons.append(btn_browser_zoom_plus)

        display_mode_f = tk.Frame(left_card, bg=self.color_bg)
        display_mode_f.pack(fill="x", pady=(0, 8))
        tk.Label(display_mode_f, text="환경 모드", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.display_mode_var = tk.StringVar(value=self._display_mode_labels().get(self._active_display_mode(), "노트북 모드"))
        self.combo_display_mode = ttk.Combobox(
            display_mode_f,
            textvariable=self.display_mode_var,
            state="readonly",
            width=12,
            values=tuple(self._display_mode_labels().values()),
            font=self.font_small,
        )
        self.combo_display_mode.pack(side="left", padx=(6, 8))
        self.combo_display_mode.bind("<<ComboboxSelected>>", self.on_display_mode_change)
        ttk.Button(display_mode_f, text="노트북 저장", command=lambda: self.on_save_display_mode("laptop")).pack(side="left")
        ttk.Button(display_mode_f, text="데스크탑 저장", command=lambda: self.on_save_display_mode("desktop")).pack(side="left", padx=6)
        self.lbl_display_mode_state = tk.Label(
            display_mode_f,
            text=f"현재 적용: {self._display_mode_labels().get(self._active_display_mode(), '노트북 모드')}",
            bg=self.color_bg,
            fg=self.color_success,
            font=self.font_small,
        )
        self.lbl_display_mode_state.pack(side="left", padx=(10, 0))

        self.lbl_display_mode_summary = tk.Label(
            left_card,
            text=self._display_mode_summary_text(),
            bg=self.color_bg,
            fg=self.color_info,
            font=self.font_small,
            justify="left",
            wraplength=620,
        )
        self.lbl_display_mode_summary.pack(anchor="w", pady=(0, 8))

        tk.Label(left_card, text="입력창 CSS Selector", bg=self.color_bg, font=self.font_small).pack(anchor="w")
        self.input_selector_var = tk.StringVar(value=self.cfg.get("input_selector", "textarea, [contenteditable='true']"))
        self.entry_input_selector = tk.Entry(left_card, textvariable=self.input_selector_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_mono)
        self.entry_input_selector.pack(fill="x", ipady=4, pady=(2, 8))
        self.entry_input_selector.bind("<FocusOut>", self.on_option_toggle)

        tk.Label(left_card, text="제출 버튼 CSS Selector", bg=self.color_bg, font=self.font_small).pack(anchor="w")
        self.submit_selector_var = tk.StringVar(value=self.cfg.get("submit_selector", "button[type='submit']"))
        self.entry_submit_selector = tk.Entry(left_card, textvariable=self.submit_selector_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_mono)
        self.entry_submit_selector.pack(fill="x", ipady=4, pady=(2, 8))
        self.entry_submit_selector.bind("<FocusOut>", self.on_option_toggle)

        selector_tool_f = tk.Frame(left_card, bg=self.color_bg)
        selector_tool_f.pack(fill="x", pady=(0, 8))
        ttk.Button(selector_tool_f, text="🔍 Selector 자동 찾기", command=self.on_auto_detect_selectors).pack(side="left")
        ttk.Button(selector_tool_f, text="🧪 Selector 테스트", command=self.on_test_selectors).pack(side="left", padx=6)
        ttk.Button(selector_tool_f, text="🤖 봇 작업창 열기", command=self.on_open_bot_work_window).pack(side="left")

        detected_state_f = tk.Frame(left_card, bg=self.color_bg)
        detected_state_f.pack(fill="x", pady=(0, 8))
        ttk.Button(detected_state_f, text="👁 상태 확인", command=self.on_refresh_detected_media_state).pack(side="left")
        self.lbl_detected_media_state = tk.Label(
            detected_state_f,
            text="현재 감지 생성 기본값: 확인 필요",
            bg=self.color_bg,
            fg=self.color_text_sec,
            font=self.font_small,
        )
        self.lbl_detected_media_state.pack(side="left", padx=(10, 0))

        browser_f = tk.Frame(left_card, bg=self.color_bg)
        browser_f.pack(fill="x", pady=(0, 10))
        self.browser_headless_var = tk.BooleanVar(value=self.cfg.get("browser_headless", False))
        tk.Checkbutton(
            browser_f,
            text="헤드리스(화면 숨김)",
            variable=self.browser_headless_var,
            command=self.on_option_toggle,
            bg=self.color_bg,
            font=self.font_small,
            activebackground=self.color_bg,
        ).pack(side="left")

        tk.Label(browser_f, text="채널:", bg=self.color_bg, font=self.font_small).pack(side="left", padx=(10, 4))
        self.browser_channel_var = tk.StringVar(value=self.cfg.get("browser_channel", "chrome"))
        self.combo_browser_channel = ttk.Combobox(
            browser_f,
            textvariable=self.browser_channel_var,
            state="readonly",
            width=10,
            font=self.font_small,
            values=("chrome", "msedge", "chromium"),
        )
        self.combo_browser_channel.pack(side="left")
        self.combo_browser_channel.bind("<<ComboboxSelected>>", self.on_option_toggle)

        new_project_f = tk.Frame(left_card, bg=self.color_bg)
        self.auto_new_project_var = tk.BooleanVar(value=self.cfg.get("auto_open_new_project", True))
        tk.Checkbutton(
            new_project_f,
            text="홈 화면이면 '새 프로젝트' 자동 클릭",
            variable=self.auto_new_project_var,
            command=self.on_option_toggle,
            bg=self.color_bg,
            font=("Malgun Gothic", 9),
            activebackground=self.color_bg,
        ).pack(side="left")

        self.new_project_selector_var = tk.StringVar(value=self.cfg.get("new_project_selector", ""))
        self.entry_new_project_selector = tk.Entry(left_card, textvariable=self.new_project_selector_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=("Consolas", 10))
        self.entry_new_project_selector.bind("<FocusOut>", self.on_option_toggle)

        self.lbl_coords = tk.Label(left_card, text=self._get_coord_text(), font=("Consolas", 9), fg=self.color_accent, bg=self.color_input_soft, padx=5, pady=4)
        
        # Options
        tk.Label(left_card, text="2. 옵션 설정", font=self.font_section, fg=self.color_text).pack(anchor="w", pady=(0, 5))
        
        op_f = tk.Frame(left_card, bg=self.color_bg)
        op_f.pack(fill="x")
        
        c1 = tk.Checkbutton(op_f, text="소리 켜기", variable=tk.BooleanVar(), command=self.on_option_toggle, bg=self.color_bg, font=self.font_body, activebackground=self.color_bg)
        self.sound_var = tk.BooleanVar(value=self.cfg.get("sound_enabled", True))
        c1.config(variable=self.sound_var)
        c1.grid(row=0, column=0, sticky="w", padx=5)
        
        c2 = tk.Checkbutton(op_f, text="대기 중 랜덤 행동", variable=tk.BooleanVar(), command=self.on_option_toggle, bg=self.color_bg, fg="#FF8CC3", selectcolor=self.color_bg, activebackground=self.color_bg, font=self.font_body_bold)
        self.afk_var = tk.BooleanVar(value=self.cfg.get("afk_mode", False))
        c2.config(variable=self.afk_var)
        c2.grid(row=0, column=1, sticky="w", padx=5)
        
        c_lang = tk.Checkbutton(op_f, text="한글+영어 모드", variable=tk.BooleanVar(), command=self.on_option_toggle, bg=self.color_bg, font=self.font_body, activebackground=self.color_bg)
        self.lang_var = tk.BooleanVar(value=(self.cfg.get("language_mode", "en") == "ko_en"))
        c_lang.config(variable=self.lang_var)
        c_lang.grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
        
        # [NEW] Input Mode Selection
        tk.Label(left_card, text="⌨️ 입력 방식 선택", font=self.font_body_bold, bg=self.color_bg).pack(anchor="w", pady=(15, 0))
        self.input_mode_var = tk.StringVar(value="typing")
        mode_f = tk.Frame(left_card, bg=self.color_bg)
        mode_f.pack(fill="x", pady=5)
        self.combo_input_mode = ttk.Combobox(mode_f, textvariable=self.input_mode_var, state="disabled", font=self.font_body, width=18)
        self.combo_input_mode['values'] = ("typing",)
        self.combo_input_mode.pack(side="left", fill="x", expand=True)
        tk.Label(mode_f, text="타이핑만 사용", bg=self.color_bg, fg=self.color_text_sec, font=self.font_small).pack(side="left", padx=(8, 0))

        speed_f = tk.Frame(left_card, bg=self.color_bg)
        speed_f.pack(fill="x", pady=(0, 8))
        tk.Label(speed_f, text="⚡ 타이핑 속도", bg=self.color_bg, font=self.font_body_bold).pack(anchor="w")
        speed_default = str(self.cfg.get("typing_speed_profile", "x5")).strip().lower() or "x5"
        legacy_speed_map = {"slow": "x2", "normal": "x5", "fast": "x10", "turbo": "x16"}
        speed_default = legacy_speed_map.get(speed_default, speed_default)
        try:
            speed_level = int(speed_default.replace("x", "").strip())
        except Exception:
            speed_level = 5
        speed_level = max(1, min(20, speed_level))
        speed_row = tk.Frame(speed_f, bg=self.color_bg)
        speed_row.pack(fill="x", pady=(4, 0))
        self.typing_speed_scale_var = tk.IntVar(value=speed_level)
        self.typing_speed_profile_var = tk.StringVar(value=f"x{speed_level}")
        self.scale_typing_speed = tk.Scale(
            speed_row,
            from_=1,
            to=20,
            orient="horizontal",
            variable=self.typing_speed_scale_var,
            command=lambda _v: self.on_typing_speed_scale_change(),
            bg=self.color_bg,
            fg=self.color_text,
            highlightthickness=0,
            troughcolor="#24324B",
            activebackground=self.color_accent,
            font=self.font_mono_small,
            length=220,
        )
        self.scale_typing_speed.pack(side="left", fill="x", expand=True)
        self.lbl_typing_speed_value = tk.Label(
            speed_row,
            text=f"x{speed_level}",
            bg=self.color_bg,
            fg=self.color_accent,
            font=(self.font_mono_family, 13, "bold"),
            width=5,
        )
        self.lbl_typing_speed_value.pack(side="left", padx=(10, 0))

        break_f = tk.Frame(left_card, bg=self.color_bg)
        break_f.pack(fill="x", pady=(6, 8))
        tk.Label(break_f, text="☕ 휴식 설정 (프롬프트/S반복 전용)", bg=self.color_bg, font=self.font_body_bold).grid(row=0, column=0, columnspan=4, sticky="w")
        tk.Label(break_f, text="몇 개 작업 후", bg=self.color_bg, font=self.font_small).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.work_break_every_var = tk.StringVar(value=str(int(self.cfg.get("work_break_every_count", 40) or 40)))
        self.entry_work_break_every = tk.Entry(break_f, textvariable=self.work_break_every_var, width=8, justify="center", bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_mono)
        self.entry_work_break_every.grid(row=1, column=1, sticky="w", padx=(6, 10), pady=(6, 0))
        tk.Label(break_f, text="개", bg=self.color_bg, font=self.font_small).grid(row=1, column=2, sticky="w", pady=(6, 0))
        tk.Label(break_f, text="쉬는 시간", bg=self.color_bg, font=self.font_small).grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.work_break_minutes_var = tk.StringVar(value=str(int(self.cfg.get("work_break_minutes", 12) or 12)))
        self.entry_work_break_minutes = tk.Entry(break_f, textvariable=self.work_break_minutes_var, width=8, justify="center", bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_mono)
        self.entry_work_break_minutes.grid(row=2, column=1, sticky="w", padx=(6, 10), pady=(6, 0))
        tk.Label(break_f, text="분", bg=self.color_bg, font=self.font_small).grid(row=2, column=2, sticky="w", pady=(6, 0))
        tk.Label(
            break_f,
            text="※ 실제 휴식은 설정값 기준으로 ±30% 랜덤 적용됩니다. 다운로드는 휴식 없이 계속 진행합니다.",
            bg=self.color_bg,
            fg=self.color_text_sec,
            font=("Malgun Gothic", 9),
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self.entry_work_break_every.bind("<FocusOut>", self.on_option_toggle)
        self.entry_work_break_every.bind("<Return>", self.on_option_toggle)
        self.entry_work_break_minutes.bind("<FocusOut>", self.on_option_toggle)
        self.entry_work_break_minutes.bind("<Return>", self.on_option_toggle)

        preset_body, _set_preset_open = self._create_collapsible_section(left_card, "프롬프트 자동화 전용 생성 옵션", opened=True)
        self._set_prompt_preset_open = _set_preset_open
        preset_f = tk.Frame(preset_body, bg=self.color_bg)
        preset_f.pack(fill="x", pady=6)

        self.prompt_mode_preset_enabled_var = tk.BooleanVar(value=True)
        tk.Label(
            preset_f,
            text="프롬프트 입력 전에 생성 옵션 자동 맞추기: 항상 ON",
            bg=self.color_bg,
            font=self.font_body_bold,
            fg=self.color_success,
        ).pack(anchor="w")

        preset_row = tk.Frame(preset_f, bg=self.color_bg)
        preset_row.pack(fill="x", pady=(8, 4))

        tk.Label(preset_row, text="모드", bg=self.color_bg, font=self.font_small).pack(side="left")
        media_label = PROMPT_MEDIA_LABELS.get(self.cfg.get("prompt_media_mode", "image"), "이미지")
        self.prompt_media_mode_var = tk.StringVar(value=media_label)
        self.combo_prompt_media_mode = ttk.Combobox(
            preset_row,
            textvariable=self.prompt_media_mode_var,
            state="readonly",
            width=8,
            values=tuple(PROMPT_MEDIA_VALUES.keys()),
            font=self.font_small,
        )
        self.combo_prompt_media_mode.pack(side="left", padx=(6, 12))
        self.combo_prompt_media_mode.bind("<<ComboboxSelected>>", self.on_option_toggle)

        tk.Label(
            preset_f,
            text="※ 이 기능은 프롬프트 자동화에서만 사용됩니다. 지금은 Image / Video 모드만 맞춥니다.",
            bg=self.color_bg,
            fg=self.color_text_sec,
            font=("Malgun Gothic", 9),
        ).pack(anchor="w", pady=(2, 0))

        baseline_row = tk.Frame(preset_f, bg=self.color_bg)
        baseline_row.pack(fill="x", pady=(8, 0))
        ttk.Button(baseline_row, text="☑ 기본값 이미지 맞춤 완료", command=self.on_mark_prompt_image_baseline_ready).pack(side="left")
        ttk.Button(baseline_row, text="↺ 다시 맞추기", command=self.on_reset_prompt_image_baseline_ready).pack(side="left", padx=6)
        self.lbl_prompt_baseline_ready = tk.Label(
            baseline_row,
            text="기본값 이미지 확인 필요",
            bg=self.color_bg,
            fg=self.color_error,
            font=self.font_body_bold,
        )
        self.lbl_prompt_baseline_ready.pack(side="left", padx=(10, 0))

        preset_btn_f = tk.Frame(preset_f, bg=self.color_bg)
        preset_btn_f.pack(fill="x", pady=(8, 0))
        ttk.Button(preset_btn_f, text="🧪 이미지→동영상", command=self.on_test_prompt_image_to_video).pack(side="left")
        ttk.Button(preset_btn_f, text="🧪 동영상→이미지", command=self.on_test_prompt_video_to_image).pack(side="left", padx=6)
        self._refresh_manual_baseline_labels()

        asset_body, _set_asset_open = self._create_collapsible_section(left_card, "S001~S### 에셋 자동 반복", opened=True)
        self._set_asset_open = _set_asset_open
        asset_f = tk.Frame(asset_body, bg=self.color_bg)
        asset_f.pack(fill="x", pady=6)
        self.asset_loop_var = tk.BooleanVar(value=self.cfg.get("asset_loop_enabled", False))
        tk.Checkbutton(
            asset_f,
            text="S번호 자동 반복 사용",
            variable=self.asset_loop_var,
            command=self.on_option_toggle,
            bg=self.color_bg,
            font=self.font_body,
            activebackground=self.color_bg,
        ).pack(anchor="w")
        tk.Label(
            asset_f,
            text="동작: 시작 클릭 -> 에셋 검색에 S번호 입력 -> 프롬프트 입력",
            bg=self.color_bg,
            fg=self.color_text_sec,
            font=self.font_small,
        ).pack(anchor="w", pady=(2, 6))

        asset_range_f = tk.Frame(asset_f, bg=self.color_bg)
        asset_range_f.pack(fill="x", pady=(0, 6))
        tk.Label(asset_range_f, text="시작 번호", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.asset_loop_start_var = tk.StringVar(value=self._format_asset_number_text(self.cfg.get("asset_loop_start", 1)))
        self.spin_asset_start = tk.Spinbox(
            asset_range_f,
            from_=1,
            to=9999,
            width=6,
            textvariable=self.asset_loop_start_var,
            command=self.on_option_toggle,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
        )
        self.spin_asset_start.pack(side="left", padx=(6, 14))
        self.spin_asset_start.bind("<FocusOut>", self.on_option_toggle)
        self.spin_asset_start.bind("<Return>", self.on_option_toggle)
        self.spin_asset_start.bind("<KeyRelease>", self.on_option_toggle)

        tk.Label(asset_range_f, text="끝 번호", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.asset_loop_end_var = tk.StringVar(value=self._format_asset_number_text(self.cfg.get("asset_loop_end", self.cfg.get("asset_loop_start", 1))))
        self.spin_asset_end = tk.Spinbox(
            asset_range_f,
            from_=1,
            to=9999,
            width=6,
            textvariable=self.asset_loop_end_var,
            command=self.on_option_toggle,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
        )
        self.spin_asset_end.pack(side="left", padx=(6, 0))
        self.spin_asset_end.bind("<FocusOut>", self.on_option_toggle)
        self.spin_asset_end.bind("<Return>", self.on_option_toggle)
        self.spin_asset_end.bind("<KeyRelease>", self.on_option_toggle)

        asset_manual_f = tk.Frame(asset_f, bg=self.color_bg)
        asset_manual_f.pack(fill="x", pady=(0, 6))
        tk.Label(asset_manual_f, text="개별 번호", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.asset_manual_selection_var = tk.StringVar(value=str(self.cfg.get("asset_manual_selection", "") or ""))
        self.entry_asset_manual_selection = tk.Entry(
            asset_manual_f,
            textvariable=self.asset_manual_selection_var,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
            insertbackground=self.color_input_fg,
            font=self.font_mono,
        )
        self.entry_asset_manual_selection.pack(side="left", fill="x", expand=True, padx=(6, 0), ipady=2)
        self.entry_asset_manual_selection.bind("<FocusOut>", self.on_option_toggle)
        self.entry_asset_manual_selection.bind("<Return>", self.on_option_toggle)
        self.entry_asset_manual_selection.bind("<KeyRelease>", self.on_option_toggle)
        ToolTip(self.entry_asset_manual_selection, "예: 005,018,048,057,071-079,110")
        ttk.Button(asset_manual_f, text="최근 실패 자동채움", command=self.on_fill_asset_manual_from_failures).pack(side="left", padx=(6, 0))
        self.lbl_asset_manual_status = tk.Label(asset_f, text="", bg=self.color_bg, fg=self.color_text_sec, font=self.font_small)
        self.lbl_asset_manual_status.pack(anchor="w", pady=(0, 6))

        asset_prefix_f = tk.Frame(asset_f, bg=self.color_bg)
        asset_prefix_f.pack(fill="x", pady=(0, 6))
        tk.Label(asset_prefix_f, text="접두어", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.asset_loop_prefix_var = tk.StringVar(value=self.cfg.get("asset_loop_prefix", "S"))
        self.entry_asset_prefix = tk.Entry(asset_prefix_f, textvariable=self.asset_loop_prefix_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=("Consolas", 10), width=8)
        self.entry_asset_prefix.pack(side="left", padx=(6, 0))
        self.entry_asset_prefix.bind("<FocusOut>", self.on_option_toggle)

        asset_prompt_source_f = tk.Frame(asset_f, bg=self.color_bg)
        asset_prompt_source_f.pack(fill="x", pady=(0, 6))
        self.asset_use_prompt_slot_var = tk.BooleanVar(value=bool(self.cfg.get("asset_use_prompt_slot", False)))
        tk.Checkbutton(
            asset_prompt_source_f,
            text="개별 프롬프트 파일 사용",
            variable=self.asset_use_prompt_slot_var,
            command=self.on_option_toggle,
            bg=self.color_bg,
            font=self.font_small,
            activebackground=self.color_bg,
        ).pack(side="left")
        tk.Label(asset_prompt_source_f, text="프롬프트 파일", bg=self.color_bg, font=self.font_small).pack(side="left", padx=(10, 0))
        self.asset_prompt_slot_var = tk.StringVar()
        self.combo_asset_prompt_slot = ttk.Combobox(
            asset_prompt_source_f,
            textvariable=self.asset_prompt_slot_var,
            state="readonly",
            width=18,
            font=self.font_small,
        )
        self.combo_asset_prompt_slot.pack(side="left", padx=(6, 0))
        self.combo_asset_prompt_slot.bind("<<ComboboxSelected>>", self.on_option_toggle)
        self.lbl_asset_prompt_source_status = tk.Label(
            asset_f,
            text="",
            bg=self.color_bg,
            fg=self.color_text_sec,
            font=self.font_small,
        )
        self.lbl_asset_prompt_source_status.pack(anchor="w", pady=(0, 6))
        tk.Label(
            asset_f,
            text="예: S004::개별 프롬프트 / 태그 없는 프롬프트는 공통 fallback",
            bg=self.color_bg,
            fg=self.color_text_sec,
            font=self.font_small,
        ).pack(anchor="w", pady=(0, 6))
        self._refresh_asset_prompt_slot_controls()

        tk.Label(asset_f, text="프롬프트 템플릿 ({tag}=S001/S002... 로 치환)", bg=self.color_bg, font=self.font_small).pack(anchor="w")
        self.asset_loop_template_var = tk.StringVar(
            value=self.cfg.get("asset_loop_prompt_template", "{tag} : Naturally Seamless Loop animation.")
        )
        self.entry_asset_template = tk.Entry(
            asset_f,
            textvariable=self.asset_loop_template_var,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
            insertbackground=self.color_input_fg,
            font=("Consolas", 10),
        )
        self.entry_asset_template.pack(fill="x", ipady=3, pady=(2, 0))
        self.entry_asset_template.bind("<FocusOut>", self.on_option_toggle)

        asset_preset_box = tk.LabelFrame(
            asset_f,
            text="S자동화 전용 생성 옵션",
            bg=self.color_bg,
            fg=self.color_text,
            font=self.font_body_bold,
            padx=8,
            pady=6,
        )
        asset_preset_box.pack(fill="x", pady=(10, 0))

        self.asset_prompt_mode_preset_enabled_var = tk.BooleanVar(value=True)
        tk.Label(
            asset_preset_box,
            text="S자동화 시작 전 생성 옵션 자동 맞추기: 항상 ON",
            bg=self.color_bg,
            font=self.font_body_bold,
            fg=self.color_success,
        ).pack(anchor="w")

        asset_preset_row = tk.Frame(asset_preset_box, bg=self.color_bg)
        asset_preset_row.pack(fill="x", pady=(8, 4))

        tk.Label(asset_preset_row, text="모드", bg=self.color_bg, font=self.font_small).pack(side="left")
        asset_media_label = PROMPT_MEDIA_LABELS.get(self.cfg.get("asset_prompt_media_mode", "video"), "영상")
        self.asset_prompt_media_mode_var = tk.StringVar(value=asset_media_label)
        self.combo_asset_prompt_media_mode = ttk.Combobox(
            asset_preset_row,
            textvariable=self.asset_prompt_media_mode_var,
            state="readonly",
            width=8,
            values=tuple(PROMPT_MEDIA_VALUES.keys()),
            font=self.font_small,
        )
        self.combo_asset_prompt_media_mode.pack(side="left", padx=(6, 12))
        self.combo_asset_prompt_media_mode.bind("<<ComboboxSelected>>", self.on_option_toggle)

        tk.Label(
            asset_preset_box,
            text="※ 이 기능은 S자동화에서만 사용됩니다. 지금은 Image / Video 모드만 맞춥니다.",
            bg=self.color_bg,
            fg=self.color_text_sec,
            font=("Malgun Gothic", 9),
        ).pack(anchor="w", pady=(2, 0))

        asset_baseline_row = tk.Frame(asset_preset_box, bg=self.color_bg)
        asset_baseline_row.pack(fill="x", pady=(8, 0))
        ttk.Button(asset_baseline_row, text="☑ 기본값 동영상 맞춤 완료", command=self.on_mark_asset_image_baseline_ready).pack(side="left")
        ttk.Button(asset_baseline_row, text="↺ 다시 맞추기", command=self.on_reset_asset_image_baseline_ready).pack(side="left", padx=6)
        self.lbl_asset_baseline_ready = tk.Label(
            asset_baseline_row,
            text="기본값 동영상 확인 필요",
            bg=self.color_bg,
            fg=self.color_error,
            font=self.font_body_bold,
        )
        self.lbl_asset_baseline_ready.pack(side="left", padx=(10, 0))

        asset_preset_btn_f = tk.Frame(asset_preset_box, bg=self.color_bg)
        asset_preset_btn_f.pack(fill="x", pady=(8, 0))
        ttk.Button(asset_preset_btn_f, text="🧪 이미지→동영상", command=self.on_test_asset_image_to_video).pack(side="left")
        ttk.Button(asset_preset_btn_f, text="🧪 동영상→이미지", command=self.on_test_asset_video_to_image).pack(side="left", padx=6)
        self._refresh_manual_baseline_labels()

        tk.Label(asset_f, text="시작 버튼 selector(선택)", bg=self.color_bg, font=("Malgun Gothic", 9)).pack(anchor="w", pady=(8, 0))
        self.asset_start_selector_var = tk.StringVar(value=self.cfg.get("asset_start_selector", ""))
        self.entry_asset_start_selector = tk.Entry(asset_f, textvariable=self.asset_start_selector_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=("Consolas", 10))
        self.entry_asset_start_selector.pack(fill="x", ipady=3, pady=(2, 4))
        self.entry_asset_start_selector.bind("<FocusOut>", self.on_option_toggle)

        tk.Label(asset_f, text="에셋 검색 버튼 selector(선택)", bg=self.color_bg, font=("Malgun Gothic", 9)).pack(anchor="w")
        self.asset_search_btn_selector_var = tk.StringVar(value=self.cfg.get("asset_search_button_selector", ""))
        self.entry_asset_search_btn_selector = tk.Entry(asset_f, textvariable=self.asset_search_btn_selector_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=("Consolas", 10))
        self.entry_asset_search_btn_selector.pack(fill="x", ipady=3, pady=(2, 4))
        self.entry_asset_search_btn_selector.bind("<FocusOut>", self.on_option_toggle)

        tk.Label(asset_f, text="에셋 검색 입력칸 selector(선택)", bg=self.color_bg, font=("Malgun Gothic", 9)).pack(anchor="w")
        self.asset_search_input_selector_var = tk.StringVar(value=self.cfg.get("asset_search_input_selector", ""))
        self.entry_asset_search_input_selector = tk.Entry(asset_f, textvariable=self.asset_search_input_selector_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=("Consolas", 10))
        self.entry_asset_search_input_selector.pack(fill="x", ipady=3, pady=(2, 6))
        self.entry_asset_search_input_selector.bind("<FocusOut>", self.on_option_toggle)

        asset_btn_f = tk.Frame(asset_f, bg=self.color_bg)
        asset_btn_f.pack(fill="x", pady=(2, 0))
        ttk.Button(asset_btn_f, text="🔍 에셋 selector 자동찾기", command=self.on_auto_detect_asset_selectors).pack(side="left")
        ttk.Button(asset_btn_f, text="🧪 에셋 selector 테스트", command=self.on_test_asset_selectors).pack(side="left", padx=6)

        dl_body, _set_dl_open = self._create_collapsible_section(left_card, "다운로드 자동화", opened=True)
        self._set_dl_open = _set_dl_open
        dl_f = tk.Frame(dl_body, bg=self.color_bg)
        dl_f.pack(fill="x", pady=6)

        mode_f = tk.Frame(dl_f, bg=self.color_bg)
        mode_f.pack(fill="x", pady=(0, 6))
        tk.Label(mode_f, text="모드", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.download_mode_var = tk.StringVar(value=self.cfg.get("download_mode", "video"))
        self.combo_download_mode = ttk.Combobox(
            mode_f,
            textvariable=self.download_mode_var,
            state="readonly",
            width=10,
            values=("video", "image"),
            font=self.font_small,
        )
        self.combo_download_mode.pack(side="left", padx=(6, 0))
        self.combo_download_mode.bind("<<ComboboxSelected>>", self.on_option_toggle)

        q_f = tk.Frame(dl_f, bg=self.color_bg)
        q_f.pack(fill="x", pady=(0, 6))
        tk.Label(q_f, text="영상 품질", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.download_video_quality_var = tk.StringVar(value=self.cfg.get("download_video_quality", "1080P"))
        self.combo_download_video_quality = ttk.Combobox(
            q_f,
            textvariable=self.download_video_quality_var,
            state="readonly",
            width=8,
            values=("1080P", "720P", "4K"),
            font=self.font_small,
        )
        self.combo_download_video_quality.pack(side="left", padx=(6, 12))
        self.combo_download_video_quality.bind("<<ComboboxSelected>>", self.on_option_toggle)

        tk.Label(q_f, text="이미지 품질", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.download_image_quality_var = tk.StringVar(value=self.cfg.get("download_image_quality", "4K"))
        self.combo_download_image_quality = ttk.Combobox(
            q_f,
            textvariable=self.download_image_quality_var,
            state="readonly",
            width=6,
            values=("4K", "2K", "1K"),
            font=self.font_small,
        )
        self.combo_download_image_quality.pack(side="left", padx=(6, 0))
        self.combo_download_image_quality.bind("<<ComboboxSelected>>", self.on_option_toggle)

        wait_f = tk.Frame(dl_f, bg=self.color_bg)
        wait_f.pack(fill="x", pady=(0, 6))
        tk.Label(wait_f, text="실패 판단 대기(초)", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.download_wait_seconds_var = tk.StringVar(value=str(self.cfg.get("download_wait_seconds", 20)))
        self.entry_download_wait = tk.Entry(
            wait_f,
            textvariable=self.download_wait_seconds_var,
            width=6,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
            insertbackground=self.color_input_fg,
            font=("Consolas", 10),
        )
        self.entry_download_wait.pack(side="left", padx=(6, 10), ipady=2)
        self.entry_download_wait.bind("<FocusOut>", self.on_option_toggle)
        self.entry_download_wait.bind("<Return>", self.on_option_toggle)
        tk.Label(
            wait_f,
            text="재시도 없이 이 시간 뒤 다음 항목으로 넘어갑니다.",
            bg=self.color_bg,
            fg=self.color_text_sec,
            font=self.font_small,
        ).pack(side="left")

        out_f = tk.Frame(dl_f, bg=self.color_bg)
        out_f.pack(fill="x", pady=(0, 6))
        tk.Label(out_f, text="저장 폴더", bg=self.color_bg, font=self.font_small).pack(side="left")
        self.download_output_dir_var = tk.StringVar(value=self.cfg.get("download_output_dir", ""))
        self.entry_download_output_dir = tk.Entry(
            out_f,
            textvariable=self.download_output_dir_var,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
            insertbackground=self.color_input_fg,
            font=("Consolas", 9),
        )
        self.entry_download_output_dir.pack(side="left", fill="x", expand=True, padx=(6, 6), ipady=2)
        self.entry_download_output_dir.bind("<FocusOut>", self.on_option_toggle)
        ttk.Button(out_f, text="폴더선택", command=self.on_pick_download_output_dir).pack(side="left")
        tk.Label(dl_body, text="개별 다운로드 번호는 위 S반복의 '개별 번호' 입력칸을 공유합니다.", bg=self.color_bg, fg=self.color_text_sec, font=self.font_small).pack(anchor="w", pady=(0, 8))

        tk.Label(dl_f, text="검색 입력 selector(공통)", bg=self.color_bg, font=self.font_small).pack(anchor="w")
        self.download_search_input_selector_var = tk.StringVar(value=self.cfg.get("download_search_input_selector", ""))
        self.entry_download_search = tk.Entry(dl_f, textvariable=self.download_search_input_selector_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=("Consolas", 10))
        self.entry_download_search.pack(fill="x", ipady=3, pady=(2, 4))
        self.entry_download_search.bind("<FocusOut>", self.on_option_toggle)

        tk.Label(dl_f, text="영상 필터 selector", bg=self.color_bg, font=self.font_small).pack(anchor="w")
        self.download_video_filter_selector_var = tk.StringVar(value=self.cfg.get("download_video_filter_selector", ""))
        self.entry_download_video_filter = tk.Entry(dl_f, textvariable=self.download_video_filter_selector_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=("Consolas", 10))
        self.entry_download_video_filter.pack(fill="x", ipady=3, pady=(2, 4))
        self.entry_download_video_filter.bind("<FocusOut>", self.on_option_toggle)

        tk.Label(dl_f, text="이미지 필터 selector", bg=self.color_bg, font=self.font_small).pack(anchor="w")
        self.download_image_filter_selector_var = tk.StringVar(value=self.cfg.get("download_image_filter_selector", ""))
        self.entry_download_image_filter = tk.Entry(dl_f, textvariable=self.download_image_filter_selector_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=("Consolas", 10))
        self.entry_download_image_filter.pack(fill="x", ipady=3, pady=(2, 4))
        self.entry_download_image_filter.bind("<FocusOut>", self.on_option_toggle)

        d1 = tk.Frame(dl_f, bg=self.color_bg)
        d1.pack(fill="x", pady=(2, 0))
        ttk.Button(d1, text="🔍 이미지 다운로드 자동찾기", command=self.on_auto_detect_image_download_selectors).pack(side="left")
        ttk.Button(d1, text="🧪 이미지 다운로드 테스트", command=self.on_test_image_download_selectors).pack(side="left", padx=6)

        d2 = tk.Frame(dl_f, bg=self.color_bg)
        d2.pack(fill="x", pady=(6, 0))
        ttk.Button(d2, text="🔍 영상 다운로드 자동찾기", command=self.on_auto_detect_video_download_selectors).pack(side="left")
        ttk.Button(d2, text="🧪 영상 다운로드 테스트", command=self.on_test_video_download_selectors).pack(side="left", padx=6)

        tk.Label(left_card, text="3. 작업 간격 (초)", font=("Malgun Gothic", 11, "bold"), fg=self.color_text).pack(anchor="w", pady=(20, 5))
        self.entry_interval = tk.Entry(left_card, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=("Consolas", 16, "bold"), justify="center", relief="solid", borderwidth=1)
        self.entry_interval.insert(0, str(self.cfg.get("interval_seconds", 180)))
        self.entry_interval.pack(fill="x", ipady=5)
        tk.Label(left_card, text="※ 설정한 시간마다 봇이 작동합니다.", font=("Malgun Gothic", 9), fg=self.color_text_sec).pack(anchor="w")

        tk.Frame(left_card, height=12, bg=self.color_bg).pack()

        # --- Right: Dashboard (HUD Design, Scrollable) ---
        right_panel = tk.Frame(self.body_pane, bg=self.color_bg)
        self.right_panel = right_panel
        right_canvas = tk.Canvas(right_panel, bg=self.color_bg, highlightthickness=0)
        self.right_canvas = right_canvas
        right_scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=right_canvas.yview)
        self.right_scrollbar = right_scrollbar
        right_scrollable = tk.Frame(right_canvas, bg=self.color_bg)
        self.right_scrollable = right_scrollable
        right_scrollable.bind("<Configure>", lambda e: right_canvas.configure(scrollregion=right_canvas.bbox("all")))
        right_canvas_window = right_canvas.create_window((0, 0), window=right_scrollable, anchor="nw")
        right_canvas.bind("<Configure>", lambda e: right_canvas.itemconfigure(right_canvas_window, width=max(e.width - 2, 220)))
        right_canvas.configure(yscrollcommand=right_scrollbar.set)
        right_canvas._scroll_canvas_target = right_canvas
        right_scrollable._scroll_canvas_target = right_canvas
        right_canvas.pack(side="left", fill="both", expand=True)
        right_scrollbar.pack(side="right", fill="y")

        self.body_pane.add(self.left_container, weight=7)
        self.body_pane.add(right_panel, weight=3)
        self.root.after(120, self._init_body_sash)
        
        # 1. Progress Card
        prog_card = ttk.LabelFrame(right_scrollable, text=" 📊 진행 상황 ", padding=8)
        prog_card.pack(fill="x", pady=(0, 8))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(prog_card, variable=self.progress_var, maximum=100, mode='determinate', style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=5)
        
        info_f = tk.Frame(prog_card, bg=self.color_bg)
        info_f.pack(fill="x")
        self.lbl_prog_text = tk.Label(info_f, text="0 / 0 (0.0%)", font=("Consolas", 13, "bold"), fg=self.color_accent, bg=self.color_bg)
        self.lbl_prog_text.pack(side="left")
        self.lbl_eta = tk.Label(info_f, text="종료 예정: --:--", font=("Malgun Gothic", 10), fg=self.color_text_sec, bg=self.color_bg)
        self.lbl_eta.pack(side="right", pady=4)
        
        # 2. Mini HUD (핵심 정보만 표시)
        mon_card = ttk.LabelFrame(right_scrollable, text=" ⚡ Mini HUD ", padding=8)
        mon_card.pack(fill="x", pady=(0, 8))

        top_line = tk.Frame(mon_card, bg=self.color_bg)
        top_line.pack(fill="x")
        self.lbl_hud_state = tk.Label(top_line, text="상태: 준비 완료", font=("Malgun Gothic", 10, "bold"), fg=self.color_success, bg=self.color_bg)
        self.lbl_hud_state.pack(side="left")
        self.btn_toggle_hud = ttk.Button(top_line, text="펼치기", width=8, command=self._toggle_mini_hud)
        self.btn_toggle_hud.pack(side="right")
        self.lbl_hud_mode = tk.Label(
            top_line,
            text=f"입력: {self.cfg.get('input_mode', 'typing')}",
            font=("Consolas", 10, "bold"),
            fg=self.color_info,
            bg=self.color_bg,
        )
        self.lbl_hud_mode.pack(side="right", padx=(0, 8))

        self.mini_hud_body = tk.Frame(mon_card, bg=self.color_bg)
        self.lbl_hud_progress = tk.Label(
            self.mini_hud_body,
            text="진행: 0 / 0 | 배치: 0 / 0",
            font=("Consolas", 10, "bold"),
            fg=self.color_accent,
            bg=self.color_bg,
        )
        self.lbl_hud_progress.pack(anchor="w", pady=(6, 2))

        self.lbl_hud_persona = tk.Label(
            self.mini_hud_body,
            text="페르소나: INITIALIZING...",
            font=("Malgun Gothic", 10, "bold"),
            fg="#343A40",
            bg=self.color_bg,
        )
        self.lbl_hud_persona.pack(anchor="w")

        self.lbl_hud_meta = tk.Label(
            self.mini_hud_body,
            text="무드: - | 속도: x1.0 | 다음휴식: -",
            font=("Consolas", 10),
            fg=self.color_text_sec,
            bg=self.color_bg,
        )
        self.lbl_hud_meta.pack(anchor="w", pady=(2, 0))

        self.lbl_hud_trait = tk.Label(
            self.mini_hud_body,
            text="특징: -",
            font=("Malgun Gothic", 9),
            fg="#495057",
            bg=self.color_bg,
            wraplength=520,
            justify="left",
        )
        self.lbl_hud_trait.pack(anchor="w", pady=(4, 0))
        self._set_mini_hud_collapsed(True)

        ctrl_card = ttk.LabelFrame(right_scrollable, text=" ▶ 실행 컨트롤 ", padding=8)
        ctrl_card.pack(fill="x", pady=(0, 8))
        self.ctrl_card = ctrl_card
        self.btn_start_prompt = ttk.Button(
            ctrl_card,
            text="▶ 프롬프트 자동화 시작",
            style="Action.TButton",
            command=self.on_start_prompt,
        )
        self.btn_start_prompt.pack(fill="x", ipady=7)
        self.btn_start_asset = ttk.Button(
            ctrl_card,
            text="▶ S반복 자동화 시작",
            style="Action.TButton",
            command=self.on_start_asset,
        )
        self.btn_start_asset.pack(fill="x", ipady=6, pady=(6, 0))
        self.btn_start_download = ttk.Button(
            ctrl_card,
            text="▶ 다운로드 자동화 시작",
            style="Action.TButton",
            command=self.on_start_download,
        )
        self.btn_start_download.pack(fill="x", ipady=6, pady=(6, 0))
        self.btn_pause = ttk.Button(ctrl_card, text="⏸ 일시정지", command=self.on_pause, state="disabled")
        self.btn_pause.pack(fill="x", pady=(6, 0), ipady=4)
        self.btn_resume = ttk.Button(ctrl_card, text="▶ 재개", command=self.on_resume, state="disabled")
        self.btn_resume.pack(fill="x", pady=(6, 0), ipady=4)
        self.btn_stop = ttk.Button(ctrl_card, text="⏹ 완전중지(브라우저 종료)", command=self.on_stop, state="disabled")
        self.btn_stop.pack(fill="x", pady=(6, 0), ipady=4)

        # 3. Bottom
        bottom = tk.Frame(self.root, bg=self.color_bg)
        bottom.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        self.bottom_frame = bottom
        
        file_top = tk.Frame(bottom, bg=self.color_bg)
        file_top.pack(fill="x", pady=5)
        file_actions_f = tk.Frame(file_top, bg=self.color_bg)
        file_actions_f.pack(side="left", fill="x", expand=True)
        tk.Label(file_actions_f, text="📁 프롬프트 파일 선택:", font=self.font_section, fg=self.color_text).pack(side="left")
        
        self.slot_var = tk.StringVar()
        self.combo_slots = ttk.Combobox(file_actions_f, textvariable=self.slot_var, state="readonly", width=12, font=self.font_body)
        self.combo_slots.pack(side="left", padx=10)
        self.combo_slots.bind("<<ComboboxSelected>>", self.on_slot_change)
        
        # [NEW] Rename Button
        ttk.Button(file_actions_f, text="✏️", width=3, command=self.on_rename_slot).pack(side="left", padx=2)
        
        # [NEW] Add Slot Button
        btn_add = ttk.Button(file_actions_f, text="➕", width=3, command=self.on_add_slot)
        btn_add.pack(side="left", padx=2)
        ToolTip(btn_add, "새로운 프롬프트 슬롯 추가")

        # [NEW] Delete Slot Button
        btn_del = ttk.Button(file_actions_f, text="🗑️", width=3, command=self.on_delete_slot)
        btn_del.pack(side="left", padx=2)
        ToolTip(btn_del, "현재 프롬프트 슬롯 삭제")

        btn_sync = ttk.Button(file_actions_f, text="🔄 슬롯 동기화", command=self.on_sync_slots)
        btn_sync.pack(side="left", padx=(6, 2))
        ToolTip(btn_sync, "flow_prompts_slot 숫자 파일을 자동으로 슬롯에 추가")

        ttk.Button(file_actions_f, text="🔄 새로고침", command=self.on_reload).pack(side="left", padx=(8, 2))
        ttk.Button(file_actions_f, text="📂 파일 열기", command=self.on_open_prompts).pack(side="left", padx=(2, 0))

        zoom_f = tk.Frame(file_top, bg=self.color_bg)
        zoom_f.pack(side="right")
        btn_ui_zoom_minus = ttk.Button(zoom_f, text="A-", width=4, command=lambda: self._set_ui_zoom_percent(delta=-10))
        btn_ui_zoom_minus.pack(side="left", padx=(0, 4))
        self.scale_control_buttons.append(btn_ui_zoom_minus)
        self.lbl_zoom_state = tk.Label(zoom_f, text=f"{self._clamp_percent(self.cfg.get('ui_zoom_percent', 100), default=100)}%", font=self.font_small, bg=self.color_bg, fg=self.color_info)
        self.lbl_zoom_state.pack(side="left", padx=(0, 4))
        btn_ui_zoom_plus = ttk.Button(zoom_f, text="A+", width=4, command=lambda: self._set_ui_zoom_percent(delta=10))
        btn_ui_zoom_plus.pack(side="left")
        self.scale_control_buttons.append(btn_ui_zoom_plus)

        file_nav = tk.Frame(bottom, bg=self.color_bg)
        file_nav.pack(fill="x", pady=(2, 0))
        btn_nav = tk.Frame(file_nav, bg=self.color_bg)
        btn_nav.pack(side="left")

        ttk.Button(btn_nav, text="⏮", width=3, command=self.on_first).pack(side="left", padx=1)
        ttk.Button(btn_nav, text="◀", width=3, command=self.on_prev).pack(side="left", padx=1)

        tk.Label(btn_nav, text="번호 이동:", font=self.font_small, bg=self.color_bg).pack(side="left", padx=(5, 2))
        self.ent_jump = tk.Entry(
            btn_nav,
            width=5,
            font=self.font_mono,
            justify="center",
            relief="solid",
            borderwidth=1,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
            insertbackground=self.color_input_fg,
        )
        self.ent_jump.pack(side="left", padx=2)
        self.ent_jump.bind("<Return>", self.on_direct_jump)
        ToolTip(self.ent_jump, "이동할 번호 입력 후 엔터(Enter)")

        self.lbl_nav_status = tk.Label(
            btn_nav,
            text="0 / 0",
            width=10,
            fg=self.color_input_fg,
            font=(self.font_mono_family, 11, "bold"),
            cursor="hand2",
            bg=self.color_accent,
            relief="flat",
        )
        self.lbl_nav_status.pack(side="left", padx=5)
        self.lbl_nav_status.bind("<Button-1>", self.on_jump_to)
        ToolTip(self.lbl_nav_status, "클릭하여 번호로 이동")

        ttk.Button(btn_nav, text="▶", width=3, command=self.on_next).pack(side="left", padx=1)
        ttk.Button(btn_nav, text="⏭", width=3, command=self.on_last).pack(side="left", padx=1)

        prompt_manual_f = tk.Frame(file_nav, bg=self.color_bg)
        prompt_manual_f.pack(side="right")
        tk.Label(prompt_manual_f, text="개별 실행:", font=self.font_small, bg=self.color_bg).pack(side="left", padx=(8, 4))
        self.prompt_manual_selection_var = tk.StringVar(value=str(self.cfg.get("prompt_manual_selection", "") or ""))
        self.entry_prompt_manual_selection = tk.Entry(
            prompt_manual_f,
            width=26,
            textvariable=self.prompt_manual_selection_var,
            font=self.font_mono_small,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
            insertbackground=self.color_input_fg,
        )
        self.entry_prompt_manual_selection.pack(side="left", padx=(0, 6), ipady=2)
        self.entry_prompt_manual_selection.bind("<FocusOut>", self.on_option_toggle)
        self.entry_prompt_manual_selection.bind("<Return>", self.on_option_toggle)
        self.entry_prompt_manual_selection.bind("<KeyRelease>", self.on_option_toggle)
        ToolTip(self.entry_prompt_manual_selection, "예: 1,8,12-14,29")
        ttk.Button(prompt_manual_f, text="최근 실패 자동채움", command=self.on_fill_prompt_manual_from_failures).pack(side="left", padx=(0, 6))
        self.lbl_prompt_manual_status = tk.Label(prompt_manual_f, text="", font=self.font_small, bg=self.color_bg, fg=self.color_text_sec)
        self.lbl_prompt_manual_status.pack(side="left")
        self.lbl_prompt_inline_ref_hint = tk.Label(
            file_nav,
            text="레퍼런스 이미지는 프롬프트 안에 @999 또는 @S999 형태로 직접 넣으면 그 자리에서 첨부됩니다.",
            font=self.font_small,
            bg=self.color_bg,
            fg=self.color_info,
            anchor="w",
            justify="left",
        )
        self.lbl_prompt_inline_ref_hint.pack(fill="x", pady=(6, 0))
        prompt_ref_test_f = tk.Frame(file_nav, bg=self.color_bg)
        prompt_ref_test_f.pack(fill="x", pady=(4, 0))
        tk.Label(prompt_ref_test_f, text="레퍼런스 테스트 번호:", font=self.font_small, bg=self.color_bg).pack(side="left")
        self.prompt_reference_test_tag_var = tk.StringVar(value=str(self.cfg.get("prompt_reference_test_tag", "S999") or "S999"))
        self.entry_prompt_reference_test_tag = tk.Entry(
            prompt_ref_test_f,
            width=8,
            textvariable=self.prompt_reference_test_tag_var,
            font=self.font_mono_small,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
            insertbackground=self.color_input_fg,
        )
        self.entry_prompt_reference_test_tag.pack(side="left", padx=(6, 8), ipady=2)
        self.entry_prompt_reference_test_tag.bind("<FocusOut>", self.on_option_toggle)
        self.entry_prompt_reference_test_tag.bind("<Return>", self.on_option_toggle)
        ToolTip(self.entry_prompt_reference_test_tag, "예: S999 또는 999")
        ttk.Button(prompt_ref_test_f, text="🧪 레퍼런스 첨부 TEST", command=self.on_test_prompt_reference_attach).pack(side="left", padx=(0, 6))
        self.lbl_prompt_reference_probe_status = tk.Label(prompt_ref_test_f, text="", font=self.font_small, bg=self.color_bg, fg=self.color_text_sec)
        self.lbl_prompt_reference_probe_status.pack(side="left", padx=(8, 0))

        btn_f = tk.Frame(bottom, bg=self.color_bg)
        btn_f.pack(fill="x", pady=8)

        btn_log = tk.Button(
            btn_f,
            text="📜 로그 및 미리보기 창 열기",
            command=self.log_window.show,
            bg="#24324B",
            fg=self.color_text,
            font=self.font_body_bold,
            relief="raised",
            borderwidth=3,
        )
        self.btn_log = btn_log
        btn_log.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=6)

        btn_refresh_big = tk.Button(
            btn_f,
            text="🔄 프롬프트 새로고침 (Reload)",
            command=self.on_reload,
            bg="#1B78D0",
            fg="white",
            font=self.font_body_bold,
            relief="raised",
            borderwidth=3,
        )
        self.btn_refresh_big = btn_refresh_big
        btn_refresh_big.pack(side="left", fill="x", expand=True, padx=(5, 0), ipady=6)

        self._build_home_menu()
        self.root.after(80, self._refresh_responsive_layout)

    def _build_home_menu(self):
        if self.home_window and self.home_window.winfo_exists():
            try:
                self.home_window.destroy()
            except Exception:
                pass
        self.home_window = tk.Toplevel(self.root)
        self.home_window.title(f"{APP_NAME} - 메인창")
        self.home_window.configure(bg=self.color_bg)
        self.home_window.resizable(True, True)
        self.home_window.minsize(760, 560)
        try:
            icon_path = self.base.parent / "icon.ico"
            if icon_path.exists():
                self.home_window.iconbitmap(str(icon_path))
        except Exception:
            pass
        self.home_window.protocol("WM_DELETE_WINDOW", self.on_home_window_close)
        self._position_home_window()

        wrap = tk.Frame(self.home_window, bg=self.color_bg)
        wrap.pack(fill="both", expand=True, padx=24, pady=108)

        top = tk.Frame(wrap, bg=self.color_bg)
        top.pack(fill="x", pady=(0, 20))
        tk.Label(top, text="Flow Classic Plus", font=(self.font_ui_family, 28, "bold"), bg=self.color_bg, fg=self.color_text).pack(anchor="w")
        tk.Label(
            top,
            text="원본 클래식과 헷갈리지 않게, 여기서는 큰 메뉴에서 골라서 들어가면 됩니다.",
            font=(self.font_ui_family, 12),
            bg=self.color_bg,
            fg=self.color_text_sec,
        ).pack(anchor="w", pady=(6, 0))

        grid = tk.Frame(wrap, bg=self.color_bg)
        grid.pack(fill="both", expand=True)
        for col in range(2):
            grid.grid_columnconfigure(col, weight=1, uniform="home")
        for row in range(3):
            grid.grid_rowconfigure(row, weight=1, uniform="home")

        self._make_home_card(grid, 0, 0, "🛠 작업창 열기", "기존 자동화 기능 전체가 들어 있는 작업창을 엽니다.", lambda: self.open_home_target("all"))
        self._make_home_card(grid, 0, 1, "🏃 이어달리기", "새 이어달리기 전용 창으로 들어갑니다.", lambda: self.open_home_target("relay"))
        self._make_home_card(grid, 1, 0, "📝 프롬프트 자동화", "작업창을 열고 프롬프트 자동화 위치로 바로 이동합니다.", lambda: self.open_home_target("prompt"))
        self._make_home_card(grid, 1, 1, "🔁 S001 자동화", "작업창을 열고 S001 반복 자동화 위치로 바로 이동합니다.", lambda: self.open_home_target("asset"))
        self._make_home_card(grid, 2, 0, "⬇ 다운로드 자동화", "작업창을 열고 다운로드 자동화 위치로 바로 이동합니다.", lambda: self.open_home_target("download"))
        self._make_home_card(grid, 2, 1, "⚙ 전체 설정 보기", "작업창 전체 설정 화면을 바로 엽니다.", lambda: self.open_home_target("all"))
        self.root.withdraw()
        self.home_window.deiconify()
        self.home_window.lift()

    def _make_home_card(self, parent, row, col, title, desc, command):
        card = tk.Frame(parent, bg=self.color_card, highlightbackground="#2A3A56", highlightthickness=1, cursor="hand2")
        card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        inner = tk.Frame(card, bg=self.color_card)
        inner.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(inner, text=title, font=(self.font_ui_family, 19, "bold"), bg=self.color_card, fg=self.color_text).pack(anchor="w")
        tk.Label(inner, text=desc, font=(self.font_ui_family, 11), bg=self.color_card, fg=self.color_text_sec, wraplength=320, justify="left").pack(anchor="w", pady=(10, 18))
        ttk.Button(inner, text="들어가기", command=command).pack(anchor="w")

        for widget in (card, inner):
            widget.bind("<Button-1>", lambda _e, cb=command: cb())

    def _position_home_window(self):
        if not (self.home_window and self.home_window.winfo_exists()):
            return
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(1080, max(820, int(sw * 0.62)))
        h = min(760, max(600, int(sh * 0.72)))
        x = max((sw - w) // 2, 0)
        y = max((sh - h) // 2, 0)
        self.home_window.geometry(f"{w}x{h}+{x}+{y}")

    def on_home_window_close(self):
        if messagebox.askyesno("종료", "프로그램을 종료할까요?", parent=self.home_window):
            self.on_exit()

    def show_home_menu(self):
        self.hide_pipeline_window()
        if self.home_window and self.home_window.winfo_exists():
            try:
                self.root.withdraw()
            except Exception:
                pass
            self.home_window.deiconify()
            self.home_window.lift()
            self.home_window.focus_force()

    def hide_home_menu(self):
        if self.home_window and self.home_window.winfo_exists():
            try:
                self.home_window.withdraw()
            except Exception:
                pass

    def _build_pipeline_window(self):
        if self.pipeline_window and self.pipeline_window.winfo_exists():
            return
        self.pipeline_window = tk.Toplevel(self.root)
        self.pipeline_window.title(f"{APP_NAME} - 이어달리기창")
        self.pipeline_window.configure(bg=self.color_bg)
        self.pipeline_window.minsize(760, 620)
        try:
            icon_path = self.base.parent / "icon.ico"
            if icon_path.exists():
                self.pipeline_window.iconbitmap(str(icon_path))
        except Exception:
            pass
        self.pipeline_window.protocol("WM_DELETE_WINDOW", self.show_home_menu)
        self._position_pipeline_window()

        outer = tk.Frame(self.pipeline_window, bg=self.color_bg)
        outer.pack(fill="both", expand=True, padx=18, pady=18)

        header = tk.Frame(outer, bg=self.color_header, highlightbackground="#24324B", highlightthickness=1)
        header.pack(fill="x", pady=(0, 14))
        top_left = tk.Frame(header, bg=self.color_header)
        top_left.pack(side="left", fill="both", expand=True, padx=16, pady=12)
        tk.Label(top_left, text="이어달리기", font=self.font_title, bg=self.color_header, fg=self.color_text).pack(anchor="w")
        tk.Label(
            top_left,
            text="작업 1번, 2번, 3번을 단계별로 저장해서 이어서 돌리는 전용 창입니다.",
            font=self.font_small,
            bg=self.color_header,
            fg=self.color_text_sec,
        ).pack(anchor="w", pady=(4, 0))
        top_right = tk.Frame(header, bg=self.color_header)
        top_right.pack(side="right", padx=14, pady=12)
        ttk.Button(top_right, text="🤖 봇작업창 열기", command=self.on_open_pipeline_bot_work_window).pack(side="left", padx=(0, 6))
        ttk.Button(top_right, text="🛠 작업창 열기", command=lambda: self.open_home_target("all")).pack(side="left", padx=(0, 6))
        ttk.Button(top_right, text="🏠 메인창", command=self.show_home_menu).pack(side="left")

        body_wrap = tk.Frame(outer, bg=self.color_bg)
        body_wrap.pack(fill="both", expand=True)

        body_canvas = tk.Canvas(body_wrap, bg=self.color_bg, highlightthickness=0)
        body_scrollbar = ttk.Scrollbar(body_wrap, orient="vertical", command=body_canvas.yview)
        body_scrollable = tk.Frame(body_canvas, bg=self.color_bg)
        body_scrollable.bind("<Configure>", lambda e: body_canvas.configure(scrollregion=body_canvas.bbox("all")))
        body_window = body_canvas.create_window((0, 0), window=body_scrollable, anchor="nw")
        body_canvas.bind("<Configure>", lambda e: body_canvas.itemconfigure(body_window, width=max(e.width - 2, 420)))
        body_canvas.configure(yscrollcommand=body_scrollbar.set)
        body_canvas.pack(side="left", fill="both", expand=True)
        body_scrollbar.pack(side="right", fill="y")
        body_canvas._scroll_canvas_target = body_canvas
        body_scrollable._scroll_canvas_target = body_canvas

        left_card = tk.Frame(body_scrollable, bg=self.color_card, highlightbackground="#2A3A56", highlightthickness=1)
        left_card.pack(fill="x", padx=2, pady=(0, 14))
        tk.Label(left_card, text="작업 단계 목록", font=self.font_section, bg=self.color_card, fg=self.color_text).pack(anchor="w", padx=16, pady=(16, 8))
        tk.Label(
            left_card,
            text="작업 순서는 위에서 아래로 저장됩니다. 여기서 추가, 복제, 삭제, 순서 변경을 하면 됩니다.",
            font=self.font_small,
            bg=self.color_card,
            fg=self.color_text_sec,
            wraplength=760,
            justify="left",
        ).pack(anchor="w", padx=16)
        left_list_row = tk.Frame(left_card, bg=self.color_card)
        left_list_row.pack(fill="x", padx=16, pady=(12, 10))
        self.pipeline_step_listbox = tk.Listbox(
            left_list_row,
            height=6,
            bg="#0F1B2E",
            fg=self.color_text,
            selectbackground="#1B78D0",
            selectforeground="white",
            font=self.font_body,
            borderwidth=0,
            relief="flat",
            highlightthickness=0,
        )
        self.pipeline_step_listbox.pack(side="left", fill="x", expand=True)
        self.pipeline_step_listbox.bind("<<ListboxSelect>>", self.on_pipeline_step_select)
        pipeline_step_scroll = ttk.Scrollbar(left_list_row, orient="vertical", command=self.pipeline_step_listbox.yview)
        pipeline_step_scroll.pack(side="right", fill="y")
        self.pipeline_step_listbox.config(yscrollcommand=pipeline_step_scroll.set, exportselection=False)

        left_btns = tk.Frame(left_card, bg=self.color_card)
        left_btns.pack(fill="x", padx=16, pady=(0, 16))
        ttk.Button(left_btns, text="➕ 작업 추가", command=self.on_add_pipeline_step).pack(side="left")
        ttk.Button(left_btns, text="📄 복제", command=self.on_duplicate_pipeline_step).pack(side="left", padx=6)
        ttk.Button(left_btns, text="🗑 삭제", command=self.on_delete_pipeline_step).pack(side="left")
        ttk.Button(left_btns, text="▲", width=3, command=lambda: self.on_move_pipeline_step(-1)).pack(side="right")
        ttk.Button(left_btns, text="▼", width=3, command=lambda: self.on_move_pipeline_step(1)).pack(side="right", padx=(0, 6))

        right_card = tk.Frame(body_scrollable, bg=self.color_card, highlightbackground="#2A3A56", highlightthickness=1)
        right_card.pack(fill="x", padx=2, pady=(0, 14))
        tk.Label(right_card, text="이어달리기 설계 화면", font=self.font_section, bg=self.color_card, fg=self.color_text).pack(anchor="w", padx=18, pady=(16, 8))
        tk.Label(
            right_card,
            text="프롬프트 자동화, S반복 자동화, 다운로드 자동화를 원하는 순서대로 저장해두는 화면입니다.",
            font=self.font_body,
            bg=self.color_card,
            fg=self.color_text_sec,
            wraplength=760,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 16))

        profile_card = tk.Frame(right_card, bg="#13233A", highlightbackground="#28405F", highlightthickness=1)
        profile_card.pack(fill="x", padx=18, pady=(0, 14))
        head_row = tk.Frame(profile_card, bg="#13233A")
        head_row.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(head_row, text="프로젝트 목록", font=self.font_body_bold, bg="#13233A", fg=self.color_info).pack(side="left")
        ttk.Button(head_row, text="➕ 추가", command=self.on_add_project_profile).pack(side="right")
        ttk.Button(head_row, text="🗑 삭제", command=self.on_delete_project_profile).pack(side="right", padx=(0, 6))
        ttk.Button(head_row, text="✏ 이름변경", command=self.on_rename_project_profile).pack(side="right", padx=(0, 6))

        profile_body = tk.Frame(profile_card, bg="#13233A")
        profile_body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        profile_body.grid_columnconfigure(1, weight=1)

        self.project_profile_listbox = tk.Listbox(
            profile_body,
            height=6,
            bg="#0F1B2E",
            fg=self.color_text,
            selectbackground="#1B78D0",
            selectforeground="white",
            font=self.font_small,
            borderwidth=0,
            relief="flat",
            highlightthickness=0,
            exportselection=False,
        )
        self.project_profile_listbox.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 12))
        self.project_profile_listbox.bind("<<ListboxSelect>>", self.on_pipeline_profile_select)

        tk.Label(profile_body, text="프로젝트 이름", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=0, column=1, sticky="w")
        self.pipeline_profile_name_var = tk.StringVar()
        self.entry_pipeline_profile_name = tk.Entry(
            profile_body,
            textvariable=self.pipeline_profile_name_var,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
            insertbackground=self.color_input_fg,
            font=self.font_body,
        )
        self.entry_pipeline_profile_name.grid(row=1, column=1, sticky="ew", pady=(2, 8), ipady=3)
        self.entry_pipeline_profile_name.bind("<FocusOut>", self.on_save_project_profile_detail)
        self.entry_pipeline_profile_name.bind("<Return>", self.on_save_project_profile_detail)

        tk.Label(profile_body, text="URL", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=2, column=1, sticky="w")
        self.pipeline_profile_url_var = tk.StringVar()
        self.entry_pipeline_profile_url = tk.Entry(
            profile_body,
            textvariable=self.pipeline_profile_url_var,
            bg=self.color_input_bg,
            fg=self.color_input_fg,
            insertbackground=self.color_input_fg,
            font=self.font_mono_small,
        )
        self.entry_pipeline_profile_url.grid(row=3, column=1, sticky="ew", pady=(2, 8), ipady=3)
        self.entry_pipeline_profile_url.bind("<FocusOut>", self.on_save_project_profile_detail)
        self.entry_pipeline_profile_url.bind("<Return>", self.on_save_project_profile_detail)

        profile_btn_row = tk.Frame(profile_card, bg="#13233A")
        profile_btn_row.pack(fill="x", padx=14, pady=(0, 10))
        ttk.Button(profile_btn_row, text="💾 프로젝트 저장", command=self.on_save_project_profile_detail).pack(side="left")
        self.lbl_pipeline_profile_status = tk.Label(profile_btn_row, text="", font=self.font_small, bg="#13233A", fg=self.color_text_sec)
        self.lbl_pipeline_profile_status.pack(side="left", padx=(10, 0))
        self._sync_project_profile_ui()

        step_detail_card = tk.Frame(right_card, bg="#13233A", highlightbackground="#28405F", highlightthickness=1)
        step_detail_card.pack(fill="x", padx=18, pady=(0, 14))
        tk.Label(step_detail_card, text="작업 상세 설정", font=self.font_body_bold, bg="#13233A", fg=self.color_info).pack(anchor="w", padx=14, pady=(12, 8))

        step_form = tk.Frame(step_detail_card, bg="#13233A")
        step_form.pack(fill="x", padx=14, pady=(0, 10))
        step_form.grid_columnconfigure(1, weight=1)
        step_form.grid_columnconfigure(3, weight=1)

        self.pipeline_step_name_var = tk.StringVar()
        self.pipeline_step_type_var = tk.StringVar()
        self.pipeline_step_prompt_slot_var = tk.StringVar()
        self.pipeline_step_start_var = tk.StringVar()
        self.pipeline_step_end_var = tk.StringVar()
        self.pipeline_step_manual_var = tk.StringVar()
        self.pipeline_step_interval_var = tk.StringVar()
        self.pipeline_step_media_mode_var = tk.StringVar()
        self.pipeline_step_download_mode_var = tk.StringVar()
        self.pipeline_step_quality_var = tk.StringVar()
        self.pipeline_step_output_dir_var = tk.StringVar()

        tk.Label(step_form, text="작업 이름", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=0, column=0, sticky="w")
        ent_step_name = tk.Entry(step_form, textvariable=self.pipeline_step_name_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_body)
        ent_step_name.grid(row=0, column=1, sticky="ew", pady=(0, 8), padx=(6, 14), ipady=3)

        tk.Label(step_form, text="작업 종류", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=0, column=2, sticky="w")
        self.combo_pipeline_step_type = ttk.Combobox(step_form, textvariable=self.pipeline_step_type_var, state="readonly", values=tuple(self._pipeline_type_labels().values()), font=self.font_small)
        self.combo_pipeline_step_type.grid(row=0, column=3, sticky="ew", pady=(0, 8))

        tk.Label(step_form, text="프로젝트", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=1, column=0, sticky="w")
        self.combo_pipeline_project_profile = ttk.Combobox(step_form, state="readonly", font=self.font_small)
        self.combo_pipeline_project_profile.grid(row=1, column=1, sticky="ew", pady=(0, 8), padx=(6, 14))

        tk.Label(step_form, text="작업 간격(초)", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=1, column=2, sticky="w")
        ent_step_interval = tk.Entry(step_form, textvariable=self.pipeline_step_interval_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_body)
        ent_step_interval.grid(row=1, column=3, sticky="ew", pady=(0, 8), ipady=3)

        self.lbl_pipeline_prompt_slot = tk.Label(step_form, text="프롬프트 파일", font=self.font_small, bg="#13233A", fg=self.color_text)
        self.lbl_pipeline_prompt_slot.grid(row=2, column=0, sticky="w")
        self.combo_pipeline_prompt_slot = ttk.Combobox(step_form, textvariable=self.pipeline_step_prompt_slot_var, state="readonly", font=self.font_small)
        self.combo_pipeline_prompt_slot.grid(row=2, column=1, sticky="ew", pady=(0, 8), padx=(6, 14))

        self.lbl_pipeline_prompt_range = tk.Label(step_form, text="프롬프트 자동화를 선택하면 파일과 범위가 표시됩니다.", font=self.font_small, bg="#13233A", fg=self.color_text_sec, anchor="w")
        self.lbl_pipeline_prompt_range.grid(row=2, column=2, columnspan=2, sticky="ew", pady=(0, 8))

        tk.Label(step_form, text="시작 번호", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=3, column=0, sticky="w")
        ent_step_start = tk.Entry(step_form, textvariable=self.pipeline_step_start_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_body)
        ent_step_start.grid(row=3, column=1, sticky="ew", pady=(0, 8), padx=(6, 14), ipady=3)

        tk.Label(step_form, text="끝 번호", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=3, column=2, sticky="w")
        ent_step_end = tk.Entry(step_form, textvariable=self.pipeline_step_end_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_body)
        ent_step_end.grid(row=3, column=3, sticky="ew", pady=(0, 8), ipady=3)

        tk.Label(step_form, text="개별 번호", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=4, column=0, sticky="w")
        ent_step_manual = tk.Entry(step_form, textvariable=self.pipeline_step_manual_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_mono_small)
        ent_step_manual.grid(row=4, column=1, sticky="ew", pady=(0, 8), padx=(6, 14), ipady=3)

        tk.Label(step_form, text="기본값 모드", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=4, column=2, sticky="w")
        self.combo_pipeline_media_mode = ttk.Combobox(step_form, textvariable=self.pipeline_step_media_mode_var, state="readonly", values=tuple(self._pipeline_mode_labels().values()), font=self.font_small)
        self.combo_pipeline_media_mode.grid(row=4, column=3, sticky="ew", pady=(0, 8))

        tk.Label(step_form, text="다운로드 모드", font=self.font_small, bg="#13233A", fg=self.color_text).grid(row=5, column=0, sticky="w")
        self.combo_pipeline_download_mode = ttk.Combobox(step_form, textvariable=self.pipeline_step_download_mode_var, state="readonly", values=tuple(self._pipeline_mode_labels().values()), font=self.font_small)
        self.combo_pipeline_download_mode.grid(row=5, column=1, sticky="ew", pady=(0, 8), padx=(6, 14))

        self.lbl_pipeline_quality = tk.Label(step_form, text="품질", font=self.font_small, bg="#13233A", fg=self.color_text)
        self.lbl_pipeline_quality.grid(row=5, column=2, sticky="w")
        self.combo_pipeline_quality = ttk.Combobox(step_form, textvariable=self.pipeline_step_quality_var, state="readonly", font=self.font_small)
        self.combo_pipeline_quality.grid(row=5, column=3, sticky="ew", pady=(0, 8))

        self.lbl_pipeline_output_dir = tk.Label(step_form, text="저장 폴더", font=self.font_small, bg="#13233A", fg=self.color_text)
        self.lbl_pipeline_output_dir.grid(row=6, column=0, sticky="w")
        pipeline_output_wrap = tk.Frame(step_form, bg="#13233A")
        pipeline_output_wrap.grid(row=6, column=1, columnspan=3, sticky="ew", pady=(0, 8))
        pipeline_output_wrap.grid_columnconfigure(0, weight=1)
        self.entry_pipeline_output_dir = tk.Entry(pipeline_output_wrap, textvariable=self.pipeline_step_output_dir_var, bg=self.color_input_bg, fg=self.color_input_fg, insertbackground=self.color_input_fg, font=self.font_mono_small, state="readonly")
        self.entry_pipeline_output_dir.grid(row=0, column=0, sticky="ew", padx=(6, 6), ipady=3)
        self.btn_pipeline_output_dir = ttk.Button(pipeline_output_wrap, text="폴더선택", command=self.on_pick_pipeline_output_dir)
        self.btn_pipeline_output_dir.grid(row=0, column=1, sticky="e")

        for widget in (
            ent_step_name,
            ent_step_interval,
            ent_step_start,
            ent_step_end,
            ent_step_manual,
            self.combo_pipeline_step_type,
            self.combo_pipeline_project_profile,
            self.combo_pipeline_prompt_slot,
            self.combo_pipeline_media_mode,
            self.combo_pipeline_download_mode,
            self.combo_pipeline_quality,
        ):
            widget.bind("<FocusOut>", self._save_pipeline_step_fields)
            if isinstance(widget, ttk.Combobox):
                widget.bind("<<ComboboxSelected>>", self._save_pipeline_step_fields)
            else:
                widget.bind("<Return>", self._save_pipeline_step_fields)

        self.combo_pipeline_step_type.bind("<<ComboboxSelected>>", self.on_pipeline_step_type_change)
        self.combo_pipeline_download_mode.bind("<<ComboboxSelected>>", self.on_pipeline_step_download_mode_change)
        self.combo_pipeline_prompt_slot.bind("<<ComboboxSelected>>", self.on_pipeline_step_prompt_slot_change)

        step_btn_row = tk.Frame(step_detail_card, bg="#13233A")
        step_btn_row.pack(fill="x", padx=14, pady=(0, 12))
        ttk.Button(step_btn_row, text="💾 작업 저장", command=self._save_pipeline_step_fields).pack(side="left")
        self.lbl_pipeline_step_status = tk.Label(step_btn_row, text="", font=self.font_small, bg="#13233A", fg=self.color_text_sec)
        self.lbl_pipeline_step_status.pack(side="left", padx=(10, 0))
        self._sync_pipeline_step_ui()

        info_box = tk.Frame(right_card, bg="#13233A", highlightbackground="#28405F", highlightthickness=1)
        info_box.pack(fill="x", padx=18, pady=(0, 14))
        tk.Label(info_box, text="다음에 붙일 핵심 기능", font=self.font_body_bold, bg="#13233A", fg=self.color_info).pack(anchor="w", padx=14, pady=(12, 6))
        for text in (
            "프로젝트 목록 저장: URL + 프로젝트 이름 저장 / 추가 / 삭제 / 이름 변경",
            "작업 단계 저장: 프롬프트, S반복, 다운로드를 1번/2번/3번으로 묶기",
            "단계별 모드 전환: 이미지 기본값 / 동영상 기본값 자동 적용",
            "이어달리기 실행: 시작 / 일시정지 / 수정 후 이어서 시작",
        ):
            tk.Label(info_box, text=f"• {text}", font=self.font_small, bg="#13233A", fg=self.color_text).pack(anchor="w", padx=14, pady=2)

        preview_box = tk.Frame(right_card, bg=self.color_bg, highlightbackground="#24324B", highlightthickness=1)
        preview_box.pack(fill="x", padx=18, pady=(0, 14))
        tk.Label(preview_box, text="예상 실행 흐름", font=self.font_body_bold, bg=self.color_bg, fg=self.color_accent).pack(anchor="w", padx=14, pady=(12, 8))
        preview_text = (
            "1. 1번 작업: 프롬프트 자동화 (이미지)\n"
            "2. 2번 작업: S반복 자동화 (동영상)\n"
            "3. 3번 작업: 다운로드 자동화 (동영상)\n\n"
            "이 흐름을 저장해두고, 이어달리기 시작 버튼으로 한 번에 돌리는 구조로 갈 예정입니다."
        )
        tk.Label(preview_box, text=preview_text, font=self.font_small, bg=self.color_bg, fg=self.color_text_sec, justify="left").pack(anchor="w", padx=14, pady=(0, 14))

        bottom = tk.Frame(right_card, bg=self.color_card)
        bottom.pack(fill="x", padx=18, pady=(0, 16))
        ttk.Button(bottom, text="💾 이어달리기 저장", command=lambda: (self.on_save_project_profile_detail(), self._save_pipeline_step_fields())).pack(side="left")
        ttk.Button(bottom, text="🛠 작업창 적용", command=self.on_apply_pipeline_step_to_work).pack(side="left", padx=6)
        self.btn_pipeline_start = ttk.Button(bottom, text="▶ 이어달리기 시작", command=self.on_start_pipeline_run)
        self.btn_pipeline_start.pack(side="left")
        self.lbl_pipeline_runtime_status = tk.Label(bottom, text="이어달리기 대기 중", font=self.font_small, bg=self.color_card, fg=self.color_text_sec)
        self.lbl_pipeline_runtime_status.pack(side="left", padx=(10, 0))
        self._refresh_display_mode_ui()
        self._set_startup_preflight_ui(
            self.last_startup_preflight_ok if self.last_startup_preflight_at else None,
            self.last_startup_preflight_summary if self.last_startup_preflight_at else "",
            self.last_startup_preflight_at,
        )

    def _position_pipeline_window(self):
        if not (self.pipeline_window and self.pipeline_window.winfo_exists()):
            return
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(1120, max(820, int(sw * 0.62)))
        h = min(860, max(640, int(sh * 0.78)))
        x = max((sw - w) // 2, 0)
        y = max((sh - h) // 2, 0)
        self.pipeline_window.geometry(f"{w}x{h}+{x}+{y}")

    def show_pipeline_window(self):
        self._build_pipeline_window()
        if self.pipeline_window and self.pipeline_window.winfo_exists():
            try:
                self.root.withdraw()
            except Exception:
                pass
            self.pipeline_window.deiconify()
            self.pipeline_window.lift()
            self.pipeline_window.focus_force()

    def hide_pipeline_window(self):
        if self.pipeline_window and self.pipeline_window.winfo_exists():
            try:
                self.pipeline_window.withdraw()
            except Exception:
                pass

    def open_home_target(self, target):
        self.hide_home_menu()
        if target == "relay":
            self.show_pipeline_window()
            return
        self.hide_pipeline_window()
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass
        self.root.after(80, self._init_body_sash)
        self._focus_work_target(target)

    def on_fill_schedule_time(self, plus_minutes):
        try:
            dt = datetime.now() + timedelta(minutes=int(plus_minutes))
            txt = dt.strftime("%Y-%m-%d %H:%M")
            self.schedule_text_var.set(txt)
            self.schedule_var.set(True)
            self.on_option_toggle()
            self.log(f"⏰ 예약 시간 입력: {txt}")
        except Exception as e:
            messagebox.showerror("오류", f"예약 시간 입력 실패: {e}")

    def on_clear_schedule_time(self):
        self.schedule_text_var.set("")
        self.schedule_var.set(False)
        self.on_option_toggle()
        self.log("🧹 예약 시간이 초기화되었습니다.")

    def on_open_schedule_picker(self):
        base_dt = self._parse_schedule_datetime(self.schedule_text_var.get())
        if base_dt is None:
            base_dt = datetime.now() + timedelta(minutes=5)

        state = {"year": base_dt.year, "month": base_dt.month, "day": base_dt.day}
        hour_var = tk.IntVar(value=base_dt.hour)
        min_var = tk.IntVar(value=base_dt.minute)

        win = tk.Toplevel(self.root)
        win.title("📅 예약 날짜/시간 선택")
        win.configure(bg="#FFFFFF")
        win.transient(self.root)
        win.grab_set()
        win.geometry("360x430")
        win.resizable(False, False)

        top = tk.Frame(win, bg="#FFFFFF")
        top.pack(fill="x", padx=12, pady=(12, 6))

        month_title = tk.Label(top, text="", font=("Malgun Gothic", 12, "bold"), bg="#FFFFFF", fg="#212529")
        month_title.pack(side="left", expand=True)

        cal_frame = tk.Frame(win, bg="#FFFFFF")
        cal_frame.pack(fill="x", padx=12, pady=6)

        week_names = ["월", "화", "수", "목", "금", "토", "일"]

        def _move_month(delta):
            y, m = state["year"], state["month"] + delta
            if m <= 0:
                y -= 1
                m = 12
            elif m >= 13:
                y += 1
                m = 1
            state["year"], state["month"] = y, m
            max_day = calendar.monthrange(y, m)[1]
            state["day"] = min(state["day"], max_day)
            _render_calendar()

        ttk.Button(top, text="◀", width=3, command=lambda: _move_month(-1)).pack(side="left")
        ttk.Button(top, text="▶", width=3, command=lambda: _move_month(1)).pack(side="right")

        def _select_day(day):
            state["day"] = day
            _render_calendar()

        def _render_calendar():
            for w in cal_frame.winfo_children():
                w.destroy()
            month_title.config(text=f"{state['year']}년 {state['month']}월")

            for col, wd in enumerate(week_names):
                fg = "#DC3545" if col == 6 else "#212529"
                tk.Label(
                    cal_frame,
                    text=wd,
                    width=4,
                    bg="#FFFFFF",
                    fg=fg,
                    font=("Malgun Gothic", 10, "bold")
                ).grid(row=0, column=col, padx=1, pady=2)

            month_weeks = calendar.monthcalendar(state["year"], state["month"])
            for row, week in enumerate(month_weeks, start=1):
                for col, day in enumerate(week):
                    if day == 0:
                        tk.Label(cal_frame, text=" ", width=4, bg="#FFFFFF").grid(row=row, column=col, padx=1, pady=1)
                        continue
                    selected = (day == state["day"])
                    bg = "#007AFF" if selected else "#F1F3F5"
                    fg = "white" if selected else ("#DC3545" if col == 6 else "#212529")
                    tk.Button(
                        cal_frame,
                        text=str(day),
                        width=4,
                        bg=bg,
                        fg=fg,
                        relief="flat",
                        activebackground="#0056b3" if selected else "#DEE2E6",
                        command=lambda d=day: _select_day(d)
                    ).grid(row=row, column=col, padx=1, pady=1)

        _render_calendar()

        time_frame = tk.Frame(win, bg="#FFFFFF")
        time_frame.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(time_frame, text="시간", bg="#FFFFFF", font=("Malgun Gothic", 10)).pack(side="left")
        tk.Spinbox(time_frame, from_=0, to=23, wrap=True, width=4, textvariable=hour_var, format="%02.0f").pack(side="left", padx=(6, 10))
        tk.Label(time_frame, text="분", bg="#FFFFFF", font=("Malgun Gothic", 10)).pack(side="left")
        tk.Spinbox(time_frame, from_=0, to=59, wrap=True, width=4, textvariable=min_var, format="%02.0f").pack(side="left", padx=(6, 0))

        btns = tk.Frame(win, bg="#FFFFFF")
        btns.pack(fill="x", padx=12, pady=(14, 12))

        def _pick_now():
            now = datetime.now()
            state["year"], state["month"], state["day"] = now.year, now.month, now.day
            hour_var.set(now.hour)
            min_var.set(now.minute)
            _render_calendar()

        def _confirm():
            try:
                picked = datetime(
                    year=state["year"],
                    month=state["month"],
                    day=state["day"],
                    hour=max(0, min(23, int(hour_var.get()))),
                    minute=max(0, min(59, int(min_var.get())))
                )
            except Exception:
                messagebox.showwarning("입력 오류", "날짜/시간을 다시 선택해주세요.")
                return

            txt = picked.strftime("%Y-%m-%d %H:%M")
            self.schedule_text_var.set(txt)
            self.schedule_var.set(True)
            self.on_option_toggle()
            self.log(f"📅 달력에서 예약 선택: {txt}")
            win.destroy()

        ttk.Button(btns, text="오늘", command=_pick_now).pack(side="left")
        ttk.Button(btns, text="취소", command=win.destroy).pack(side="right")
        ttk.Button(btns, text="선택 완료", command=_confirm).pack(side="right", padx=6)

    def on_sync_slots(self):
        existing_files = {s.get("file") for s in self.cfg.get("prompt_slots", [])}
        discovered = []
        for path in self.base.iterdir():
            if not path.is_file():
                continue
            name = path.name
            m = SLOT_FILE_REGEX.match(name)
            if not m:
                continue
            discovered.append((int(m.group(1)), name))

        if not discovered:
            messagebox.showinfo("동기화", "동기화할 슬롯 파일이 없습니다.")
            self.log("ℹ️ 슬롯 동기화: 신규 파일 없음")
            return

        discovered.sort(key=lambda x: (x[0], x[1]))
        added = []
        for slot_num, file_name in discovered:
            if file_name in existing_files:
                continue
            slot_name = self._make_unique_slot_name(f"자동 슬롯 {slot_num}")
            self.cfg["prompt_slots"].append({"name": slot_name, "file": file_name})
            existing_files.add(file_name)
            added.append((slot_name, file_name))

        if not added:
            messagebox.showinfo("동기화", "이미 모든 슬롯이 등록되어 있습니다.")
            self.log("✅ 슬롯 동기화: 이미 최신 상태")
            return

        self.save_config()
        slots = [s["name"] for s in self.cfg["prompt_slots"]]
        self.combo_slots["values"] = slots
        self.combo_slots.current(self._clamp_slot_index(self.cfg.get("active_prompt_slot", 0)))
        self._sync_relay_range_controls()
        self._sync_relay_selection_label()
        added_preview = ", ".join([f"{n}({f})" for n, f in added[:3]])
        if len(added) > 3:
            added_preview += f" 외 {len(added) - 3}개"
        self.log(f"🔄 슬롯 동기화 완료: {len(added)}개 추가")
        messagebox.showinfo("동기화 완료", f"{len(added)}개 슬롯을 추가했습니다.\n{added_preview}")

    def on_pick_download_output_dir(self):
        initial = str(self.cfg.get("download_output_dir", "") or "").strip()
        if not initial:
            initial = str(self._resolve_download_output_dir())
        picked = filedialog.askdirectory(initialdir=initial, title="다운로드 저장 폴더 선택")
        if not picked:
            return
        if hasattr(self, "download_output_dir_var"):
            self.download_output_dir_var.set(picked)
        self.on_option_toggle()
        self.log(f"📁 다운로드 저장 폴더 설정: {picked}")

    def on_fill_asset_manual_from_failures(self):
        numbers, source_name = self._load_recent_failed_asset_numbers()
        if not numbers:
            messagebox.showinfo("안내", "최근 실패한 S번호를 찾지 못했습니다.")
            return
        spec = self._compress_numbers_to_spec(numbers, pad_width=self._asset_pad_width())
        self.asset_manual_selection_var.set(spec)
        self.on_option_toggle()
        source_text = source_name or "최근 로그"
        self.log(f"🧩 S 개별 번호 자동채움: {spec} ({source_text})")
        messagebox.showinfo("자동채움", f"최근 실패한 S번호를 불러왔습니다.\n출처: {source_text}\n번호: {spec}")

    def on_fill_prompt_manual_from_failures(self):
        numbers, source_name = self._load_recent_failed_prompt_numbers()
        if not numbers:
            messagebox.showinfo("안내", "최근 실패한 프롬프트 번호를 찾지 못했습니다.")
            return
        spec = self._compress_numbers_to_spec(numbers, pad_width=0)
        self.prompt_manual_selection_var.set(spec)
        self.on_option_toggle()
        source_text = source_name or "최근 로그"
        self.log(f"🧩 프롬프트 개별 실행 자동채움: {spec} ({source_text})")
        messagebox.showinfo("자동채움", f"최근 실패한 프롬프트 번호를 불러왔습니다.\n출처: {source_text}\n번호: {spec}")

    def _normalized_prompt_reference_test_tag(self):
        raw = ""
        if hasattr(self, "prompt_reference_test_tag_var"):
            raw = str(self.prompt_reference_test_tag_var.get() or "").strip()
        if not raw:
            raw = str(self.cfg.get("prompt_reference_test_tag", "S999") or "S999").strip()
        return self._normalize_reference_asset_tag(raw) or "S999"

    def on_auto_detect_prompt_reference_attach(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 레퍼런스 첨부 탐색을 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._prompt_reference_attach_probe_worker(test_only=False)

    def on_test_prompt_reference_attach(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 레퍼런스 첨부 테스트를 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._prompt_reference_attach_probe_worker(test_only=True)

    def _prompt_reference_attach_probe_worker(self, test_only=False):
        opened_here = False
        tag = self._normalized_prompt_reference_test_tag()
        mode_label = "TEST" if test_only else "자동탐색"
        try:
            if not self.action_log_fp:
                self._open_action_log("prompt_reference_attach_test" if test_only else "prompt_reference_attach_detect")
                opened_here = True
            self.update_status_label(f"🧪 레퍼런스 첨부 {mode_label} 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url and start_url not in (self.page.url or ""):
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(0.8, 1.6))
            self._prepare_page_for_selector_detection()

            input_selector = (self.cfg.get("input_selector") or "").strip()
            input_locator, resolved_input_selector = self._resolve_prompt_input_locator(input_selector, timeout_ms=2600)
            if input_locator is None:
                raise RuntimeError("프롬프트 입력칸을 찾지 못했습니다.")
            self.log(f"🧭 레퍼런스 테스트 입력창: {resolved_input_selector or '자동 탐색'}")
            try:
                input_locator.click(timeout=1200)
            except Exception:
                pass

            input_locator = self._attach_prompt_reference_asset(input_locator, tag)
            search_sel = self.cfg.get("prompt_reference_search_input_selector", "") or ""
            if not test_only:
                self.cfg["prompt_reference_search_input_selector"] = search_sel or self.cfg.get("prompt_reference_search_input_selector", "")
                self.save_config()

            summary = (
                f"🧪 레퍼런스 첨부 {mode_label} | "
                f"@호출(page type('@'))=OK | "
                f"검색입력({search_sel or '직접입력'})=OK | "
                "Enter선택=OK"
            )
            self.log(summary)
            self.update_status_label(f"✅ 레퍼런스 첨부 {mode_label} 통과", self.color_success)
            if hasattr(self, "lbl_prompt_reference_probe_status"):
                self.lbl_prompt_reference_probe_status.config(text=f"{tag} OK", fg=self.color_success)

            try:
                self.actor.clear_input_field(input_locator, label="입력창")
            except Exception:
                pass
        except Exception as e:
            self.log(f"❌ 레퍼런스 첨부 {mode_label} 실패: {e}")
            self.update_status_label(f"❌ 레퍼런스 첨부 {mode_label} 실패", self.color_error)
            if hasattr(self, "lbl_prompt_reference_probe_status"):
                self.lbl_prompt_reference_probe_status.config(text="실패", fg=self.color_error)
        finally:
            if opened_here:
                self._close_action_log()

    def on_add_prompt_reference_item(self):
        items = list(self.cfg.get("prompt_reference_items", []) or [])
        items.append({"name": "", "asset_tag": "", "scene_spec": ""})
        self.cfg["prompt_reference_items"] = [self._normalize_prompt_reference_item(x) for x in items]
        self.save_config()
        self._refresh_prompt_reference_ui()
        self.log("➕ 프롬프트 레퍼런스 항목 추가")

    def on_delete_prompt_reference_item(self, idx):
        items = list(self.cfg.get("prompt_reference_items", []) or [])
        if not (0 <= idx < len(items)):
            return
        removed = self._normalize_prompt_reference_item(items[idx])
        items.pop(idx)
        self.cfg["prompt_reference_items"] = [self._normalize_prompt_reference_item(x) for x in items]
        self.save_config()
        self._refresh_prompt_reference_ui()
        label = removed.get("name") or removed.get("asset_tag") or f"{idx + 1}번"
        self.log(f"🗑️ 프롬프트 레퍼런스 삭제: {label}")

    def on_option_toggle(self, event=None):
        self.cfg["scale_lock_enabled"] = False
        self.cfg["afk_mode"] = self.afk_var.get()
        self.cfg["sound_enabled"] = self.sound_var.get()
        self.cfg["relay_mode"] = False
        self.cfg["scheduled_start_enabled"] = False
        self.cfg["scheduled_start_at"] = ""
        if hasattr(self, "display_mode_var"):
            self.cfg["work_env_mode"] = self._display_mode_values().get(
                str(self.display_mode_var.get() or "").strip(),
                self._active_display_mode(),
            )
        self.cfg["language_mode"] = "ko_en" if self.lang_var.get() else "en"
        self.cfg["prompt_mode_preset_enabled"] = True
        media_label = self.prompt_media_mode_var.get().strip() if hasattr(self, "prompt_media_mode_var") else ""
        self.cfg["prompt_media_mode"] = PROMPT_MEDIA_VALUES.get(media_label, self.cfg.get("prompt_media_mode", "image"))
        if hasattr(self, "prompt_mode_preset_enabled_var"):
            self.prompt_mode_preset_enabled_var.set(True)
        self.cfg["asset_prompt_mode_preset_enabled"] = True
        asset_media_label = self.asset_prompt_media_mode_var.get().strip() if hasattr(self, "asset_prompt_media_mode_var") else ""
        self.cfg["asset_prompt_media_mode"] = PROMPT_MEDIA_VALUES.get(asset_media_label, self.cfg.get("asset_prompt_media_mode", "video"))
        if hasattr(self, "asset_prompt_mode_preset_enabled_var"):
            self.asset_prompt_mode_preset_enabled_var.set(True)
        self.cfg["asset_loop_enabled"] = self.asset_loop_var.get() if hasattr(self, "asset_loop_var") else self.cfg.get("asset_loop_enabled", False)
        raw_start = ""
        raw_end = ""
        try:
            if hasattr(self, "spin_asset_start"):
                raw_start = str(self.spin_asset_start.get()).strip()
            elif hasattr(self, "asset_loop_start_var"):
                raw_start = str(self.asset_loop_start_var.get()).strip()
        except Exception:
            raw_start = ""
        try:
            if hasattr(self, "spin_asset_end"):
                raw_end = str(self.spin_asset_end.get()).strip()
            elif hasattr(self, "asset_loop_end_var"):
                raw_end = str(self.asset_loop_end_var.get()).strip()
        except Exception:
            raw_end = ""

        try:
            asset_start = int(raw_start) if raw_start else int(self.cfg.get("asset_loop_start", 1))
        except Exception:
            asset_start = 1
        try:
            asset_end = int(raw_end) if raw_end else int(self.cfg.get("asset_loop_end", 1))
        except Exception:
            asset_end = asset_start
        self.cfg["asset_loop_start"] = max(1, asset_start)
        self.cfg["asset_loop_end"] = max(1, asset_end)

        # S 자동화는 항상 S001 형식 이상으로 고정한다.
        requested_width = 0
        for raw in (raw_start, raw_end):
            if raw and raw.isdigit() and len(raw) > 1 and raw.startswith("0"):
                requested_width = max(requested_width, len(raw))
        try:
            prev_width = int(self.cfg.get("asset_loop_num_width", 0))
        except Exception:
            prev_width = 3
        if requested_width > 0:
            self.cfg["asset_loop_num_width"] = max(3, requested_width)
        else:
            self.cfg["asset_loop_num_width"] = max(3, prev_width)

        asset_prefix = self.asset_loop_prefix_var.get().strip() if hasattr(self, "asset_loop_prefix_var") else str(self.cfg.get("asset_loop_prefix", "S"))
        self.cfg["asset_loop_prefix"] = asset_prefix or "S"
        self.cfg["asset_use_prompt_slot"] = self.asset_use_prompt_slot_var.get() if hasattr(self, "asset_use_prompt_slot_var") else bool(self.cfg.get("asset_use_prompt_slot", False))
        if hasattr(self, "combo_asset_prompt_slot") and self.combo_asset_prompt_slot.current() >= 0:
            self.cfg["asset_prompt_slot"] = self._clamp_slot_index(self.combo_asset_prompt_slot.current())
        else:
            self.cfg["asset_prompt_slot"] = self._clamp_slot_index(self.cfg.get("asset_prompt_slot", 0))
        asset_template = self.asset_loop_template_var.get().strip() if hasattr(self, "asset_loop_template_var") else str(self.cfg.get("asset_loop_prompt_template", ""))
        self.cfg["asset_loop_prompt_template"] = asset_template or "{tag} : Naturally Seamless Loop animation."
        self.cfg["asset_manual_selection"] = self.asset_manual_selection_var.get().strip() if hasattr(self, "asset_manual_selection_var") else str(self.cfg.get("asset_manual_selection", "") or "").strip()
        self.cfg["asset_start_selector"] = self.asset_start_selector_var.get().strip() if hasattr(self, "asset_start_selector_var") else self.cfg.get("asset_start_selector", "")
        self.cfg["asset_search_button_selector"] = self.asset_search_btn_selector_var.get().strip() if hasattr(self, "asset_search_btn_selector_var") else self.cfg.get("asset_search_button_selector", "")
        self.cfg["asset_search_input_selector"] = self.asset_search_input_selector_var.get().strip() if hasattr(self, "asset_search_input_selector_var") else self.cfg.get("asset_search_input_selector", "")
        self.cfg["prompt_manual_selection"] = self.prompt_manual_selection_var.get().strip() if hasattr(self, "prompt_manual_selection_var") else str(self.cfg.get("prompt_manual_selection", "") or "").strip()
        self.cfg["prompt_reference_test_tag"] = self._normalized_prompt_reference_test_tag()
        self.cfg["prompt_reference_enabled"] = self.prompt_reference_enabled_var.get() if hasattr(self, "prompt_reference_enabled_var") else bool(self.cfg.get("prompt_reference_enabled", False))
        if hasattr(self, "prompt_reference_row_vars"):
            prompt_ref_items = []
            for row in self.prompt_reference_row_vars:
                prompt_ref_items.append(self._normalize_prompt_reference_item({
                    "name": row["name"].get().strip() if row.get("name") else "",
                    "asset_tag": row["asset_tag"].get().strip() if row.get("asset_tag") else "",
                    "scene_spec": row["scene_spec"].get().strip() if row.get("scene_spec") else "",
                }))
            self.cfg["prompt_reference_items"] = prompt_ref_items
        self.cfg["download_mode"] = self.download_mode_var.get().strip().lower() if hasattr(self, "download_mode_var") else self.cfg.get("download_mode", "video")
        if self.cfg["download_mode"] not in ("video", "image"):
            self.cfg["download_mode"] = "video"
        self.cfg["download_video_quality"] = self.download_video_quality_var.get().strip().upper() if hasattr(self, "download_video_quality_var") else str(self.cfg.get("download_video_quality", "1080P"))
        if self.cfg["download_video_quality"] not in ("720P", "1080P", "4K"):
            self.cfg["download_video_quality"] = "1080P"
        self.cfg["download_image_quality"] = self.download_image_quality_var.get().strip().upper() if hasattr(self, "download_image_quality_var") else str(self.cfg.get("download_image_quality", "4K"))
        if self.cfg["download_image_quality"] not in ("1K", "2K", "4K"):
            self.cfg["download_image_quality"] = "4K"
        try:
            raw_download_wait = self.download_wait_seconds_var.get().strip() if hasattr(self, "download_wait_seconds_var") else str(self.cfg.get("download_wait_seconds", 20))
            self.cfg["download_wait_seconds"] = max(3, min(120, int(raw_download_wait or 20)))
        except Exception:
            self.cfg["download_wait_seconds"] = int(self.cfg.get("download_wait_seconds", 20) or 20)
        self.cfg["download_output_dir"] = self.download_output_dir_var.get().strip() if hasattr(self, "download_output_dir_var") else self.cfg.get("download_output_dir", "")
        self.cfg["download_search_input_selector"] = self.download_search_input_selector_var.get().strip() if hasattr(self, "download_search_input_selector_var") else self.cfg.get("download_search_input_selector", "")
        self.cfg["download_video_filter_selector"] = self.download_video_filter_selector_var.get().strip() if hasattr(self, "download_video_filter_selector_var") else self.cfg.get("download_video_filter_selector", "")
        self.cfg["download_image_filter_selector"] = self.download_image_filter_selector_var.get().strip() if hasattr(self, "download_image_filter_selector_var") else self.cfg.get("download_image_filter_selector", "")
        try:
            raw_break_every = self.work_break_every_var.get().strip() if hasattr(self, "work_break_every_var") else str(self.cfg.get("work_break_every_count", 40))
            self.cfg["work_break_every_count"] = max(1, min(9999, int(raw_break_every or 40)))
        except Exception:
            self.cfg["work_break_every_count"] = int(self.cfg.get("work_break_every_count", 40) or 40)
        try:
            raw_break_minutes = self.work_break_minutes_var.get().strip() if hasattr(self, "work_break_minutes_var") else str(self.cfg.get("work_break_minutes", 12))
            self.cfg["work_break_minutes"] = max(1, min(180, int(raw_break_minutes or 12)))
        except Exception:
            self.cfg["work_break_minutes"] = int(self.cfg.get("work_break_minutes", 12) or 12)
        self.cfg["work_break_random_ratio"] = 0.30
        # 실행 중에는 시작 시 확정한 입력방식을 유지(중간 변경으로 typing/paste 뒤바뀜 방지)
        self.cfg["input_mode"] = "typing"
        try:
            if hasattr(self, "input_mode_var") and self.input_mode_var.get() != "typing":
                self.input_mode_var.set("typing")
        except Exception:
            pass
        if hasattr(self, "typing_speed_scale_var"):
            try:
                level = int(self.typing_speed_scale_var.get())
            except Exception:
                level = 5
            level = max(1, min(20, level))
            self.cfg["typing_speed_profile"] = f"x{level}"
            if hasattr(self, "typing_speed_profile_var"):
                self.typing_speed_profile_var.set(f"x{level}")
            if hasattr(self, "lbl_typing_speed_value"):
                self.lbl_typing_speed_value.config(text=f"x{level}")
        elif hasattr(self, "typing_speed_profile_var"):
            self.cfg["typing_speed_profile"] = self.typing_speed_profile_var.get().strip()
        else:
            self.cfg["typing_speed_profile"] = str(self.cfg.get("typing_speed_profile", "x5")).strip() or "x5"
        self.cfg["start_url"] = self.start_url_var.get().strip() if hasattr(self, "start_url_var") else self.cfg.get("start_url", "")
        self.cfg["input_selector"] = self.input_selector_var.get().strip() if hasattr(self, "input_selector_var") else self.cfg.get("input_selector", "")
        self.cfg["submit_selector"] = self.submit_selector_var.get().strip() if hasattr(self, "submit_selector_var") else self.cfg.get("submit_selector", "")
        self.cfg["auto_open_new_project"] = self.auto_new_project_var.get() if hasattr(self, "auto_new_project_var") else self.cfg.get("auto_open_new_project", True)
        self.cfg["new_project_selector"] = self.new_project_selector_var.get().strip() if hasattr(self, "new_project_selector_var") else self.cfg.get("new_project_selector", "")
        self.cfg["browser_headless"] = self.browser_headless_var.get() if hasattr(self, "browser_headless_var") else self.cfg.get("browser_headless", False)
        self.cfg["browser_channel"] = self.browser_channel_var.get().strip() if hasattr(self, "browser_channel_var") else self.cfg.get("browser_channel", "chrome")
        self.cfg["browser_window_scale_percent"] = self._clamp_percent(self.browser_window_scale_var.get() if hasattr(self, "browser_window_scale_var") else self.cfg.get("browser_window_scale_percent", 100), default=100, minimum=50, maximum=150)
        self.cfg["browser_zoom_percent"] = self._clamp_percent(self.browser_zoom_var.get() if hasattr(self, "browser_zoom_var") else self.cfg.get("browser_zoom_percent", 100), default=100, minimum=50, maximum=150)
        if hasattr(self, "lbl_browser_window_scale_state"):
            self.lbl_browser_window_scale_state.config(text=f"{self.cfg['browser_window_scale_percent']}%")
        if hasattr(self, "lbl_browser_zoom_state"):
            self.lbl_browser_zoom_state.config(text=f"{self.cfg['browser_zoom_percent']}%")
        self.cfg["ui_zoom_percent"] = self._clamp_percent(self.cfg.get("ui_zoom_percent", 100), default=100, minimum=50, maximum=150)
        self._sync_active_display_mode_from_current_settings(save=False)
        self.cfg["prompt_image_baseline_ready"] = bool(self.prompt_image_baseline_ready)
        self.cfg["asset_image_baseline_ready"] = bool(self.asset_image_baseline_ready)
        self.cfg["current_media_state"] = self.current_media_state or ""
        if hasattr(self, "lbl_coords"):
            self.lbl_coords.config(text=self._get_coord_text())
        self.cfg["relay_count"] = 1
        self.cfg["relay_use_selection"] = False
        self.cfg["relay_start_slot"] = None
        self.cfg["relay_end_slot"] = None
        self.cfg["relay_selected_slots"] = []
        self.save_config()
        self._refresh_prompt_preset_selector_label()
        self._sync_relay_selection_label()
        self._refresh_manual_selection_labels()
        self._refresh_prompt_reference_ui()
        if hasattr(self, 'actor'):
            self.actor.language_mode = self.cfg["language_mode"]
            self.actor.set_typing_speed_profile(self.cfg.get("typing_speed_profile", "normal"))
            self._apply_actor_break_settings(reset_batch=False)
        if hasattr(self, "lbl_hud_mode"):
            self.lbl_hud_mode.config(text=f"입력: {self.cfg['input_mode']}")
        if self.page:
            self._apply_browser_zoom()
            self._apply_browser_window_scale_live()
        self._refresh_display_mode_ui()
        self._set_startup_preflight_ui(
            self.last_startup_preflight_ok if self.last_startup_preflight_at else None,
            self.last_startup_preflight_summary if self.last_startup_preflight_at else "",
            self.last_startup_preflight_at,
        )
        focus_widget = None
        try:
            focus_widget = self.root.focus_get()
        except Exception:
            focus_widget = None
        if focus_widget not in (getattr(self, "spin_asset_start", None), getattr(self, "spin_asset_end", None)):
            self._sync_asset_range_display()
        self.log(f"⚙️ 설정 동기화 완료 (입력방식: {self.cfg['input_mode']})")

    def _pick_first_visible_selector(self, candidates):
        if not self.page:
            return None
        for sel in candidates:
            try:
                loc = self.page.locator(sel).first
                if loc.count() <= 0:
                    continue
                if loc.is_visible(timeout=1200):
                    return sel
            except Exception:
                continue
        return None

    def _normalize_candidate_list(self, value):
        out = []
        if isinstance(value, str):
            v = value.strip()
            if v:
                out.append(v)
        elif isinstance(value, (list, tuple)):
            for x in value:
                if isinstance(x, str):
                    v = x.strip()
                    if v:
                        out.append(v)
        return out

    def _input_candidates(self):
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get("input_selector", "")))
        cands.extend(self._normalize_candidate_list(self.cfg.get("input_selectors", [])))
        cands.extend([
            "textarea[placeholder*='무엇을 만들고 싶으신가요' i]",
            "textarea[aria-label*='무엇을 만들고 싶으신가요' i]",
            "[role='textbox'][aria-label*='무엇을 만들고 싶으신가요' i]",
            "[contenteditable='true'][aria-label*='무엇을 만들고 싶으신가요' i]",
            "#PINHOLE_TEXT_AREA_ELEMENT_ID",
            "textarea#PINHOLE_TEXT_AREA_ELEMENT_ID",
            "[id*='PINHOLE' i]",
            "textarea:not([placeholder*='검색' i]):not([aria-label*='검색' i]):not([placeholder*='asset' i]):not([aria-label*='asset' i])",
            "[role='textbox']:not([aria-label*='검색' i]):not([aria-label*='asset' i])",
            "[contenteditable='true']:not([aria-label*='검색' i]):not([aria-label*='asset' i])",
            "textarea",
            "[contenteditable='true']",
            "[contenteditable='plaintext-only']",
            "div[contenteditable='true']",
            "div[contenteditable='plaintext-only']",
            "[role='textbox']",
            "div.ProseMirror[contenteditable='true']",
            "div[data-lexical-editor='true']",
            "textarea[placeholder*='무엇을 만들' i]",
            "textarea[aria-label*='무엇을 만들' i]",
            "textarea[placeholder*='프롬프트' i]",
            "textarea[aria-label*='프롬프트' i]",
            "textarea[placeholder*='prompt' i]",
            "textarea[placeholder*='message' i]",
            "textarea[placeholder*='메시지' i]",
            "textarea[aria-label*='prompt' i]",
            "textarea[aria-label*='message' i]",
        ])
        # 중복 제거(순서 유지)
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _is_generic_input_selector(self, selector):
        sel = str(selector or "").strip().lower()
        if not sel:
            return False
        generic_set = {
            "textarea",
            "[contenteditable='true']",
            "[contenteditable='plaintext-only']",
            "div[contenteditable='true']",
            "div[contenteditable='plaintext-only']",
            "[role='textbox']",
            "textarea, [contenteditable='true']",
            "#pinhole_text_area_element_id, textarea, [role='textbox'], [contenteditable='true']",
        }
        return sel in generic_set

    def _submit_candidates(self):
        cands = []
        cands.extend(self._normalize_candidate_list(self.cfg.get("submit_selector", "")))
        cands.extend(self._normalize_candidate_list(self.cfg.get("submit_selectors", [])))
        cands.extend([
            "button[type='submit']",
            "button[aria-label*='generate' i]",
            "button[aria-label*='생성' i]",
            "button[aria-label*='보내' i]",
            "button[aria-label*='send' i]",
            "button[aria-label*='submit' i]",
            "[role='button'][aria-label*='생성' i]",
            "[role='button'][aria-label*='보내' i]",
            "[role='button'][aria-label*='send' i]",
            "button:has-text('Generate')",
            "button:has-text('생성')",
            "button:has-text('보내기')",
            # 마지막 fallback으로만 사용
            "button[aria-label*='create' i]",
            "button:has-text('Create')",
        ])
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    def _resolve_submit_by_geometry(self, input_locator, timeout_ms=1200):
        """
        텍스트 기반 selector가 부정확할 때, 입력창 오른쪽의 실제 전송 버튼을 기하학적으로 추정한다.
        """
        if (not self.page) or (input_locator is None):
            return None
        try:
            ib = input_locator.bounding_box()
        except Exception:
            ib = None
        if not ib:
            return None

        ix = ib["x"]
        iy = ib["y"]
        iw = ib["width"]
        ih = ib["height"]
        input_cx = ix + iw / 2.0
        input_cy = iy + ih / 2.0
        input_right = ix + iw

        best = None
        best_score = float("inf")
        try:
            loc = self.page.locator("button, [role='button']")
            total = loc.count()
        except Exception:
            return None

        upper = min(total, 250)
        for i in range(upper):
            cand = loc.nth(i)
            try:
                if not cand.is_visible(timeout=timeout_ms):
                    continue
            except Exception:
                continue
            try:
                if not cand.is_enabled(timeout=200):
                    continue
            except Exception:
                pass
            try:
                b = cand.bounding_box()
            except Exception:
                b = None
            if not b:
                continue
            if b["width"] < 18 or b["height"] < 18:
                continue

            cx = b["x"] + b["width"] / 2.0
            cy = b["y"] + b["height"] / 2.0
            score = 0.0

            # 입력창 행과 가까운 버튼(특히 우측)을 선호
            score += abs(cy - input_cy) * 3.0
            score += abs(cx - (input_right - 24.0)) * 1.5

            # 입력창보다 너무 위쪽(상단바)은 강한 패널티
            if cy < (iy - 180):
                score += 3000.0
            # 입력창 왼쪽에 있는 버튼(+) 등은 패널티
            if cx < (ix + iw * 0.45):
                score += 900.0

            try:
                meta = cand.evaluate(
                    """(el) => ((el.getAttribute('aria-label') || '') + ' ' + (el.innerText || '')).toLowerCase()"""
                )
            except Exception:
                meta = ""
            if meta:
                if any(x in meta for x in ("menu", "메뉴", "설정", "setting", "도움", "help", "프로젝트")):
                    score += 1600.0
                if any(x in meta for x in ("생성", "generate", "send", "보내")):
                    score -= 350.0

            if score < best_score:
                best_score = score
                best = cand

        return best

    def _resolve_visible_locator(self, candidates, timeout_ms=1200):
        if not self.page:
            return None, None
        # main frame 우선
        for sel in candidates:
            try:
                loc = self.page.locator(sel).first
                if loc.count() > 0 and loc.is_visible(timeout=timeout_ms):
                    return loc, sel
            except Exception:
                continue
        # iframe 탐색
        try:
            for fr in self.page.frames:
                if fr == self.page.main_frame:
                    continue
                for sel in candidates:
                    try:
                        loc = fr.locator(sel).first
                        if loc.count() > 0 and loc.is_visible(timeout=timeout_ms):
                            return loc, sel
                    except Exception:
                        continue
        except Exception:
            pass
        return None, None

    def _resolve_best_locator(self, candidates, near_locator=None, timeout_ms=1200, prefer_enabled=True, reject_fn=None):
        """
        selector가 여러 개 매칭될 때 가장 적절한 요소를 고르는 함수.
        - near_locator가 있으면 그 근처의 요소를 우선 선택
        - 비활성(disabled) 요소는 강한 패널티
        """
        if not self.page:
            return None, None

        near_cx = None
        near_cy = None
        if near_locator is not None:
            try:
                nb = near_locator.bounding_box()
                if nb:
                    near_cx = nb["x"] + nb["width"] / 2.0
                    near_cy = nb["y"] + nb["height"] / 2.0
            except Exception:
                pass

        best = None
        best_selector = None
        best_score = float("inf")

        def _consider(loc, sel):
            nonlocal best, best_selector, best_score
            try:
                total = loc.count()
            except Exception:
                return
            if total <= 0:
                return
            # 너무 많은 요소일 때 과도한 탐색 방지
            upper = min(total, 20)
            for i in range(upper):
                cand = loc.nth(i)
                try:
                    if not cand.is_visible(timeout=timeout_ms):
                        continue
                except Exception:
                    continue
                if reject_fn is not None:
                    try:
                        if reject_fn(cand, sel):
                            continue
                    except Exception:
                        pass
                try:
                    box = cand.bounding_box()
                except Exception:
                    box = None
                if not box:
                    continue

                score = 0.0
                try:
                    enabled = cand.is_enabled(timeout=300)
                except Exception:
                    enabled = True
                # 입력 전 단계에서는 제출 버튼이 disabled일 수 있어 과도 패널티를 피한다.
                if not enabled and prefer_enabled:
                    score += 1200.0

                # 너무 작은 요소는 오탐 가능성이 큼
                if box["width"] < 20 or box["height"] < 12:
                    score += 3000.0

                if near_cx is not None and near_cy is not None:
                    cx = box["x"] + box["width"] / 2.0
                    cy = box["y"] + box["height"] / 2.0
                    dx = cx - near_cx
                    dy = cy - near_cy
                    score += (dx * dx + dy * dy) ** 0.5
                else:
                    score += float(i)

                if score < best_score:
                    best_score = score
                    best = cand
                    best_selector = sel

        # main frame
        for sel in candidates:
            try:
                _consider(self.page.locator(sel), sel)
            except Exception:
                continue

        # iframes
        try:
            for fr in self.page.frames:
                if fr == self.page.main_frame:
                    continue
                for sel in candidates:
                    try:
                        _consider(fr.locator(sel), sel)
                    except Exception:
                        continue
        except Exception:
            pass

        return best, best_selector

    def _locator_meta_text(self, locator):
        try:
            return locator.evaluate(
                """(el) => {
                    const a = (name) => (el.getAttribute(name) || "");
                    const parts = [
                        (el.tagName || ""),
                        (el.id || ""),
                        (el.className || ""),
                        a("name"),
                        a("placeholder"),
                        a("aria-label"),
                        a("title"),
                        (el.innerText || ""),
                    ];
                    return parts.join(" ").toLowerCase();
                }"""
            ) or ""
        except Exception:
            return ""

    def _locator_selector_hint(self, locator):
        try:
            return locator.evaluate(
                """(el) => {
                    const esc = (value) => String(value || "").replace(/\\/g, "\\\\").replace(/"/g, '\\"');
                    const tag = (el.tagName || "").toLowerCase();
                    const id = el.id || "";
                    if (id) return `#${id}`;
                    const aria = el.getAttribute("aria-label") || "";
                    if (aria) return `${tag || "*"}[aria-label="${esc(aria)}"]`;
                    const title = el.getAttribute("title") || "";
                    if (title) return `${tag || "*"}[title="${esc(title)}"]`;
                    const name = el.getAttribute("name") || "";
                    if (name) return `${tag || "*"}[name="${esc(name)}"]`;
                    const cls = String(el.className || "").trim().split(/\\s+/).filter(Boolean).slice(0, 2);
                    if (tag && cls.length) return `${tag}.${cls.join(".")}`;
                    return tag || "*";
                }"""
            ) or ""
        except Exception:
            return ""

    def _locator_prompt_input_score(self, locator, selector=""):
        try:
            info = locator.evaluate(
                """(el) => {
                    const a = (name) => (el.getAttribute(name) || "");
                    const text = (el.innerText || el.textContent || "");
                    const r = el.getBoundingClientRect();
                    return {
                        tag: (el.tagName || "").toLowerCase(),
                        role: a("role").toLowerCase(),
                        placeholder: a("placeholder").toLowerCase(),
                        aria: a("aria-label").toLowerCase(),
                        title: a("title").toLowerCase(),
                        name: a("name").toLowerCase(),
                        contenteditable: a("contenteditable").toLowerCase(),
                        text_len: text.length || 0,
                        rect: {x: r.x || 0, y: r.y || 0, width: r.width || 0, height: r.height || 0},
                    };
                }"""
            ) or {}
        except Exception:
            return float("-inf")

        rect = info.get("rect") or {}
        width = float(rect.get("width") or 0.0)
        height = float(rect.get("height") or 0.0)
        y = float(rect.get("y") or 0.0)
        if width < 40 or height < 18:
            return float("-inf")

        viewport_h = 900.0
        try:
            vp = getattr(self.page, "viewport_size", None) or {}
            viewport_h = float(vp.get("height") or viewport_h)
        except Exception:
            viewport_h = 900.0

        tag = str(info.get("tag") or "")
        role = str(info.get("role") or "")
        contenteditable = str(info.get("contenteditable") or "")
        text_len = int(info.get("text_len") or 0)
        meta = " ".join(
            [
                str(info.get("placeholder") or ""),
                str(info.get("aria") or ""),
                str(info.get("title") or ""),
                str(info.get("name") or ""),
                self._locator_meta_text(locator),
            ]
        ).lower()

        prompt_keys = ("무엇을 만들", "prompt", "프롬프트", "message", "메시지")
        search_keys = ("asset", "search", "에셋", "검색")
        tile_noise_keys = ("보안", "약관", "패턴", "온·오프라인", "신원 연동", "판단기준")

        score = 0.0
        if any(k in meta for k in prompt_keys):
            score += 1700.0
        if any(k in meta for k in search_keys):
            score -= 2400.0
        if any(k.lower() in meta for k in tile_noise_keys):
            score -= 1400.0

        if tag == "textarea":
            score += 240.0
        if role == "textbox":
            score += 120.0
        if contenteditable in ("true", "plaintext-only"):
            score += 100.0

        if 180 <= width <= 1200:
            score += 120.0
        elif width > 1500:
            score -= 180.0

        if 28 <= height <= 180:
            score += 220.0
        elif height > 260:
            score -= 1800.0

        area = width * height
        if area > 260000:
            score -= 1200.0

        center_y = y + (height / 2.0)
        y_ratio = center_y / max(1.0, viewport_h)
        if 0.45 <= y_ratio <= 0.96:
            score += 260.0
        elif y_ratio < 0.22:
            score -= 260.0
        elif y_ratio < 0.34:
            score -= 520.0

        if text_len > 160:
            score -= 700.0
        elif 0 <= text_len <= 12:
            score += 45.0

        if selector:
            if self._is_generic_input_selector(selector):
                score -= 120.0
            else:
                score += 90.0

        return score

    def _is_asset_search_like_locator(self, locator):
        meta = self._locator_meta_text(locator)
        if not meta:
            return False
        search_keys = ("asset", "search", "에셋", "검색", "swap_horiz", "swap")
        prompt_keys = ("무엇을 만들고 싶으신가요", "prompt", "프롬프트", "message", "메시지")
        has_search = any(k in meta for k in search_keys)
        has_prompt = any(k in meta for k in prompt_keys)
        return has_search and (not has_prompt)

    def _resolve_prompt_input_locator(self, input_selector, timeout_ms=2500, near_locator=None):
        # 동적 UI에서 ref 재할당이 발생해도 매번 "프롬프트 입력칸"을 다시 찾도록 강제한다.
        configured = self._normalize_candidate_list(input_selector)
        specific = [sel for sel in configured if not self._is_generic_input_selector(sel)]
        generic = [sel for sel in configured if self._is_generic_input_selector(sel)]

        candidates = []
        for sel in specific:
            if sel not in candidates:
                candidates.append(sel)
        for sel in self._input_candidates():
            if sel not in candidates:
                candidates.append(sel)
        for sel in generic:
            if sel not in candidates:
                candidates.append(sel)

        best = None
        best_selector = None
        best_score = float("-inf")
        near_box = None
        if near_locator is not None:
            try:
                near_box = near_locator.bounding_box()
            except Exception:
                near_box = None

        def _consider(container):
            nonlocal best, best_selector, best_score
            for sel in candidates:
                try:
                    loc = container.locator(sel)
                    total = loc.count()
                except Exception:
                    continue
                upper = min(total, 18)
                for idx in range(upper):
                    cand = loc.nth(idx)
                    try:
                        if not cand.is_visible(timeout=timeout_ms):
                            continue
                    except Exception:
                        continue
                    if self._is_asset_search_like_locator(cand):
                        continue
                    score = self._locator_prompt_input_score(cand, sel)
                    if near_box:
                        try:
                            box = cand.bounding_box()
                        except Exception:
                            box = None
                        if box:
                            near_cx = float(near_box["x"]) + float(near_box["width"]) * 0.5
                            near_cy = float(near_box["y"]) + float(near_box["height"]) * 0.5
                            cx = float(box["x"]) + float(box["width"]) * 0.5
                            cy = float(box["y"]) + float(box["height"]) * 0.5
                            dist = ((cx - near_cx) ** 2 + (cy - near_cy) ** 2) ** 0.5
                            score -= dist * 0.9
                            if cy < (near_cy - 120.0):
                                score -= 1200.0
                    score -= idx * 6.0
                    if score > best_score:
                        best = cand
                        best_selector = sel
                        best_score = score

        if self.page:
            _consider(self.page)
            try:
                for fr in self.page.frames:
                    if fr == self.page.main_frame:
                        continue
                    _consider(fr)
            except Exception:
                pass

        if best is not None:
            return best, best_selector

        # 마지막 폴백: 기존 일반 탐색 1회
        input_loc, resolved_selector = self._resolve_best_locator(
            candidates,
            near_locator=near_locator,
            timeout_ms=timeout_ms,
            reject_fn=lambda cand, _sel: self._is_asset_search_like_locator(cand),
        )
        if input_loc is not None:
            return input_loc, resolved_selector
        return None, None

    def _prompt_media_candidates(self, media_mode, profile="prompt"):
        media_mode = "video" if str(media_mode).strip().lower() == "video" else "image"
        target = "Video" if media_mode == "video" else "Image"
        alt = "영상" if media_mode == "video" else "이미지"
        cands = []
        saved_selector = str(self.cfg.get(self._preset_cfg_key(profile, "media_mode_selector"), "") or "").strip()
        if self._selector_matches_media_state(saved_selector, media_mode):
            cands.append(saved_selector)
        cands.extend([
            f"button:text-is('{target}')",
            f"[role='button']:text-is('{target}')",
            f"button:has-text('{target}')",
            f"[role='button']:has-text('{target}')",
            f"button[aria-label*='{target.lower()}' i]",
            f"[role='button'][aria-label*='{target.lower()}' i]",
            f"button:has-text('{alt}')",
            f"[role='button']:has-text('{alt}')",
        ])
        return self._normalize_candidate_list(cands)

    def _panel_media_tab_candidates(self, state, profile="prompt"):
        state = "video" if str(state).strip().lower() == "video" else "image"
        target = "Video" if state == "video" else "Image"
        alt = "영상" if state == "video" else "이미지"
        cands = []
        saved_selector = str(self.cfg.get(self._preset_cfg_key(profile, "media_mode_selector"), "") or "").strip()
        if self._selector_matches_media_state(saved_selector, state):
            cands.append(saved_selector)
        cands.extend([
            f"button:text-is('{target}')",
            f"[role='button']:text-is('{target}')",
            f"[role='tab']:text-is('{target}')",
            f"button:has-text('{target}')",
            f"[role='button']:has-text('{target}')",
            f"[role='tab']:has-text('{target}')",
            f"button:has-text('{alt}')",
            f"[role='button']:has-text('{alt}')",
            f"[role='tab']:has-text('{alt}')",
            f"button[aria-label*='{target.lower()}' i]",
            f"[role='button'][aria-label*='{target.lower()}' i]",
            f"[role='tab'][aria-label*='{target.lower()}' i]",
            f"button[title*='{target.lower()}' i]",
            f"[role='button'][title*='{target.lower()}' i]",
            f"[role='tab'][title*='{target.lower()}' i]",
            f"div[role='tab']:has-text('{target}')",
            f"span[role='tab']:has-text('{target}')",
            f"div[role='tab']:has-text('{alt}')",
            f"span[role='tab']:has-text('{alt}')",
        ])
        return self._normalize_candidate_list(cands)

    def _selector_matches_media_state(self, selector, state):
        selector = str(selector or "").strip().lower()
        if not selector:
            return False
        state = "video" if str(state).strip().lower() == "video" else "image"
        image_terms = ("image", "이미지", "nano banana")
        video_terms = ("video", "동영상", "영상")
        has_image = any(term in selector for term in image_terms)
        has_video = any(term in selector for term in video_terms)
        if has_image and not has_video:
            return state == "image"
        if has_video and not has_image:
            return state == "video"
        return True

    def _media_state_terms(self, state):
        state = "video" if str(state).strip().lower() == "video" else "image"
        if state == "video":
            return {
                "state": "video",
                "primary": "Video",
                "localized": "동영상",
                "keywords": ("video", "동영상", "영상", "movie", "clip", "veo"),
                "exact": ("video", "동영상", "영상"),
            }
        return {
            "state": "image",
            "primary": "Image",
            "localized": "이미지",
            "keywords": ("image", "이미지", "사진", "photo", "nano banana"),
            "exact": ("image", "이미지"),
        }

    def _locator_box(self, locator):
        if locator is None:
            return None
        try:
            return locator.bounding_box()
        except Exception:
            return None

    def _score_panel_media_candidate(self, info, desired_state=None, input_box=None, opener_box=None, selector=""):
        rect = info.get("rect") or {}
        width = float(rect.get("width") or 0.0)
        height = float(rect.get("height") or 0.0)
        x = float(rect.get("x") or 0.0)
        y = float(rect.get("y") or 0.0)
        cx = x + (width / 2.0)
        cy = y + (height / 2.0)

        tag = str(info.get("tag") or "").lower()
        role = str(info.get("role") or "").lower()
        text = str(info.get("text") or "").strip()
        inner = str(info.get("innerText") or "").strip()
        aria = str(info.get("aria") or "").strip()
        title = str(info.get("title") or "").strip()
        class_name = str(info.get("className") or "").strip()

        meta = " ".join([tag, role, text, inner, aria, title, class_name]).lower()
        compact_inner = re.sub(r"\s+", " ", inner or text).strip().lower()

        target_terms = self._media_state_terms(desired_state) if desired_state else None
        other_terms = None
        if target_terms is not None:
            other_terms = self._media_state_terms("image" if desired_state == "video" else "video")

        target_hits = 0
        other_hits = 0
        exact_match = False
        if target_terms is not None:
            target_hits = sum(1 for key in target_terms["keywords"] if key in meta)
            other_hits = sum(1 for key in other_terms["keywords"] if key in meta)
            exact_match = compact_inner in target_terms["exact"] or aria.lower() in target_terms["exact"] or title.lower() in target_terms["exact"]

        score = 0.0
        if tag == "button":
            score += 120.0
        if role == "button":
            score += 140.0
        if role == "tab":
            score += 220.0
        if any(token in class_name.lower() for token in ("tab", "segment", "segmented", "pill", "chip", "toggle")):
            score += 90.0
        if any(token in meta for token in ("image", "video", "이미지", "동영상", "영상", "nano banana", "veo")):
            score += 140.0
        if target_hits:
            score += 380.0 + (target_hits * 35.0)
        if exact_match:
            score += 260.0
        if other_hits and not target_hits:
            score -= 130.0
        elif other_hits:
            score -= 40.0

        if any(token in meta for token in ("generate", "생성", "send", "보내", "close", "닫기", "menu", "메뉴", "setting", "설정")) and not target_hits:
            score -= 220.0

        if any(token in meta for token in ("대시보드", "dashboard", "정렬", "필터", "search", "검색", "장면 빌더", "scene builder", "미디어 추가", "카메라", "camera")):
            score -= 520.0
        if any(token in meta for token in ("보기", "view")) and x < 120.0:
            score -= 1100.0
        if x < 96.0:
            score -= 680.0
        if x < 96.0 and width <= 72.0 and height <= 72.0:
            score -= 520.0

        if not any((text, inner, aria, title, class_name)):
            score -= 240.0
        if width < 22 or height < 12:
            score -= 400.0
        if width > 520:
            score -= 180.0
        if height > 180:
            score -= 220.0
        if len(inner) > 120 and role not in ("tab", "button") and tag != "button":
            score -= 180.0
        if 30 <= width <= 260:
            score += 45.0
        if 20 <= height <= 88:
            score += 35.0

        ref_box = opener_box or input_box
        if ref_box:
            ref_cx = float(ref_box.get("x") or 0.0) + (float(ref_box.get("width") or 0.0) / 2.0)
            ref_cy = float(ref_box.get("y") or 0.0) + (float(ref_box.get("height") or 0.0) / 2.0)
            dist = ((cx - ref_cx) ** 2 + (cy - ref_cy) ** 2) ** 0.5
            score -= min(dist, 1800.0) * (0.22 if opener_box else 0.16)
            if opener_box:
                opener_x = float(opener_box.get("x") or 0.0)
                if x < (opener_x - 280.0):
                    score -= 760.0

        if input_box:
            input_top = float(input_box.get("y") or 0.0)
            input_bottom = input_top + float(input_box.get("height") or 0.0)
            if cy < (input_top - 280.0):
                score -= 160.0
            if cy > (input_bottom + 260.0):
                score -= 140.0

        return {
            "score": score,
            "target_hits": target_hits,
            "other_hits": other_hits,
            "exact_match": exact_match,
            "meta": meta,
            "compact_inner": compact_inner,
            "selector": selector,
        }

    def _collect_panel_media_candidates(self, desired_state, input_locator=None, opener_locator=None, timeout_ms=200):
        if not self.page:
            return []

        input_box = self._locator_box(input_locator)
        opener_box = self._locator_box(opener_locator)
        candidates = []
        seen = set()
        selectors = (
            ("button", 80),
            ("[role='button']", 120),
            ("[role='tab']", 120),
            ("div", 180),
            ("span", 180),
        )

        containers = [("main", self.page)]
        try:
            for idx, fr in enumerate(self.page.frames):
                if fr == self.page.main_frame:
                    continue
                containers.append((f"frame{idx}", fr))
        except Exception:
            pass

        for frame_label, container in containers:
            for selector, limit in selectors:
                try:
                    loc = container.locator(selector)
                    total = loc.count()
                except Exception:
                    continue
                upper = min(total, limit)
                for idx in range(upper):
                    cand = loc.nth(idx)
                    try:
                        if not cand.is_visible(timeout=timeout_ms):
                            continue
                    except Exception:
                        continue
                    try:
                        info = cand.evaluate(
                            """(el) => {
                                const a = (name) => (el.getAttribute(name) || "");
                                const rect = el.getBoundingClientRect();
                                return {
                                    tag: (el.tagName || "").toLowerCase(),
                                    role: a("role"),
                                    aria: a("aria-label"),
                                    title: a("title"),
                                    className: String(el.className || ""),
                                    id: a("id"),
                                    text: String(el.textContent || "").trim(),
                                    innerText: String(el.innerText || "").trim(),
                                    rect: {
                                        x: Number(rect.x || 0),
                                        y: Number(rect.y || 0),
                                        width: Number(rect.width || 0),
                                        height: Number(rect.height || 0),
                                    },
                                };
                            }"""
                        ) or {}
                    except Exception:
                        continue

                    rect = info.get("rect") or {}
                    width = float(rect.get("width") or 0.0)
                    height = float(rect.get("height") or 0.0)
                    if width < 18.0 or height < 12.0:
                        continue

                    x = round(float(rect.get("x") or 0.0), 1)
                    y = round(float(rect.get("y") or 0.0), 1)
                    key = (
                        frame_label,
                        selector,
                        info.get("tag") or "",
                        info.get("role") or "",
                        x,
                        y,
                        round(width, 1),
                        round(height, 1),
                        str(info.get("aria") or "")[:80],
                        str(info.get("innerText") or "")[:80],
                    )
                    if key in seen:
                        continue
                    seen.add(key)

                    scored = self._score_panel_media_candidate(
                        info,
                        desired_state=desired_state,
                        input_box=input_box,
                        opener_box=opener_box,
                        selector=selector,
                    )
                    info.update(scored)

                    role = str(info.get("role") or "").lower()
                    meta = str(info.get("meta") or "")
                    if selector in ("div", "span") and role not in ("button", "tab"):
                        if info["target_hits"] <= 0 and not any(token in meta for token in ("image", "video", "이미지", "동영상", "영상", "tab", "segment", "chip", "pill", "toggle")):
                            if info["score"] < -40.0:
                                continue

                    info["frame"] = frame_label
                    info["locator"] = cand
                    candidates.append(info)

        candidates.sort(key=lambda item: item.get("score", float("-inf")), reverse=True)
        return candidates

    def _log_panel_media_candidates_dump(self, desired_state, candidates, stage_label=""):
        state_label = "동영상" if str(desired_state).strip().lower() == "video" else "이미지"
        head = "🧩 패널 후보 덤프"
        if stage_label:
            head += f" | {stage_label}"
        head += f" | 목표={state_label} | 후보 {len(candidates)}개"
        self.log(head)

        if not candidates:
            self.log("   - 보이는 후보가 없습니다.")
            return

        for idx, item in enumerate(candidates[:30], start=1):
            rect = item.get("rect") or {}
            text = re.sub(r"\s+", " ", str(item.get("text") or "")).strip()
            inner = re.sub(r"\s+", " ", str(item.get("innerText") or "")).strip()
            aria = re.sub(r"\s+", " ", str(item.get("aria") or "")).strip()
            title = re.sub(r"\s+", " ", str(item.get("title") or "")).strip()
            class_name = re.sub(r"\s+", " ", str(item.get("className") or "")).strip()
            self.log(
                f"   {idx:02d}. tag={item.get('tag') or '-'} role={item.get('role') or '-'} "
                f"text='{text[:70]}' inner='{inner[:70]}' aria='{aria[:60]}' title='{title[:60]}' "
                f"class='{class_name[:80]}' box=({float(rect.get('x') or 0.0):.1f}, {float(rect.get('y') or 0.0):.1f}, "
                f"{float(rect.get('width') or 0.0):.1f}, {float(rect.get('height') or 0.0):.1f}) "
                f"score={float(item.get('score') or 0.0):.1f} frame={item.get('frame') or 'main'} src={item.get('selector') or '-'}"
            )

    def _resolve_panel_media_target(self, desired_state, input_locator=None, opener_locator=None, profile="prompt", timeout_ms=3200, dump_stage_label=""):
        profile = "asset" if str(profile).strip().lower() == "asset" else "prompt"
        desired_state = "video" if str(desired_state).strip().lower() == "video" else "image"
        wait_steps = (0.12, 0.28, 0.55, 0.9, 1.2)
        deadline = time.time() + max(1.0, timeout_ms / 1000.0)
        dumped = False
        last_candidates = []

        while time.time() < deadline:
            for near in (input_locator, opener_locator, None):
                media_loc, media_sel = self._resolve_best_locator(
                    self._panel_media_tab_candidates(desired_state, profile=profile),
                    near_locator=near if near is not None else None,
                    timeout_ms=220,
                    prefer_enabled=False,
                )
                if media_loc is not None:
                    if not dumped:
                        last_candidates = self._collect_panel_media_candidates(
                            desired_state,
                            input_locator=input_locator,
                            opener_locator=opener_locator,
                            timeout_ms=120,
                        )
                        self._log_panel_media_candidates_dump(desired_state, last_candidates, stage_label=dump_stage_label or "selector 탐색 직후")
                        dumped = True
                    return media_loc, media_sel

            last_candidates = self._collect_panel_media_candidates(
                desired_state,
                input_locator=input_locator,
                opener_locator=opener_locator,
                timeout_ms=160,
            )
            if not dumped:
                self._log_panel_media_candidates_dump(desired_state, last_candidates, stage_label=dump_stage_label or "패널 직후 visible dump")
                dumped = True

            for item in last_candidates:
                if item.get("target_hits", 0) <= 0:
                    continue
                if item.get("exact_match"):
                    return item.get("locator"), self._locator_to_button_selector(item.get("locator")) or item.get("selector") or "dom-exact"
                role = str(item.get("role") or "").lower()
                tag = str(item.get("tag") or "").lower()
                if role in ("tab", "button") or tag == "button" or float(item.get("score") or 0.0) >= 120.0:
                    return item.get("locator"), self._locator_to_button_selector(item.get("locator")) or item.get("selector") or "dom-near"

            if not wait_steps:
                break
            time.sleep(wait_steps[0])
            wait_steps = wait_steps[1:]

        if not dumped:
            last_candidates = self._collect_panel_media_candidates(
                desired_state,
                input_locator=input_locator,
                opener_locator=opener_locator,
                timeout_ms=160,
            )
            self._log_panel_media_candidates_dump(desired_state, last_candidates, stage_label=dump_stage_label or "최종 실패 dump")
        return None, None

    def _apply_prompt_generation_preset(self, input_locator=None, profile="prompt"):
        if not self.page:
            return
        profile = "asset" if str(profile).strip().lower() == "asset" else "prompt"
        self.cfg[self._preset_cfg_key(profile, "mode_preset_enabled")] = True
        desired_state = str(self.cfg.get(self._preset_cfg_key(profile, "media_mode"), "image")).strip().lower()
        desired_state = "video" if desired_state == "video" else "image"
        ok = self._switch_media_state(desired_state, input_locator=input_locator, profile=profile)
        if not ok:
            raise RuntimeError("생성 모드 전환에 실패했습니다. 상태 확인과 이미지/동영상 전환 테스트를 다시 확인해주세요.")

    def _auto_detect_media_panel_selectors(self, input_locator=None, profile="prompt"):
        profile = "asset" if str(profile).strip().lower() == "asset" else "prompt"
        current_button, _current_desc, current_state = self._resolve_current_media_panel_button(input_locator=input_locator, profile=profile)
        current_state = current_state or self.current_media_state or "image"
        if current_button is None:
            raise RuntimeError("현재 생성 옵션 패널 버튼을 찾지 못했습니다.")

        current_selector = self._locator_to_button_selector(current_button)
        if not current_selector:
            raise RuntimeError("현재 생성 옵션 패널 selector를 만들지 못했습니다.")

        target_state = "video" if current_state == "image" else "image"
        if not self._click_with_actor_fallback(current_button, f"{current_state} 패널 열기"):
            raise RuntimeError(f"{current_state} 패널 열기 클릭 실패")
        time.sleep(0.5)

        target_button, media_mode_selector = self._resolve_panel_media_target(
            target_state,
            input_locator=input_locator,
            opener_locator=current_button,
            profile=profile,
            timeout_ms=3600,
            dump_stage_label=f"{profile} {current_state}->{target_state}",
        )
        if target_button is None:
            raise RuntimeError(f"{target_state} 선택 버튼을 찾지 못했습니다.")
        if not self._click_with_actor_fallback(target_button, f"{target_state} 선택"):
            raise RuntimeError(f"{target_state} 선택 클릭 실패")
        time.sleep(0.5)

        switched_button, _switched_desc, switched_state = self._resolve_current_media_panel_button(input_locator=input_locator, profile=profile)
        switched_selector = self._locator_to_button_selector(switched_button)
        switched_state = switched_state or target_state
        if not switched_selector:
            raise RuntimeError("변경 후 생성 옵션 패널 selector를 만들지 못했습니다.")

        if current_state == "image":
            image_panel_selector = current_selector
            video_panel_selector = switched_selector
        else:
            image_panel_selector = switched_selector
            video_panel_selector = current_selector

        self.cfg[self._panel_selector_key(profile, "image")] = image_panel_selector
        self.cfg[self._panel_selector_key(profile, "video")] = video_panel_selector
        self.cfg[self._preset_cfg_key(profile, "media_mode_selector")] = media_mode_selector or ""
        self.current_media_state = switched_state
        self.cfg["current_media_state"] = switched_state
        self.save_config()
        self._refresh_prompt_preset_selector_label()

        # 자동찾기 후에는 원래 상태로 복원해 둔다.
        self._switch_media_state(current_state, input_locator=input_locator, profile=profile)
        self.current_media_state = current_state
        self.cfg["current_media_state"] = current_state
        self.save_config()

        return image_panel_selector, video_panel_selector, media_mode_selector or ""

    def _run_media_transition_test(self, profile="prompt", from_state="image", to_state="video"):
        profile = "asset" if str(profile).strip().lower() == "asset" else "prompt"
        from_state = "video" if str(from_state).strip().lower() == "video" else "image"
        to_state = "video" if str(to_state).strip().lower() == "video" else "image"
        if from_state == to_state:
            raise RuntimeError("같은 방향 테스트는 실행할 수 없습니다.")

        self._ensure_browser_session()
        self.actor.set_page(self.page)

        start_url = (self.cfg.get("start_url") or "").strip()
        if start_url and start_url not in (self.page.url or ""):
            self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(1.0, 2.5))

        input_hint = (self.cfg.get("input_selector") or "").strip() or "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [contenteditable='true'], [role='textbox']"
        self._try_open_new_project_if_needed(input_hint)
        input_locator, _ = self._resolve_prompt_input_locator(input_hint, timeout_ms=2200)
        if input_locator is None:
            self.log("ℹ️ 입력칸 미탐지 상태 - 생성 옵션만 전역 탐색으로 테스트합니다.")

        self.current_media_state = from_state
        self.cfg["current_media_state"] = from_state
        self.save_config()
        return self._switch_media_state(to_state, input_locator=input_locator, profile=profile)

    def _resolve_prompt_preset_controls(self, input_locator=None, profile="prompt"):
        if not self.page:
            raise RuntimeError("브라우저 페이지가 없습니다.")
        profile = "asset" if str(profile).strip().lower() == "asset" else "prompt"

        defs = [
            ("media", "생성 모드", self._prompt_media_candidates(self.cfg.get(self._preset_cfg_key(profile, "media_mode"), "image"), profile=profile)),
        ]
        found = {}
        used = {}
        for key, _label, candidates in defs:
            locator, selector = self._resolve_best_locator(
                candidates,
                near_locator=input_locator if input_locator is not None else None,
                timeout_ms=1600,
                prefer_enabled=False,
            )
            found[key] = locator
            used[key] = selector or ""
        return found, used

    def _resolve_prompt_preset_toggle_button(self, input_locator=None, timeout_ms=1200):
        if not self.page:
            return None, None
        if input_locator is None:
            return self._resolve_prompt_preset_toggle_button_global(timeout_ms=timeout_ms)
        try:
            input_locator.scroll_into_view_if_needed(timeout=900)
        except Exception:
            pass
        try:
            ib = input_locator.bounding_box()
        except Exception:
            ib = None
        if not ib:
            return self._resolve_prompt_preset_toggle_button_global(timeout_ms=timeout_ms)

        input_left = ib["x"]
        input_right = ib["x"] + ib["width"]
        input_top = ib["y"]
        input_mid_y = ib["y"] + ib["height"] / 2.0
        target_x = max(input_left + ib["width"] * 0.68, input_right - 150.0)
        target_y = input_mid_y

        best = None
        best_desc = None
        best_score = float("inf")
        try:
            loc = self.page.locator("button, [role='button']")
            total = loc.count()
        except Exception:
            return None, None

        upper = min(total, 220)
        for i in range(upper):
            cand = loc.nth(i)
            try:
                if not cand.is_visible(timeout=timeout_ms):
                    continue
            except Exception:
                continue
            try:
                box = cand.bounding_box()
            except Exception:
                box = None
            if not box:
                continue
            if box["width"] < 70 or box["height"] < 24:
                continue

            cx = box["x"] + box["width"] / 2.0
            cy = box["y"] + box["height"] / 2.0
            try:
                meta = cand.evaluate(
                    """(el) => ((el.getAttribute('aria-label') || '') + ' ' + (el.innerText || '') + ' ' + (el.getAttribute('title') || '')).toLowerCase()"""
                ) or ""
            except Exception:
                meta = ""

            has_count_chip = any(x in meta for x in ("x1", "x2", "x3", "x4"))
            looks_like_model_dropdown = any(
                x in meta for x in (
                    "quality", "lower priority", "priority", "fast", "arrow_drop_down",
                    "veo 3.1", "veo 2", "veo3.1", "veo2",
                )
            )
            has_mode_hint = any(x in meta for x in ("nano banana", "동영상", "image", "video", "이미지", "영상"))
            bad_tokens = (
                "카메라", "camera", "삽입", "삭제", "확장", "mute", "fullscreen", "play", "pause",
                "search", "검색", "필터", "정렬", "장면 빌더", "scene builder", "미디어 추가",
                "dashboard", "대시보드", "옵션 더보기", "more_vert", "보기", "view",
            )

            if any(x in meta for x in ("생성", "generate", "submit", "send", "보내", "arrow_forward", "메인 메뉴", "설정", "닫기", "close")):
                continue
            if looks_like_model_dropdown:
                continue
            if any(x.lower() in meta for x in bad_tokens):
                continue
            if not (
                has_count_chip
                or has_mode_hint
            ):
                continue
            if box["width"] > 300 or box["height"] > 70:
                continue

            score = abs(cx - target_x) + (abs(cy - target_y) * 3.2)
            if cy < (input_top - 20):
                score += 1200.0
            if cy > (input_top + ib["height"] + 70):
                score += 1200.0
            if cx < (input_left + ib["width"] * 0.45):
                score += 450.0

            if has_count_chip:
                score -= 320.0
            if any(x in meta for x in ("nano banana", "동영상", "영상", "이미지")):
                score -= 180.0
            if any(x in meta for x in ("image", "video", "가로", "세로", "프레임", "재료")):
                score -= 120.0
            if any(x in meta for x in ("frames", "ingredients", "프레임", "재료")):
                score += 380.0
            if has_count_chip and has_mode_hint:
                score -= 220.0

            if score < best_score:
                best = cand
                best_desc = meta[:80] or "프롬프트 생성 옵션 패널 버튼"
                best_score = score

        if best is not None:
            return best, best_desc
        return self._resolve_prompt_preset_toggle_button_global(timeout_ms=timeout_ms)

    def _resolve_prompt_preset_toggle_button_global(self, timeout_ms=1200):
        if not self.page:
            return None, None

        best = None
        best_desc = None
        best_score = float("inf")
        try:
            viewport = getattr(self.page, "viewport_size", None) or {}
            viewport_w = float(viewport.get("width") or 1600.0)
            viewport_h = float(viewport.get("height") or 900.0)
        except Exception:
            viewport_w = 1600.0
            viewport_h = 900.0

        target_x = max(540.0, viewport_w * 0.66)
        target_y = min(viewport_h * 0.74, viewport_h - 150.0)

        try:
            loc = self.page.locator("button, [role='button']")
            total = loc.count()
        except Exception:
            return None, None

        upper = min(total, 260)
        for i in range(upper):
            cand = loc.nth(i)
            try:
                if not cand.is_visible(timeout=timeout_ms):
                    continue
            except Exception:
                continue
            try:
                box = cand.bounding_box()
            except Exception:
                box = None
            if not box:
                continue
            if box["width"] < 70 or box["height"] < 24:
                continue
            if box["x"] < 120:
                continue

            cx = box["x"] + box["width"] / 2.0
            cy = box["y"] + box["height"] / 2.0
            try:
                meta = cand.evaluate(
                    """(el) => ((el.getAttribute('aria-label') || '') + ' ' + (el.innerText || '') + ' ' + (el.getAttribute('title') || '')).toLowerCase()"""
                ) or ""
            except Exception:
                meta = ""

            has_count_chip = any(x in meta for x in ("x1", "x2", "x3", "x4"))
            looks_like_model_dropdown = any(
                x in meta for x in (
                    "quality", "lower priority", "priority", "fast", "arrow_drop_down",
                    "veo 3.1", "veo 2", "veo3.1", "veo2",
                )
            )
            has_mode_hint = any(x in meta for x in ("nano banana", "동영상", "image", "video", "이미지", "영상"))
            bad_tokens = (
                "카메라", "camera", "삽입", "삭제", "확장", "mute", "fullscreen", "play", "pause",
                "search", "검색", "필터", "정렬", "장면 빌더", "scene builder", "미디어 추가",
                "dashboard", "대시보드", "옵션 더보기", "more_vert", "보기", "view",
            )

            if any(x in meta for x in ("생성", "generate", "submit", "send", "보내", "arrow_forward", "메인 메뉴", "설정", "닫기", "close")):
                continue
            if looks_like_model_dropdown:
                continue
            if any(x.lower() in meta for x in bad_tokens):
                continue
            if not (has_count_chip or has_mode_hint):
                continue
            if box["width"] > 320 or box["height"] > 74:
                continue

            score = abs(cx - target_x) + (abs(cy - target_y) * 2.8)
            if cy < max(120.0, viewport_h * 0.20):
                score += 920.0
            if cy > (viewport_h - 50.0):
                score += 520.0
            if has_count_chip:
                score -= 280.0
            if has_mode_hint:
                score -= 180.0
            if any(x in meta for x in ("nano banana", "동영상", "영상", "이미지", "image", "video")):
                score -= 120.0

            if score < best_score:
                best = cand
                best_desc = meta[:80] or "프롬프트 생성 옵션 패널 버튼"
                best_score = score

        return best, best_desc

    def _locator_to_button_selector(self, locator):
        if locator is None:
            return ""
        try:
            info = locator.evaluate(
                """(el) => {
                    const a = (k) => (el.getAttribute(k) || "").trim();
                    const textLines = String(el.innerText || "")
                        .split(/\\n+/)
                        .map(x => x.trim())
                        .filter(Boolean);
                    return {
                        tag: (el.tagName || "button").toLowerCase(),
                        role: a("role"),
                        id: a("id"),
                        testid: a("data-testid"),
                        aria: a("aria-label"),
                        title: a("title"),
                        textLines,
                    };
                }"""
            ) or {}
        except Exception:
            return ""

        tag = str(info.get("tag") or "button").strip().lower() or "button"
        role = str(info.get("role") or "").strip().lower()

        raw_id = str(info.get("id") or "").strip()
        if raw_id:
            esc_id = raw_id.replace("\\", "\\\\").replace("'", "\\'")
            return f"{tag}[id='{esc_id}']"

        raw_testid = str(info.get("testid") or "").strip()
        if raw_testid:
            esc_testid = raw_testid.replace("\\", "\\\\").replace("'", "\\'")
            if role:
                return f"[role='{role}'][data-testid*='{esc_testid}']"
            return f"{tag}[data-testid*='{esc_testid}']"

        raw_aria = str(info.get("aria") or "").strip()
        if raw_aria:
            esc = raw_aria.replace("'", "\\'")
            if role:
                return f"[role='{role}'][aria-label*='{esc}']"
            return f"{tag}[aria-label*='{esc}']"

        raw_title = str(info.get("title") or "").strip()
        if raw_title:
            esc = raw_title.replace("'", "\\'")
            if role:
                return f"[role='{role}'][title*='{esc}']"
            return f"{tag}[title*='{esc}']"

        bad_lines = {
            "image", "video", "가로 모드", "세로 모드", "frames", "ingredients",
            "x1", "x2", "x3", "x4", "생성 시 0크레딧이 사용됩니다.", "생성 시 10크레딧이 사용됩니다.",
            "동영상", "이미지", "가로", "세로", "프레임", "재료",
        }
        for line in info.get("textLines") or []:
            v = str(line or "").strip()
            if not v or v.lower() in bad_lines:
                continue
            vl = v.lower()
            if any(x in vl for x in ("quality", "lower priority", "priority", "fast", "veo 3.1", "veo 2", "veo3.1", "veo2")):
                continue
            if ("nano banana" in vl or "동영상" in vl or "이미지" in vl) and not any(x in vl for x in ("x1", "x2", "x3", "x4")):
                continue
            if len(v) > 48:
                continue
            esc = v.replace("'", "\\'")
            if role:
                return f"[role='{role}']:has-text('{esc}')"
            return f"{tag}:has-text('{esc}')"
        return ""

    def _ensure_prompt_generation_panel_open(self, input_locator=None, profile="prompt"):
        found, used = self._resolve_prompt_preset_controls(input_locator=input_locator, profile=profile)
        visible_count = sum(1 for x in found.values() if x is not None)
        opener = None
        opener_desc = None
        opened_now = False
        if visible_count >= 1:
            return found, used, opener, opener_desc, opened_now

        opener, opener_desc = self._resolve_prompt_preset_toggle_button(input_locator=input_locator)
        if opener is not None:
            ok = self._click_with_actor_fallback(opener, "생성 옵션 패널 열기")
            if ok:
                opened_now = True
                self.log(f"📂 생성 옵션 패널 열기: {opener_desc or '토글 버튼'}")
                time.sleep(0.6)
                found, used = self._resolve_prompt_preset_controls(input_locator=input_locator, profile=profile)
        return found, used, opener, opener_desc, opened_now

    def _resolve_saved_panel_button(self, profile, state):
        selector = str(self.cfg.get(self._panel_selector_key(profile, state), "") or "").strip()
        if not selector or not self.page:
            return None, selector
        other_state = "video" if state == "image" else "image"
        other_selector = str(self.cfg.get(self._panel_selector_key(profile, other_state), "") or "").strip()
        if other_selector and selector == other_selector:
            return None, selector
        loc, used = self._resolve_best_locator([selector], timeout_ms=1200, prefer_enabled=False)
        return loc, used or selector

    def _resolve_saved_panel_button_any_profile(self, state, profile="prompt"):
        primary = "asset" if str(profile).strip().lower() == "asset" else "prompt"
        order = (primary, "prompt" if primary == "asset" else "asset")
        for key in order:
            image_sel = str(self.cfg.get(self._panel_selector_key(key, "image"), "") or "").strip()
            video_sel = str(self.cfg.get(self._panel_selector_key(key, "video"), "") or "").strip()
            if image_sel and video_sel and image_sel == video_sel:
                continue
            loc, used = self._resolve_saved_panel_button(key, state)
            if loc is not None:
                return loc, used, key
        return None, "", primary

    def _infer_media_state_from_locator(self, locator):
        if locator is None:
            return None
        meta = self._locator_meta_text(locator)
        if not meta:
            meta = ""
        if any(x in meta for x in ("대시보드", "dashboard", "카메라", "camera", "삽입", "삭제", "확장", "보기", "view", "검색", "정렬", "필터")):
            return None
        if any(x in meta for x in ("nano banana", "image", "이미지")):
            return "image"
        if any(x in meta for x in ("동영상", "영상", " video ", "video", "videocam")):
            return "video"
        return None

    def _resolve_current_media_panel_button(self, input_locator=None, profile="prompt"):
        opener, opener_desc = self._resolve_prompt_preset_toggle_button(input_locator=input_locator)
        opener_state = self._infer_media_state_from_locator(opener)
        if opener is not None:
            return opener, opener_desc or "", opener_state
        opener, opener_desc = self._resolve_prompt_preset_toggle_button_global(timeout_ms=900)
        opener_state = self._infer_media_state_from_locator(opener)
        if opener is not None:
            return opener, opener_desc or "", opener_state
        for state in ("image", "video"):
            loc, used, _profile_used = self._resolve_saved_panel_button_any_profile(state, profile=profile)
            if loc is not None:
                return loc, used or "", state
        return None, "", None

    def _switch_media_state(self, desired_state, input_locator=None, profile="prompt"):
        profile = "asset" if str(profile).strip().lower() == "asset" else "prompt"
        desired_state = "video" if str(desired_state).strip().lower() == "video" else "image"
        try:
            if input_locator is not None:
                input_locator.scroll_into_view_if_needed(timeout=900)
        except Exception:
            pass
        open_loc, open_desc, inferred_state = self._resolve_current_media_panel_button(input_locator=input_locator, profile=profile)
        current_state = inferred_state or self.current_media_state or "image"
        if (inferred_state is not None) and current_state == desired_state:
            self.log(f"ℹ️ 생성 모드 유지: {desired_state}")
            self.current_media_state = desired_state
            self.cfg["current_media_state"] = desired_state
            self.save_config()
            self.refresh_detected_media_state(ensure_session=False)
            return True

        if open_loc is None:
            self.log(f"⚠️ 현재 생성 모드 버튼을 찾지 못했습니다. ({profile}/{current_state})")
            return False
        if not self._click_with_actor_fallback(open_loc, f"{current_state} 패널 열기"):
            self.log(f"⚠️ {current_state} 패널 열기 실패")
            return False
        time.sleep(0.5)

        media_loc, media_sel = self._resolve_panel_media_target(
            desired_state,
            input_locator=input_locator,
            opener_locator=open_loc,
            profile=profile,
            timeout_ms=3600,
            dump_stage_label=f"{profile} {current_state}->{desired_state}",
        )
        if media_loc is None:
            self.log(f"⚠️ {desired_state} 선택 버튼을 찾지 못했습니다.")
            return False
        if not self._click_with_actor_fallback(media_loc, f"{desired_state} 선택"):
            self.log(f"⚠️ {desired_state} 선택 클릭 실패")
            return False
        self.log(f"🎛️ 생성 모드 전환: {current_state} -> {desired_state} ({media_sel or '텍스트 버튼'})")
        time.sleep(0.5)

        close_loc, close_desc, inferred_close_state = self._resolve_current_media_panel_button(input_locator=input_locator, profile=profile)
        if close_loc is None:
            close_loc, _close_sel, _close_profile = self._resolve_saved_panel_button_any_profile(desired_state, profile=profile)
        if close_loc is not None:
            if not self._click_with_actor_fallback(close_loc, f"{desired_state} 패널 닫기"):
                self.log(f"⚠️ {desired_state} 패널 닫기 실패")
            else:
                time.sleep(0.4)
        else:
            self._close_prompt_generation_panel(input_locator=input_locator, opener=None, opener_desc=close_desc or inferred_close_state or desired_state)
        verified_state = self.refresh_detected_media_state(ensure_session=False, input_locator=input_locator, profile=profile, write_log=True)
        if verified_state and verified_state != desired_state:
            self.log(f"⚠️ 생성 모드 전환 검증 실패: 기대={desired_state} / 감지={verified_state}")
            return False
        self.current_media_state = desired_state
        self.cfg["current_media_state"] = desired_state
        self.save_config()
        return True

    def _close_prompt_generation_panel(self, input_locator=None, opener=None, opener_desc=None):
        target = opener
        label = opener_desc or "생성 옵션 패널 닫기"
        if target is None:
            target, opener_desc = self._resolve_prompt_preset_toggle_button(input_locator=input_locator)
            label = opener_desc or label
        if target is None:
            try:
                self.page.keyboard.press("Escape")
                self.log("📁 생성 옵션 패널 닫기: Escape 폴백")
                time.sleep(0.35)
                return True
            except Exception:
                return False
        ok = self._click_with_actor_fallback(target, "생성 옵션 패널 닫기")
        if ok:
            self.log(f"📁 생성 옵션 패널 닫기: {label}")
            time.sleep(0.35)
            return True
        try:
            self.page.keyboard.press("Escape")
            self.log("📁 생성 옵션 패널 닫기: Escape 폴백")
            time.sleep(0.35)
            return True
        except Exception:
            return False

    def _read_input_text(self, input_locator):
        if input_locator is None:
            return ""
        try:
            val = input_locator.evaluate(
                """(el) => {
                    if (!el) return "";
                    if ("value" in el && typeof el.value === "string") return el.value;
                    return (el.innerText || el.textContent || "");
                }"""
            )
            return (val or "").strip()
        except Exception:
            return ""

    def _is_generation_indicator_visible(self):
        if not self.page:
            return False
        indicators = [
            "button:has-text('생성 중')",
            "button:has-text('처리 중')",
            "button:has-text('중지')",
            "button:has-text('취소')",
            "button:has-text('Stop')",
            "button:has-text('Cancel')",
            "text=/생성 중|Generating/i",
        ]
        for sel in indicators:
            try:
                loc = self.page.locator(sel).first
                if loc.count() > 0 and loc.is_visible(timeout=250):
                    return True
            except Exception:
                continue
        return False

    def _confirm_submission_started(self, input_locator, before_text, timeout_sec=12):
        """
        제출 직후 실제로 동작이 시작됐는지 검증.
        """
        end_ts = time.time() + max(2, timeout_sec)
        before_text = (before_text or "").strip()
        while time.time() < end_ts:
            if self._is_generation_indicator_visible():
                return True
            current = self._read_input_text(input_locator)
            # 입력창이 비워졌거나 크게 변하면 제출 성공으로 판단
            if before_text and current != before_text:
                if len(current) <= max(2, int(len(before_text) * 0.4)):
                    return True
                # 완전히 같은 프롬프트가 아니면 일부 변형도 성공으로 인정
                if current[:40] != before_text[:40]:
                    return True
            time.sleep(0.5)
        return False

    def _is_input_visible(self, input_selector):
        if not self.page:
            return False
        loc, _ = self._resolve_prompt_input_locator(input_selector, timeout_ms=1200)
        return loc is not None

    def _wait_until_input_visible(self, input_selector, timeout_sec=18):
        if not self.page:
            return False
        end_ts = time.time() + max(1, timeout_sec)
        while time.time() < end_ts:
            if self._is_input_visible(input_selector):
                return True
            time.sleep(0.6)
        return False

    def _try_open_new_project_if_needed(self, input_selector):
        if not self.page:
            return False
        if self._is_input_visible(input_selector):
            return True
        if not self.cfg.get("auto_open_new_project", True):
            return False

        custom_selector = (self.cfg.get("new_project_selector") or "").strip()
        candidates = []
        if custom_selector:
            candidates.append(custom_selector)

        candidates.extend([
            "button:has-text('새 프로젝트')",
            "button:has-text('새 프로젝트 만들기')",
            "[role='button']:has-text('새 프로젝트')",
            "a:has-text('새 프로젝트')",
            "button:has-text('Create')",
            "[role='button']:has-text('Create')",
            "button:has-text('New project')",
            "button:has-text('New Project')",
            "button:has-text('Create new')",
            "[role='button']:has-text('New project')",
            "a:has-text('New project')",
        ])

        clicked = False
        for sel in candidates:
            try:
                loc = self.page.locator(sel).first
                if loc.count() <= 0:
                    continue
                if not loc.is_visible(timeout=1000):
                    continue
                self.log(f"🧭 새 프로젝트 버튼 감지: {sel}")
                try:
                    self.actor.move_to_locator(loc, label="새 프로젝트 버튼")
                    self.actor.smart_click(label="새 프로젝트 버튼 클릭")
                except Exception:
                    loc.click(timeout=3000)
                try:
                    # 랜덤 클릭 실패 대비해서 Playwright 직접 클릭 한 번 더 시도
                    loc.click(timeout=2500)
                except Exception:
                    pass
                clicked = True
                break
            except Exception:
                continue

        if not clicked:
            return False

        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass
        return self._wait_until_input_visible(input_selector, timeout_sec=20)

    def _pick_input_selector_by_dom_heuristic(self):
        if not self.page:
            return None
        try:
            return self.page.evaluate(
                """() => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const rect = el.getBoundingClientRect();
                        if (rect.width < 20 || rect.height < 12) return false;
                        const style = window.getComputedStyle(el);
                        return style.visibility !== 'hidden' && style.display !== 'none' && style.opacity !== '0';
                    };
                    const all = Array.from(document.querySelectorAll("textarea, [contenteditable='true'], [role='textbox']"));
                    const visible = all.filter(isVisible);
                    if (!visible.length) return null;

                    const score = (el) => {
                        const tag = (el.tagName || '').toLowerCase();
                        const ph = (el.getAttribute('placeholder') || '').toLowerCase();
                        const ar = (el.getAttribute('aria-label') || '').toLowerCase();
                        const ce = el.getAttribute('contenteditable');
                        const r = el.getBoundingClientRect();
                        let s = r.width * r.height;
                        if (tag === 'textarea') s += 100000;
                        if (ce === 'true' || ce === 'plaintext-only') s += 20000;
                        if (ph.includes('무엇을 만들') || ar.includes('무엇을 만들')) s += 120000;
                        if (ph.includes('프롬프트') || ar.includes('프롬프트')) s += 90000;
                        if (ph.includes('prompt') || ph.includes('message') || ph.includes('메시지')) s += 80000;
                        if (ar.includes('prompt') || ar.includes('message') || ar.includes('메시지')) s += 80000;
                        if (ph.includes('asset') || ph.includes('search') || ph.includes('에셋') || ph.includes('검색')) s -= 220000;
                        if (ar.includes('asset') || ar.includes('search') || ar.includes('에셋') || ar.includes('검색')) s -= 220000;
                        return s;
                    };
                    visible.sort((a, b) => score(b) - score(a));
                    const el = visible[0];

                    const id = el.getAttribute('id');
                    if (id) return `#${CSS.escape(id)}`;

                    const name = el.getAttribute('name');
                    if (name) {
                        const tag = el.tagName.toLowerCase();
                        return `${tag}[name="${name.replace(/"/g, '\\\\"')}"]`;
                    }

                    const ar = el.getAttribute('aria-label');
                    if (ar) {
                        const tag = el.tagName.toLowerCase();
                        return `${tag}[aria-label*="${ar.replace(/"/g, '\\\\"')}"]`;
                    }

                    const ph = el.getAttribute('placeholder');
                    if (ph) {
                        const tag = el.tagName.toLowerCase();
                        return `${tag}[placeholder*="${ph.replace(/"/g, '\\\\"')}"]`;
                    }

                    const tag = el.tagName.toLowerCase();
                    if (el.getAttribute('contenteditable') === 'true') return `${tag}[contenteditable='true']`;
                    if (el.getAttribute('contenteditable') === 'plaintext-only') return `${tag}[contenteditable='plaintext-only']`;
                    if (el.getAttribute('role') === 'textbox') return `${tag}[role='textbox']`;
                    return tag;
                }"""
            )
        except Exception:
            return None

    def on_auto_detect_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 탐색을 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._auto_detect_selectors_worker()

    def _auto_detect_selectors_worker(self):
        try:
            self.update_status_label("🔍 selector 자동 탐색 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url:
                if start_url not in (self.page.url or ""):
                    self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(random.uniform(1.0, 2.5))
            input_hint = (self.cfg.get("input_selector") or "").strip() or "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [contenteditable='true'], [role='textbox']"
            self._try_open_new_project_if_needed(input_hint)

            submit_candidates = self._submit_candidates()

            found_input_loc, found_input = self._resolve_prompt_input_locator(
                self.cfg.get("input_selector", ""),
                timeout_ms=1400,
            )
            if not found_input:
                found_input = self._pick_input_selector_by_dom_heuristic()
                if found_input:
                    found_input_loc, _ = self._resolve_best_locator(
                        self._normalize_candidate_list(found_input),
                        timeout_ms=1200,
                    )
            found_submit = None
            # 입력창을 찾은 경우에만 제출 버튼을 확정(홈 화면 Create 오탐 방지)
            if found_input:
                _, found_submit = self._resolve_best_locator(
                    submit_candidates,
                    near_locator=found_input_loc,
                    timeout_ms=1200,
                )
                if not found_submit:
                    # 근접 기준으로 못 찾으면 일반 visible 기준으로 1회 폴백
                    _, found_submit = self._resolve_visible_locator(submit_candidates, timeout_ms=1200)

            if found_input:
                self.input_selector_var.set(found_input)
                self.cfg["input_selector"] = found_input
            if found_submit:
                self.submit_selector_var.set(found_submit)
                self.cfg["submit_selector"] = found_submit
            self.save_config()
            self.lbl_coords.config(text=self._get_coord_text())
            if found_input and found_submit:
                self.log(f"✅ 자동 탐색 성공 | 입력: {found_input} | 제출: {found_submit}")
                self.update_status_label("✅ selector 자동 탐색 완료", self.color_success)
            else:
                self.log(f"⚠️ 자동 탐색 부분 성공 | 입력: {found_input or '미탐지'} | 제출: {found_submit or '미탐지'}")
                self.update_status_label("⚠️ 일부 selector 미탐지", self.color_error)
        except Exception as e:
            self.log(f"❌ selector 자동 탐색 실패: {e}")
            self.update_status_label("❌ selector 자동 탐색 실패", self.color_error)

    def on_test_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 테스트를 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._test_selectors_worker()

    def _test_selectors_worker(self):
        try:
            self.update_status_label("🧪 selector 테스트 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            input_selector = (self.cfg.get("input_selector") or "").strip()
            submit_selector = (self.cfg.get("submit_selector") or "").strip()

            def _check_once():
                try:
                    input_loc, _ = self._resolve_prompt_input_locator(
                        input_selector,
                        timeout_ms=2200,
                    )
                    input_ok_local = input_loc is not None
                except Exception:
                    input_ok_local = False
                try:
                    submit_loc, _ = self._resolve_best_locator(
                        self._normalize_candidate_list(submit_selector) or self._submit_candidates(),
                        near_locator=input_loc if input_ok_local else None,
                        timeout_ms=2200,
                    )
                    submit_ok_local = submit_loc is not None
                except Exception:
                    submit_ok_local = False
                return input_ok_local, submit_ok_local

            # 1차: 현재 화면에서 바로 검사 (사용자가 이미 편집화면일 수 있음)
            input_ok, submit_ok = _check_once()

            # 2차: 실패 시에만 시작 URL 이동 + 새 프로젝트 자동 진입 시도 후 재검사
            if not (input_ok and submit_ok):
                if start_url:
                    self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                self._try_open_new_project_if_needed(
                    input_selector or "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [contenteditable='true'], [role='textbox']"
                )
                # 동적 렌더링 대기 후 재검사
                for _ in range(6):
                    time.sleep(0.7)
                    input_ok, submit_ok = _check_once()
                    if input_ok and submit_ok:
                        break

            self.log(
                f"🧪 selector 테스트 결과 | URL({self.page.url}) | 입력({input_selector}): {'OK' if input_ok else 'FAIL'} | "
                f"제출({submit_selector}): {'OK' if submit_ok else 'FAIL'}"
            )
            if input_ok and submit_ok:
                self.update_status_label("✅ selector 테스트 통과", self.color_success)
            else:
                self.update_status_label("⚠️ selector 확인 필요", self.color_error)
        except Exception as e:
            self.log(f"❌ selector 테스트 실패: {e}")
            self.update_status_label("❌ selector 테스트 실패", self.color_error)

    def on_auto_detect_prompt_preset_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 탐색을 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._auto_detect_prompt_preset_selectors_worker()

    def on_auto_detect_asset_prompt_preset_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 탐색을 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._auto_detect_asset_prompt_preset_selectors_worker()

    def _auto_detect_prompt_preset_selectors_worker(self):
        try:
            self._open_action_log("prompt_preset_detect")
            self.update_status_label("🔍 생성 옵션 selector 자동 탐색 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url:
                if start_url not in (self.page.url or ""):
                    self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(random.uniform(1.0, 2.5))

            input_hint = (self.cfg.get("input_selector") or "").strip() or "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [contenteditable='true'], [role='textbox']"
            self._try_open_new_project_if_needed(input_hint)
            input_locator, _ = self._resolve_prompt_input_locator(input_hint, timeout_ms=2200)
            if input_locator is None:
                self.log("ℹ️ 프롬프트 입력칸 미탐지 상태 - 생성 옵션만 전역 탐색으로 계속 진행합니다.")

            image_panel_selector, video_panel_selector, video_media_selector = self._auto_detect_media_panel_selectors(
                input_locator=input_locator,
                profile="prompt",
            )

            self.log(
                f"🔍 생성 옵션 자동탐색 결과 | 이미지 패널({image_panel_selector})=OK | "
                f"동영상 패널({video_panel_selector})=OK | Video({video_media_selector or '-'})=OK"
            )
            self.update_status_label("✅ 생성 옵션 selector 자동찾기 완료", self.color_success)
        except Exception as e:
            self.log(f"❌ 생성 옵션 selector 자동찾기 실패: {e}")
            self.update_status_label("❌ 생성 옵션 selector 자동찾기 실패", self.color_error)
        finally:
            self._close_action_log()

    def _auto_detect_asset_prompt_preset_selectors_worker(self):
        try:
            self._open_action_log("asset_preset_detect")
            self.update_status_label("🔍 S 생성 옵션 selector 자동 탐색 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url:
                if start_url not in (self.page.url or ""):
                    self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(random.uniform(1.0, 2.5))

            input_hint = (self.cfg.get("input_selector") or "").strip() or "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [contenteditable='true'], [role='textbox']"
            self._try_open_new_project_if_needed(input_hint)
            input_locator, _ = self._resolve_prompt_input_locator(input_hint, timeout_ms=2200)
            if input_locator is None:
                self.log("ℹ️ S입력칸 미탐지 상태 - 생성 옵션만 전역 탐색으로 계속 진행합니다.")

            image_panel_selector, video_panel_selector, video_media_selector = self._auto_detect_media_panel_selectors(
                input_locator=input_locator,
                profile="asset",
            )

            self.log(
                f"🔍 S 생성 옵션 자동탐색 결과 | 이미지 패널({image_panel_selector})=OK | "
                f"동영상 패널({video_panel_selector})=OK | Video({video_media_selector or '-'})=OK"
            )
            self.update_status_label("✅ S 생성 옵션 selector 자동찾기 완료", self.color_success)
        except Exception as e:
            self.log(f"❌ S 생성 옵션 selector 자동찾기 실패: {e}")
            self.update_status_label("❌ S 생성 옵션 selector 자동찾기 실패", self.color_error)
        finally:
            self._close_action_log()

    def on_test_prompt_preset_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 테스트를 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._test_prompt_preset_selectors_worker()

    def on_test_prompt_image_to_video(self):
        self._test_media_transition_button(profile="prompt", from_state="image", to_state="video", title="프롬프트 이미지→동영상")

    def on_test_prompt_video_to_image(self):
        self._test_media_transition_button(profile="prompt", from_state="video", to_state="image", title="프롬프트 동영상→이미지")

    def on_test_asset_prompt_preset_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 테스트를 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._test_asset_prompt_preset_selectors_worker()

    def on_test_asset_image_to_video(self):
        self._test_media_transition_button(profile="asset", from_state="image", to_state="video", title="S자동화 이미지→동영상")

    def on_test_asset_video_to_image(self):
        self._test_media_transition_button(profile="asset", from_state="video", to_state="image", title="S자동화 동영상→이미지")

    def _test_media_transition_button(self, profile="prompt", from_state="image", to_state="video", title="생성 옵션 전환"):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 테스트를 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        try:
            self.on_option_toggle()
            self._open_action_log(f"{profile}_media_switch_test")
            self.update_status_label(f"🧪 {title} 테스트 중...", self.color_info)
            ok = self._run_media_transition_test(profile=profile, from_state=from_state, to_state=to_state)
            self.log(f"🧪 {title} 테스트 | {'OK' if ok else 'FAIL'}")
            self.update_status_label(f"{'✅' if ok else '⚠️'} {title} 테스트 {'통과' if ok else '확인 필요'}", self.color_success if ok else self.color_error)
        except Exception as e:
            self.log(f"❌ {title} 테스트 실패: {e}")
            self.update_status_label(f"❌ {title} 테스트 실패", self.color_error)
        finally:
            self._close_action_log()

    def _test_prompt_preset_selectors_worker(self):
        try:
            self._open_action_log("prompt_preset_test")
            self.update_status_label("🧪 생성 옵션 테스트 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url:
                if start_url not in (self.page.url or ""):
                    self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(random.uniform(1.0, 2.5))

            input_hint = (self.cfg.get("input_selector") or "").strip() or "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [contenteditable='true'], [role='textbox']"
            self._try_open_new_project_if_needed(input_hint)
            input_locator, _ = self._resolve_prompt_input_locator(input_hint, timeout_ms=2200)
            if input_locator is None:
                self.log("ℹ️ 프롬프트 입력칸 미탐지 상태 - 생성 옵션만 전역 탐색으로 테스트합니다.")

            detected_state = self.refresh_detected_media_state(
                ensure_session=False,
                input_locator=input_locator,
                profile="prompt",
                write_log=True,
            )
            if detected_state not in ("image", "video"):
                raise RuntimeError("현재 생성 기본값을 읽지 못했습니다.")
            target_state = "video" if detected_state == "image" else "image"
            first_ok = self._switch_media_state(target_state, input_locator=input_locator, profile="prompt")
            second_ok = self._switch_media_state(detected_state, input_locator=input_locator, profile="prompt")

            self.log(
                f"🧪 생성 옵션 테스트 | 현재={detected_state} | "
                f"{detected_state}→{target_state}={'OK' if first_ok else 'FAIL'} | "
                f"{target_state}→{detected_state}={'OK' if second_ok else 'FAIL'}"
            )
            if first_ok and second_ok:
                self.update_status_label("✅ 생성 옵션 테스트 통과", self.color_success)
            else:
                self.update_status_label("⚠️ 생성 옵션 확인 필요", self.color_error)
        except Exception as e:
            self.log(f"❌ 생성 옵션 테스트 실패: {e}")
            self.update_status_label("❌ 생성 옵션 테스트 실패", self.color_error)
        finally:
            self._close_action_log()

    def _test_asset_prompt_preset_selectors_worker(self):
        try:
            self._open_action_log("asset_preset_test")
            self.update_status_label("🧪 S 생성 옵션 테스트 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url:
                if start_url not in (self.page.url or ""):
                    self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(random.uniform(1.0, 2.5))

            input_hint = (self.cfg.get("input_selector") or "").strip() or "#PINHOLE_TEXT_AREA_ELEMENT_ID, textarea, [contenteditable='true'], [role='textbox']"
            self._try_open_new_project_if_needed(input_hint)
            input_locator, _ = self._resolve_prompt_input_locator(input_hint, timeout_ms=2200)
            if input_locator is None:
                self.log("ℹ️ S입력칸 미탐지 상태 - 생성 옵션만 전역 탐색으로 테스트합니다.")

            detected_state = self.refresh_detected_media_state(
                ensure_session=False,
                input_locator=input_locator,
                profile="asset",
                write_log=True,
            )
            if detected_state not in ("image", "video"):
                raise RuntimeError("현재 S 생성 기본값을 읽지 못했습니다.")
            target_state = "video" if detected_state == "image" else "image"
            first_ok = self._switch_media_state(target_state, input_locator=input_locator, profile="asset")
            second_ok = self._switch_media_state(detected_state, input_locator=input_locator, profile="asset")

            self.log(
                f"🧪 S 생성 옵션 테스트 | 현재={detected_state} | "
                f"{detected_state}→{target_state}={'OK' if first_ok else 'FAIL'} | "
                f"{target_state}→{detected_state}={'OK' if second_ok else 'FAIL'}"
            )
            if first_ok and second_ok:
                self.update_status_label("✅ S 생성 옵션 테스트 통과", self.color_success)
            else:
                self.update_status_label("⚠️ S 생성 옵션 확인 필요", self.color_error)
        except Exception as e:
            self.log(f"❌ S 생성 옵션 테스트 실패: {e}")
            self.update_status_label("❌ S 생성 옵션 테스트 실패", self.color_error)
        finally:
            self._close_action_log()

    def on_auto_detect_asset_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 탐색을 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._auto_detect_asset_selectors_worker()

    def _auto_detect_asset_selectors_worker(self):
        try:
            self.update_status_label("🔍 에셋 selector 자동 탐색 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url and start_url not in (self.page.url or ""):
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(1.0, 2.3))
            self._prepare_page_for_selector_detection()
            self._ensure_asset_workspace_visible(timeout_sec=4)

            start_loc, start_sel = self._resolve_best_locator_with_scroll(
                self._asset_start_button_candidates(),
                timeout_ms=2200,
                prefer_enabled=False,
            )
            search_candidates = self._asset_search_button_candidates() + [
                "text=에셋 검색",
                "text=Asset search",
                "text=Search assets",
            ]
            search_loc, search_sel = self._resolve_best_locator_with_scroll(
                search_candidates,
                timeout_ms=2200,
                prefer_enabled=False,
                ratios=(0.0, 0.12, 0.24, 0.36, 0.50),
            )
            if start_loc is None:
                start_loc, start_sel = self._resolve_text_locator_any_frame(["시작", "Start"], timeout_ms=1000)
            if start_loc is not None:
                try:
                    self._click_with_actor_fallback(start_loc, "자동탐색 시작 버튼")
                    self.actor.random_action_delay("자동탐색 시작 후 대기", 0.4, 1.1)
                except Exception:
                    pass
            if search_loc is None:
                search_loc, search_sel = self._resolve_text_locator_any_frame(
                    ["에셋 검색", "Asset search", "Search assets"],
                    timeout_ms=1200,
                )

            input_loc, input_sel = self._resolve_best_locator_with_scroll(
                self._asset_search_input_candidates(),
                timeout_ms=1200,
                prefer_enabled=False,
                ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
            )
            if (input_loc is None) and (search_loc is not None):
                try:
                    search_loc.click(timeout=2000)
                    self.actor.random_action_delay("에셋 검색 입력칸 표시 대기", 0.3, 1.2)
                except Exception:
                    pass
                input_loc, input_sel = self._resolve_best_locator_with_scroll(
                    self._asset_search_input_candidates(),
                    timeout_ms=2200,
                    prefer_enabled=False,
                    ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
                )

            if start_sel:
                self.cfg["asset_start_selector"] = start_sel
                if hasattr(self, "asset_start_selector_var"):
                    self.asset_start_selector_var.set(start_sel)
            if search_sel:
                self.cfg["asset_search_button_selector"] = search_sel
                if hasattr(self, "asset_search_btn_selector_var"):
                    self.asset_search_btn_selector_var.set(search_sel)
            if input_sel:
                self.cfg["asset_search_input_selector"] = input_sel
                if hasattr(self, "asset_search_input_selector_var"):
                    self.asset_search_input_selector_var.set(input_sel)
            self.save_config()

            self.log(
                "🔍 에셋 selector 자동탐색 결과 | "
                f"시작: {start_sel or '미탐지'} | 에셋검색: {search_sel or '미탐지'} | 검색입력: {input_sel or '미탐지'}"
            )
            if start_sel and input_sel:
                self.update_status_label("✅ 에셋 selector 자동탐색 완료", self.color_success)
            else:
                self.update_status_label("⚠️ 에셋 selector 일부 미탐지", self.color_error)
        except Exception as e:
            self.log(f"❌ 에셋 selector 자동탐색 실패: {e}")
            self.update_status_label("❌ 에셋 selector 자동탐색 실패", self.color_error)

    def on_test_asset_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 테스트를 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._test_asset_selectors_worker()

    def _test_asset_selectors_worker(self):
        try:
            self.update_status_label("🧪 에셋 selector 테스트 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url and start_url not in (self.page.url or ""):
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(0.8, 1.8))
            self._prepare_page_for_selector_detection()
            self._ensure_asset_workspace_visible(timeout_sec=4)
            self._open_asset_search_surface_for_detection()

            start_candidates = self._normalize_candidate_list(self.cfg.get("asset_start_selector", "")) or self._asset_start_button_candidates()
            search_candidates = self._normalize_candidate_list(self.cfg.get("asset_search_button_selector", "")) or self._asset_search_button_candidates()
            input_candidates = self._normalize_candidate_list(self.cfg.get("asset_search_input_selector", "")) or self._asset_search_input_candidates()

            start_loc, start_sel = self._resolve_best_locator_with_scroll(start_candidates, timeout_ms=2200, prefer_enabled=False)
            search_loc, search_sel = self._resolve_best_locator_with_scroll(
                search_candidates + ["text=에셋 검색", "text=Asset search"],
                timeout_ms=2200,
                prefer_enabled=False,
                ratios=(0.0, 0.12, 0.24, 0.36, 0.50),
            )
            if start_loc is None:
                start_loc, start_sel = self._resolve_text_locator_any_frame(["시작", "Start"], timeout_ms=1000)
            if search_loc is None:
                search_loc, search_sel = self._resolve_text_locator_any_frame(
                    ["에셋 검색", "Asset search", "Search assets"],
                    timeout_ms=1200,
                )

            input_loc, input_sel = self._resolve_best_locator_with_scroll(
                input_candidates,
                timeout_ms=1800,
                prefer_enabled=False,
                ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
            )
            if (input_loc is None) and (search_loc is not None):
                try:
                    search_loc.click(timeout=2000)
                except Exception:
                    pass
                self.actor.random_action_delay("검색 입력칸 확인 대기", 0.3, 1.0)
                input_loc, input_sel = self._resolve_best_locator_with_scroll(
                    input_candidates,
                    timeout_ms=2200,
                    prefer_enabled=False,
                    ratios=(0.0, 0.18, 0.30, 0.42, 0.56),
                )

            start_ok = start_loc is not None
            search_ok = search_loc is not None
            input_ok = input_loc is not None
            # 일부 UI는 버튼 없이 검색 입력칸이 바로 노출되므로 search 버튼은 선택 항목으로 처리
            flow_ok = start_ok and input_ok

            self.log(
                f"🧪 에셋 selector 테스트 | 시작({start_sel or start_candidates[0] if start_candidates else '-'})={'OK' if start_ok else 'FAIL'} | "
                f"에셋검색({search_sel or search_candidates[0] if search_candidates else '-'})={'OK' if search_ok else 'FAIL'} | "
                f"검색입력({input_sel or input_candidates[0] if input_candidates else '-'})={'OK' if input_ok else 'FAIL'}"
            )
            if flow_ok:
                self.update_status_label("✅ 에셋 selector 테스트 통과", self.color_success)
            else:
                self.update_status_label("⚠️ 에셋 selector 확인 필요", self.color_error)
        except Exception as e:
            self.log(f"❌ 에셋 selector 테스트 실패: {e}")
            self.update_status_label("❌ 에셋 selector 테스트 실패", self.color_error)

    def on_auto_detect_image_download_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 탐색을 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._auto_detect_download_selectors_worker("image")

    def on_auto_detect_video_download_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 탐색을 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._auto_detect_download_selectors_worker("video")

    def _auto_detect_download_selectors_worker(self, mode):
        mode = "image" if mode == "image" else "video"
        mode_txt = "이미지" if mode == "image" else "영상"
        opened_here = False
        try:
            if not self.action_log_fp:
                self._open_action_log("download_trace")
                opened_here = True
            self.update_status_label(f"🔍 {mode_txt} 다운로드 selector 자동 탐색 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url and start_url not in (self.page.url or ""):
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(0.8, 1.6))

            items = self._build_download_items()
            tag = items[0] if items else "S01"
            quality = self._download_quality(mode)
            result = self._run_single_download_flow(mode=mode, tag=tag, quality=quality, dry_run=True, wait_sec=25)
            self._apply_download_used_selectors(mode, result.get("used", {}))
            self.save_config()
            used = result.get("used", {})
            self.log(
                f"🔍 {mode_txt} 다운로드 selector 자동탐색 결과 | "
                f"검색입력: {used.get('search_input') or '미탐지'} | "
                f"필터: {used.get('filter') or '미탐지'} | "
                f"카드: {used.get('card') or '미탐지'} | "
                f"더보기: {used.get('more') or '미탐지'} | "
                f"다운로드: {used.get('menu') or '미탐지'} | "
                f"품질: {used.get('quality') or '미탐지'}"
            )
            self.update_status_label(f"✅ {mode_txt} 다운로드 selector 자동탐색 완료", self.color_success)
        except Exception as e:
            self.log(f"❌ {mode_txt} 다운로드 selector 자동탐색 실패: {e}")
            self.update_status_label(f"❌ {mode_txt} 다운로드 selector 자동탐색 실패", self.color_error)
        finally:
            if opened_here:
                self._close_action_log()

    def on_test_image_download_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 테스트를 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._test_download_selectors_worker("image")

    def on_test_video_download_selectors(self):
        if self.running:
            messagebox.showwarning("안내", "자동화 실행 중에는 selector 테스트를 할 수 없습니다.\n먼저 중지 후 시도해주세요.")
            return
        self.on_option_toggle()
        self._test_download_selectors_worker("video")

    def _test_download_selectors_worker(self, mode):
        mode = "image" if mode == "image" else "video"
        mode_txt = "이미지" if mode == "image" else "영상"
        opened_here = False
        try:
            if not self.action_log_fp:
                self._open_action_log("download_trace")
                opened_here = True
            self.update_status_label(f"🧪 {mode_txt} 다운로드 selector 테스트 중...", self.color_info)
            self._ensure_browser_session()
            self.actor.set_page(self.page)

            start_url = (self.cfg.get("start_url") or "").strip()
            if start_url and start_url not in (self.page.url or ""):
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(0.8, 1.6))

            items = self._build_download_items()
            default_tag = items[0] if items else "S01"
            tag = simpledialog.askstring(
                f"{mode_txt} 다운로드 테스트",
                "테스트할 태그를 입력하세요. (예: S01)",
                initialvalue=default_tag,
                parent=self.root,
            )
            if tag is None:
                self.update_status_label(f"ℹ️ {mode_txt} 다운로드 테스트 취소됨", self.color_info)
                return
            tag = (tag or "").strip()
            if not tag:
                messagebox.showwarning("입력 오류", "태그를 입력해주세요.")
                self.update_status_label(f"⚠️ {mode_txt} 다운로드 테스트 취소", self.color_error)
                return

            quality = self._download_quality(mode)
            result = self._run_single_download_flow(mode=mode, tag=tag, quality=quality, dry_run=False, wait_sec=60, is_test=True)
            self._apply_download_used_selectors(mode, result.get("used", {}))
            self.save_config()
            self.log(
                f"🧪 {mode_txt} 다운로드 selector 테스트 성공 | 태그: {tag} | 품질: {quality} | "
                f"파일: {result.get('file') or '-'} | 경로: {result.get('path') or '-'}"
            )
            self.update_status_label(f"✅ {mode_txt} 다운로드 selector 테스트 통과", self.color_success)
        except Exception as e:
            self.log(f"❌ {mode_txt} 다운로드 selector 테스트 실패: {e}")
            self.update_status_label(f"❌ {mode_txt} 다운로드 selector 테스트 실패", self.color_error)
        finally:
            if opened_here:
                self._close_action_log()

    def on_open_relay_selector(self):
        slots = self.cfg.get("prompt_slots", [])
        if not slots:
            messagebox.showwarning("주의", "선택할 문서가 없습니다.")
            return

        selected = set(self._normalize_relay_selected_slots(self.cfg.get("relay_selected_slots", [])))
        win = tk.Toplevel(self.root)
        win.title("이어달리기 문서 선택")
        win.transient(self.root)
        win.grab_set()
        win.configure(bg="#FFFFFF")
        win.geometry("420x520")

        tk.Label(win, text="실행할 문서를 체크하세요", font=("Malgun Gothic", 11, "bold"), bg="#FFFFFF").pack(anchor="w", padx=12, pady=(12, 6))

        list_frame = tk.Frame(win, bg="#FFFFFF")
        list_frame.pack(fill="both", expand=True, padx=12, pady=6)

        canvas = tk.Canvas(list_frame, bg="#FFFFFF", highlightthickness=0)
        scrolly = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="#FFFFFF")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrolly.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrolly.pack(side="right", fill="y")

        vars_selected = []
        for i, slot in enumerate(slots):
            v = tk.BooleanVar(value=(i in selected))
            vars_selected.append(v)
            text = f"{i+1}. {slot['name']} ({slot['file']})"
            tk.Checkbutton(inner, text=text, variable=v, bg="#FFFFFF", font=("Malgun Gothic", 10), anchor="w").pack(fill="x", pady=2)

        btn_f = tk.Frame(win, bg="#FFFFFF")
        btn_f.pack(fill="x", padx=12, pady=10)

        def _set_all(flag):
            for var in vars_selected:
                var.set(flag)

        def _save():
            picked = [i for i, var in enumerate(vars_selected) if var.get()]
            self.cfg["relay_selected_slots"] = picked
            self.cfg["relay_use_selection"] = bool(picked)
            self.relay_pick_var.set(bool(picked))
            self.save_config()
            self._sync_relay_selection_label()
            if picked:
                self.log(f"✅ 체크 문서 저장 완료 ({len(picked)}개)")
            else:
                self.log("ℹ️ 체크 문서가 비어 있어 기존 범위 방식으로 실행됩니다.")
            win.destroy()

        ttk.Button(btn_f, text="전체선택", command=lambda: _set_all(True)).pack(side="left")
        ttk.Button(btn_f, text="전체해제", command=lambda: _set_all(False)).pack(side="left", padx=6)
        ttk.Button(btn_f, text="저장", command=_save).pack(side="right")

    def _get_coord_text(self):
        url_ok = bool((self.cfg.get("start_url") or "").strip())
        input_ok = bool((self.cfg.get("input_selector") or "").strip())
        submit_ok = bool((self.cfg.get("submit_selector") or "").strip())
        return f"URL[{'✅' if url_ok else '❌'}] 입력Selector[{'✅' if input_ok else '❌'}] 제출Selector[{'✅' if submit_ok else '❌'}]"

    def _get_img_coord_text(self):
        return "Playwright 모드에서는 이미지 좌표 지정 기능을 사용하지 않습니다."

    def log(self, msg):
        if hasattr(self, 'log_window'):
            self.log_window.log(msg)
        self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def start_capture(self, kind):
        messagebox.showinfo("안내", "Playwright 전환 버전에서는 화면 좌표 캡처를 사용하지 않습니다.\nURL/Selector 입력값을 사용해주세요.")

    def on_slot_change(self, event=None):
        idx = self.combo_slots.current()
        if idx >= 0:
            self.cfg["active_prompt_slot"] = idx
            self.cfg["prompts_file"] = self.cfg["prompt_slots"][idx]["file"]
            self.save_config()
            self.on_reload()

    def on_reload(self):
        try:
            if self.cfg.get("asset_loop_enabled"):
                self.asset_loop_items = self._build_asset_loop_items()
                self.prompts = [item["prompt"] for item in self.asset_loop_items]
                raw = "\n".join(self.prompts)
                if hasattr(self, "log_window"):
                    self.log_window.set_preview(raw)
            else:
                self.asset_loop_items = []
                self.prompts = self._load_prompt_source_prompts(update_preview=True)
            if self.prompts:
                if self.running and self.index >= len(self.prompts):
                    # 완료 상태(index == len)를 유지해서 자동 재시작을 방지
                    self.index = len(self.prompts)
                else:
                    self.index = min(self.index, len(self.prompts) - 1)
            else:
                self.index = 0
            self._update_progress_ui()
            if self.cfg.get("asset_loop_enabled"):
                self.log(f"로드 완료 (S반복 {len(self.prompts)}개)")
            else:
                self.log(f"로드 완료 ({len(self.prompts)}개)")
            slots = [s["name"] for s in self.cfg["prompt_slots"]]
            self.combo_slots["values"] = slots
            self.combo_slots.current(self.cfg["active_prompt_slot"])
            self._sync_relay_range_controls()
            self._sync_relay_selection_label()
            self._sync_asset_range_display()
            self._refresh_manual_selection_labels()
            self._refresh_asset_prompt_slot_controls()
            if self.cfg.get("asset_loop_enabled") and self.cfg.get("asset_use_prompt_slot"):
                missing = list(getattr(self, "asset_prompt_missing_numbers", []) or [])
                if hasattr(self, "lbl_asset_prompt_source_status") and missing:
                    preview = ", ".join(f"S{str(n).zfill(self._asset_pad_width())}" for n in missing[:3])
                    if len(missing) > 3:
                        preview += f" 외 {len(missing) - 3}개"
                    self.lbl_asset_prompt_source_status.config(
                        text=f"{self._asset_prompt_slot_summary()} | 누락: {preview}",
                        fg=self.color_error,
                    )
        except: pass

    def _update_progress_ui(self):
        if self.current_run_mode == "download":
            total = len(self.download_items)
            current = self.download_index
        else:
            total = len(self.prompts)
            current = self.index
        shown = 0 if total == 0 else min(current + 1, total)
        self.lbl_nav_status.config(text=f"{shown} / {total}")
        if total > 0:
            pct = (min(current, total) / total) * 100
            self.progress_var.set(pct)
            self.lbl_prog_text.config(text=f"{min(current, total)} / {total} ({pct:.1f}%)")
            if hasattr(self, "lbl_header_progress"):
                self.lbl_header_progress.config(text=f"{min(current, total)} / {total} ({pct:.1f}%)")
            self._draw_header_progress_bar(pct)
        else:
            self.progress_var.set(0)
            self.lbl_prog_text.config(text="0 / 0 (0%)")
            if hasattr(self, "lbl_header_progress"):
                self.lbl_header_progress.config(text="0 / 0 (0.0%)")
            self._draw_header_progress_bar(0)
        if hasattr(self, "lbl_hud_progress"):
            try:
                processed = getattr(self.actor, "processed_count", 0)
                batch_size = getattr(self.actor, "current_batch_size", 0)
            except Exception:
                processed = 0
                batch_size = 0
            self.lbl_hud_progress.config(text=f"진행: {min(current, total)} / {total} | 배치: {processed} / {batch_size}")

    def _update_monitor_ui(self):
        # 미니 HUD 갱신: 핵심 정보만 짧게 표시
        try:
            p_name = self.actor.current_persona_name
            mood = self.actor.current_mood
            speed_mult = self.actor.cfg.get('speed_multiplier', 1.0)

            processed = self.actor.processed_count
            batch_size = self.actor.current_batch_size
            if self.current_run_mode == "download":
                next_break_text = "휴식없음"
            else:
                next_break_text = str(max(0, batch_size - processed))
            active_traits = self.actor.get_active_traits()
            total = len(self.prompts)
            current = min(self.index, total)
            real_speed = 1.0 / speed_mult if speed_mult > 0 else 0.0

            if hasattr(self, "lbl_hud_progress"):
                self.lbl_hud_progress.config(text=f"진행: {current} / {total} | 배치: {processed} / {batch_size}")
            if hasattr(self, "lbl_hud_persona"):
                self.lbl_hud_persona.config(text=f"페르소나: {p_name}")
            if hasattr(self, "lbl_hud_meta"):
                self.lbl_hud_meta.config(text=f"무드: {mood} | 속도: x{real_speed:.1f} | 다음휴식: {next_break_text}")
            if hasattr(self, "lbl_hud_trait"):
                if active_traits:
                    self.lbl_hud_trait.config(text=f"특징: {active_traits[0]}")
                else:
                    self.lbl_hud_trait.config(text="특징: 기본 모드")
        except Exception as e:
            print(f"Failed to update monitor UI: {e}")

    def _normalize_work_break_config(self):
        try:
            every_count = int(self.cfg.get("work_break_every_count", 40) or 40)
        except Exception:
            every_count = 40
        try:
            break_minutes = int(self.cfg.get("work_break_minutes", 12) or 12)
        except Exception:
            break_minutes = 12
        self.cfg["work_break_every_count"] = max(1, min(9999, every_count))
        self.cfg["work_break_minutes"] = max(1, min(180, break_minutes))
        self.cfg["work_break_random_ratio"] = 0.30

    def _apply_actor_break_settings(self, reset_batch=False):
        self._normalize_work_break_config()
        if not hasattr(self, "actor") or self.actor is None:
            return
        try:
            self.actor.set_break_policy(
                base_count=self.cfg.get("work_break_every_count", 40),
                base_minutes=self.cfg.get("work_break_minutes", 12),
                random_ratio=self.cfg.get("work_break_random_ratio", 0.30),
                reset_batch=reset_batch,
            )
        except Exception as e:
            self.log(f"⚠️ 휴식 설정 적용 오류: {e}")

    def _set_run_mode(self, mode):
        self.current_run_mode = mode
        if mode in ("prompt", "asset"):
            use_asset = (mode == "asset")
            self.cfg["asset_loop_enabled"] = use_asset
            if hasattr(self, "asset_loop_var"):
                self.asset_loop_var.set(use_asset)
        self.save_config()

    def on_start_prompt(self):
        self._set_run_mode("prompt")
        self.on_start()

    def on_start_asset(self):
        self._set_run_mode("asset")
        self.on_start()

    def on_start_download(self):
        self._set_run_mode("download")
        self.on_start()

    def on_start(self):
        if self.running:
            self.log("ℹ️ 이미 자동화가 실행 중입니다.")
            return
        if self.paused:
            self.on_resume()
            return
        run_mode = self.current_run_mode or ("asset" if self.cfg.get("asset_loop_enabled") else "prompt")
        is_download_mode = (run_mode == "download")
        if not is_download_mode:
            self.on_reload() # 시작 시 프롬프트 최신화
        try:
            self.cfg["interval_seconds"] = int(self.entry_interval.get())
        except: pass
        self.cfg["scheduled_start_enabled"] = self.schedule_var.get() if hasattr(self, "schedule_var") else self.cfg.get("scheduled_start_enabled", False)
        self.cfg["scheduled_start_at"] = self.schedule_text_var.get().strip() if hasattr(self, "schedule_text_var") else self.cfg.get("scheduled_start_at", "")
        self.save_config()

        if (not is_download_mode) and self.cfg.get("asset_loop_enabled") and self.cfg.get("relay_mode"):
            self.cfg["relay_mode"] = False
            if hasattr(self, "relay_var"):
                self.relay_var.set(False)
            self.save_config()
            self.log("ℹ️ S반복 모드에서는 이어달리기를 자동 해제합니다.")

        if (not is_download_mode) and self.cfg.get("relay_mode"):
            seq = self._get_effective_relay_sequence()
            if not seq:
                messagebox.showwarning("주의", "이어달리기 대상 문서가 없습니다.")
                return
            start_slot, end_slot = seq[0], seq[-1]
            if self.cfg.get("active_prompt_slot") != start_slot:
                self.cfg["active_prompt_slot"] = start_slot
                self.cfg["prompts_file"] = self.cfg["prompt_slots"][start_slot]["file"]
                self.save_config()
                self.on_reload()
            self.index = 0
            self._update_progress_ui()
            if self.cfg.get("relay_use_selection") and self.cfg.get("relay_selected_slots"):
                self.log(f"🏃 체크 문서 이어달리기 시작 ({len(seq)}개)")
            else:
                self.log(f"🏃 이어달리기 범위: {self.cfg['prompt_slots'][start_slot]['name']} → {self.cfg['prompt_slots'][end_slot]['name']}")

        if is_download_mode:
            if not self.cfg.get("start_url", "").strip():
                messagebox.showwarning("주의", "시작 URL을 먼저 입력해주세요.")
                return
            asset_plan = self._resolve_asset_number_plan()
            if str(self.cfg.get("asset_manual_selection", "") or "").strip() and asset_plan.get("invalid_tokens"):
                messagebox.showwarning("주의", f"S/다운로드 개별 번호 입력 형식을 확인해주세요.\n문제값: {', '.join(asset_plan['invalid_tokens'][:5])}")
                return
            self.download_items = self._build_download_items()
            self.download_index = 0
            self.download_session_log = []
            if not self.download_items:
                messagebox.showwarning("주의", "다운로드 대상 S번호가 비어 있습니다.\n시작/끝 번호를 확인해주세요.")
                return
            self.current_selection_input = str(self.cfg.get("asset_manual_selection", "") or "").strip()
            if self.current_selection_input:
                self.current_selection_summary = self._format_manual_selection_preview(
                    asset_plan.get("numbers", []),
                    prefix=(self.cfg.get("asset_loop_prefix") or "S").strip() or "S",
                    pad_width=self._asset_pad_width(),
                )
            else:
                self.current_selection_summary = "시작~끝 범위 전체 실행"
            self._update_progress_ui()
            self.cfg["scheduled_start_enabled"] = False
            self.cfg["scheduled_start_at"] = ""
            if hasattr(self, "schedule_var"):
                self.schedule_var.set(False)
            if hasattr(self, "schedule_text_var"):
                self.schedule_text_var.set("")
            self.save_config()
        else:
            if not (self.cfg.get("start_url", "").strip() and self.cfg.get("input_selector", "").strip()):
                messagebox.showwarning("주의", "시작 URL / 입력 셀렉터를 먼저 입력해주세요.")
                return

            if self.cfg.get("asset_loop_enabled"):
                asset_plan = self._resolve_asset_number_plan()
                if str(self.cfg.get("asset_manual_selection", "") or "").strip() and asset_plan.get("invalid_tokens"):
                    messagebox.showwarning("주의", f"S 개별 번호 입력 형식을 확인해주세요.\n문제값: {', '.join(asset_plan['invalid_tokens'][:5])}")
                    return
                self.asset_loop_items = self._build_asset_loop_items()
                missing_asset_prompts = list(getattr(self, "asset_prompt_missing_numbers", []) or [])
                self.prompts = [item["prompt"] for item in self.asset_loop_items]
                self.current_selection_input = str(self.cfg.get("asset_manual_selection", "") or "").strip()
                if self.current_selection_input:
                    self.current_selection_summary = self._format_manual_selection_preview(
                        asset_plan.get("numbers", []),
                        prefix=(self.cfg.get("asset_loop_prefix") or "S").strip() or "S",
                        pad_width=self._asset_pad_width(),
                    )
                else:
                    self.current_selection_summary = "시작~끝 범위 전체 실행"
                if self.cfg.get("asset_use_prompt_slot") and missing_asset_prompts:
                    preview = ", ".join(f"S{str(n).zfill(self._asset_pad_width())}" for n in missing_asset_prompts[:5])
                    if len(missing_asset_prompts) > 5:
                        preview += f" 외 {len(missing_asset_prompts) - 5}개"
                    self.log(f"⚠️ S 개별 프롬프트 누락 번호는 건너뜁니다: {preview}")
            else:
                prompt_numbers, prompt_info = self._build_prompt_run_numbers()
                if prompt_info.get("invalid_tokens"):
                    messagebox.showwarning("주의", f"프롬프트 개별 번호 입력 형식을 확인해주세요.\n문제값: {', '.join(prompt_info['invalid_tokens'][:5])}")
                    return
                if str(self.cfg.get("prompt_manual_selection", "") or "").strip() and not prompt_numbers:
                    messagebox.showwarning("주의", "프롬프트 개별 실행 번호가 비어 있거나 범위를 벗어났습니다.")
                    return
                self.prompt_run_numbers = prompt_numbers
                self._refresh_prompt_run_sequence(update_preview=False)
                self.current_selection_input = str(self.cfg.get("prompt_manual_selection", "") or "").strip()
                self.current_selection_summary = self._format_manual_selection_preview(prompt_numbers, prefix="", pad_width=3) if self.current_selection_input else "전체 프롬프트 실행"
            
            if not self.prompts and not self.cfg.get("relay_mode"):
                if self.cfg.get("asset_loop_enabled"):
                    messagebox.showwarning("주의", "S반복 목록이 비어 있습니다.\n시작/끝 번호를 확인해주세요.")
                else:
                    messagebox.showwarning("주의", "프롬프트 파일이 비어있습니다!\n먼저 프롬프트를 입력하고 저장을 눌러주세요.")
                return
            
            if self.index >= len(self.prompts):
                self.index = 0
                self._update_progress_ui()

        scheduled_dt = None
        if (not is_download_mode) and self.cfg.get("scheduled_start_enabled"):
            raw = self.cfg.get("scheduled_start_at", "")
            scheduled_dt = self._parse_schedule_datetime(raw)
            if not scheduled_dt:
                messagebox.showwarning(
                    "예약 시간 형식 오류",
                    "예약 시간 형식이 잘못되었습니다.\n예시처럼 입력해주세요: 2026-02-26 21:30"
                )
                return
            if scheduled_dt <= datetime.now():
                messagebox.showwarning("예약 시간 오류", "예약 시간은 현재 시각보다 미래여야 합니다.")
                return

        if self.relay_progress == 0:
            self.session_start_time = datetime.now()
            self.session_log = []
            self.retry_error_log = []
            self._open_action_log("download_trace" if is_download_mode else "action_trace")
            self.session_report_path = self.logs_dir / f"session_report_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}.json"
            self.completion_summary_path = None
            if is_download_mode:
                self.download_report_path = self.logs_dir / f"download_report_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.running = True
        self.paused = False
        self.pause_remaining = None
        if hasattr(self, "btn_start_prompt"):
            self.btn_start_prompt.config(state="disabled")
        if hasattr(self, "btn_start_asset"):
            self.btn_start_asset.config(state="disabled")
        if hasattr(self, "btn_start_download"):
            self.btn_start_download.config(state="disabled")
        if hasattr(self, "btn_pause"):
            self.btn_pause.config(state="normal")
        if hasattr(self, "btn_resume"):
            self.btn_resume.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.update_status_label("🚀 시작 중...", self.color_success)
        self.play_sound("start")
        self.on_option_toggle()
        if is_download_mode:
            mode_label = "영상" if self._download_mode() == "video" else "이미지"
            self.log(f"🚀 다운로드 자동화 시작 | 모드={mode_label} | 대상={len(self.download_items)}개 | 실패판단대기={self.cfg.get('download_wait_seconds', 20)}초 | 선택={self.current_selection_summary}")
        elif self.cfg.get("asset_loop_enabled"):
            prompt_source = self._asset_prompt_slot_summary() if self.cfg.get("asset_use_prompt_slot") else "공통 템플릿"
            self.log(f"🚀 S반복 자동화 시작 | 선택={self.current_selection_summary} | 프롬프트={prompt_source}")
        else:
            self.log(f"🚀 프롬프트 자동화 시작 | 선택={self.current_selection_summary}")
        if not is_download_mode:
            # 실행 시점 입력방식 고정: 중간에 설정이 바뀌어도 현재 런에는 영향 없게 한다.
            self.run_input_mode = "typing"
            self.cfg["input_mode"] = self.run_input_mode
            self.input_mode_var.set(self.run_input_mode)
            self.save_config()
            try:
                self.combo_input_mode.config(state="disabled")
            except Exception:
                pass
            self.log(f"🔒 실행 입력방식 고정: {self.run_input_mode}")
        else:
            self.run_input_mode = None
        # 안정성 우선: UI(Selector 테스트)와 작업 스레드 간 Playwright 세션 충돌 방지
        # 실행 시작 시 기존 세션을 정리하고, 작업 스레드에서 세션을 새로 만든다.
        try:
            has_existing = bool(self.browser_context and self.page and (not self.page.is_closed()))
        except Exception:
            has_existing = False
        if has_existing:
            self.log("♻️ 실행 전 브라우저 세션 정리(스레드 충돌 방지)")
        self._shutdown_browser()
        self._ensure_worker_thread()
        try:
            self.actor.update_batch_size()
            self.actor.processed_count = 0
        except: pass
        if scheduled_dt:
            self.scheduled_waiting = True
            self.scheduled_start_ts = scheduled_dt.timestamp()
            self.t_next = self.scheduled_start_ts
            self.update_status_label(f"⏰ 예약 대기: {scheduled_dt.strftime('%Y-%m-%d %H:%M')}", self.color_info)
            self.log(f"⏰ 1회 예약 설정 완료: {scheduled_dt.strftime('%Y-%m-%d %H:%M')}")
        else:
            self.scheduled_waiting = False
            self.scheduled_start_ts = None
            self.t_next = time.time() # 즉시 시작

    def on_pause(self):
        if self.paused:
            return
        if (not self.running) and (not self.is_processing):
            return
        self.paused = True
        self.running = False
        if self.t_next:
            self.pause_remaining = max(1, int(self.t_next - time.time()))
        else:
            self.pause_remaining = 1
        self.scheduled_waiting = False
        self.scheduled_start_ts = None
        if hasattr(self, "btn_pause"):
            self.btn_pause.config(state="disabled")
        if hasattr(self, "btn_resume"):
            self.btn_resume.config(state="normal")
        self.btn_stop.config(state="normal")
        self.update_status_label("⏸ 일시정지", self.color_info)
        self.log("⏸ 자동화 일시정지 (브라우저/탭 유지)")

    def on_resume(self):
        if not self.paused:
            return
        self.paused = False
        self.running = True
        if hasattr(self, "btn_pause"):
            self.btn_pause.config(state="normal")
        if hasattr(self, "btn_resume"):
            self.btn_resume.config(state="disabled")
        if hasattr(self, "btn_start_prompt"):
            self.btn_start_prompt.config(state="disabled")
        if hasattr(self, "btn_start_asset"):
            self.btn_start_asset.config(state="disabled")
        if hasattr(self, "btn_start_download"):
            self.btn_start_download.config(state="disabled")
        self.btn_stop.config(state="normal")
        self._ensure_worker_thread()
        wait_sec = max(1, int(self.pause_remaining or 1))
        self.pause_remaining = None
        if not self.is_processing:
            self.t_next = time.time() + wait_sec
        self.update_status_label("▶ 재개됨", self.color_success)
        self.log(f"▶ 자동화 재개 (다음 작업까지 약 {wait_sec}초)")

    def on_stop(self, pipeline_transition=False):
        prev_mode = self.current_run_mode
        self.running = False
        self.paused = False
        self.pause_remaining = None
        if hasattr(self, "btn_start_prompt"):
            self.btn_start_prompt.config(state="normal")
        if hasattr(self, "btn_start_asset"):
            self.btn_start_asset.config(state="normal")
        if hasattr(self, "btn_start_download"):
            self.btn_start_download.config(state="normal")
        if hasattr(self, "btn_pause"):
            self.btn_pause.config(state="disabled")
        if hasattr(self, "btn_resume"):
            self.btn_resume.config(state="disabled")
        self.btn_stop.config(state="disabled")
        self.update_status_label("중지됨", self.color_error)
        self.is_processing = False
        self.relay_progress = 0
        self.scheduled_waiting = False
        self.scheduled_start_ts = None
        if self.alert_window:
            self.alert_window.close()
            self.alert_window = None
        if prev_mode == "download":
            self.save_download_report()
        else:
            self.save_session_report()
        self._stop_worker_thread()
        self._shutdown_browser()
        self._close_action_log()
        self.run_input_mode = None
        self.current_run_mode = None
        self.prompt_run_numbers = None
        self.download_items = []
        self.download_index = 0
        self.download_session_log = []
        self.download_report_path = None
        self.current_selection_summary = ""
        self.current_selection_input = ""
        try:
            self.combo_input_mode.config(state="readonly")
        except Exception:
            pass
        try:
            self.on_reload()
        except Exception:
            pass
        if self.pipeline_runtime_active and (not pipeline_transition):
            self._clear_pipeline_runtime(cancelled=True)

    def _create_tray_image(self):
        if Image is None:
            return None
        icon_path = self.base.parent / "icon.ico"
        try:
            if icon_path.exists():
                return Image.open(str(icon_path))
        except Exception:
            pass
        try:
            # fallback: 단색 아이콘
            img = Image.new("RGB", (64, 64), color=(0, 122, 255))
            return img
        except Exception:
            return None

    def _start_tray_icon(self):
        if not TRAY_AVAILABLE:
            return False
        if self.tray_icon is not None:
            return True

        image = self._create_tray_image()
        if image is None:
            return False

        def _on_open(icon, item):
            try:
                self.root.after(0, self.show_from_tray)
            except Exception:
                pass

        def _on_exit(icon, item):
            try:
                self.root.after(0, self.on_tray_exit_request)
            except Exception:
                pass

        menu = pystray.Menu(
            pystray.MenuItem("열기", _on_open, default=True),
            pystray.MenuItem("종료", _on_exit),
        )
        self.tray_icon = pystray.Icon("flow_veo_bot", image, APP_NAME, menu)

        def _run():
            try:
                self.tray_icon.run()
            except Exception:
                pass

        self.tray_thread = threading.Thread(target=_run, daemon=True)
        self.tray_thread.start()
        return True

    def _stop_tray_icon(self):
        icon = self.tray_icon
        self.tray_icon = None
        if icon is not None:
            try:
                icon.stop()
            except Exception:
                pass
        t = self.tray_thread
        self.tray_thread = None
        if t and t.is_alive():
            try:
                t.join(timeout=1.5)
            except Exception:
                pass

    def hide_to_tray(self):
        if not self._start_tray_icon():
            if not self._tray_warned_unavailable:
                self._tray_warned_unavailable = True
                messagebox.showwarning("트레이 미지원", "트레이 기능이 없어 창만 숨깁니다.\n(pystray/Pillow 설치 시 트레이 사용 가능)")
            self.root.withdraw()
            self.hidden_to_tray = True
            return
        self.root.withdraw()
        if hasattr(self, "log_window") and self.log_window:
            try:
                self.log_window.root.withdraw()
            except Exception:
                pass
        self.hidden_to_tray = True
        self.log("🧩 트레이로 숨김")

    def show_from_tray(self):
        self.hidden_to_tray = False
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def on_tray_exit_request(self):
        if not messagebox.askyesno("종료 확인", "정말 프로그램을 종료할까요?"):
            return
        self.on_exit()

    def _persist_ui_options(self):
        try:
            self.on_option_toggle()
        except Exception:
            pass

    def _ask_close_action(self):
        result = {"action": "cancel"}

        win = tk.Toplevel(self.root)
        win.title("종료 방식 선택")
        win.configure(bg=self.color_bg)
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)
        win.attributes("-topmost", True)

        box_w = 360
        box_h = 180
        try:
            self.root.update_idletasks()
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            rw = self.root.winfo_width()
            rh = self.root.winfo_height()
            x = rx + max((rw - box_w) // 2, 0)
            y = ry + max((rh - box_h) // 2, 0)
            win.geometry(f"{box_w}x{box_h}+{x}+{y}")
        except Exception:
            win.geometry(f"{box_w}x{box_h}")

        wrap = tk.Frame(win, bg=self.color_bg, padx=18, pady=16)
        wrap.pack(fill="both", expand=True)
        tk.Label(wrap, text="X 버튼을 눌렀을 때 어떻게 할까요?", font=("Malgun Gothic", 12, "bold"), bg=self.color_bg, fg=self.color_text).pack(anchor="w")
        tk.Label(wrap, text="원하시는 동작을 바로 선택하시면 됩니다.", font=("Malgun Gothic", 10), bg=self.color_bg, fg=self.color_text_sec).pack(anchor="w", pady=(6, 14))

        btn_row = tk.Frame(wrap, bg=self.color_bg)
        btn_row.pack(fill="x", pady=(6, 0))

        def _choose(action):
            result["action"] = action
            try:
                win.grab_release()
            except Exception:
                pass
            win.destroy()

        ttk.Button(btn_row, text="바로 종료", command=lambda: _choose("exit")).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_row, text="트레이로 가기", command=lambda: _choose("tray")).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(btn_row, text="취소", command=lambda: _choose("cancel")).pack(side="left", fill="x", expand=True)

        win.protocol("WM_DELETE_WINDOW", lambda: _choose("cancel"))
        self.root.wait_window(win)
        return result["action"]

    def on_window_close(self):
        self._persist_ui_options()
        action = self._ask_close_action()
        if action == "exit":
            self.on_exit()
        elif action == "tray":
            self.hide_to_tray()

    def on_exit(self):
        self._persist_ui_options()
        if self.current_run_mode == "download":
            self.save_download_report()
        else:
            self.save_session_report()
        self.running = False
        self._stop_worker_thread()
        self._shutdown_browser()
        self._close_action_log()
        self._stop_tray_icon()
        self.run_input_mode = None
        self.current_run_mode = None
        if self.pipeline_window and self.pipeline_window.winfo_exists():
            try:
                self.pipeline_window.destroy()
            except Exception:
                pass
        if self.home_window and self.home_window.winfo_exists():
            try:
                self.home_window.destroy()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _tick(self):
        if self.running and self.t_next:
            remain = self.t_next - time.time()
            if remain > 0:
                if not self.is_processing:
                    if self.scheduled_waiting:
                        self.update_status_label(f"⏰ 예약 대기 중... {int(remain)}초", self.color_info)
                    else:
                        self.update_status_label(f"⏳ 대기 중... {int(remain)}초", "#FFC107")

                    # 예약 대기 중이 아니고, 랜덤 행동 옵션이 켜져 있으면 페이지 내부에서 가벼운 행동 수행
                    if (self.current_run_mode != "download") and (not self.scheduled_waiting) and self.cfg.get("afk_mode") and random.random() < 0.3:
                        try:
                            self.actor.random_behavior_routine()
                        except Exception:
                            pass
            
            try: base = int(self.entry_interval.get())
            except: base = 180
            if self.current_run_mode == "download":
                remain_cnt = len(self.download_items) - self.download_index
            else:
                remain_cnt = len(self.prompts) - self.index
            total_sec = remain_cnt * base + max(0, int(remain))
            finish_time = datetime.fromtimestamp(time.time() + total_sec).strftime("%p %I:%M")
            self.lbl_eta.config(text=f"🏁 종료 예정: {finish_time}")

            if self.scheduled_waiting:
                if self.alert_window:
                    self.alert_window.close()
                    self.alert_window = None
            elif not self.is_processing and 0 < remain <= 30:
                if self.alert_window is None:
                    self.alert_window = CountdownAlert(self.root, remain, self.cfg.get("sound_enabled"))
                else:
                    self.alert_window.update_time(remain)
            
            if remain <= 0:
                if self.alert_window:
                    self.alert_window.close()
                    self.alert_window = None
                if not self.is_processing:
                    if self.scheduled_waiting:
                        self.scheduled_waiting = False
                        self.scheduled_start_ts = None
                        self.log("⏰ 예약 시각 도달! 자동화를 시작합니다.")
                    self.is_processing = True
                    self._ensure_worker_thread()
                    self.task_queue.put("run")
                if self.current_run_mode == "download":
                    interval = max(1, int(base))
                else:
                    try:
                        speed = self.actor.cfg.get('speed_multiplier', 1.0)
                    except: speed = 1.0
                    interval = int(base + random.uniform(0, base * 0.3 * speed))
                self.t_next = time.time() + interval
        self.root.after(1000, self._tick)

    def _run_task(self):
        print(f"[{datetime.now()}] Task started")
        if self.current_run_mode == "download":
            self._run_download_task()
            return
        if self.current_run_mode == "asset":
            self.on_reload()
        else:
            self._refresh_prompt_run_sequence(update_preview=True)
        self.log("작업 스레드 시작 (프롬프트 동기화 완료)")
        if not self.prompts or self.index >= len(self.prompts):
            print("No prompts or index out of range")
            self.log("프롬프트 없음 또는 범위 초과")
            self.save_session_report()
            if self.cfg.get("relay_mode"):
                seq = self._get_effective_relay_sequence()
                if not seq:
                    self._show_completion_popup()
                    return
                curr_slot = self._clamp_slot_index(self.cfg.get("active_prompt_slot", 0))
                try:
                    pos = seq.index(curr_slot)
                except ValueError:
                    pos = -1
                    for i, slot_idx in enumerate(seq):
                        if slot_idx > curr_slot:
                            pos = i - 1
                            break
                    else:
                        pos = len(seq) - 1
                next_pos = pos + 1
                if next_pos < len(seq):
                    next_slot = seq[next_pos]
                    self.cfg["active_prompt_slot"] = next_slot
                    self.cfg["prompts_file"] = self.cfg["prompt_slots"][next_slot]["file"]
                    self.save_config()
                    self.relay_progress += 1
                    self.index = 0
                    self.root.after(0, self.on_reload)
                    if 0 <= pos < len(seq):
                        prev_name = self.cfg["prompt_slots"][seq[pos]]["name"]
                    else:
                        prev_name = "시작"
                    self.log(f"🏃 이어달리기 이동: {prev_name} → {self.cfg['prompt_slots'][next_slot]['name']}")
                    self.play_sound("success")
                    self.t_next = time.time() + 10
                    return
            self._show_completion_popup()
            return

        try:
            if self.current_run_mode in ("prompt", "asset") and self.actor.processed_count >= self.actor.current_batch_size:
                print("Bio break triggered")
                self.actor.take_bio_break(status_callback=lambda m: self.update_status_label(m, self.color_error))
                self.actor.update_batch_size()
                self.actor.processed_count = 0
                self.is_processing = False
                return
        except Exception as e:
            print(f"Bio break check failed: {e}")
            self.log(f"⚠️ 휴식 체크 오류: {e}")

        asset_tag = None
        source_no = None
        try:
            # 작업 스레드 전용 세션 생성
            self._ensure_browser_session()
            self.actor.set_page(self.page)
            start_url = (self.cfg.get("start_url") or "").strip()
            input_selector = (self.cfg.get("input_selector") or "").strip()
            input_mode = "typing"

            if not (start_url and input_selector):
                raise RuntimeError("URL 또는 입력 selector 설정이 비어 있습니다.")

            # 현재 URL이 다르면 시작 페이지로 이동
            current_url = self.page.url or ""
            if (not current_url) or (start_url not in current_url):
                self.log(f"🌐 페이지 이동: {start_url}")
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                self.actor.random_action_delay("페이지 로딩 안정화", 1.0, 3.0)
                self._apply_browser_zoom()

            prompt = self.prompts[self.index]
            if self.current_run_mode == "prompt" and self.prompt_run_numbers:
                if 0 <= self.index < len(self.prompt_run_numbers):
                    source_no = self.prompt_run_numbers[self.index]
            if self.cfg.get("asset_loop_enabled"):
                if 0 <= self.index < len(self.asset_loop_items):
                    asset_tag = self.asset_loop_items[self.index].get("tag")
                    source_no = self.asset_loop_items[self.index].get("number")
                if not asset_tag:
                    m = re.match(r"^\s*([A-Za-z]+[0-9]+)\s*:", prompt)
                    if m:
                        asset_tag = m.group(1)
                preset_input_locator = None
                if input_selector:
                    try:
                        preset_input_locator, preset_input_selector = self._resolve_prompt_input_locator(
                            input_selector,
                            timeout_ms=2200,
                        )
                        if preset_input_locator is not None:
                            self.log(f"🧭 S전환 기준 입력칸 확인: {preset_input_selector or '자동 탐색'}")
                    except Exception:
                        preset_input_locator = None
                self.refresh_detected_media_state(
                    ensure_session=False,
                    input_locator=preset_input_locator,
                    profile="asset",
                    write_log=True,
                )
                try:
                    self.update_status_label("🎛️ 생성 옵션 맞추는 중...", self.color_info)
                    self._apply_prompt_generation_preset(input_locator=preset_input_locator, profile="asset")
                except Exception as e:
                    self.log(f"⚠️ 프롬프트 생성 옵션 자동 맞춤 실패: {e}")
                if asset_tag:
                    self.update_status_label(f"🔁 에셋 준비 중... ({asset_tag})", self.color_info)
                    self._run_asset_loop_prestep(asset_tag)

            # 실행 시점 안정화: 입력창이 늦게 뜨는 경우를 대비해 충분히 대기
            input_probe = self._normalize_candidate_list(input_selector)
            for sel in self._input_candidates():
                if sel not in input_probe:
                    input_probe.append(sel)

            already_ready = self._wait_until_input_visible(input_probe, timeout_sec=12)
            if not already_ready:
                opened = self._try_open_new_project_if_needed(input_probe)
                if opened:
                    self.log("✅ 편집 화면 감지(입력창 확인)")
                else:
                    self.log("ℹ️ 새 프로젝트 자동 진입 실패 또는 불필요 - 현재 화면에서 계속 진행")
                # 새 프로젝트 클릭 후 렌더링 대기
                self._wait_until_input_visible(input_probe, timeout_sec=15)
            else:
                self.log("✅ 편집 화면 감지(입력창 확인)")

            print("Randomizing persona...")
            try:
                self.actor.randomize_persona()
                self.root.after(0, self._update_monitor_ui)
            except Exception as e:
                print(f"Persona update failed: {e}")
                self.log(f"⚠️ 페르소나 업데이트 오류: {e}")

            start_t = datetime.now()

            input_locator, resolved_input_selector = self._resolve_prompt_input_locator(
                input_selector,
                timeout_ms=2800,
            )
            if input_locator is None:
                raise RuntimeError("프롬프트 입력칸을 찾지 못했습니다(에셋 검색칸 제외). selector 자동찾기/테스트를 다시 실행해주세요.")

            # 자동으로 더 좋은 selector를 찾았으면 설정 동기화
            if resolved_input_selector and resolved_input_selector != input_selector:
                self.cfg["input_selector"] = resolved_input_selector
                self.root.after(0, lambda v=resolved_input_selector: self.input_selector_var.set(v))
            self.save_config()
            self.log(f"🧭 프롬프트 입력창 확정: {resolved_input_selector or '자동 탐색'}")
            self.refresh_detected_media_state(
                ensure_session=False,
                input_locator=input_locator,
                profile="prompt",
                write_log=True,
            )

            if not self.cfg.get("asset_loop_enabled"):
                try:
                    self.update_status_label("🎛️ 생성 옵션 맞추는 중...", self.color_info)
                    self._apply_prompt_generation_preset(input_locator=input_locator, profile="prompt")
                except Exception as e:
                    self.log(f"⚠️ 프롬프트 생성 옵션 자동 맞춤 실패: {e}")

            if self.cfg.get("afk_mode") and random.random() < 0.5:
                self.actor.random_behavior_routine()

            self.update_status_label("🧹 입력창 초기화 중...", "white")
            self.actor.clear_input_field(input_locator, label="입력창")

            print(f"Typing prompt: {prompt[:20]}...")
            self.update_status_label("✍️ 프롬프트 입력 중...", "white")
            input_locator = self._type_prompt_with_inline_references(prompt, input_locator, input_mode)

            typed_text = self._read_input_text(input_locator)
            if len(typed_text.strip()) < max(4, min(24, len(prompt.strip()) // 6)):
                self.log("⚠️ 입력 확인 결과가 비어 있거나 너무 짧아서 입력창을 다시 찾습니다.")
                input_locator, resolved_input_selector = self._resolve_prompt_input_locator(
                    input_selector,
                    timeout_ms=2600,
                )
                if input_locator is None:
                    raise RuntimeError("생성 옵션 적용 후 프롬프트 입력창을 다시 찾지 못했습니다.")
                self.update_status_label("✍️ 프롬프트 재입력 중...", "white")
                self.actor.clear_input_field(input_locator, label="입력창")
                input_locator = self._type_prompt_with_inline_references(prompt, input_locator, input_mode)
                typed_text = self._read_input_text(input_locator)

            if len(typed_text.strip()) < max(4, min(24, len(prompt.strip()) // 6)):
                raise RuntimeError("프롬프트 입력이 실제 입력창에 반영되지 않았습니다.")

            has_inline_prompt_refs = bool(re.search(r"@(S?\d{3,4})\b", str(prompt or ""), re.IGNORECASE))
            self.update_status_label("✅ 입력 완료!", self.color_success)
            if has_inline_prompt_refs:
                self.log("ℹ️ inline 레퍼런스 프롬프트는 검토 대기를 생략합니다.")
            else:
                self.update_status_label("📖 검토 중...", self.color_info)
                self.actor.read_prompt_pause(prompt)
            before_submit_text = self._read_input_text(input_locator)

            # 전체 흐름 불규칙성을 위해 가끔 예측 불가 행동 추가
            if (not has_inline_prompt_refs) and random.random() < 0.35:
                self.actor.hesitate_on_submit()

            # 최종 제출
            print("Submitting...")
            self.update_status_label("🚀 제출 중...", self.color_accent)
            submitted = False
            attempt_notes = []
            self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 제출 정책: 안전 단일 제출")

            try:
                input_locator.click(timeout=1200)
            except Exception:
                pass
            self.actor.random_action_delay("Enter 제출 전 딜레이", 0.2, 0.8)
            self.page.keyboard.press("Enter")
            self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 제출 시도: Enter(단일 1회)")
            submitted = self._confirm_submission_started(input_locator, before_submit_text, timeout_sec=10)
            attempt_notes.append(f"Enter={'OK' if submitted else 'FAIL'}")

            if not submitted:
                raise RuntimeError(f"제출 확인 실패(생성 시작 신호 없음): {', '.join(attempt_notes)}")

            self._action_log(
                f"[{datetime.now().strftime('%H:%M:%S')}] 제출 검증 완료: {', '.join(attempt_notes) if attempt_notes else 'OK'}"
            )

            print("Task success")
            if asset_tag:
                self.log(f"성공 #{self.index+1} ({asset_tag})")
            elif source_no:
                self.log(f"성공 #{self.index+1} (원본 {source_no}번)")
            else:
                self.log(f"성공 #{self.index+1}")
            self.update_status_label("🎉 작업 완료!", self.color_success)
            self.play_sound("success")
            self.session_log.append({
                "index": self.index + 1,
                "source_no": source_no or (self.index + 1),
                "tag": asset_tag or "",
                "prompt": prompt,
                "duration": f"{(datetime.now()-start_t).total_seconds():.1f}초",
                "status": "success",
                "error": "",
            })
            self.actor.processed_count += 1
            self.index += 1
            self._action_log(f"[{datetime.now().strftime('%H:%M:%S')}] 프롬프트 #{self.index} 처리 완료")
        except PlaywrightTimeoutError as e:
            print(f"TIMEOUT in run_task: {e}")
            self.log(f"⏳ 요소 대기 시간 초과: {e}")
            self.update_status_label("⚠️ 요소 탐색 시간 초과", self.color_error)
            self.retry_error_log.append(f"{asset_tag or source_no or (self.index + 1)} | 요소 대기 시간 초과 | {str(e).strip().splitlines()[0][:160]}")
            self.t_next = time.time() + 5
        except PlaywrightError as e:
            print(f"PLAYWRIGHT ERROR in run_task: {e}")
            self.log(f"❌ Playwright 오류: {e}")
            self.update_status_label("⚠️ 브라우저 오류 재시도...", self.color_error)
            self.retry_error_log.append(f"{asset_tag or source_no or (self.index + 1)} | Playwright 오류 | {str(e).strip().splitlines()[0][:160]}")
            self.t_next = time.time() + 5
            self._shutdown_browser()
        except Exception as e:
            print(f"ERROR in run_task: {e}")
            traceback.print_exc()
            self.log(f"❌ 오류: {e}")
            self.update_status_label("⚠️ 재시도 대기...", self.color_error)
            self.retry_error_log.append(f"{asset_tag or source_no or (self.index + 1)} | 일반 오류 | {str(e).strip().splitlines()[0][:160]}")
            self.t_next = time.time() + 5
        finally:
            # 같은 worker 스레드에서 연속 작업을 수행하므로 브라우저 세션을 유지한다.
            # (중지/종료/치명 오류 시에만 세션 종료)
            self.root.after(0, self._update_progress_ui)
            self.is_processing = False

    def _run_download_task(self):
        print(f"[{datetime.now()}] Download task started")
        self.log("다운로드 작업 스레드 시작")
        if not self.download_items or self.download_index >= len(self.download_items):
            self.log("다운로드 대상 없음 또는 범위 초과")
            self.save_download_report()
            self._show_completion_popup()
            self.is_processing = False
            return

        start_url = (self.cfg.get("start_url") or "").strip()
        mode = self._download_mode()
        quality = self._download_quality(mode)
        tag = self.download_items[self.download_index]
        started_at = datetime.now()
        self.log(f"⬇️ 다운로드 시작: {tag} | {mode}/{quality}")

        try:
            self._ensure_browser_session()
            self.actor.set_page(self.page)
            current_url = self.page.url or ""
            if (not current_url) or (start_url and start_url not in current_url):
                self.log(f"🌐 페이지 이동: {start_url}")
                self.page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
                self.actor.random_action_delay("페이지 로딩 안정화", 1.0, 2.0)

            self.update_status_label(f"⬇️ 다운로드 중... {tag}", self.color_info)
            wait_sec = int(self.cfg.get("download_wait_seconds", 60) or 60)
            result = self._run_single_download_flow(
                mode=mode,
                tag=tag,
                quality=quality,
                dry_run=False,
                wait_sec=wait_sec,
            )
            self._apply_download_used_selectors(mode, result.get("used", {}))
            self.save_config()
            file_name = result.get("file") or ""
            file_path = result.get("path") or ""
            self.download_session_log.append({
                "tag": tag,
                "mode": mode,
                "quality": quality,
                "status": "success",
                "file_name": file_name,
                "file_path": file_path,
                "started_at": started_at.isoformat(),
                "ended_at": datetime.now().isoformat(),
                "error": "",
            })
            self.log(f"✅ 다운로드 성공: {tag} -> {file_name or '파일명 확인 필요'}")
            self.play_sound("success")
        except Exception as e:
            short_err = str(e).strip().splitlines()[0][:120]
            self.download_session_log.append({
                "tag": tag,
                "mode": mode,
                "quality": quality,
                "status": "failed",
                "file_name": "",
                "file_path": "",
                "started_at": started_at.isoformat(),
                "ended_at": datetime.now().isoformat(),
                "error": short_err,
            })
            self.log(f"❌ 다운로드 실패: {tag} | {short_err}")
            self.log(f"↪ 재시도 없이 다음 항목으로 이동: {tag}")
            self.update_status_label(f"⚠️ 실패 후 다음으로 이동: {tag}", self.color_error)
            self.retry_error_log.append(f"{tag} | 다운로드 실패 | {short_err}")
        finally:
            self.download_index += 1
            self.root.after(0, self._update_progress_ui)
            self.is_processing = False
            if self.download_index >= len(self.download_items):
                self._show_completion_popup()

    def on_first(self): 
        self.index = 0
        self._update_progress_ui()
        
    def on_prev(self): 
        if self.index > 0: self.index -= 1; self._update_progress_ui()
        
    def on_next(self):
        if self.index < len(self.prompts) - 1: self.index += 1; self._update_progress_ui()
        
    def on_last(self): 
        if self.prompts: self.index = len(self.prompts)-1
        self._update_progress_ui()
        
    def on_jump_to(self, event=None):
        if not self.prompts: return
        total = len(self.prompts)
        try:
            target = simpledialog.askinteger("이동", f"이동할 번호를 입력하세요 (1 ~ {total}):", parent=self.root)
            if target is not None:
                idx = target - 1
                if 0 <= idx < total:
                    self.index = idx
                    self._update_progress_ui()
                    self.log(f"🚀 {target}번으로 점프!")
                else:
                    messagebox.showwarning("범위 초과", "존재하지 않는 번호입니다.")
        except: pass

    def on_direct_jump(self, event=None):
        if not self.prompts: return
        try:
            val = self.ent_jump.get().strip()
            if not val: return
            target = int(val)
            total = len(self.prompts)
            idx = target - 1
            if 0 <= idx < total:
                self.index = idx
                self._update_progress_ui()
                self.log(f"🚀 {target}번으로 직접 이동!")
                self.ent_jump.delete(0, 'end')
                self.root.focus() # 포커스 해제
            else:
                messagebox.showwarning("범위 초과", f"1부터 {total} 사이의 숫자를 입력하세요.")
        except ValueError:
            messagebox.showerror("오류", "숫자만 입력 가능합니다.")

    def on_open_prompts(self): os.startfile(self.base / self.cfg["prompts_file"])
    
    def on_rename_slot(self):
        idx = self.combo_slots.current()
        if idx < 0: return
        
        current_name = self.cfg["prompt_slots"][idx]["name"]
        new_name = simpledialog.askstring("이름 변경", "새로운 슬롯 이름을 입력하세요:", initialvalue=current_name)
        
        if new_name:
            self.cfg["prompt_slots"][idx]["name"] = new_name
            self.save_config()
            
            # UI Update
            slots = [s["name"] for s in self.cfg["prompt_slots"]]
            self.combo_slots["values"] = slots
            self.combo_slots.current(idx)
            self._sync_relay_range_controls()
            self._sync_relay_selection_label()
            self._refresh_asset_prompt_slot_controls()
            self.log(f"📝 슬롯 이름 변경: {current_name} -> {new_name}")

    def on_add_slot(self):
        new_name = simpledialog.askstring("슬롯 추가", "새로운 슬롯의 이름을 입력하세요:")
        if not new_name: return
        
        # 파일명 생성 (중복 피하기)
        slot_id = 1
        while True:
            new_file = f"flow_prompts_slot_{slot_id}.txt"
            if not any(s["file"] == new_file for s in self.cfg["prompt_slots"]):
                break
            slot_id += 1
            
        # 파일 생성
        try:
            (self.base / new_file).write_text("", encoding="utf-8")
        except Exception as e:
            messagebox.showerror("오류", f"파일 생성 실패: {e}")
            return
            
        # 설정 추가
        self.cfg["prompt_slots"].append({"name": new_name, "file": new_file})
        self.save_config()
        
        # UI 갱신
        slots = [s["name"] for s in self.cfg["prompt_slots"]]
        self.combo_slots["values"] = slots
        new_idx = len(self.cfg["prompt_slots"]) - 1
        self.combo_slots.current(new_idx)
        self._sync_relay_range_controls()
        self._sync_relay_selection_label()
        self._refresh_asset_prompt_slot_controls()
        self.on_slot_change()
        self.log(f"➕ 새 슬롯 추가됨: {new_name} ({new_file})")
        messagebox.showinfo("성공", f"'{new_name}' 슬롯이 추가되었습니다!")

    def on_delete_slot(self):
        if len(self.cfg["prompt_slots"]) <= 1:
            messagebox.showwarning("삭제 불가", "최소 하나 이상의 슬롯은 유지해야 합니다.")
            return
            
        idx = self.combo_slots.current()
        if idx < 0: return
        
        slot_name = self.cfg["prompt_slots"][idx]["name"]
        if not messagebox.askyesno("슬롯 삭제", f"'{slot_name}' 슬롯을 삭제할까요?\n(실제 파일은 안전을 위해 삭제되지 않습니다)"):
            return
            
        # 설정 제거
        old_selected = self._normalize_relay_selected_slots(self.cfg.get("relay_selected_slots", []))
        self.cfg["prompt_slots"].pop(idx)
        
        # 인덱스 조정
        if self.cfg["active_prompt_slot"] >= len(self.cfg["prompt_slots"]):
            self.cfg["active_prompt_slot"] = len(self.cfg["prompt_slots"]) - 1
        elif self.cfg["active_prompt_slot"] == idx:
            # 현재 활성화된 슬롯을 삭제한 경우
            self.cfg["active_prompt_slot"] = 0

        for key in ("relay_start_slot", "relay_end_slot"):
            val = self.cfg.get(key)
            if val is not None and val >= len(self.cfg["prompt_slots"]):
                self.cfg[key] = len(self.cfg["prompt_slots"]) - 1

        new_selected = []
        for sidx in old_selected:
            if sidx == idx:
                continue
            if sidx > idx:
                new_selected.append(sidx - 1)
            else:
                new_selected.append(sidx)
        self.cfg["relay_selected_slots"] = self._normalize_relay_selected_slots(new_selected)
        if self.cfg.get("relay_use_selection") and not self.cfg["relay_selected_slots"]:
            self.cfg["relay_use_selection"] = False
            if hasattr(self, "relay_pick_var"):
                self.relay_pick_var.set(False)
            
        self.save_config()
        
        # UI 갱신
        slots = [s["name"] for s in self.cfg["prompt_slots"]]
        self.combo_slots["values"] = slots
        self.combo_slots.current(self.cfg["active_prompt_slot"])
        self._sync_relay_range_controls()
        self._sync_relay_selection_label()
        self._refresh_asset_prompt_slot_controls()
        self.on_slot_change()
        self.log(f"🗑️ 슬롯 삭제됨: {slot_name}")
        messagebox.showinfo("성공", f"'{slot_name}' 슬롯이 목록에서 제거되었습니다.")

    def save_session_report(self):
        if not hasattr(self, "session_log"):
            return
        if self.session_report_path is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_report_path = self.logs_dir / f"session_report_{stamp}.json"
        try:
            payload = {
                "created_at": datetime.now().isoformat(),
                "started_at": getattr(self, "session_start_time", datetime.now()).isoformat() if hasattr(getattr(self, "session_start_time", None), "isoformat") else str(getattr(self, "session_start_time", "")),
                "prompt_file": self.cfg.get("prompts_file"),
                "total_processed": len(self.session_log),
                "selection_summary": self.current_selection_summary,
                "selection_input": self.current_selection_input,
                "retry_errors": list(getattr(self, "retry_error_log", []) or []),
                "entries": self.session_log,
            }
            self.session_report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.log(f"🧾 세션 리포트 저장: {self.session_report_path.name}")
        except Exception as e:
            self.log(f"⚠️ 세션 리포트 저장 실패: {e}")

    def save_download_report(self):
        if not hasattr(self, "download_session_log"):
            return
        if self.download_report_path is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.download_report_path = self.logs_dir / f"download_report_{stamp}.json"
        try:
            failed = [x for x in self.download_session_log if x.get("status") != "success"]
            payload = {
                "created_at": datetime.now().isoformat(),
                "started_at": getattr(self, "session_start_time", datetime.now()).isoformat() if hasattr(getattr(self, "session_start_time", None), "isoformat") else str(getattr(self, "session_start_time", "")),
                "mode": self._download_mode(),
                "video_quality": self._download_quality("video"),
                "image_quality": self._download_quality("image"),
                "failure_wait_seconds": int(self.cfg.get("download_wait_seconds", 20) or 20),
                "output_dir": str(self._resolve_download_output_dir()),
                "selection_summary": self.current_selection_summary,
                "selection_input": self.current_selection_input,
                "retry_errors": list(getattr(self, "retry_error_log", []) or []),
                "total": len(self.download_session_log),
                "success": len(self.download_session_log) - len(failed),
                "failed": len(failed),
                "failed_tags": [x.get("tag", "") for x in failed],
                "entries": self.download_session_log,
                "summary_lines": [
                    f"{x.get('tag', '')} | {'성공' if x.get('status') == 'success' else '실패'} | {x.get('mode', '')}/{x.get('quality', '')} | {(x.get('file_name') or x.get('error') or '').strip()}"
                    for x in self.download_session_log
                ],
            }
            self.download_report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.log(f"🧾 다운로드 리포트 저장: {self.download_report_path.name}")
        except Exception as e:
            self.log(f"⚠️ 다운로드 리포트 저장 실패: {e}")

if __name__ == "__main__":
    try: FlowVisionApp().root.mainloop()
    except Exception as e:
        with open("CRASH_LOG.txt", "w") as f: f.write(traceback.format_exc())
