from __future__ import annotations

import json
import os
import threading
import traceback
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

from .core import DEFAULT_LIBRARY_PATH, DEFAULT_MANUAL_PATH, DEFAULT_SCENE_PATH, DEFAULT_STEP_MACRO_PATH
from .core import PipelineConfig, StoryPipeline
from .web import GeminiWebRunner


def sanitize_instance_name(raw: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in str(raw or "").strip())
    safe = safe.strip("_") or "story_worker1"
    return safe


class StoryPromptPipelineApp:
    def __init__(self, instance_name: str = "story_worker1") -> None:
        self.instance_name = sanitize_instance_name(instance_name)
        self.root = tk.Tk()
        self.root.title(f"똑똑즈 자동화 파이프라인 - ttz_worker ({self.instance_name})")
        self.root.geometry("840x595")
        self.root.minsize(800, 560)
        self.root.configure(bg="#ECE7DF")

        self.queue: Queue[str] = Queue()
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.runner: GeminiWebRunner | None = None
        self.current_log_file: Path | None = None
        self.log_visible = True

        self.cfg = self._load_config()
        self._build_ui()
        self._pump_log_queue()

    def _load_config(self) -> PipelineConfig:
        path = self._config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                cfg = PipelineConfig(**data)
                cfg.instance_name = self.instance_name
                if not cfg.browser_profile_dir:
                    cfg.browser_profile_dir = self._default_browser_profile_dir()
                if not cfg.output_root:
                    cfg.output_root = self._default_output_root()
                return cfg
            except Exception:
                pass
        return PipelineConfig(
            instance_name=self.instance_name,
            browser_profile_dir=self._default_browser_profile_dir(),
            output_root=self._default_output_root(),
        )

    def _config_path(self) -> Path:
        return Path("runtime") / f"story_prompt_pipeline_config_{self.instance_name}.json"

    def _default_browser_profile_dir(self) -> str:
        return f"runtime/story_gemini_profile_pw_{self.instance_name}"

    def _default_output_root(self) -> str:
        return f"logs/story_prompt_pipeline/{self.instance_name}"

    def _save_config(self) -> None:
        self._read_ui_into_cfg()
        self._config_path().write_text(json.dumps(self.cfg.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read_ui_into_cfg(self) -> None:
        self.cfg.instance_name = self.instance_name
        self.cfg.pipeline_mode = self.var_pipeline_mode.get().strip() or "manual_style"
        self.cfg.manual_path = self.var_manual_path.get().strip() or str(DEFAULT_MANUAL_PATH)
        self.cfg.step_macro_path = self.var_step_macro_path.get().strip() or str(DEFAULT_STEP_MACRO_PATH)
        self.cfg.library_path = self.var_library_path.get().strip() or str(DEFAULT_LIBRARY_PATH)
        self.cfg.scene_file_path = self.var_scene_file_path.get().strip() or str(DEFAULT_SCENE_PATH)
        self.cfg.gemini_url = self.var_gemini_url.get().strip() or "https://gemini.google.com/app"
        self.cfg.browser_profile_dir = self.var_browser_profile_dir.get().strip() or self._default_browser_profile_dir()
        self.cfg.output_root = self.var_output_root.get().strip() or self._default_output_root()
        self.cfg.start_scene = int(self.var_start_scene.get() or 1)
        self.cfg.end_scene = int(self.var_end_scene.get() or self.cfg.start_scene)
        self.cfg.batch_size = int(self.var_batch_size.get() or 15)
        self.cfg.micro_batch_size = int(self.var_micro_batch_size.get() or 5)
        self.cfg.send_wait_seconds = float(self.var_send_wait_seconds.get() or 2.0)
        self.cfg.poll_interval_seconds = float(self.var_poll_interval_seconds.get() or 2.0)
        self.cfg.stable_rounds_required = int(self.var_stable_rounds_required.get() or 2)
        self.cfg.max_wait_seconds = float(self.var_max_wait_seconds.get() or 300.0)
        self.cfg.reset_chat_each_batch = bool(self.var_reset_chat.get())
        self.cfg.open_notepad_live = bool(self.var_open_notepad.get())
        self.cfg.manual_is_baked_into_gem = bool(self.var_manual_baked.get())

    def _browse_file(self, variable: tk.StringVar, title: str) -> None:
        current = variable.get().strip()
        path = filedialog.askopenfilename(title=title, initialdir=str(Path(current).parent if current else Path.cwd()))
        if path:
            variable.set(path)
            self._save_config()
            self._refresh_compact_labels()

    def _browse_dir(self, variable: tk.StringVar, title: str) -> None:
        current = variable.get().strip()
        path = filedialog.askdirectory(title=title, initialdir=str(Path(current) if current else Path.cwd()))
        if path:
            variable.set(path)
            self._save_config()
            self._refresh_compact_labels()

    def _edit_url(self) -> None:
        current = self.var_gemini_url.get().strip()
        value = simpledialog.askstring("Gem URL", "실제 Gem 채팅 URL을 넣어주세요.", initialvalue=current, parent=self.root)
        if value:
            self.var_gemini_url.set(value.strip())
            self._save_config()
            self._refresh_compact_labels()

    def _short_text(self, raw: str, mode: str = "path") -> str:
        text = str(raw or "").strip()
        if not text:
            return "-"
        if mode == "url":
            text = text.replace("https://", "").replace("http://", "")
            if len(text) > 42:
                return text[:39] + "..."
            return text
        name = Path(text).name or text
        if len(name) > 32:
            return name[:29] + "..."
        return name

    def _refresh_compact_labels(self) -> None:
        if hasattr(self, "lbl_step_macro_value"):
            self.lbl_step_macro_value.config(text=self._short_text(self.var_step_macro_path.get()))
        if hasattr(self, "lbl_scene_file_value"):
            self.lbl_scene_file_value.config(text=self._short_text(self.var_scene_file_path.get()))
        if hasattr(self, "lbl_url_value"):
            self.lbl_url_value.config(text=self._short_text(self.var_gemini_url.get(), mode="url"))
        if hasattr(self, "lbl_output_value"):
            self.lbl_output_value.config(text=self._short_text(self.var_output_root.get()))
        if hasattr(self, "lbl_worker_name"):
            self.lbl_worker_name.config(text=f"ttz_worker | {self.instance_name}")
        if hasattr(self, "lbl_profile_info"):
            self.lbl_profile_info.config(
                text=f"브라우저 프로필: {self._short_text(self.var_browser_profile_dir.get())}"
            )
        if hasattr(self, "lbl_log_file"):
            self.lbl_log_file.config(
                text=f"로그 파일: {self._short_text(str(self.current_log_file or '-'))}"
            )

    def _toggle_log(self) -> None:
        self.log_visible = not self.log_visible
        if self.log_visible:
            self.log_body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            self.btn_toggle_log.config(text="로그 숨기기")
        else:
            self.log_body.pack_forget()
            self.btn_toggle_log.config(text="로그 보기")

    def _refresh_toggle_button(self, variable: tk.BooleanVar, button: tk.Button, label: str) -> None:
        button.config(
            text=f"{label} {'ON' if variable.get() else 'OFF'}",
            bg="#D7E4DE" if variable.get() else "#E7DED2",
            fg="#1C4138" if variable.get() else "#685D51",
        )

    def _toggle_option(self, variable: tk.BooleanVar, button: tk.Button, label: str) -> None:
        variable.set(not variable.get())
        self._refresh_toggle_button(variable, button, label)
        self._save_config()

    def _make_toggle_button(self, parent: tk.Widget, variable: tk.BooleanVar, label: str) -> tk.Button:
        button = tk.Button(
            parent,
            command=lambda: self._toggle_option(variable, button, label),
            relief="flat",
            font=("맑은 고딕", 9, "bold"),
            padx=10,
            pady=5,
            cursor="hand2",
        )
        self._refresh_toggle_button(variable, button, label)
        return button

    def _prepare_log_file(self, mode: str) -> None:
        self._save_config()
        root = Path(self.cfg.output_root or self._default_output_root())
        root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = root / f"ttz_worker_{self.instance_name}_{mode}_{stamp}.log"
        self.current_log_file.write_text(
            f"# ttz_worker 실행 로그\n# worker: {self.instance_name}\n# mode: {mode}\n# started_at: {stamp}\n\n",
            encoding="utf-8",
        )
        self._refresh_compact_labels()

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", background="#ECE7DF", foreground="#23302B")
        style.configure("TLabelframe", background="#F7F2EA", foreground="#23302B")
        style.configure("TLabelframe.Label", background="#F7F2EA", foreground="#23302B")
        style.configure("TButton", padding=6, font=("맑은 고딕", 10))
        style.configure("Primary.TButton", padding=8, font=("맑은 고딕", 10, "bold"))
        style.configure("Secondary.TButton", padding=7, font=("맑은 고딕", 10))

        outer = tk.Frame(self.root, bg="#ECE7DF")
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        self.var_manual_path = tk.StringVar(value=self.cfg.manual_path)
        self.var_step_macro_path = tk.StringVar(value=self.cfg.step_macro_path)
        self.var_library_path = tk.StringVar(value=self.cfg.library_path)
        self.var_scene_file_path = tk.StringVar(value=self.cfg.scene_file_path)
        self.var_pipeline_mode = tk.StringVar(value=self.cfg.pipeline_mode)
        self.var_gemini_url = tk.StringVar(value=self.cfg.gemini_url)
        self.var_browser_profile_dir = tk.StringVar(value=self.cfg.browser_profile_dir)
        self.var_output_root = tk.StringVar(value=self.cfg.output_root)
        self.var_start_scene = tk.StringVar(value=str(self.cfg.start_scene))
        self.var_end_scene = tk.StringVar(value=str(self.cfg.end_scene))
        self.var_batch_size = tk.StringVar(value=str(self.cfg.batch_size))
        self.var_micro_batch_size = tk.StringVar(value=str(self.cfg.micro_batch_size))
        self.var_send_wait_seconds = tk.StringVar(value=str(self.cfg.send_wait_seconds))
        self.var_poll_interval_seconds = tk.StringVar(value=str(self.cfg.poll_interval_seconds))
        self.var_stable_rounds_required = tk.StringVar(value=str(self.cfg.stable_rounds_required))
        self.var_max_wait_seconds = tk.StringVar(value=str(self.cfg.max_wait_seconds))
        self.var_reset_chat = tk.BooleanVar(value=self.cfg.reset_chat_each_batch)
        self.var_open_notepad = tk.BooleanVar(value=self.cfg.open_notepad_live)
        self.var_manual_baked = tk.BooleanVar(value=self.cfg.manual_is_baked_into_gem)

        header = tk.Frame(outer, bg="#ECE7DF")
        header.pack(fill="x", pady=(0, 10))
        left_header = tk.Frame(header, bg="#ECE7DF")
        left_header.pack(side="left")
        self.lbl_worker_name = tk.Label(left_header, text="", bg="#ECE7DF", fg="#1F6F5F", font=("맑은 고딕", 16, "bold"))
        self.lbl_worker_name.pack(anchor="w")
        self.lbl_profile_info = tk.Label(left_header, text="", bg="#ECE7DF", fg="#6A6B62", font=("맑은 고딕", 9))
        self.lbl_profile_info.pack(anchor="w", pady=(4, 0))
        tk.Label(header, text="manual_style", bg="#DDE9E5", fg="#1F6F5F", font=("맑은 고딕", 9, "bold"), padx=10, pady=4).pack(side="right")

        top_card = tk.Frame(outer, bg="#F7F2EA", highlightbackground="#D7CCBE", highlightthickness=1)
        top_card.pack(fill="x", pady=(0, 10))
        top_card.grid_columnconfigure(1, weight=1)

        def compact_row(parent, row, title, value_attr, action_text, action_cmd):
            tk.Label(parent, text=title, bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9, "bold")).grid(row=row, column=0, sticky="w", padx=12, pady=8)
            label = tk.Label(parent, text="-", bg="#EFE8DD", fg="#1E2B28", anchor="w", padx=10, pady=8, font=("맑은 고딕", 10))
            label.grid(row=row, column=1, sticky="ew", padx=(0, 8), pady=8)
            ttk.Button(parent, text=action_text, command=action_cmd, style="Secondary.TButton").grid(row=row, column=2, padx=(0, 12), pady=8)
            setattr(self, value_attr, label)

        compact_row(top_card, 0, "Step 매크로", "lbl_step_macro_value", "파일 선택", lambda: self._browse_file(self.var_step_macro_path, "Step 매크로 선택"))
        compact_row(top_card, 1, "장면 분할", "lbl_scene_file_value", "파일 선택", lambda: self._browse_file(self.var_scene_file_path, "장면 분할 파일 선택"))
        compact_row(top_card, 2, "Gem URL", "lbl_url_value", "URL 설정", self._edit_url)
        compact_row(top_card, 3, "출력 폴더", "lbl_output_value", "폴더 선택", lambda: self._browse_dir(self.var_output_root, "출력 폴더 선택"))

        middle = tk.Frame(outer, bg="#ECE7DF")
        middle.pack(fill="x", pady=(0, 10))

        left_card = tk.Frame(middle, bg="#F7F2EA", highlightbackground="#D7CCBE", highlightthickness=1)
        left_card.pack(side="left", fill="x", expand=True)
        right_card = tk.Frame(middle, bg="#F7F2EA", highlightbackground="#D7CCBE", highlightthickness=1)
        right_card.pack(side="left", anchor="n", padx=(10, 0))

        tk.Label(left_card, text="작업 범위", bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))
        left_card.grid_columnconfigure(5, weight=1)
        tk.Label(left_card, text="시작", bg="#F7F2EA", fg="#23302B").grid(row=1, column=0, sticky="w", padx=(12, 6), pady=6)
        start_entry = tk.Entry(left_card, textvariable=self.var_start_scene, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        start_entry.grid(row=1, column=1, sticky="w", pady=6)
        tk.Label(left_card, text="끝", bg="#F7F2EA", fg="#23302B").grid(row=1, column=2, sticky="w", padx=(18, 6), pady=6)
        end_entry = tk.Entry(left_card, textvariable=self.var_end_scene, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        end_entry.grid(row=1, column=3, sticky="w", pady=6)

        tk.Label(left_card, text="배치", bg="#F7F2EA", fg="#23302B").grid(row=2, column=0, sticky="w", padx=(12, 6), pady=6)
        batch_entry = tk.Entry(left_card, textvariable=self.var_batch_size, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        batch_entry.grid(row=2, column=1, sticky="w", pady=6)
        tk.Label(left_card, text="마이크로", bg="#F7F2EA", fg="#23302B").grid(row=2, column=2, sticky="w", padx=(18, 6), pady=6)
        micro_entry = tk.Entry(left_card, textvariable=self.var_micro_batch_size, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        micro_entry.grid(row=2, column=3, sticky="w", pady=6)

        tk.Label(left_card, text="입력후 대기", bg="#F7F2EA", fg="#23302B").grid(row=1, column=4, sticky="w", padx=(22, 6), pady=6)
        send_wait_entry = tk.Entry(left_card, textvariable=self.var_send_wait_seconds, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        send_wait_entry.grid(row=1, column=5, sticky="w", pady=6)
        tk.Label(left_card, text="확인 간격", bg="#F7F2EA", fg="#23302B").grid(row=2, column=4, sticky="w", padx=(22, 6), pady=6)
        poll_entry = tk.Entry(left_card, textvariable=self.var_poll_interval_seconds, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        poll_entry.grid(row=2, column=5, sticky="w", pady=6)

        tk.Label(left_card, text="안정 횟수", bg="#F7F2EA", fg="#23302B").grid(row=3, column=0, sticky="w", padx=(12, 6), pady=6)
        stable_entry = tk.Entry(left_card, textvariable=self.var_stable_rounds_required, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        stable_entry.grid(row=3, column=1, sticky="w", pady=6)
        tk.Label(left_card, text="최대 대기", bg="#F7F2EA", fg="#23302B").grid(row=3, column=2, sticky="w", padx=(18, 6), pady=6)
        max_wait_entry = tk.Entry(left_card, textvariable=self.var_max_wait_seconds, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        max_wait_entry.grid(row=3, column=3, sticky="w", pady=6)

        for entry in (start_entry, end_entry, batch_entry, micro_entry, send_wait_entry, poll_entry, stable_entry, max_wait_entry):
            entry.bind("<FocusOut>", lambda _e: self._save_config())

        opt_wrap = tk.Frame(left_card, bg="#F7F2EA")
        opt_wrap.grid(row=4, column=0, columnspan=6, sticky="ew", padx=12, pady=(8, 10))
        self._make_toggle_button(opt_wrap, self.var_reset_chat, "새 채팅").pack(side="left")
        self._make_toggle_button(opt_wrap, self.var_open_notepad, "메모장 저장").pack(side="left", padx=(10, 0))

        btn_wrap = tk.Frame(right_card, bg="#F7F2EA")
        btn_wrap.pack(anchor="n", padx=12, pady=12)
        tk.Label(btn_wrap, text="실행", bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9, "bold")).pack(anchor="w", pady=(0, 8))
        btn_grid = tk.Frame(btn_wrap, bg="#F7F2EA")
        btn_grid.pack()
        btn_opts = {"relief": "flat", "font": ("맑은 고딕", 10, "bold"), "width": 10, "pady": 10, "cursor": "hand2"}
        tk.Button(btn_grid, text="브라우저", command=self.on_open_browser, bg="#1F6F5F", fg="white", **btn_opts).grid(row=0, column=0, padx=4, pady=4)
        tk.Button(btn_grid, text="시작", command=self.on_start, bg="#C66A2B", fg="white", **btn_opts).grid(row=0, column=1, padx=4, pady=4)
        tk.Button(btn_grid, text="중지", command=self.on_stop, bg="#6F3B2A", fg="white", **btn_opts).grid(row=1, column=0, padx=4, pady=4)
        tk.Button(btn_grid, text="폴더", command=self.on_open_output_dir, bg="#5E7A74", fg="white", **btn_opts).grid(row=1, column=1, padx=4, pady=4)

        log_box = tk.Frame(outer, bg="#F7F2EA", highlightbackground="#D7CCBE", highlightthickness=1)
        log_box.pack(fill="both", expand=True)
        log_head = tk.Frame(log_box, bg="#F7F2EA")
        log_head.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(log_head, text="실행 로그", bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9, "bold")).pack(side="left")
        self.lbl_log_file = tk.Label(log_head, text="로그 파일: -", bg="#F7F2EA", fg="#7A746B", font=("맑은 고딕", 8))
        self.lbl_log_file.pack(side="left", padx=(12, 0))
        self.btn_toggle_log = tk.Button(log_head, text="로그 숨기기", command=self._toggle_log, bg="#E7DED2", fg="#4D443B", relief="flat", font=("맑은 고딕", 9, "bold"), padx=10, pady=4, cursor="hand2")
        self.btn_toggle_log.pack(side="right")
        self.log_body = tk.Frame(log_box, bg="#F7F2EA")
        self.log_body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.txt_log = ScrolledText(self.log_body, height=10, bg="#16211E", fg="#F6F3EA", insertbackground="#F6F3EA", relief="flat")
        self.txt_log.pack(fill="both", expand=True)
        self.txt_log.insert("end", "스토리 자동화 준비 완료\n")
        self.txt_log.configure(state="disabled")
        self._refresh_compact_labels()

    def log(self, text: str) -> None:
        if self.current_log_file is not None:
            try:
                with self.current_log_file.open("a", encoding="utf-8") as f:
                    f.write(text.rstrip() + "\n")
            except Exception:
                pass
        self.queue.put(text)

    def _pump_log_queue(self) -> None:
        try:
            while True:
                line = self.queue.get_nowait()
                self.txt_log.configure(state="normal")
                self.txt_log.insert("end", line.rstrip() + "\n")
                self.txt_log.see("end")
                self.txt_log.configure(state="disabled")
        except Empty:
            pass
        self.root.after(150, self._pump_log_queue)

    def _build_runner(self) -> GeminiWebRunner:
        self._save_config()
        return GeminiWebRunner(
            start_url=self.cfg.gemini_url,
            profile_dir=Path(self.cfg.browser_profile_dir),
            log=self.log,
            wait_timeout_ms=int(max(30.0, self.cfg.max_wait_seconds) * 1000),
            send_wait_seconds=self.cfg.send_wait_seconds,
            poll_interval_seconds=self.cfg.poll_interval_seconds,
            stable_rounds_required=self.cfg.stable_rounds_required,
        )

    def _sync_runner_config(self) -> None:
        if self.runner is None:
            self.runner = self._build_runner()
            return
        self.runner.start_url = self.cfg.gemini_url
        self.runner.profile_dir = Path(self.cfg.browser_profile_dir)
        self.runner.wait_timeout_ms = int(max(30.0, self.cfg.max_wait_seconds) * 1000)
        self.runner.send_wait_seconds = max(0.0, float(self.cfg.send_wait_seconds))
        self.runner.poll_interval_seconds = max(0.5, float(self.cfg.poll_interval_seconds))
        self.runner.stable_rounds_required = max(1, int(self.cfg.stable_rounds_required))

    def on_open_browser(self) -> None:
        try:
            if self.current_log_file is None:
                self._prepare_log_file("browser")
            self._sync_runner_config()
            self.log(f"🪟 워커: {self.instance_name}")
            self.log(f"🧭 브라우저 프로필: {self.cfg.browser_profile_dir}")
            self.runner.open_browser()
            self.log("🌐 브라우저 열기 완료")
        except Exception as exc:
            self.log(f"❌ 브라우저 열기 실패: {exc}")

    def on_start(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            self.log("⚠️ 이미 실행 중입니다.")
            return
        self.stop_event.clear()
        self._save_config()
        self._prepare_log_file("run")
        self._sync_runner_config()
        self.log(f"🚀 자동화 시작 요청 | worker={self.instance_name}")
        self.log(f"🧭 브라우저 프로필: {self.cfg.browser_profile_dir}")
        self.log(
            "⏱ 대기 설정 | 입력후 "
            f"{self.cfg.send_wait_seconds:.1f}초 | 확인간격 {self.cfg.poll_interval_seconds:.1f}초 | "
            f"안정 {self.cfg.stable_rounds_required}회 | 최대 {self.cfg.max_wait_seconds:.1f}초"
        )
        self.worker_thread = threading.Thread(target=self._run_pipeline_thread, daemon=True)
        self.worker_thread.start()

    def _run_pipeline_thread(self) -> None:
        assert self.runner is not None
        try:
            pipeline = StoryPipeline(cfg=self.cfg, runner=self.runner, log=self.log, stop_event=self.stop_event)
            paths = pipeline.run()
            self.log(f"📁 세션 폴더: {paths.session_root}")
            self.log(f"📝 통합 누적 파일: {paths.final_live_txt}")
            self.log(f"🖼 이미지 전용 파일: {paths.final_image_txt}")
            self.log(f"🎬 비디오 전용 파일: {paths.final_video_txt}")
        except Exception as exc:
            self.log(f"❌ 자동화 실패: {exc}")
            self.log(traceback.format_exc().strip())

    def on_stop(self) -> None:
        self.stop_event.set()
        self.log("⏹ 중지 요청을 보냈습니다.")

    def on_open_output_dir(self) -> None:
        self._save_config()
        path = Path(self.cfg.output_root)
        path.mkdir(parents=True, exist_ok=True)
        try:
            if hasattr(Path, "resolve"):
                resolved = path.resolve()
            else:
                resolved = path
            if hasattr(__import__("os"), "startfile"):
                __import__("os").startfile(str(resolved))  # type: ignore[attr-defined]
                return
        except Exception:
            pass
        try:
            import subprocess

            subprocess.Popen(["cmd.exe", "/c", "start", str(path.resolve())])
        except Exception as exc:
            self.log(f"❌ 출력 폴더 열기 실패: {exc}")

    def run(self) -> None:
        self.root.mainloop()


def main(instance_name: Optional[str] = None) -> None:
    app = StoryPromptPipelineApp(instance_name=instance_name or "story_worker1")
    app.run()
