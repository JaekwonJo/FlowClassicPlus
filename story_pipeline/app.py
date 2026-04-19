from __future__ import annotations

import json
import os
import threading
import time
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
        self.preview_runner: GeminiWebRunner | None = None
        self.geometry_save_job = None
        self.root = tk.Tk()
        self.root.title(f"똑똑즈 자동화 파이프라인 - ttz_worker ({self.instance_name})")
        self.root.geometry(self.cfg.window_geometry if hasattr(self, "cfg") else "620x520")
        self.root.minsize(580, 460)
        self.root.configure(bg="#ECE7DF")

        self.queue: Queue[str] = Queue()
        self.status_queue: Queue[dict] = Queue()
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.runner: GeminiWebRunner | None = None
        self.current_log_file: Path | None = None
        self.log_visible = True
        self.run_started_at: float | None = None
        self.countdown_label = "대기 없음"
        self.countdown_remaining_seconds = 0.0

        self.cfg = self._load_config()
        self.log_visible = bool(self.cfg.log_visible)
        self.root.geometry(self._compact_window_geometry(self.cfg.window_geometry))
        self._build_ui()
        try:
            self._save_config()
        except Exception:
            pass
        self.root.bind("<Configure>", self._on_root_configure)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._pump_log_queue()
        self._pump_status_queue()
        self._tick_elapsed_clock()

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

    def _compact_window_geometry(self, raw: str) -> str:
        text = str(raw or "").strip()
        if not text:
            return "620x520"
        body, plus, offset = text.partition("+")
        if "x" not in body:
            return "620x520"
        try:
            width_text, height_text = body.split("x", 1)
            width = max(580, int(width_text))
            height = max(460, int(height_text))
            if plus:
                return f"{width}x{height}+{offset}"
            return f"{width}x{height}"
        except Exception:
            return "620x520"

    def _read_ui_into_cfg(self) -> None:
        self.cfg.instance_name = self.instance_name
        self.cfg.window_geometry = self.root.geometry()
        self.cfg.log_visible = bool(self.log_visible)
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
        self.cfg.pre_input_delay_seconds = float(self.var_pre_input_delay_seconds.get() or 4.0)
        self.cfg.send_wait_seconds = float(self.var_send_wait_seconds.get() or 2.0)
        self.cfg.poll_interval_seconds = float(self.var_poll_interval_seconds.get() or 2.0)
        self.cfg.stable_rounds_required = int(self.var_stable_rounds_required.get() or 2)
        self.cfg.max_wait_seconds = float(self.var_max_wait_seconds.get() or 300.0)
        self.cfg.human_typing_enabled = False
        self.cfg.typing_speed_level = int(self.var_typing_speed_level.get() or 5)
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
            self.log(f"🗂 선택됨 | {title} | {self._short_text(path)}")

    def _browse_dir(self, variable: tk.StringVar, title: str) -> None:
        current = variable.get().strip()
        path = filedialog.askdirectory(title=title, initialdir=str(Path(current) if current else Path.cwd()))
        if path:
            variable.set(path)
            self._save_config()
            self._refresh_compact_labels()
            self.log(f"📁 선택됨 | {title} | {self._short_text(path)}")

    def _edit_url(self) -> None:
        current = self.var_gemini_url.get().strip()
        value = simpledialog.askstring("Gem URL", "실제 Gem 채팅 URL을 넣어주세요.", initialvalue=current, parent=self.root)
        if value:
            self.var_gemini_url.set(value.strip())
            self._save_config()
            self._refresh_compact_labels()
            self.log(f"🔗 Gem URL 변경됨 | {self._short_text(value.strip(), mode='url')}")

    def _open_wait_settings_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("대기 설정")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#F7F2EA")
        dialog.resizable(False, False)

        fields = [
            ("창 뜬 뒤 기다림(초)", self.var_pre_input_delay_seconds),
            ("제출 후 대기(초)", self.var_send_wait_seconds),
            ("몇 초마다 확인(초)", self.var_poll_interval_seconds),
            ("같은 응답 몇 번 확인", self.var_stable_rounds_required),
            ("응답 최대 대기(초)", self.var_max_wait_seconds),
        ]
        local_vars: list[tk.StringVar] = []
        for row, (label_text, source_var) in enumerate(fields):
            tk.Label(dialog, text=label_text, bg="#F7F2EA", fg="#23302B", font=("맑은 고딕", 9)).grid(
                row=row, column=0, sticky="w", padx=14, pady=(12 if row == 0 else 6, 0)
            )
            local_var = tk.StringVar(value=source_var.get())
            local_vars.append(local_var)
            tk.Entry(
                dialog,
                textvariable=local_var,
                width=10,
                bg="#FFFFFF",
                fg="#111",
                insertbackground="#111",
                relief="flat",
            ).grid(row=row, column=1, sticky="w", padx=(10, 14), pady=(12 if row == 0 else 6, 0))

        tk.Label(
            dialog,
            text="설명: 300초는 꼭 기다린다는 뜻이 아니라,\n그 시간 안에 응답이 안 오면 실패로 보는 최대 제한입니다.",
            bg="#F7F2EA",
            fg="#6B6D63",
            justify="left",
            font=("맑은 고딕", 8),
        ).grid(row=len(fields), column=0, columnspan=2, sticky="w", padx=14, pady=(12, 0))

        btn_row = tk.Frame(dialog, bg="#F7F2EA")
        btn_row.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="e", padx=14, pady=14)

        def _save_and_close() -> None:
            (
                self.var_pre_input_delay_seconds,
                self.var_send_wait_seconds,
                self.var_poll_interval_seconds,
                self.var_stable_rounds_required,
                self.var_max_wait_seconds,
            ) = local_vars
            self._save_config()
            dialog.destroy()
            self.log(
                "⚙️ 대기 설정 변경 | 창 뜬 뒤 "
                f"{self.var_pre_input_delay_seconds.get()}초 | 제출 후 대기 {self.var_send_wait_seconds.get()}초 | "
                f"확인간격 {self.var_poll_interval_seconds.get()}초 | 같은 응답 {self.var_stable_rounds_required.get()}회 | "
                f"최대 {self.var_max_wait_seconds.get()}초"
            )

        tk.Button(
            btn_row,
            text="취소",
            command=dialog.destroy,
            relief="flat",
            bg="#E7DED2",
            fg="#4D443B",
            font=("맑은 고딕", 9, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="right")
        tk.Button(
            btn_row,
            text="저장",
            command=_save_and_close,
            relief="flat",
            bg="#1F6F5F",
            fg="white",
            font=("맑은 고딕", 9, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="right", padx=(0, 8))

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
        if hasattr(self, "lbl_worker_name"):
            self.lbl_worker_name.config(text=f"ttz_worker | {self.instance_name}")
        if hasattr(self, "lbl_profile_info"):
            self.lbl_profile_info.config(
                text=f"브라우저 프로필: {self._short_text(self.var_browser_profile_dir.get())}"
            )
        if hasattr(self, "btn_open_output_dir"):
            self.btn_open_output_dir.config(text="결과 폴더")

    def _refresh_hud_compact_summary(self) -> None:
        headline = self.var_hud_detail.get().strip() or self.var_hud_status.get().strip() or "준비 완료"
        step = self.var_hud_step.get().strip()
        batch = self.var_hud_batch.get().strip()
        scene = self.var_hud_scene.get().strip()
        pieces = []
        if step and step != "-":
            pieces.append(step)
        if scene:
            pieces.append(scene)
        if batch and batch != "작업 묶음 0 / 0":
            pieces.append(batch)
        self.var_hud_headline.set(headline)
        self.var_hud_subline.set("  |  ".join(pieces) if pieces else "아직 시작하지 않았습니다.")

    def _format_elapsed(self, seconds: float) -> str:
        total = max(0, int(seconds))
        hour = total // 3600
        minute = (total % 3600) // 60
        second = total % 60
        return f"{hour:02d}:{minute:02d}:{second:02d}"

    def _format_countdown(self, label: str, seconds: float) -> str:
        remain = max(0.0, float(seconds))
        return f"{label} {remain:05.1f}초"

    def _queue_status(self, payload: dict) -> None:
        self.status_queue.put(payload)

    def _apply_status(self, payload: dict) -> None:
        status = str(payload.get("status") or "").strip()
        if status:
            self.var_hud_status.set(status)
        detail = str(payload.get("detail") or "").strip()
        if detail:
            self.var_hud_detail.set(detail)
        step = str(payload.get("current_step") or "").strip()
        if step:
            self.var_hud_step.set(step)

        batch_index = payload.get("batch_index")
        batch_total = payload.get("batch_total")
        if batch_index is not None and batch_total is not None and int(batch_total) > 0:
            self.var_hud_batch.set(f"작업 묶음 {int(batch_index)} / {int(batch_total)}")

        micro_index = payload.get("micro_index")
        micro_total = payload.get("micro_total")
        batch_micro_index = payload.get("batch_micro_index")
        batch_micro_total = payload.get("batch_micro_total")
        micro_parts = []
        if micro_index is not None and micro_total is not None and int(micro_total) > 0:
            micro_parts.append(f"전체 묶음 {int(micro_index)} / {int(micro_total)}")
        if batch_micro_index is not None and batch_micro_total is not None and int(batch_micro_total) > 0:
            micro_parts.append(f"이번 배치 {int(batch_micro_index)} / {int(batch_micro_total)}")
        if micro_parts:
            self.var_hud_micro.set(" | ".join(micro_parts))

        scene_done = payload.get("scene_done")
        scene_total = payload.get("scene_total")
        scene_range = str(payload.get("scene_range") or "").strip()
        scene_text_parts = []
        if scene_done is not None and scene_total is not None and int(scene_total) > 0:
            scene_text_parts.append(f"장면 {int(scene_done)} / {int(scene_total)}")
        if scene_range:
            scene_text_parts.append(f"현재 {scene_range}")
        if scene_text_parts:
            self.var_hud_scene.set(" | ".join(scene_text_parts))

        if "countdown_label" in payload or "countdown_remaining_seconds" in payload:
            self.countdown_label = str(payload.get("countdown_label") or self.countdown_label or "대기 없음")
            self.countdown_remaining_seconds = max(0.0, float(payload.get("countdown_remaining_seconds") or 0.0))
            self.var_hud_countdown.set(self._format_countdown(self.countdown_label, self.countdown_remaining_seconds))

        if status in {"전체 완료", "실패", "중지 요청"}:
            self.countdown_label = "대기 없음"
            self.countdown_remaining_seconds = 0.0
            self.var_hud_countdown.set(self._format_countdown(self.countdown_label, 0.0))
        self._refresh_hud_compact_summary()

    def _pump_status_queue(self) -> None:
        try:
            while True:
                payload = self.status_queue.get_nowait()
                self._apply_status(payload)
        except Empty:
            pass
        self.root.after(120, self._pump_status_queue)

    def _tick_elapsed_clock(self) -> None:
        if self.run_started_at is None:
            self.var_hud_elapsed.set("00:00:00")
        else:
            self.var_hud_elapsed.set(self._format_elapsed(time.time() - self.run_started_at))
            if self.countdown_remaining_seconds > 0:
                self.countdown_remaining_seconds = max(0.0, self.countdown_remaining_seconds - 0.2)
                self.var_hud_countdown.set(self._format_countdown(self.countdown_label, self.countdown_remaining_seconds))
        self.root.after(200, self._tick_elapsed_clock)

    def _reset_hud(self) -> None:
        self.var_hud_status.set("준비 완료")
        self.var_hud_detail.set("아직 시작하지 않았습니다.")
        self.var_hud_step.set("-")
        self.var_hud_batch.set("작업 묶음 0 / 0")
        self.var_hud_micro.set("전체 묶음 0 / 0")
        self.var_hud_scene.set("장면 0 / 0")
        self.countdown_label = "대기 없음"
        self.countdown_remaining_seconds = 0.0
        self.var_hud_countdown.set(self._format_countdown(self.countdown_label, 0.0))
        self.var_hud_elapsed.set("00:00:00")
        self._refresh_hud_compact_summary()

    def _toggle_log(self) -> None:
        self.log_visible = not self.log_visible
        if self.log_visible:
            self.log_body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            self.btn_toggle_log.config(text="로그 숨기기")
        else:
            self.log_body.pack_forget()
            self.btn_toggle_log.config(text="로그 보기")
        try:
            self._save_config()
        except Exception:
            pass

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
        self.var_pre_input_delay_seconds = tk.StringVar(value=str(self.cfg.pre_input_delay_seconds))
        self.var_send_wait_seconds = tk.StringVar(value=str(self.cfg.send_wait_seconds))
        self.var_poll_interval_seconds = tk.StringVar(value=str(self.cfg.poll_interval_seconds))
        self.var_stable_rounds_required = tk.StringVar(value=str(self.cfg.stable_rounds_required))
        self.var_max_wait_seconds = tk.StringVar(value=str(self.cfg.max_wait_seconds))
        self.var_human_typing = tk.BooleanVar(value=self.cfg.human_typing_enabled)
        self.var_typing_speed_level = tk.StringVar(value=str(self.cfg.typing_speed_level))
        self.var_reset_chat = tk.BooleanVar(value=self.cfg.reset_chat_each_batch)
        self.var_open_notepad = tk.BooleanVar(value=self.cfg.open_notepad_live)
        self.var_manual_baked = tk.BooleanVar(value=self.cfg.manual_is_baked_into_gem)
        self.var_hud_status = tk.StringVar()
        self.var_hud_detail = tk.StringVar()
        self.var_hud_step = tk.StringVar()
        self.var_hud_batch = tk.StringVar()
        self.var_hud_micro = tk.StringVar()
        self.var_hud_scene = tk.StringVar()
        self.var_hud_countdown = tk.StringVar()
        self.var_hud_elapsed = tk.StringVar()
        self.var_hud_headline = tk.StringVar()
        self.var_hud_subline = tk.StringVar()

        header = tk.Frame(outer, bg="#ECE7DF")
        header.pack(fill="x", pady=(0, 8))
        left_header = tk.Frame(header, bg="#ECE7DF")
        left_header.pack(side="left")
        self.lbl_worker_name = tk.Label(left_header, text="", bg="#ECE7DF", fg="#1F6F5F", font=("맑은 고딕", 15, "bold"))
        self.lbl_worker_name.pack(anchor="w")
        self.lbl_profile_info = tk.Label(left_header, text="", bg="#ECE7DF", fg="#6A6B62", font=("맑은 고딕", 9))
        self.lbl_profile_info.pack(anchor="w", pady=(2, 0))
        tk.Label(header, text="수동처럼 실행", bg="#DDE9E5", fg="#1F6F5F", font=("맑은 고딕", 8, "bold"), padx=8, pady=3).pack(side="right")

        hud_card = tk.Frame(outer, bg="#F7F2EA", highlightbackground="#D7CCBE", highlightthickness=1)
        hud_card.pack(fill="x", pady=(0, 8))
        hud_card.grid_columnconfigure(0, weight=1)
        hud_card.grid_columnconfigure(1, weight=0)
        left_hud = tk.Frame(hud_card, bg="#F7F2EA")
        left_hud.grid(row=0, column=0, sticky="nsew", padx=(12, 8), pady=10)
        right_hud = tk.Frame(hud_card, bg="#F7F2EA")
        right_hud.grid(row=0, column=1, sticky="ne", padx=(0, 12), pady=10)

        tk.Label(left_hud, textvariable=self.var_hud_status, bg="#DDE9E5", fg="#1F6F5F", font=("맑은 고딕", 8, "bold"), padx=8, pady=3).pack(anchor="w")
        tk.Label(left_hud, textvariable=self.var_hud_headline, bg="#F7F2EA", fg="#23302B", font=("맑은 고딕", 11, "bold")).pack(anchor="w", pady=(8, 2))
        tk.Label(left_hud, textvariable=self.var_hud_subline, bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9)).pack(anchor="w")
        tk.Label(right_hud, textvariable=self.var_hud_countdown, bg="#EFE8DD", fg="#23302B", font=("맑은 고딕", 10, "bold"), padx=10, pady=6).pack(anchor="e")
        tk.Label(right_hud, textvariable=self.var_hud_elapsed, bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9)).pack(anchor="e", pady=(6, 0))

        tool_card = tk.Frame(outer, bg="#F7F2EA", highlightbackground="#D7CCBE", highlightthickness=1)
        tool_card.pack(fill="x", pady=(0, 8))
        tk.Label(tool_card, text="빠른 설정", bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9, "bold")).pack(anchor="w", padx=12, pady=(8, 6))
        tool_buttons = tk.Frame(tool_card, bg="#F7F2EA")
        tool_buttons.pack(fill="x", padx=10, pady=(0, 10))
        tool_btn_opts = {"relief": "flat", "font": ("맑은 고딕", 9, "bold"), "padx": 10, "pady": 8, "cursor": "hand2", "bg": "#EFE8DD", "fg": "#31423D"}
        tk.Button(tool_buttons, text="Step 파일", command=lambda: self._browse_file(self.var_step_macro_path, "Step 규칙 파일 선택"), **tool_btn_opts).pack(side="left", padx=(0, 6))
        tk.Button(tool_buttons, text="장면 파일", command=lambda: self._browse_file(self.var_scene_file_path, "장면 파일 선택"), **tool_btn_opts).pack(side="left", padx=6)
        tk.Button(tool_buttons, text="Gem URL", command=self._edit_url, **tool_btn_opts).pack(side="left", padx=6)
        self.btn_open_output_dir = tk.Button(tool_buttons, text="결과 폴더", command=lambda: self._browse_dir(self.var_output_root, "결과 저장 폴더 선택"), **tool_btn_opts)
        self.btn_open_output_dir.pack(side="left", padx=6)

        action_card = tk.Frame(outer, bg="#F7F2EA", highlightbackground="#D7CCBE", highlightthickness=1)
        action_card.pack(fill="x", pady=(0, 8))
        tk.Label(action_card, text="실행", bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9, "bold")).pack(anchor="w", padx=12, pady=(8, 6))
        action_buttons = tk.Frame(action_card, bg="#F7F2EA")
        action_buttons.pack(fill="x", padx=10, pady=(0, 10))
        action_btn_opts = {"relief": "flat", "font": ("맑은 고딕", 10, "bold"), "pady": 9, "cursor": "hand2", "width": 10}
        tk.Button(action_buttons, text="브라우저", command=self.on_open_browser, bg="#1F6F5F", fg="white", **action_btn_opts).pack(side="left", padx=(0, 6))
        tk.Button(action_buttons, text="시작", command=self.on_start, bg="#C66A2B", fg="white", **action_btn_opts).pack(side="left", padx=6)
        tk.Button(action_buttons, text="완전 중지", command=self.on_stop, bg="#6F3B2A", fg="white", **action_btn_opts).pack(side="left", padx=6)
        tk.Button(action_buttons, text="폴더 열기", command=self.on_open_output_dir, bg="#5E7A74", fg="white", **action_btn_opts).pack(side="left", padx=6)

        middle = tk.Frame(outer, bg="#ECE7DF")
        middle.pack(fill="x", pady=(0, 8))

        left_card = tk.Frame(middle, bg="#F7F2EA", highlightbackground="#D7CCBE", highlightthickness=1)
        left_card.pack(fill="x", expand=True)

        tk.Label(left_card, text="핵심 설정", bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 6))
        left_card.grid_columnconfigure(1, weight=1)
        left_card.grid_columnconfigure(3, weight=1)

        tk.Label(left_card, text="시작 장면 번호", bg="#F7F2EA", fg="#23302B").grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)
        start_entry = tk.Entry(left_card, textvariable=self.var_start_scene, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        start_entry.grid(row=1, column=1, sticky="w", pady=4)
        tk.Label(left_card, text="끝 장면 번호", bg="#F7F2EA", fg="#23302B").grid(row=1, column=2, sticky="w", padx=(12, 6), pady=4)
        end_entry = tk.Entry(left_card, textvariable=self.var_end_scene, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        end_entry.grid(row=1, column=3, sticky="w", pady=4)

        tk.Label(left_card, text="한번에 보낼 장면 수", bg="#F7F2EA", fg="#23302B").grid(row=2, column=0, sticky="w", padx=(12, 6), pady=4)
        micro_entry = tk.Entry(left_card, textvariable=self.var_micro_batch_size, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        micro_entry.grid(row=2, column=1, sticky="w", pady=4)
        tk.Label(left_card, text="창 뜬 뒤 기다림(초)", bg="#F7F2EA", fg="#23302B").grid(row=2, column=2, sticky="w", padx=(12, 6), pady=4)
        pre_input_entry = tk.Entry(left_card, textvariable=self.var_pre_input_delay_seconds, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        pre_input_entry.grid(row=2, column=3, sticky="w", pady=4)

        tk.Label(left_card, text="제출 후 대기(초)", bg="#F7F2EA", fg="#23302B").grid(row=3, column=0, sticky="w", padx=(12, 6), pady=4)
        send_wait_entry = tk.Entry(left_card, textvariable=self.var_send_wait_seconds, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        send_wait_entry.grid(row=3, column=1, sticky="w", pady=4)

        for entry in (start_entry, end_entry, micro_entry, pre_input_entry, send_wait_entry):
            entry.bind("<FocusOut>", lambda _e: self._save_config())

        opt_wrap = tk.Frame(left_card, bg="#F7F2EA")
        opt_wrap.grid(row=4, column=0, columnspan=4, sticky="ew", padx=12, pady=(8, 10))
        self._make_toggle_button(opt_wrap, self.var_reset_chat, "새 채팅").pack(side="left")
        self._make_toggle_button(opt_wrap, self.var_open_notepad, "메모장 저장").pack(side="left", padx=(8, 0))

        tk.Label(
            left_card,
            text="설명: 시간 숫자는 전부 초입니다. 예) 제출 후 대기 2.0 = 2초, 창 뜬 뒤 기다림 5.0 = 5초",
            bg="#F7F2EA",
            fg="#6B6D63",
            font=("맑은 고딕", 8),
        ).grid(row=5, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 10))

        log_box = tk.Frame(outer, bg="#F7F2EA", highlightbackground="#D7CCBE", highlightthickness=1, height=120)
        log_box.pack(fill="both", expand=True)
        log_box.pack_propagate(False)
        log_head = tk.Frame(log_box, bg="#F7F2EA")
        log_head.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(log_head, text="실행 로그", bg="#F7F2EA", fg="#6B6D63", font=("맑은 고딕", 9, "bold")).pack(side="left")
        self.btn_toggle_log = tk.Button(log_head, text="로그 숨기기", command=self._toggle_log, bg="#E7DED2", fg="#4D443B", relief="flat", font=("맑은 고딕", 9, "bold"), padx=10, pady=4, cursor="hand2")
        self.btn_toggle_log.pack(side="right")
        self.log_body = tk.Frame(log_box, bg="#F7F2EA", height=86)
        self.log_body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log_body.pack_propagate(False)
        self.txt_log = ScrolledText(self.log_body, height=5, bg="#16211E", fg="#F6F3EA", insertbackground="#F6F3EA", relief="flat")
        self.txt_log.pack(fill="both", expand=True)
        self.txt_log.insert("end", "스토리 자동화 준비 완료\n")
        self.txt_log.configure(state="disabled")
        if not self.log_visible:
            self.log_body.pack_forget()
            self.btn_toggle_log.config(text="로그 보기")
        self._refresh_compact_labels()
        self._reset_hud()

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
            pre_input_delay_seconds=self.cfg.pre_input_delay_seconds,
            send_wait_seconds=self.cfg.send_wait_seconds,
            poll_interval_seconds=self.cfg.poll_interval_seconds,
            stable_rounds_required=self.cfg.stable_rounds_required,
            human_typing_enabled=self.cfg.human_typing_enabled,
            typing_speed_level=self.cfg.typing_speed_level,
            status_callback=self._queue_status,
        )

    def _on_root_configure(self, _event=None) -> None:
        if not hasattr(self, "var_pipeline_mode"):
            return
        if self.geometry_save_job is not None:
            try:
                self.root.after_cancel(self.geometry_save_job)
            except Exception:
                pass
        self.geometry_save_job = self.root.after(400, self._save_geometry_only)

    def _save_geometry_only(self) -> None:
        self.geometry_save_job = None
        try:
            path = self._config_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
            data["window_geometry"] = self.root.geometry()
            data["log_visible"] = bool(self.log_visible)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _on_close(self) -> None:
        try:
            self._save_config()
        except Exception:
            pass
        try:
            if self.preview_runner is not None:
                self.preview_runner.close()
        except Exception:
            pass
        self.root.destroy()

    def _sync_runner_config(self) -> None:
        if self.runner is None:
            self.runner = self._build_runner()
            return
        self.runner.start_url = self.cfg.gemini_url
        self.runner.profile_dir = Path(self.cfg.browser_profile_dir)
        self.runner.wait_timeout_ms = int(max(30.0, self.cfg.max_wait_seconds) * 1000)
        self.runner.pre_input_delay_seconds = max(0.0, float(self.cfg.pre_input_delay_seconds))
        self.runner.send_wait_seconds = max(0.0, float(self.cfg.send_wait_seconds))
        self.runner.poll_interval_seconds = max(0.5, float(self.cfg.poll_interval_seconds))
        self.runner.stable_rounds_required = max(1, int(self.cfg.stable_rounds_required))
        self.runner.human_typing_enabled = bool(self.cfg.human_typing_enabled)
        self.runner.typing_speed_level = max(1, min(20, int(self.cfg.typing_speed_level)))

    def on_open_browser(self) -> None:
        try:
            if self.current_log_file is None:
                self._prepare_log_file("browser")
            if self.worker_thread and self.worker_thread.is_alive():
                self.log("⚠️ 자동화 실행 중에는 브라우저 미리보기를 따로 열지 않습니다.")
                return
            if self.preview_runner is None:
                self.preview_runner = self._build_runner()
            else:
                self.preview_runner.start_url = self.cfg.gemini_url
                self.preview_runner.profile_dir = Path(self.cfg.browser_profile_dir)
            self.log(f"🪟 워커: {self.instance_name}")
            self.log(f"🧭 브라우저 프로필: {self.cfg.browser_profile_dir}")
            self.preview_runner.open_browser()
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
        self.run_started_at = time.time()
        self._reset_hud()
        self._queue_status(
            {
                "status": "시작 준비",
                "detail": "브라우저와 작업 범위를 준비하는 중입니다.",
                "current_step": "준비",
            }
        )
        self.log(f"🚀 자동화 시작 요청 | worker={self.instance_name}")
        self.log(f"🧭 브라우저 프로필: {self.cfg.browser_profile_dir}")
        self.log(
            "⏱ 대기 설정 | 창 뜬 뒤 "
            f"{self.cfg.pre_input_delay_seconds:.1f}초 | 제출 후 대기 "
            f"{self.cfg.send_wait_seconds:.1f}초 | 확인간격 {self.cfg.poll_interval_seconds:.1f}초 | "
            f"같은 응답 확인 {self.cfg.stable_rounds_required}회 | 최대 {self.cfg.max_wait_seconds:.1f}초"
        )
        self.log(
            f"⌨️ 입력 설정 | 키보드처럼 천천히 입력 {'ON' if self.cfg.human_typing_enabled else 'OFF'} | 속도 x{self.cfg.typing_speed_level}"
        )
        if self.preview_runner is not None:
            try:
                self.preview_runner.close()
                self.log("🔄 브라우저 미리보기 세션을 닫고 자동화 세션으로 다시 엽니다.")
            except Exception:
                pass
            self.preview_runner = None
        self.worker_thread = threading.Thread(target=self._run_pipeline_thread, daemon=True)
        self.worker_thread.start()

    def _run_pipeline_thread(self) -> None:
        runner = self._build_runner()
        should_close_runner = True
        try:
            pipeline = StoryPipeline(
                cfg=self.cfg,
                runner=runner,
                log=self.log,
                stop_event=self.stop_event,
                status_callback=self._queue_status,
            )
            paths = pipeline.run()
            self.log(f"📁 세션 폴더: {paths.session_root}")
            self.log(f"📝 통합 누적 파일: {paths.final_live_txt}")
            self.log(f"🖼 이미지 전용 파일: {paths.final_image_txt}")
            self.log(f"🎬 비디오 전용 파일: {paths.final_video_txt}")
        except Exception as exc:
            should_close_runner = False
            self._queue_status(
                {
                    "status": "실패",
                    "detail": str(exc),
                    "current_step": "오류",
                    "countdown_label": "대기 없음",
                    "countdown_remaining_seconds": 0.0,
                }
            )
            self.log(f"❌ 자동화 실패: {exc}")
            self.log(traceback.format_exc().strip())
        finally:
            if should_close_runner or self.stop_event.is_set():
                try:
                    runner.close()
                except Exception:
                    pass
            else:
                self.log("🧷 오류 확인용으로 브라우저는 그대로 둡니다. 다시 시작 전 직접 닫아 주세요.")

    def on_stop(self) -> None:
        self.stop_event.set()
        self._queue_status(
            {
                "status": "중지 요청",
                "detail": "현재 작업이 안전하게 멈추기를 기다리는 중입니다.",
                "current_step": "중지",
                "countdown_label": "대기 없음",
                "countdown_remaining_seconds": 0.0,
            }
        )
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
