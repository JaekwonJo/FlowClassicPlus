from __future__ import annotations

import json
import os
import re
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

from .core import DEFAULT_LIBRARY_PATH, DEFAULT_MANUAL_PATH, DEFAULT_SCENE_PATH, DEFAULT_STEP_MACRO_PATH
from .core import PipelineConfig, StoryPipeline
from .core import SCENE_LINE_RE, resolve_local_path
from .web import GeminiWebRunner


def sanitize_instance_name(raw: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in str(raw or "").strip())
    safe = safe.strip("_") or "story_worker1"
    return safe


def normalize_path_key(raw: str | Path) -> str:
    text = str(raw or "").strip().replace("\\", "/").lower()
    if not text:
        return ""
    if ":/" in text:
        drive, tail = text.split(":/", 1)
        text = f"/mnt/{drive}/{tail}"
    text = text.replace("//", "/")
    return text.rstrip("/")


class StoryPromptPipelineApp:
    def __init__(self, instance_name: str = "story_worker1") -> None:
        self.instance_name = sanitize_instance_name(instance_name)
        self.preview_runner: GeminiWebRunner | None = None
        self.geometry_save_job = None
        self.root = tk.Tk()
        self.root.title("똑똑즈 파이프라인 워커")
        self.root.geometry(self.cfg.window_geometry if hasattr(self, "cfg") else "620x520")
        self.root.minsize(580, 460)
        self.palette = self._select_palette()
        self.root.configure(bg=self.palette["root_bg"])

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
        self._resize_drag_origin: tuple[int, int, int, int] | None = None

        self.cfg = self._load_config()
        self.log_visible = bool(self.cfg.log_visible)
        self.root.geometry(self._compact_window_geometry(self.cfg.window_geometry))
        self._build_ui()
        self._refresh_window_title()
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
        legacy_path = self._legacy_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        for candidate in (path, legacy_path):
            if not candidate.exists():
                continue
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                cfg = PipelineConfig(**data)
                cfg.instance_name = self.instance_name
                if not cfg.display_name:
                    cfg.display_name = ""
                if not cfg.browser_profile_dir:
                    cfg.browser_profile_dir = self._default_browser_profile_dir()
                if not cfg.output_root:
                    cfg.output_root = self._default_output_root()
                self._migrate_legacy_paths(cfg)
                return cfg
            except Exception:
                continue
        cfg = PipelineConfig(
            instance_name=self.instance_name,
            browser_profile_dir=self._default_browser_profile_dir(),
            output_root=self._default_output_root(),
        )
        self._migrate_legacy_paths(cfg)
        return cfg

    def _config_path(self) -> Path:
        return Path("runtime") / f"ttz_pipeline_worker_config_{self.instance_name}.json"

    def _legacy_config_path(self) -> Path:
        return Path("runtime") / f"story_prompt_pipeline_config_{self.instance_name}.json"

    def _default_browser_profile_dir(self) -> str:
        return f"runtime/ttz_gemini_profile_pw_{self.instance_name}"

    def _instance_folder_name(self) -> str:
        digits = "".join(ch for ch in self.instance_name if ch.isdigit())
        return f"설정{int(digits)}" if digits else self.instance_name

    def _default_output_root(self) -> str:
        return f"logs/똑똑즈_워커/{self._instance_folder_name()}"

    def _legacy_browser_profile_dirs(self) -> list[str]:
        return [
            f"runtime/story_gemini_profile_pw_{self.instance_name}",
        ]

    def _legacy_output_roots(self) -> list[str]:
        return [
            f"logs/story_prompt_pipeline/{self.instance_name}",
            f"logs/ttz_pipeline_worker/{self.instance_name}",
            f"logs/똑똑즈_워커/{self.instance_name}",
        ]

    def _migrate_legacy_paths(self, cfg: PipelineConfig) -> None:
        current_profile = normalize_path_key(cfg.browser_profile_dir)
        if current_profile in {normalize_path_key(item) for item in self._legacy_browser_profile_dirs()}:
            cfg.browser_profile_dir = self._default_browser_profile_dir()

        current_output = normalize_path_key(cfg.output_root)
        legacy_outputs = {normalize_path_key(item) for item in self._legacy_output_roots()}
        legacy_outputs.add(normalize_path_key(Path.cwd() / f"logs/story_prompt_pipeline/{self.instance_name}"))
        legacy_outputs.add(normalize_path_key(Path.cwd() / f"logs/ttz_pipeline_worker/{self.instance_name}"))
        if current_output in legacy_outputs:
            cfg.output_root = self._default_output_root()

    def _select_palette(self) -> dict[str, str]:
        palettes = [
            {
                "root_bg": "#ECE7DF",
                "panel_bg": "#F7F2EA",
                "card_border": "#D7CCBE",
                "accent": "#1F6F5F",
                "accent_soft": "#DDE9E5",
                "accent_text": "#1F6F5F",
                "subtle": "#6A6B62",
                "countdown_bg": "#EFE8DD",
                "browse_btn": "#1F6F5F",
                "mode_badge_bg": "#DDE9E5",
                "mode_badge_fg": "#1F6F5F",
            },
            {
                "root_bg": "#E9EDF2",
                "panel_bg": "#F5F8FC",
                "card_border": "#CDD8E5",
                "accent": "#2C5D8A",
                "accent_soft": "#DCE8F5",
                "accent_text": "#2C5D8A",
                "subtle": "#65717C",
                "countdown_bg": "#E8EEF6",
                "browse_btn": "#2C5D8A",
                "mode_badge_bg": "#DCE8F5",
                "mode_badge_fg": "#2C5D8A",
            },
            {
                "root_bg": "#EEE8E2",
                "panel_bg": "#FAF4ED",
                "card_border": "#DDCFC1",
                "accent": "#7A5A2D",
                "accent_soft": "#F1E5D2",
                "accent_text": "#7A5A2D",
                "subtle": "#75685A",
                "countdown_bg": "#F2E7DA",
                "browse_btn": "#7A5A2D",
                "mode_badge_bg": "#F1E5D2",
                "mode_badge_fg": "#7A5A2D",
            },
        ]
        digits = "".join(ch for ch in self.instance_name if ch.isdigit())
        index = (int(digits) - 1) % len(palettes) if digits else (sum(ord(ch) for ch in self.instance_name) % len(palettes))
        return palettes[index]

    def _display_name_text(self) -> str:
        name = str(getattr(self.cfg, "display_name", "") or "").strip()
        return name or "이름 미정"

    def _refresh_window_title(self) -> None:
        label = self._display_name_text()
        self.root.title(f"똑똑즈 파이프라인 워커 - {label}")

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
        self.cfg.display_name = str(getattr(self, "var_display_name", tk.StringVar(value=self.cfg.display_name)).get()).strip()
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
        self.cfg.rest_every_micro_batches = int(self.var_rest_every_micro_batches.get() or 0)
        self.cfg.rest_seconds = float(self.var_rest_seconds.get() or 0.0)
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

    def _edit_display_name(self) -> None:
        current = self.var_display_name.get().strip()
        value = simpledialog.askstring(
            "작업 이름",
            "이 창을 구별할 이름을 적어주세요.\n예) 금성대군 1부 / 2부 검수 / 실험용",
            initialvalue=current,
            parent=self.root,
        )
        if value is None:
            return
        self.var_display_name.set(value.strip())
        self._save_config()
        self._refresh_compact_labels()
        shown = self._display_name_text()
        self.log(f"🏷 작업 이름 변경 | {shown}")

    def _suggest_new_browser_profile_dir(self) -> str:
        current = Path(self.var_browser_profile_dir.get().strip() or self._default_browser_profile_dir())
        parent = current.parent if str(current.parent) not in {"", "."} else Path("runtime")
        stem = current.name or f"ttz_gemini_profile_pw_{self.instance_name}"
        match = re.match(r"^(.*?)(?:_(\d+))?$", stem)
        base_name = (match.group(1) if match else stem).strip("_") or stem
        number = int(match.group(2)) + 1 if match and match.group(2) else 2
        while True:
            candidate = parent / f"{base_name}_{number}"
            if not candidate.exists():
                return str(candidate).replace("\\", "/")
            number += 1

    def create_browser_profile(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showwarning("안내", "작업 실행 중에는 새 브라우저를 만들 수 없습니다.\n먼저 완전 중지 후 다시 눌러주세요.", parent=self.root)
            return
        current = self.var_browser_profile_dir.get().strip() or self._default_browser_profile_dir()
        new_profile = self._suggest_new_browser_profile_dir()
        try:
            Path(new_profile).mkdir(parents=True, exist_ok=True)
            self.var_browser_profile_dir.set(new_profile)
            self._save_config()
            self._refresh_compact_labels()
            self.log(f"🆕 새 브라우저 준비 완료 | {self._short_text(current)} -> {self._short_text(new_profile)}")
            messagebox.showinfo(
                "새 브라우저 준비",
                "새 브라우저 프로필을 만들었습니다.\n\n"
                f"- 이전 프로필: {Path(current).name}\n"
                f"- 새 프로필: {Path(new_profile).name}\n\n"
                "이제 브라우저 버튼을 다시 누르면 새 프로필로 열립니다.",
                parent=self.root,
            )
        except Exception as exc:
            messagebox.showerror("새 브라우저 만들기 실패", f"새 프로필 생성 중 오류가 났습니다.\n{exc}", parent=self.root)

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

    def _scene_label(self, number: int) -> str:
        return f"S{max(0, int(number)):03d}"

    def _detect_scene_file_bounds(self) -> tuple[int | None, int | None]:
        raw_path = ""
        if hasattr(self, "var_scene_file_path"):
            raw_path = self.var_scene_file_path.get().strip()
        elif getattr(self.cfg, "scene_file_path", ""):
            raw_path = str(self.cfg.scene_file_path).strip()
        if not raw_path:
            return (None, None)
        try:
            path = resolve_local_path(raw_path)
            text = path.read_text(encoding="utf-8")
        except Exception:
            return (None, None)
        numbers: list[int] = []
        for raw_line in text.splitlines():
            match = SCENE_LINE_RE.match(raw_line.strip())
            if match:
                numbers.append(int(match.group("number")))
        if not numbers:
            return (None, None)
        return (min(numbers), max(numbers))

    def _refresh_scene_range_labels(self) -> None:
        if not hasattr(self, "var_scene_file_summary"):
            return
        start_all, end_all = self._detect_scene_file_bounds()
        if start_all is None or end_all is None:
            self.var_scene_file_summary.set("이 파일 전체: 장면 번호를 읽지 못했습니다.")
        else:
            self.var_scene_file_summary.set(
                f"이 파일 전체: {self._scene_label(start_all)} ~ {self._scene_label(end_all)}"
            )

        start_text = self.var_start_scene.get().strip() if hasattr(self, "var_start_scene") else ""
        end_text = self.var_end_scene.get().strip() if hasattr(self, "var_end_scene") else ""
        try:
            start_num = int(start_text or 1)
            end_num = int(end_text or start_num)
            if end_num < start_num:
                start_num, end_num = end_num, start_num
            self.var_scene_run_summary.set(
                f"이번 실행: {self._scene_label(start_num)} ~ {self._scene_label(end_num)}"
            )
        except Exception:
            self.var_scene_run_summary.set("이번 실행: 시작/끝 번호를 확인해 주세요.")

    def _refresh_wait_settings_label(self) -> None:
        return None

    def _refresh_compact_labels(self) -> None:
        if hasattr(self, "lbl_worker_name"):
            self.lbl_worker_name.config(text=f"똑똑즈 워커 | {self._display_name_text()}")
        if hasattr(self, "lbl_instance_info"):
            self.lbl_instance_info.config(text=f"설정 번호: {self.instance_name}")
        if hasattr(self, "lbl_profile_info"):
            self.lbl_profile_info.config(
                text=f"브라우저 프로필: {self._short_text(self.var_browser_profile_dir.get())}"
            )
        if hasattr(self, "btn_open_output_dir"):
            self.btn_open_output_dir.config(text="저장 위치")
        self._refresh_window_title()
        self._refresh_scene_range_labels()
        self._refresh_wait_settings_label()

    def _start_resize_drag(self, event) -> None:
        self._resize_drag_origin = (event.x_root, event.y_root, self.root.winfo_width(), self.root.winfo_height())

    def _on_resize_drag(self, event) -> None:
        if not self._resize_drag_origin:
            return
        start_x, start_y, start_w, start_h = self._resize_drag_origin
        new_w = max(self.root.minsize()[0], start_w + (event.x_root - start_x))
        new_h = max(self.root.minsize()[1], start_h + (event.y_root - start_y))
        self.root.geometry(f"{new_w}x{new_h}")

    def _end_resize_drag(self, _event=None) -> None:
        self._resize_drag_origin = None

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
        log_root = root / "실행로그"
        log_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H시%M분%S초")
        mode_label = "브라우저" if mode == "browser" else "실행"
        self.current_log_file = log_root / f"{stamp}_{self.instance_name}_{mode_label}.txt"
        self.current_log_file.write_text(
            f"# 똑똑즈 워커 실행 로그\n# 설정 번호: {self.instance_name}\n# 작업 이름: {self._display_name_text()}\n# 모드: {mode_label}\n# 시작: {stamp}\n\n",
            encoding="utf-8",
        )
        self._refresh_compact_labels()

    def _build_ui(self) -> None:
        root_bg = self.palette["root_bg"]
        panel_bg = self.palette["panel_bg"]
        card_border = self.palette["card_border"]
        accent = self.palette["accent"]
        accent_soft = self.palette["accent_soft"]
        accent_text = self.palette["accent_text"]
        subtle = self.palette["subtle"]
        countdown_bg = self.palette["countdown_bg"]
        browse_btn = self.palette["browse_btn"]
        mode_badge_bg = self.palette["mode_badge_bg"]
        mode_badge_fg = self.palette["mode_badge_fg"]

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", background=root_bg, foreground="#23302B")
        style.configure("TLabelframe", background=panel_bg, foreground="#23302B")
        style.configure("TLabelframe.Label", background=panel_bg, foreground="#23302B")
        style.configure("TButton", padding=6, font=("맑은 고딕", 10))
        style.configure("Primary.TButton", padding=8, font=("맑은 고딕", 10, "bold"))
        style.configure("Secondary.TButton", padding=7, font=("맑은 고딕", 10))

        outer = tk.Frame(self.root, bg=root_bg)
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        self.var_display_name = tk.StringVar(value=self.cfg.display_name)
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
        self.var_rest_every_micro_batches = tk.StringVar(value=str(self.cfg.rest_every_micro_batches))
        self.var_rest_seconds = tk.StringVar(value=str(self.cfg.rest_seconds))
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
        self.var_scene_file_summary = tk.StringVar()
        self.var_scene_run_summary = tk.StringVar()

        header = tk.Frame(outer, bg=root_bg)
        header.pack(fill="x", pady=(0, 8))
        left_header = tk.Frame(header, bg=root_bg)
        left_header.pack(side="left")
        title_row = tk.Frame(left_header, bg=root_bg)
        title_row.pack(anchor="w")
        self.lbl_worker_name = tk.Label(title_row, text="", bg=root_bg, fg=accent_text, font=("맑은 고딕", 15, "bold"))
        self.lbl_worker_name.pack(anchor="w")
        tk.Button(
            title_row,
            text="이름 변경",
            command=self._edit_display_name,
            relief="flat",
            bg="#E7DED2",
            fg="#4D443B",
            font=("맑은 고딕", 8, "bold"),
            padx=8,
            pady=3,
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))
        info_row = tk.Frame(left_header, bg=root_bg)
        info_row.pack(anchor="w", pady=(2, 0))
        self.lbl_instance_info = tk.Label(info_row, text="", bg=root_bg, fg=subtle, font=("맑은 고딕", 8))
        self.lbl_instance_info.pack(side="left")
        self.lbl_profile_info = tk.Label(info_row, text="", bg=root_bg, fg=subtle, font=("맑은 고딕", 9))
        self.lbl_profile_info.pack(side="left", padx=(10, 0))
        tk.Label(header, textvariable=self.var_hud_status, bg=mode_badge_bg, fg=mode_badge_fg, font=("맑은 고딕", 8, "bold"), padx=8, pady=3).pack(side="right")

        hud_card = tk.Frame(outer, bg=panel_bg, highlightbackground=card_border, highlightthickness=1)
        hud_card.pack(fill="x", pady=(0, 8))
        hud_card.grid_columnconfigure(0, weight=1)
        hud_card.grid_columnconfigure(1, weight=0)
        left_hud = tk.Frame(hud_card, bg=panel_bg)
        left_hud.grid(row=0, column=0, sticky="nsew", padx=(12, 8), pady=10)
        right_hud = tk.Frame(hud_card, bg=panel_bg)
        right_hud.grid(row=0, column=1, sticky="ne", padx=(0, 12), pady=10)

        tk.Label(left_hud, textvariable=self.var_hud_headline, bg=panel_bg, fg="#23302B", font=("맑은 고딕", 11, "bold")).pack(anchor="w", pady=(8, 2))
        tk.Label(left_hud, textvariable=self.var_hud_subline, bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 9)).pack(anchor="w")
        tk.Label(right_hud, textvariable=self.var_hud_countdown, bg=countdown_bg, fg="#23302B", font=("맑은 고딕", 10, "bold"), padx=10, pady=6).pack(anchor="e")
        tk.Label(right_hud, textvariable=self.var_hud_elapsed, bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 9)).pack(anchor="e", pady=(6, 0))

        tool_card = tk.Frame(outer, bg=panel_bg, highlightbackground=card_border, highlightthickness=1)
        tool_card.pack(fill="x", pady=(0, 8))
        tk.Label(tool_card, text="빠른 설정", bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 9, "bold")).pack(anchor="w", padx=12, pady=(8, 6))
        tool_buttons = tk.Frame(tool_card, bg=panel_bg)
        tool_buttons.pack(fill="x", padx=10, pady=(0, 10))
        tool_btn_opts = {"relief": "flat", "font": ("맑은 고딕", 9, "bold"), "padx": 10, "pady": 8, "cursor": "hand2", "bg": "#EFE8DD", "fg": "#31423D"}
        tk.Button(tool_buttons, text="Step 파일", command=lambda: self._browse_file(self.var_step_macro_path, "Step 규칙 파일 선택"), **tool_btn_opts).pack(side="left", padx=(0, 6))
        tk.Button(tool_buttons, text="장면 파일", command=lambda: self._browse_file(self.var_scene_file_path, "장면 파일 선택"), **tool_btn_opts).pack(side="left", padx=6)
        tk.Button(tool_buttons, text="Gem URL", command=self._edit_url, **tool_btn_opts).pack(side="left", padx=6)
        self.btn_open_output_dir = tk.Button(tool_buttons, text="저장 위치", command=lambda: self._browse_dir(self.var_output_root, "결과 저장 폴더 선택"), **tool_btn_opts)
        self.btn_open_output_dir.pack(side="left", padx=6)
        summary_row = tk.Frame(tool_card, bg=panel_bg)
        summary_row.pack(fill="x", padx=12, pady=(0, 10))
        summary_left = tk.Frame(summary_row, bg=panel_bg)
        summary_left.pack(side="left", fill="x", expand=True)
        tk.Label(summary_left, textvariable=self.var_scene_file_summary, bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 8)).pack(anchor="w", pady=(0, 2))
        tk.Label(summary_left, textvariable=self.var_scene_run_summary, bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 8, "bold")).pack(anchor="w")

        action_card = tk.Frame(outer, bg=panel_bg, highlightbackground=card_border, highlightthickness=1)
        action_card.pack(fill="x", pady=(0, 8))
        tk.Label(action_card, text="실행", bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 9, "bold")).pack(anchor="w", padx=12, pady=(8, 6))
        action_buttons = tk.Frame(action_card, bg=panel_bg)
        action_buttons.pack(fill="x", padx=10, pady=(0, 10))
        action_btn_opts = {"relief": "flat", "font": ("맑은 고딕", 10, "bold"), "pady": 9, "cursor": "hand2", "width": 10}
        tk.Button(action_buttons, text="브라우저", command=self.on_open_browser, bg=browse_btn, fg="white", **action_btn_opts).pack(side="left", padx=(0, 6))
        tk.Button(action_buttons, text="시작", command=self.on_start, bg="#C66A2B", fg="white", **action_btn_opts).pack(side="left", padx=6)
        tk.Button(action_buttons, text="완전 중지", command=self.on_stop, bg="#6F3B2A", fg="white", **action_btn_opts).pack(side="left", padx=6)
        tk.Button(action_buttons, text="최근 결과 보기", command=self.on_open_output_dir, bg="#5E7A74", fg="white", **action_btn_opts).pack(side="left", padx=6)

        middle = tk.Frame(outer, bg=root_bg)
        middle.pack(fill="x", pady=(0, 8))

        left_card = tk.Frame(middle, bg=panel_bg, highlightbackground=card_border, highlightthickness=1)
        left_card.pack(fill="x", expand=True)

        tk.Label(left_card, text="핵심 설정", bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 9, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 6))
        left_card.grid_columnconfigure(1, weight=1)
        left_card.grid_columnconfigure(3, weight=1)

        tk.Label(left_card, text="시작 장면 번호", bg=panel_bg, fg="#23302B").grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)
        start_entry = tk.Entry(left_card, textvariable=self.var_start_scene, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        start_entry.grid(row=1, column=1, sticky="w", pady=4)
        tk.Label(left_card, text="끝 장면 번호", bg=panel_bg, fg="#23302B").grid(row=1, column=2, sticky="w", padx=(12, 6), pady=4)
        end_entry = tk.Entry(left_card, textvariable=self.var_end_scene, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        end_entry.grid(row=1, column=3, sticky="w", pady=4)

        tk.Label(left_card, text="한번에 보낼 장면 수", bg=panel_bg, fg="#23302B").grid(row=2, column=0, sticky="w", padx=(12, 6), pady=4)
        micro_entry = tk.Entry(left_card, textvariable=self.var_micro_batch_size, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        micro_entry.grid(row=2, column=1, sticky="w", pady=4)
        tk.Label(left_card, text="창 뜬 뒤 기다림(초)", bg=panel_bg, fg="#23302B").grid(row=2, column=2, sticky="w", padx=(12, 6), pady=4)
        pre_input_entry = tk.Entry(left_card, textvariable=self.var_pre_input_delay_seconds, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        pre_input_entry.grid(row=2, column=3, sticky="w", pady=4)

        tk.Label(left_card, text="제출 후 대기(초)", bg=panel_bg, fg="#23302B").grid(row=3, column=0, sticky="w", padx=(12, 6), pady=4)
        send_wait_entry = tk.Entry(left_card, textvariable=self.var_send_wait_seconds, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        send_wait_entry.grid(row=3, column=1, sticky="w", pady=4)
        tk.Label(left_card, text="최대 기다림(초)", bg=panel_bg, fg="#23302B").grid(row=3, column=2, sticky="w", padx=(12, 6), pady=4)
        self.ent_max_wait_seconds = tk.Entry(left_card, textvariable=self.var_max_wait_seconds, width=7, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        self.ent_max_wait_seconds.grid(row=3, column=3, sticky="w", pady=4)

        for entry in (start_entry, end_entry, micro_entry, pre_input_entry, send_wait_entry, self.ent_max_wait_seconds):
            entry.bind("<FocusOut>", lambda _e: (self._save_config(), self._refresh_compact_labels()))

        opt_wrap = tk.Frame(left_card, bg=panel_bg)
        opt_wrap.grid(row=4, column=0, columnspan=4, sticky="ew", padx=12, pady=(8, 10))
        self._make_toggle_button(opt_wrap, self.var_reset_chat, "새 채팅").pack(side="left")
        self._make_toggle_button(opt_wrap, self.var_open_notepad, "메모장 저장").pack(side="left", padx=(8, 0))
        tk.Button(
            opt_wrap,
            text="새 브라우저",
            command=self.create_browser_profile,
            relief="flat",
            bg="#E6E8EC",
            fg="#6A7380",
            font=("맑은 고딕", 8, "bold"),
            padx=10,
            pady=5,
            cursor="hand2",
        ).pack(side="right")

        rest_wrap = tk.Frame(summary_row, bg=panel_bg)
        rest_wrap.pack(side="right", anchor="s", padx=(8, 0))
        tk.Label(rest_wrap, text="휴식", bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 8)).pack(side="left")
        rest_every_entry = tk.Entry(rest_wrap, textvariable=self.var_rest_every_micro_batches, width=3, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        rest_every_entry.pack(side="left", padx=(6, 4))
        tk.Label(rest_wrap, text="묶음마다", bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 8)).pack(side="left")
        tk.Label(rest_wrap, text="시간", bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 8)).pack(side="left", padx=(12, 4))
        rest_seconds_entry = tk.Entry(rest_wrap, textvariable=self.var_rest_seconds, width=4, bg="#FFFFFF", fg="#111", insertbackground="#111", relief="flat")
        rest_seconds_entry.pack(side="left", padx=(2, 4))
        tk.Label(rest_wrap, text="초(±30%)", bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 8)).pack(side="left")

        tk.Label(
            left_card,
            text="설명: 시간 숫자는 전부 초입니다. 예) 제출 후 대기 2.0 = 2초, 창 뜬 뒤 기다림 5.0 = 5초, 최대 기다림 180.0 = 180초입니다.",
            bg=panel_bg,
            fg="#6B6D63",
            font=("맑은 고딕", 8),
        ).grid(row=5, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 10))

        log_box = tk.Frame(outer, bg=panel_bg, highlightbackground=card_border, highlightthickness=1, height=120)
        log_box.pack(fill="both", expand=True)
        log_box.pack_propagate(False)
        log_head = tk.Frame(log_box, bg=panel_bg)
        log_head.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(log_head, text="실행 로그", bg=panel_bg, fg="#6B6D63", font=("맑은 고딕", 9, "bold")).pack(side="left")
        self.btn_toggle_log = tk.Button(log_head, text="로그 숨기기", command=self._toggle_log, bg="#E7DED2", fg="#4D443B", relief="flat", font=("맑은 고딕", 9, "bold"), padx=10, pady=4, cursor="hand2")
        self.btn_toggle_log.pack(side="right")
        self.log_body = tk.Frame(log_box, bg=panel_bg, height=86)
        self.log_body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log_body.pack_propagate(False)
        self.txt_log = ScrolledText(self.log_body, height=5, bg="#16211E", fg="#F6F3EA", insertbackground="#F6F3EA", relief="flat")
        self.txt_log.pack(fill="both", expand=True)
        self.txt_log.insert("end", "똑똑즈 워커 준비 완료\n")
        self.txt_log.configure(state="disabled")
        if not self.log_visible:
            self.log_body.pack_forget()
            self.btn_toggle_log.config(text="로그 보기")

        self.resize_hint_label = tk.Label(
            self.root,
            text="창 크기 조절",
            bg=root_bg,
            fg="#7A7C74",
            font=("맑은 고딕", 8),
        )
        self.resize_hint_label.place(relx=1.0, rely=1.0, x=-48, y=-8, anchor="se")
        resize_handle = tk.Frame(
            self.root,
            bg="#D8D0C3",
            width=34,
            height=22,
            cursor="size_nw_se",
            highlightthickness=1,
            highlightbackground="#BFB5A5",
        )
        resize_handle.place(relx=1.0, rely=1.0, x=-8, y=-8, anchor="se")
        resize_handle.pack_propagate(False)
        tk.Label(resize_handle, text="◢", bg="#D8D0C3", fg="#6A6258", font=("맑은 고딕", 10, "bold")).pack(expand=True)
        self.resize_handle = resize_handle
        resize_handle.bind("<ButtonPress-1>", self._start_resize_drag)
        resize_handle.bind("<B1-Motion>", self._on_resize_drag)
        resize_handle.bind("<ButtonRelease-1>", self._end_resize_drag)
        for entry in (rest_every_entry, rest_seconds_entry):
            entry.bind("<FocusOut>", lambda _e: (self._save_config(), self._refresh_compact_labels()))
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

    def _latest_output_target(self) -> Path:
        root = Path(self.cfg.output_root)
        root.mkdir(parents=True, exist_ok=True)
        candidates = [item for item in root.iterdir() if item.is_dir() and item.name != "실행로그"]
        if not candidates:
            return root
        return max(candidates, key=lambda item: item.stat().st_mtime)

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
        try:
            if self.runner is not None:
                self.runner.close()
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
            self.log(f"🪟 워커: {self._display_name_text()} ({self.instance_name})")
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
        self.log(f"🚀 자동화 시작 요청 | worker={self._display_name_text()} ({self.instance_name})")
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
        if self.runner is None:
            self.runner = self._build_runner()
        else:
            self._sync_runner_config()
        runner = self.runner
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
            if self.stop_event.is_set():
                self.log("🧷 중지 후에도 브라우저는 그대로 둡니다. 프로그램을 닫을 때만 브라우저가 꺼집니다.")
            else:
                self.log("🧷 작업이 끝나도 브라우저는 그대로 둡니다. 프로그램을 닫을 때만 브라우저가 꺼집니다.")

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
        path = self._latest_output_target()
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
            self.log(f"❌ 최근 결과 폴더 열기 실패: {exc}")

    def run(self) -> None:
        self.root.mainloop()


def main(instance_name: Optional[str] = None) -> None:
    app = StoryPromptPipelineApp(instance_name=instance_name or "story_worker1")
    app.run()
