from __future__ import annotations

import json
import threading
import traceback
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

import tkinter as tk
from tkinter import filedialog, ttk
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
        self.root.title(f"똑똑즈 스토리 프롬프트 파이프라인 - {self.instance_name}")
        self.root.geometry("1120x860")
        self.root.configure(bg="#10233D")

        self.queue: Queue[str] = Queue()
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.runner: GeminiWebRunner | None = None

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
        self.cfg.reset_chat_each_batch = bool(self.var_reset_chat.get())
        self.cfg.open_notepad_live = bool(self.var_open_notepad.get())
        self.cfg.manual_is_baked_into_gem = bool(self.var_manual_baked.get())

    def _browse_file(self, variable: tk.StringVar, title: str) -> None:
        current = variable.get().strip()
        path = filedialog.askopenfilename(title=title, initialdir=str(Path(current).parent if current else Path.cwd()))
        if path:
            variable.set(path)
            self._save_config()

    def _browse_dir(self, variable: tk.StringVar, title: str) -> None:
        current = variable.get().strip()
        path = filedialog.askdirectory(title=title, initialdir=str(Path(current) if current else Path.cwd()))
        if path:
            variable.set(path)
            self._save_config()

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", background="#10233D", foreground="#F5F7FB")
        style.configure("TLabelframe", background="#132A47", foreground="#F5F7FB")
        style.configure("TLabelframe.Label", background="#132A47", foreground="#F5F7FB")
        style.configure("TButton", padding=6)

        outer = tk.Frame(self.root, bg="#10233D")
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        top = tk.Frame(outer, bg="#10233D")
        top.pack(fill="x")

        left = tk.Frame(top, bg="#10233D")
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(top, bg="#10233D")
        right.pack(side="left", fill="y", padx=(12, 0))

        self.var_manual_path = tk.StringVar(value=self.cfg.manual_path)
        self.var_step_macro_path = tk.StringVar(value=self.cfg.step_macro_path)
        self.var_library_path = tk.StringVar(value=self.cfg.library_path)
        self.var_scene_file_path = tk.StringVar(value=self.cfg.scene_file_path)
        self.var_gemini_url = tk.StringVar(value=self.cfg.gemini_url)
        self.var_browser_profile_dir = tk.StringVar(value=self.cfg.browser_profile_dir)
        self.var_output_root = tk.StringVar(value=self.cfg.output_root)
        self.var_start_scene = tk.StringVar(value=str(self.cfg.start_scene))
        self.var_end_scene = tk.StringVar(value=str(self.cfg.end_scene))
        self.var_batch_size = tk.StringVar(value=str(self.cfg.batch_size))
        self.var_micro_batch_size = tk.StringVar(value=str(self.cfg.micro_batch_size))
        self.var_reset_chat = tk.BooleanVar(value=self.cfg.reset_chat_each_batch)
        self.var_open_notepad = tk.BooleanVar(value=self.cfg.open_notepad_live)
        self.var_manual_baked = tk.BooleanVar(value=self.cfg.manual_is_baked_into_gem)

        file_box = ttk.LabelFrame(left, text="기본 파일")
        file_box.pack(fill="x", pady=(0, 10))

        def add_file_row(parent, row, label, variable, browse_title, directory=False):
            tk.Label(parent, text=label, bg="#132A47", fg="#F5F7FB").grid(row=row, column=0, sticky="w", padx=10, pady=6)
            entry = tk.Entry(parent, textvariable=variable, bg="#F4F7FB", fg="#111", insertbackground="#111")
            entry.grid(row=row, column=1, sticky="ew", padx=(0, 8), pady=6, ipady=3)
            cmd = (lambda v=variable, t=browse_title: self._browse_dir(v, t)) if directory else (lambda v=variable, t=browse_title: self._browse_file(v, t))
            ttk.Button(parent, text="선택", command=cmd).grid(row=row, column=2, padx=(0, 10), pady=6)
            entry.bind("<FocusOut>", lambda _e: self._save_config())

        file_box.columnconfigure(1, weight=1)
        add_file_row(file_box, 0, "Gems 매뉴얼", self.var_manual_path, "Gems 매뉴얼 선택")
        add_file_row(file_box, 1, "Step 매크로", self.var_step_macro_path, "Step 매크로 선택")
        add_file_row(file_box, 2, "미장센 라이브러리", self.var_library_path, "미장센 라이브러리 선택")
        add_file_row(file_box, 3, "장면 분할 파일", self.var_scene_file_path, "장면 분할 파일 선택")

        run_box = ttk.LabelFrame(left, text="실행 설정")
        run_box.pack(fill="x", pady=(0, 10))
        run_box.columnconfigure(1, weight=1)
        add_file_row(run_box, 0, "Gem URL", self.var_gemini_url, "Gem URL", directory=False)
        add_file_row(run_box, 1, "브라우저 프로필 폴더", self.var_browser_profile_dir, "브라우저 프로필 폴더", directory=True)
        add_file_row(run_box, 2, "출력 폴더", self.var_output_root, "출력 폴더", directory=True)

        range_box = ttk.LabelFrame(left, text="범위 / 분할")
        range_box.pack(fill="x", pady=(0, 10))
        for idx in range(8):
            range_box.columnconfigure(idx, weight=1 if idx % 2 == 1 else 0)

        items = [
            ("시작 번호", self.var_start_scene),
            ("끝 번호", self.var_end_scene),
            ("배치 크기", self.var_batch_size),
            ("마이크로배치", self.var_micro_batch_size),
        ]
        for idx, (label, variable) in enumerate(items):
            row = idx // 2
            col = (idx % 2) * 4
            tk.Label(range_box, text=label, bg="#132A47", fg="#F5F7FB").grid(row=row, column=col, sticky="w", padx=(10, 6), pady=8)
            entry = tk.Entry(range_box, textvariable=variable, width=12, bg="#F4F7FB", fg="#111", insertbackground="#111")
            entry.grid(row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=8, ipady=3)
            entry.bind("<FocusOut>", lambda _e: self._save_config())

        opt_box = ttk.LabelFrame(left, text="자동화 옵션")
        opt_box.pack(fill="x", pady=(0, 10))
        ttk.Checkbutton(opt_box, text="배치마다 새 채팅 시도", variable=self.var_reset_chat, command=self._save_config).pack(anchor="w", padx=10, pady=(8, 4))
        ttk.Checkbutton(opt_box, text="검증 통과 파일 메모장으로 열기", variable=self.var_open_notepad, command=self._save_config).pack(anchor="w", padx=10, pady=4)
        ttk.Checkbutton(opt_box, text="Gem 안에 매뉴얼이 이미 들어 있음", variable=self.var_manual_baked, command=self._save_config).pack(anchor="w", padx=10, pady=(4, 8))

        action_box = ttk.LabelFrame(right, text="실행")
        action_box.pack(fill="x")
        ttk.Button(action_box, text="🌐 브라우저만 열기", command=self.on_open_browser).pack(fill="x", padx=10, pady=(10, 6))
        ttk.Button(action_box, text="▶ Step5~7 자동화 시작", command=self.on_start).pack(fill="x", padx=10, pady=6)
        ttk.Button(action_box, text="⏹ 중지 요청", command=self.on_stop).pack(fill="x", padx=10, pady=6)
        ttk.Button(action_box, text="📂 출력 폴더 열기", command=self.on_open_output_dir).pack(fill="x", padx=10, pady=(6, 10))

        status_box = ttk.LabelFrame(right, text="설명")
        status_box.pack(fill="x", pady=(10, 0))
        help_text = (
            f"현재 워커 이름: {self.instance_name}\n"
            f"현재 워커 설정파일: {self._config_path()}\n\n"
            "1. Step0~4는 지금처럼 직접 진행합니다.\n"
            "2. Gem URL은 Step5~7을 돌릴 Gem 채팅 주소를 넣습니다.\n"
            "3. 한 번 시작하면 Step5 -> Step6 -> Step7 -> 검증 통과분 즉시 저장으로 진행됩니다.\n"
            "4. 최종 통과 프롬프트는 세션 폴더의 validated_prompts_*.txt 에 계속 누적됩니다.\n"
            "5. 여러 워커를 동시에 돌릴 때는 워커 이름을 다르게 열어야 프로필이 안 꼬입니다."
        )
        tk.Label(status_box, text=help_text, justify="left", wraplength=290, bg="#132A47", fg="#D5E2F0").pack(fill="x", padx=10, pady=10)

        log_box = ttk.LabelFrame(outer, text="실행 로그")
        log_box.pack(fill="both", expand=True)
        self.txt_log = ScrolledText(log_box, height=24, bg="#09111E", fg="#E7F0FF", insertbackground="#E7F0FF")
        self.txt_log.pack(fill="both", expand=True, padx=8, pady=8)
        self.txt_log.insert("end", "스토리 자동화 준비 완료\n")
        self.txt_log.configure(state="disabled")

    def log(self, text: str) -> None:
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
        )

    def on_open_browser(self) -> None:
        try:
            if self.runner is None:
                self.runner = self._build_runner()
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
        if self.runner is None:
            self.runner = self._build_runner()
        self.worker_thread = threading.Thread(target=self._run_pipeline_thread, daemon=True)
        self.worker_thread.start()

    def _run_pipeline_thread(self) -> None:
        assert self.runner is not None
        try:
            pipeline = StoryPipeline(cfg=self.cfg, runner=self.runner, log=self.log, stop_event=self.stop_event)
            paths = pipeline.run()
            self.log(f"📁 세션 폴더: {paths.session_root}")
            self.log(f"📝 실시간 누적 파일: {paths.final_live_txt}")
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
