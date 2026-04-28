from __future__ import annotations

import json
import os
import random
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_MANUAL_PATH = Path(
    "/mnt/c/Users/jaekw/Pictures/똑똑즈 스토리/똑똑즈 스토리 기획/똑똑즈 스토리 이미지 Gems매뉴얼.txt"
)
DEFAULT_STEP_MACRO_PATH = Path(
    "/mnt/c/Users/jaekw/Pictures/똑똑즈 스토리/똑똑즈 스토리 기획/[똑똑즈 스토리 Step 0~9 최종 매크로 v1].txt"
)
DEFAULT_LIBRARY_PATH = Path(
    "/mnt/c/Users/jaekw/Pictures/똑똑즈 스토리/똑똑즈 스토리 기획/똑똑즈 스토리 시네마틱 미장센 & 질감 마스터 라이브러리 업데이트.txt"
)
DEFAULT_SCENE_PATH = Path(
    "/mnt/c/Users/jaekw/Pictures/똑똑즈 스토리/똑똑즈 스토리 기획/0418_금성대군1부_대본_장면분할.txt"
)


def resolve_local_path(raw: str | Path) -> Path:
    text = str(raw or "").strip()
    if not text:
        return Path("")
    normalized = re.sub(r"/+", "/", text.replace("\\", "/"))
    if os.name == "nt" and re.match(r"^/mnt/[a-zA-Z]/", normalized):
        drive = normalized[5].upper()
        tail = normalized[7:].replace("/", "\\")
        return Path(f"{drive}:\\{tail}")
    return Path(text)


PROMPT_BLOCK_RE = re.compile(
    r"^([SV]\d{3}(?:>[SV]\d{3})*)\s+(?:(Video)\s+)?Prompt\s*:\s*(.*?)\s*\|\|\|\s*$",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
SCENE_LINE_RE = re.compile(
    r"^\[S(?P<number>\d{3})\]\s*(?P<body>.*?)(?:\s*\(약\s*[\d.]+초\))?\s*$"
)
STEP_SECTION_RE = re.compile(
    r"^🛑\s*Step\s*(?P<num>\d+)\s*:\s*(?P<title>.+?)\s*$",
    re.MULTILINE,
)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@dataclass
class Scene:
    number: int
    label: str
    text: str
    raw_line: str


@dataclass
class PipelineConfig:
    instance_name: str = "story_worker1"
    display_name: str = ""
    site_target: str = "gemini"
    pipeline_mode: str = "manual_style"
    window_geometry: str = "620x520"
    log_visible: bool = True
    manual_path: str = str(DEFAULT_MANUAL_PATH)
    step_macro_path: str = str(DEFAULT_STEP_MACRO_PATH)
    library_path: str = str(DEFAULT_LIBRARY_PATH)
    scene_file_path: str = str(DEFAULT_SCENE_PATH)
    scene_file_slots: List[Dict[str, str]] = field(default_factory=list)
    gemini_url: str = "https://gemini.google.com/app"
    browser_profile_dir: str = ""
    output_root: str = ""
    start_scene: int = 1
    end_scene: int = 15
    batch_size: int = 15
    micro_batch_size: int = 5
    pre_input_delay_seconds: float = 4.0
    send_wait_seconds: float = 2.0
    poll_interval_seconds: float = 5.0
    stable_rounds_required: int = 2
    max_wait_seconds: float = 300.0
    rest_every_micro_batches: int = 0
    rest_seconds: float = 0.0
    human_typing_enabled: bool = False
    typing_speed_level: int = 5
    reset_chat_each_batch: bool = True
    open_notepad_live: bool = True
    manual_is_baked_into_gem: bool = True


@dataclass
class PromptBlock:
    header: str
    body: str
    start_number: int
    numbers: List[int]
    prompt_type: str

    @property
    def key(self) -> Tuple[int, str]:
        return (self.start_number, self.prompt_type)

    def render(self) -> str:
        return f"{self.header} Prompt : {self.body.strip()} |||"


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    blocks: List[PromptBlock] = field(default_factory=list)


@dataclass
class BatchWindow:
    batch_index: int
    scenes: List[Scene]
    micro_batches: List[List[Scene]]

    @property
    def label(self) -> str:
        if not self.scenes:
            return "empty"
        return f"S{self.scenes[0].number:03d}_S{self.scenes[-1].number:03d}"


@dataclass
class SessionPaths:
    session_root: Path
    final_live_txt: Path
    final_image_txt: Path
    final_video_txt: Path
    manifest_json: Path
    raw_dir: Path
    reports_dir: Path


@dataclass
class ResumeCandidate:
    session_root: Path
    scene_range_label: str
    start_scene: int
    end_scene: int
    last_complete_scene: int
    manifest: Dict[str, object] = field(default_factory=dict)


class LiveOutputWriter:
    def __init__(
        self,
        output_root: Path,
        scene_range_label: str,
        display_name: str = "",
        resume_candidate: ResumeCandidate | None = None,
    ):
        self.output_root = output_root
        self.output_root.mkdir(parents=True, exist_ok=True)
        stamp = now_stamp()
        self.resumed = resume_candidate is not None
        self.resumed_from_scene = resume_candidate.last_complete_scene if resume_candidate else None
        safe_name = re.sub(r'[\\/:*?"<>|]+', "_", str(display_name or "").strip())
        manifest_data = dict(resume_candidate.manifest) if resume_candidate else {}
        effective_range_label = resume_candidate.scene_range_label if resume_candidate else scene_range_label
        pretty_range = effective_range_label.replace("_", "~")
        if resume_candidate:
            self.session_root = resume_candidate.session_root
        else:
            pretty_stamp = datetime.now().strftime("%Y-%m-%d_%H시%M분%S초")
            folder_name = f"{pretty_stamp}_장면_{pretty_range}"
            if safe_name:
                folder_name = f"{pretty_stamp}_{safe_name}_장면_{pretty_range}"
            self.session_root = self.output_root / folder_name
        self.raw_dir = self.session_root / "원본응답"
        self.reports_dir = self.session_root / "검수리포트"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.final_live_txt = self._manifest_path_or_default(
            manifest_data.get("final_live_txt"),
            self.session_root / f"검수통과_전체프롬프트_{pretty_range}.txt",
        )
        self.final_image_txt = self._manifest_path_or_default(
            manifest_data.get("final_image_txt"),
            self.session_root / f"검수통과_이미지프롬프트_{pretty_range}.txt",
        )
        self.final_video_txt = self._manifest_path_or_default(
            manifest_data.get("final_video_txt"),
            self.session_root / f"검수통과_비디오프롬프트_{pretty_range}.txt",
        )
        self.manifest_json = self.session_root / "세션기록.json"
        for path in (self.final_live_txt, self.final_image_txt, self.final_video_txt):
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
        self._manifest: Dict[str, object] = manifest_data or {
            "created_at": stamp,
            "scene_range": effective_range_label,
            "steps": [],
            "display_name": str(display_name or "").strip(),
        }
        self._manifest["scene_range"] = effective_range_label
        self._manifest["display_name"] = str(display_name or "").strip()
        self._manifest["final_live_txt"] = str(self.final_live_txt)
        self._manifest["final_image_txt"] = str(self.final_image_txt)
        self._manifest["final_video_txt"] = str(self.final_video_txt)
        if self.resumed:
            resumed_log = list(self._manifest.get("resumed_runs", []))
            resumed_log.append(
                {
                    "resumed_at": stamp,
                    "continued_from_scene": self.resumed_from_scene,
                    "requested_range": scene_range_label,
                }
            )
            self._manifest["resumed_runs"] = resumed_log
        self._flush_manifest()

    def _flush_manifest(self) -> None:
        self.manifest_json.write_text(
            json.dumps(self._manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _manifest_path_or_default(raw: object, default_path: Path) -> Path:
        text = str(raw or "").strip()
        if not text:
            return default_path
        resolved = resolve_local_path(text)
        if resolved.is_absolute():
            return resolved
        return default_path

    @staticmethod
    def _parse_scene_range_label(raw: str) -> Tuple[int, int] | None:
        text = str(raw or "").strip().replace("~", "_")
        match = re.search(r"S(?P<start>\d{3})_S(?P<end>\d{3})", text)
        if not match:
            return None
        start = int(match.group("start"))
        end = int(match.group("end"))
        if start > end:
            start, end = end, start
        return start, end

    @classmethod
    def _read_saved_numbers(cls, candidate_dir: Path, manifest: Dict[str, object]) -> Tuple[set[int], set[int]]:
        validator = PromptValidator()
        scene_range_label = str(manifest.get("scene_range") or "")
        pretty_range = scene_range_label.replace("_", "~")
        possible_files = [
            cls._manifest_path_or_default(manifest.get("final_live_txt"), candidate_dir / f"검수통과_전체프롬프트_{pretty_range}.txt"),
            cls._manifest_path_or_default(manifest.get("final_image_txt"), candidate_dir / f"검수통과_이미지프롬프트_{pretty_range}.txt"),
            cls._manifest_path_or_default(manifest.get("final_video_txt"), candidate_dir / f"검수통과_비디오프롬프트_{pretty_range}.txt"),
        ]
        image_numbers: set[int] = set()
        video_numbers: set[int] = set()
        seen: set[Path] = set()
        for path in possible_files:
            if path in seen or not path.exists():
                continue
            seen.add(path)
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            for block in validator.parse_blocks(text):
                numbers = set(block.numbers or [block.start_number])
                if block.prompt_type == "image":
                    image_numbers.update(numbers)
                else:
                    video_numbers.update(numbers)
        return image_numbers, video_numbers

    @classmethod
    def find_resume_candidate(cls, output_root: Path, current_start_scene: int, display_name: str = "") -> ResumeCandidate | None:
        if current_start_scene <= 1 or not output_root.exists():
            return None
        safe_name = re.sub(r'[\\/:*?"<>|]+', "_", str(display_name or "").strip())
        best: ResumeCandidate | None = None
        best_key: Tuple[int, float] | None = None
        for child in output_root.iterdir():
            if not child.is_dir():
                continue
            manifest_path = child / "세션기록.json"
            if not manifest_path.exists():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            manifest_name = str(manifest.get("display_name") or "").strip()
            if safe_name:
                manifest_safe_name = re.sub(r'[\\/:*?"<>|]+', "_", manifest_name)
                if manifest_safe_name != safe_name and safe_name not in child.name:
                    continue
            range_info = cls._parse_scene_range_label(str(manifest.get("scene_range") or child.name))
            if not range_info:
                continue
            start_scene, end_scene = range_info
            if not (start_scene <= current_start_scene <= end_scene):
                continue
            image_numbers, video_numbers = cls._read_saved_numbers(child, manifest)
            complete_numbers = image_numbers & video_numbers
            last_complete = start_scene - 1
            for number in range(start_scene, end_scene + 1):
                if number in complete_numbers:
                    last_complete = number
                    continue
                break
            if last_complete != current_start_scene - 1:
                continue
            sort_key = (last_complete, child.stat().st_mtime)
            if best_key is None or sort_key > best_key:
                best_key = sort_key
                best = ResumeCandidate(
                    session_root=child,
                    scene_range_label=str(manifest.get("scene_range") or f"S{start_scene:03d}_S{end_scene:03d}"),
                    start_scene=start_scene,
                    end_scene=end_scene,
                    last_complete_scene=last_complete,
                    manifest=manifest,
                )
        return best

    def append_manifest_step(self, item: Dict[str, object]) -> None:
        steps = list(self._manifest.get("steps", []))
        steps.append(item)
        self._manifest["steps"] = steps
        self._flush_manifest()

    def write_raw(self, name: str, content: str) -> Path:
        path = self.raw_dir / name
        path.write_text(content, encoding="utf-8")
        return path

    def write_report(self, name: str, data: Dict[str, object]) -> Path:
        path = self.reports_dir / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def append_validated_prompts(self, title: str, content: str) -> None:
        with self.final_live_txt.open("a", encoding="utf-8") as f:
            f.write(content.strip())
            f.write("\n\n")
        blocks = PromptValidator().parse_blocks(content)
        image_lines = [block.render() for block in blocks if block.prompt_type == "image"]
        video_lines = [block.render() for block in blocks if block.prompt_type == "video"]
        if image_lines:
            with self.final_image_txt.open("a", encoding="utf-8") as f:
                f.write("\n\n".join(image_lines).strip())
                f.write("\n\n")
        if video_lines:
            with self.final_video_txt.open("a", encoding="utf-8") as f:
                f.write("\n\n".join(video_lines).strip())
                f.write("\n\n")

    @property
    def paths(self) -> SessionPaths:
        return SessionPaths(
            session_root=self.session_root,
            final_live_txt=self.final_live_txt,
            final_image_txt=self.final_image_txt,
            final_video_txt=self.final_video_txt,
            manifest_json=self.manifest_json,
            raw_dir=self.raw_dir,
            reports_dir=self.reports_dir,
        )


class StoryPromptSource:
    def __init__(self, cfg: PipelineConfig):
        self.cfg = cfg
        self.manual_text = ""
        if not cfg.manual_is_baked_into_gem:
            self.manual_text = resolve_local_path(cfg.manual_path).read_text(encoding="utf-8")
        self.step_macro_text = resolve_local_path(cfg.step_macro_path).read_text(encoding="utf-8")
        self.library_text = ""
        if not cfg.manual_is_baked_into_gem:
            self.library_text = resolve_local_path(cfg.library_path).read_text(encoding="utf-8")
        self.scene_file_text = resolve_local_path(cfg.scene_file_path).read_text(encoding="utf-8")
        self.step_sections = self._extract_step_sections(self.step_macro_text)
        self._validate_required_steps()
        self.scenes = self._parse_scenes(self.scene_file_text)

    def _validate_required_steps(self) -> None:
        required_steps = (6, 7) if self.cfg.pipeline_mode == "manual_style" else (5, 6, 7)
        missing = [num for num in required_steps if num not in self.step_sections]
        if missing:
            raise ValueError(f"Step 매크로 파일에 필요한 Step이 없습니다: {', '.join(f'Step {n}' for n in missing)}")
        empty = [num for num in required_steps if not (self.step_sections.get(num, {}).get('body') or '').strip()]
        if empty:
            raise ValueError(
                "Step 매크로 파일 본문이 비어 있습니다: "
                + ", ".join(f"Step {n}" for n in empty)
                + " 본문을 채워 주세요."
            )

    def _extract_step_sections(self, text: str) -> Dict[int, Dict[str, str]]:
        matches = list(STEP_SECTION_RE.finditer(text))
        result: Dict[int, Dict[str, str]] = {}
        for idx, match in enumerate(matches):
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            num = int(match.group("num"))
            result[num] = {
                "title": match.group("title").strip(),
                "body": text[start:end].strip(),
            }
        return result

    def _parse_scenes(self, text: str) -> List[Scene]:
        scenes: List[Scene] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = SCENE_LINE_RE.match(line)
            if not match:
                continue
            number = int(match.group("number"))
            scenes.append(
                Scene(
                    number=number,
                    label=f"S{number:03d}",
                    text=match.group("body").strip(),
                    raw_line=line,
                )
            )
        return scenes

    def scene_slice(self, start_num: int, end_num: int) -> List[Scene]:
        return [scene for scene in self.scenes if start_num <= scene.number <= end_num]

    def build_windows(self, start_num: int, end_num: int, batch_size: int, micro_batch_size: int) -> List[BatchWindow]:
        selected = self.scene_slice(start_num, end_num)
        windows: List[BatchWindow] = []
        for batch_index, base_idx in enumerate(range(0, len(selected), batch_size), start=1):
            batch_scenes = selected[base_idx : base_idx + batch_size]
            micro_batches = [
                batch_scenes[micro_idx : micro_idx + micro_batch_size]
                for micro_idx in range(0, len(batch_scenes), micro_batch_size)
            ]
            windows.append(BatchWindow(batch_index=batch_index, scenes=batch_scenes, micro_batches=micro_batches))
        return windows


class PromptComposer:
    def __init__(self, source: StoryPromptSource):
        self.source = source

    @staticmethod
    def _render_scene_chunk(scenes: Sequence[Scene]) -> str:
        return "\n".join(f"[{scene.label}] {scene.text}" for scene in scenes)

    def _manual_sync_block(self) -> str:
        if self.source.cfg.manual_is_baked_into_gem:
            return (
                "[매뉴얼 상태]\n"
                "- 현재 Gem 안에 매뉴얼이 이미 들어가 있다고 가정합니다.\n"
                "- 아래 작업에서는 장면/라이브러리/Step 원문만 기준으로 삼아 주세요.\n"
            )
        return (
            "[매뉴얼 전문]\n"
            f"{self.source.manual_text.strip()}\n"
            "[매뉴얼 끝]\n"
        )

    def build_step5_prompt(self, batch: BatchWindow) -> str:
        section = self.source.step_sections[5]["body"]
        scene_chunk = self._render_scene_chunk(batch.scenes)
        return (
            "[자동화 실행 모드]\n"
            "- 당신은 지금 Step 5만 수행합니다.\n"
            "- 프롬프트는 아직 만들지 말고, 기획 요약만 출력하세요.\n"
            "- 이 배치는 이후 Step 6과 Step 7 자동화의 기준이 되므로 번호를 정확히 지켜 주세요.\n\n"
            f"{self._manual_sync_block()}\n"
            "[미장센 라이브러리]\n"
            f"{self.source.library_text.strip()}\n\n"
            "[Step 5 원문]\n"
            f"{section}\n\n"
            f"[이번 배치 범위]\n{batch.scenes[0].label} ~ {batch.scenes[-1].label}\n\n"
            "[장면 대본]\n"
            f"{scene_chunk}\n"
        )

    def build_manual_style_step6_prompt(self, micro_scenes: Sequence[Scene]) -> str:
        section = self.source.step_sections[6]["body"]
        scene_chunk = self._render_scene_chunk(micro_scenes)
        return (
            f"{section.strip()}\n\n"
            "[장면 묶음]\n"
            f"{scene_chunk}\n"
        )

    def build_step6_prompt(self, batch: BatchWindow, micro_scenes: Sequence[Scene], step5_plan: str) -> str:
        section = self.source.step_sections[6]["body"]
        scene_chunk = self._render_scene_chunk(micro_scenes)
        return (
            "[자동화 실행 모드]\n"
            "- 당신은 지금 Step 6만 수행합니다.\n"
            "- 아래 Step 5 기획안을 참고해 이번 마이크로배치 장면만 처리하세요.\n"
            "- 이번 출력은 이미지 프롬프트 + 비디오 프롬프트를 모두 포함해야 합니다.\n"
            "- 번호 누락 금지, 다른 인삿말 금지.\n\n"
            f"{self._manual_sync_block()}\n"
            "[미장센 라이브러리]\n"
            f"{self.source.library_text.strip()}\n\n"
            "[Step 5 기획안]\n"
            f"{step5_plan.strip()}\n\n"
            "[Step 6 원문]\n"
            f"{section}\n\n"
            f"[이번 마이크로배치 범위]\n{micro_scenes[0].label} ~ {micro_scenes[-1].label}\n\n"
            "[장면 대본]\n"
            f"{scene_chunk}\n\n"
            "[출력 추가 규칙]\n"
            "- 오직 프롬프트 본문만 출력하세요.\n"
            "- 이미지 프롬프트는 반드시 `S### Prompt : ... |||` 또는 `S###>S### Prompt : ... |||` 형식입니다.\n"
            "- 비디오 프롬프트는 반드시 `V### Prompt : ... |||` 또는 `V###>V### Prompt : ... |||` 형식입니다.\n"
        )

    def build_step7_prompt(self, micro_scenes: Sequence[Scene], draft_text: str, code_validation_errors: Sequence[str]) -> str:
        section = self.source.step_sections[7]["body"]
        scene_chunk = self._render_scene_chunk(micro_scenes)
        error_block = "\n".join(f"- {item}" for item in code_validation_errors) if code_validation_errors else "- 코드 검수 1차 통과"
        return (
            "[자동화 실행 모드]\n"
            "- 당신은 지금 Step 7 검수자입니다.\n"
            "- 아래 체크리스트를 바탕으로 초안을 검수하고, 최종적으로 이번 묶음 전체 프롬프트를 다시 완성본으로 출력하세요.\n"
            "- 사람이 읽는 설명도 좋지만, 자동화 파이프라인이 읽어야 하므로 아래 출력 형식을 절대 깨지 마세요.\n\n"
            "[반드시 지킬 출력 형식]\n"
            "[검수요약]\n"
            "한두 줄 요약\n"
            "[문제번호]\n"
            "문제가 있으면 번호와 이유, 없으면 '없음'\n"
            "[최종프롬프트]\n"
            "이번 묶음의 이미지/비디오 프롬프트를 전부 다시 출력\n"
            "[끝]\n\n"
            "[Step 7 원문]\n"
            f"{section}\n\n"
            "[이번 묶음 장면]\n"
            f"{scene_chunk}\n\n"
            "[코드 1차 검수 결과]\n"
            f"{error_block}\n\n"
            "[Step 6 초안]\n"
            f"{draft_text.strip()}\n"
        )

    def build_manual_style_step7_prompt(
        self,
        micro_scenes: Sequence[Scene],
        current_text: str = "",
        validation_errors: Sequence[str] = (),
    ) -> str:
        section = self.source.step_sections[7]["body"]
        scene_chunk = self._render_scene_chunk(micro_scenes)
        error_block = "\n".join(f"- {item}" for item in validation_errors) if validation_errors else "- 없음"
        return (
            f"{section.strip()}\n\n"
            "[자동화 범위 고정]\n"
            f"- 이번 검수 범위는 {micro_scenes[0].label} ~ {micro_scenes[-1].label} 입니다.\n"
            "- 이 범위 밖 번호는 절대로 새로 쓰지 마세요.\n"
            "- `S061>S062` 같은 연결 라벨은 왼쪽 시작 번호 S061의 단 1개 컷입니다. S062를 대체하지 않습니다.\n"
            "- 마지막 묶음이 5개뿐이면 그 5개만 검수하고, 다음 번호를 이어 쓰지 마세요.\n"
            "- 문제가 있는 번호만 다시 출력하라는 지시가 있더라도, 범위 밖 번호는 출력하지 마세요.\n\n"
            "[이번 묶음 장면]\n"
            f"{scene_chunk}\n\n"
            "[현재 기계 검수 오류]\n"
            f"{error_block}\n\n"
            "[현재 저장 후보]\n"
            f"{current_text.strip()}\n"
        )

    def build_repair_prompt(self, micro_scenes: Sequence[Scene], broken_text: str, errors: Sequence[str]) -> str:
        scene_chunk = self._render_scene_chunk(micro_scenes)
        error_block = "\n".join(f"- {item}" for item in errors)
        return (
            "[자동화 복구 모드]\n"
            "- 바로 직전 검수 결과가 기계 파싱에 실패했습니다.\n"
            "- 설명을 줄이고 최종 프롬프트 블록만 정확히 다시 써 주세요.\n"
            "- 아래 형식을 절대 깨지 마세요.\n\n"
            "[출력 형식]\n"
            "[최종프롬프트]\n"
            "S### Prompt : ... |||\n"
            "V### Prompt : ... |||\n"
            "[끝]\n\n"
            "[이번 묶음 장면]\n"
            f"{scene_chunk}\n\n"
            "[현재 오류]\n"
            f"{error_block}\n\n"
            "[잘못된 응답]\n"
            f"{broken_text.strip()}\n"
        )

    def build_missing_blocks_prompt(
        self,
        micro_scenes: Sequence[Scene],
        current_text: str,
        missing_items: Sequence[tuple[int, str]],
    ) -> str:
        scene_chunk = self._render_scene_chunk(micro_scenes)
        request_lines = []
        for number, prompt_type in missing_items:
            if prompt_type == "image":
                request_lines.append(f"- S{number:03d} 이미지 프롬프트 1개")
            else:
                request_lines.append(f"- V{number:03d} 비디오 프롬프트 1개")
        request_block = "\n".join(request_lines) if request_lines else "- 없음"
        return (
            "[누락 프롬프트만 보완]\n"
            "- 아래 현재 최종본에서 빠진 프롬프트만 다시 써 주세요.\n"
            "- 이미 있는 번호는 다시 쓰지 말고, 빠진 번호만 출력하세요.\n"
            "- 이번 자동화에서는 비디오 생략 금지입니다. 빠진 비디오가 있으면 반드시 작성하세요.\n"
            "- 설명, 브리핑, 머리말 없이 프롬프트 줄만 출력하세요.\n"
            "- 이미지면 `S### Prompt : ... |||`, 비디오면 `V### Prompt : ... |||` 형식만 사용하세요.\n\n"
            "[이번 묶음 장면]\n"
            f"{scene_chunk}\n\n"
            "[현재까지 저장 후보]\n"
            f"{current_text.strip()}\n\n"
            "[꼭 다시 써야 하는 누락 번호]\n"
            f"{request_block}\n"
        )


class PromptValidator:
    VIDEO_HINTS = (
        "absolutely preserve 3D text sharp",
        "no character transition",
        "camera work",
        "starting @s",
        "ending @s",
    )
    NO_CHANGE_HINTS = (
        "추가로 재작성할 프롬프트가 없습니다",
        "추가로 수정할 위반 사항이 발견되지 않았습니다",
        "위반 사항이 모두 완벽히 클리어",
        "모든 규칙이 완벽하게 적용되어",
        "현재 모든 프롬프트가 규칙을 완벽히 충족",
        "추가적인 수정 및 재출력이 필요하지 않습니다",
        "중복된 재작성 렌더링은 생략",
        "이미 완벽하게 수행 및 검증을 마친 상태",
        "다음 대본",
        "최종 검수 완료",
    )
    STEP_ACK_HINTS = (
        "ready.",
        "ready",
        "준비 완료",
        "준비됐습니다",
        "준비되었습니다",
    )

    def parse_blocks(self, text: str) -> List[PromptBlock]:
        blocks: List[PromptBlock] = []
        for match in PROMPT_BLOCK_RE.finditer(text):
            header = match.group(1).strip()
            is_video_header = bool((match.group(2) or "").strip())
            body = match.group(3).strip()
            number_matches = [int(item[1:]) for item in re.findall(r"[SV]\d{3}", header, re.IGNORECASE)]
            prompt_type = "video" if is_video_header or header.upper().startswith("V") else self._classify_block(body)
            blocks.append(
                PromptBlock(
                    header=header,
                    body=body,
                    start_number=number_matches[0],
                    numbers=number_matches,
                    prompt_type=prompt_type,
                )
            )
        return blocks

    def _classify_block(self, body: str) -> str:
        lowered = body.lower()
        if re.match(r"^\s*@s\d{3}", lowered):
            return "video"
        if any(hint in lowered for hint in self.VIDEO_HINTS):
            return "video"
        return "image"

    def extract_final_prompt_text(self, text: str) -> str:
        marker = re.search(r"\[최종프롬프트\](.*?)(?:\n\[끝\]|\Z)", text, re.DOTALL)
        if marker:
            return marker.group(1).strip()
        return text.strip()

    def is_no_change_response(self, text: str) -> bool:
        raw = str(text or "").strip()
        if not raw:
            return False
        if self.parse_blocks(raw):
            return False
        lowered = raw.lower()
        return any(hint in lowered for hint in self.NO_CHANGE_HINTS)

    def is_step_ack_response(self, text: str) -> bool:
        raw = str(text or "").strip()
        if not raw:
            return False
        if self.parse_blocks(raw):
            return False
        lowered = raw.lower()
        compact = re.sub(r"\s+", " ", lowered).strip()
        return compact in self.STEP_ACK_HINTS

    def _video_optional_numbers(self, blocks: Sequence[PromptBlock]) -> set[int]:
        optional_numbers: set[int] = set()
        for block in blocks:
            if block.prompt_type != "image":
                continue
            body = block.body or ""
            if re.search(r"@S[78]\d{2}", body, re.IGNORECASE):
                optional_numbers.add(block.start_number)
        return optional_numbers

    def validate(self, text: str, expected_scenes: Sequence[Scene]) -> ValidationResult:
        errors: List[str] = []
        blocks = self.parse_blocks(text)
        if not blocks:
            return ValidationResult(ok=False, errors=["프롬프트 블록을 하나도 찾지 못했습니다."], blocks=[])

        expected_numbers = [scene.number for scene in expected_scenes]
        allowed_numbers = set(expected_numbers)
        in_scope_blocks = [
            block
            for block in blocks
            if block.start_number in allowed_numbers
        ]
        if not in_scope_blocks:
            errors.append("현재 묶음에 해당하는 프롬프트 블록이 없습니다.")

        grouped: Dict[Tuple[int, str], PromptBlock] = {}
        duplicate_keys: List[Tuple[int, str]] = []
        for block in in_scope_blocks:
            if block.key in grouped:
                duplicate_keys.append(block.key)
            grouped[block.key] = block

        for key in duplicate_keys:
            number, prompt_type = key
            head = f"S{number:03d}"
            errors.append(f"{head} {prompt_type} 프롬프트가 중복되었습니다.")

        coverage: Dict[str, set[int]] = {"image": set(), "video": set()}
        for block in in_scope_blocks:
            coverage.setdefault(block.prompt_type, set()).add(block.start_number)
        optional_video_numbers = self._video_optional_numbers(in_scope_blocks)

        for number in expected_numbers:
            if number not in coverage.get("image", set()):
                errors.append(f"S{number:03d} 이미지 프롬프트가 없습니다.")
            if number not in coverage.get("video", set()) and number not in optional_video_numbers:
                errors.append(f"S{number:03d} 비디오 프롬프트가 없습니다.")

        for block in in_scope_blocks:
            rendered = block.render()
            if "|||" not in rendered:
                errors.append(f"{block.header} 종료 구분자 `|||` 가 없습니다.")

        return ValidationResult(ok=not errors, errors=errors, blocks=in_scope_blocks)

    def missing_items_from_errors(self, errors: Sequence[str]) -> List[tuple[int, str]]:
        items: List[tuple[int, str]] = []
        for error in errors:
            match = re.match(r"^S(\d{3})\s+(이미지|비디오)\s+프롬프트가 없습니다\.$", str(error).strip())
            if not match:
                continue
            prompt_type = "image" if match.group(2) == "이미지" else "video"
            items.append((int(match.group(1)), prompt_type))
        return items

    def normalize_text(self, blocks: Sequence[PromptBlock], expected_scenes: Sequence[Scene]) -> str:
        order = {scene.number: idx for idx, scene in enumerate(expected_scenes)}
        normalized = sorted(
            list(blocks),
            key=lambda item: (order.get(item.start_number, 9999), 0 if item.prompt_type == "image" else 1),
        )
        return "\n\n".join(block.render() for block in normalized)

    def merge_partial_with_draft(self, reviewed: ValidationResult, draft: ValidationResult, expected_scenes: Sequence[Scene]) -> str:
        merged: Dict[Tuple[int, str], PromptBlock] = {block.key: block for block in draft.blocks}
        for block in reviewed.blocks:
            merged[block.key] = block
        return self.normalize_text(list(merged.values()), expected_scenes)


class StoryPipeline:
    def __init__(
        self,
        cfg: PipelineConfig,
        runner,
        log: Callable[[str], None],
        stop_event: threading.Event,
        status_callback: Optional[Callable[[dict], None]] = None,
    ):
        self.cfg = cfg
        self.runner = runner
        self.log = log
        self.stop_event = stop_event
        self.status_callback = status_callback
        self.source = StoryPromptSource(cfg)
        self.composer = PromptComposer(self.source)
        self.validator = PromptValidator()
        self.live_file_opened = False

    def _status(self, **payload) -> None:
        if self.status_callback is None:
            return
        try:
            self.status_callback(payload)
        except Exception:
            pass

    def _check_stop(self) -> None:
        if self.stop_event.is_set():
            raise RuntimeError("사용자 중지 요청")

    def _wait_before_retry(self, seconds: float, step_label: str, attempt: int) -> None:
        wait_seconds = max(1.0, float(seconds))
        self._status(
            status="자동 재시도 대기",
            detail=f"{step_label} 실패 후 같은 자리에서 {attempt}회차 재시도 준비",
            current_step="자동 재시도",
            countdown_label="재시도까지",
            countdown_remaining_seconds=wait_seconds,
        )
        end_at = time.time() + wait_seconds
        while time.time() < end_at:
            self._check_stop()
            time.sleep(0.2)

    def _should_reset_browser_after_send_failure(self, exc: Exception, attempt: int) -> bool:
        text = str(exc or "")
        lowered = text.lower()
        if attempt < 2:
            return False
        pointer_blocked = "intercepts pointer events" in lowered
        offscreen = "outside of the viewport" in lowered
        click_timeout = "locator.click: timeout" in lowered
        input_focus_fail = "입력창 포커스 실패" in text
        return pointer_blocked or offscreen or click_timeout or input_focus_fail

    def _recover_browser_for_send_retry(self, step_label: str, attempt: int) -> None:
        self.log(
            f"🧭 {step_label} 입력 복구 | 같은 클릭 실패가 이어져 저장된 URL로 다시 들어갑니다. "
            f"(재시도 {attempt}회차)"
        )
        self._status(
            status="브라우저 복구 중",
            detail=f"{step_label} 저장된 URL 재진입 후 입력창 재정렬",
            current_step="브라우저 복구",
        )
        self.runner.reset_conversation()

    def _send_prompt_resilient(self, prompt: str, step_label: str) -> str:
        attempt = 1
        while True:
            self._check_stop()
            label = step_label if attempt == 1 else f"{step_label}_auto_retry{attempt - 1}"
            try:
                return self.runner.send_prompt(prompt, step_label=label)
            except Exception as exc:
                if self.stop_event.is_set():
                    raise
                self.log(
                    f"⚠️ {step_label} 전송/응답 확인 실패 | 같은 자리에서 자동 재시도 {attempt}회차 | {exc}"
                )
                if self._should_reset_browser_after_send_failure(exc, attempt):
                    try:
                        self._recover_browser_for_send_retry(step_label, attempt)
                    except Exception as recovery_exc:
                        self.log(f"⚠️ 저장된 URL 복구도 실패했습니다 | {step_label} | {recovery_exc}")
                self._wait_before_retry(
                    max(5.0, float(getattr(self.cfg, "poll_interval_seconds", 5.0) or 5.0)),
                    step_label,
                    attempt,
                )
                attempt += 1

    def _open_live_file_if_needed(self, path: Path) -> None:
        if not self.cfg.open_notepad_live:
            return
        try:
            if hasattr(os, "startfile"):
                os.startfile(str(path))  # type: ignore[attr-defined]
                return
        except Exception:
            pass

    def _take_random_break_if_needed(
        self,
        completed_micro_batches: int,
        total_micro_batches: int,
        total_batches: int,
        batch: BatchWindow,
        micro_index: int,
        completed_scenes: int,
        total_scenes: int,
        current_range: str,
    ) -> None:
        every = max(0, int(self.cfg.rest_every_micro_batches or 0))
        base_seconds = max(0.0, float(self.cfg.rest_seconds or 0.0))
        if every <= 0 or base_seconds <= 0:
            return
        if completed_micro_batches <= 0 or completed_micro_batches >= total_micro_batches:
            return
        if completed_micro_batches % every != 0:
            return

        actual_seconds = round(base_seconds * random.uniform(0.7, 1.3), 1)
        self.log(
            f"😴 사람처럼 잠깐 쉬기 | {completed_micro_batches}묶음 처리 후 {actual_seconds:.1f}초 휴식"
        )
        self._status(
            status="잠깐 쉬는 중",
            detail=f"{completed_micro_batches}묶음 끝나서 {actual_seconds:.1f}초 쉬는 중",
            current_step="휴식",
            scene_range=current_range.replace("_", " ~ "),
            batch_index=batch.batch_index,
            batch_total=total_batches,
            micro_index=completed_micro_batches,
            micro_total=total_micro_batches,
            batch_micro_index=micro_index,
            batch_micro_total=len(batch.micro_batches),
            scene_done=completed_scenes,
            scene_total=total_scenes,
            countdown_label="휴식",
            countdown_remaining_seconds=actual_seconds,
        )
        end_at = time.time() + actual_seconds
        while time.time() < end_at:
            self._check_stop()
            time.sleep(0.2)
        try:
            import subprocess

            subprocess.Popen(["cmd.exe", "/c", "start", "notepad.exe", str(path)])
        except Exception:
            pass

    def run(self) -> SessionPaths:
        effective_batch_size = self.cfg.micro_batch_size if self.cfg.pipeline_mode == "manual_style" else self.cfg.batch_size
        windows = self.source.build_windows(
            start_num=self.cfg.start_scene,
            end_num=self.cfg.end_scene,
            batch_size=effective_batch_size,
            micro_batch_size=self.cfg.micro_batch_size,
        )
        if not windows:
            raise ValueError("선택한 범위에서 장면을 찾지 못했습니다.")

        scene_range_label = f"S{windows[0].scenes[0].number:03d}_S{windows[-1].scenes[-1].number:03d}"
        total_batches = len(windows)
        total_micro_batches = sum(len(batch.micro_batches) for batch in windows)
        total_scenes = sum(len(batch.scenes) for batch in windows)
        completed_micro_batches = 0
        completed_scenes = 0
        output_root = Path(self.cfg.output_root)
        resume_candidate = LiveOutputWriter.find_resume_candidate(
            output_root,
            self.cfg.start_scene,
            self.cfg.display_name,
        )
        writer = LiveOutputWriter(
            output_root,
            scene_range_label,
            self.cfg.display_name,
            resume_candidate=resume_candidate,
        )
        self.runner.open_browser()
        if resume_candidate:
            self.log(
                f"♻️ 기존 세션 이어 저장 | 마지막 완성 S{resume_candidate.last_complete_scene:03d} | {writer.session_root}"
            )
        self.log(f"🧠 똑똑즈 워커 세션 시작 | 범위 {scene_range_label}")
        self.log(f"📝 검수 통과 프롬프트 저장 파일: {writer.final_live_txt}")
        self.log(f"🎛️ 실행 모드: {self.cfg.pipeline_mode}")
        self._status(
            status="세션 시작",
            detail=f"범위 {scene_range_label}",
            current_step="준비",
            scene_range=scene_range_label.replace("_", " ~ "),
            batch_index=0,
            batch_total=total_batches,
            micro_index=0,
            micro_total=total_micro_batches,
            scene_done=0,
            scene_total=total_scenes,
        )

        for batch in windows:
            self._check_stop()
            self.log(f"📦 작업 묶음 {batch.batch_index} 시작 | {batch.label}")
            self._status(
                status="작업 묶음 시작",
                detail=f"{batch.label} 준비",
                current_step="묶음 준비",
                scene_range=batch.label.replace("_", " ~ "),
                batch_index=batch.batch_index,
                batch_total=total_batches,
                micro_index=completed_micro_batches,
                micro_total=total_micro_batches,
                scene_done=completed_scenes,
                scene_total=total_scenes,
            )
            if self.cfg.reset_chat_each_batch:
                self.runner.reset_conversation()
                self.log("🧹 새 채팅 기준으로 배치 시작")
                self._status(
                    status="새 채팅 준비",
                    detail=f"{batch.label} 새 대화 상태 맞춤",
                    current_step="채팅 초기화",
                    scene_range=batch.label.replace("_", " ~ "),
                    batch_index=batch.batch_index,
                    batch_total=total_batches,
                    micro_index=completed_micro_batches,
                    micro_total=total_micro_batches,
                    scene_done=completed_scenes,
                    scene_total=total_scenes,
                )

            step5_text = ""
            if self.cfg.pipeline_mode == "step5_step7":
                step5_prompt = self.composer.build_step5_prompt(batch)
                self._status(
                    status="Step5 생성",
                    detail=f"{batch.label} 기획 요약 요청",
                    current_step="Step5",
                    scene_range=batch.label.replace("_", " ~ "),
                    batch_index=batch.batch_index,
                    batch_total=total_batches,
                    micro_index=completed_micro_batches,
                    micro_total=total_micro_batches,
                    scene_done=completed_scenes,
                    scene_total=total_scenes,
                )
                step5_text = self._send_prompt_resilient(step5_prompt, step_label=f"{batch.label}_step5")
                writer.write_raw(f"{batch.label}_step5.txt", step5_text)
                writer.append_manifest_step(
                    {"batch": batch.label, "step": 5, "raw_file": f"{batch.label}_step5.txt"}
                )

            for micro_index, micro_scenes in enumerate(batch.micro_batches, start=1):
                self._check_stop()
                micro_label = f"{micro_scenes[0].label}_{micro_scenes[-1].label}"
                self.log(f"🎬 Step6 생성 시작 | {micro_label}")
                self._status(
                    status="Step6 생성",
                    detail=f"{micro_label} 프롬프트 초안 요청",
                    current_step="Step6",
                    scene_range=micro_label.replace("_", " ~ "),
                    batch_index=batch.batch_index,
                    batch_total=total_batches,
                    micro_index=completed_micro_batches + 1,
                    micro_total=total_micro_batches,
                    batch_micro_index=micro_index,
                    batch_micro_total=len(batch.micro_batches),
                    scene_done=completed_scenes,
                    scene_total=total_scenes,
                )

                if self.cfg.pipeline_mode == "manual_style":
                    step6_prompt = self.composer.build_manual_style_step6_prompt(micro_scenes)
                else:
                    step6_prompt = self.composer.build_step6_prompt(batch, micro_scenes, step5_text)
                step6_text = self._send_prompt_resilient(step6_prompt, step_label=f"{micro_label}_step6")
                writer.write_raw(f"{micro_label}_step6_draft.txt", step6_text)

                draft_validation = self.validator.validate(step6_text, micro_scenes)
                if not draft_validation.blocks:
                    for retry_index in range(1, 3):
                        if self.validator.is_step_ack_response(step6_text):
                            self.log(f"🔁 Step6 응답이 준비 신호만 와서 다시 요청 {retry_index}회차 | {micro_label}")
                        else:
                            self.log(f"🔁 Step6 프롬프트가 없어 다시 요청 {retry_index}회차 | {micro_label}")
                        self._status(
                            status="Step6 다시 요청",
                            detail=f"{micro_label} Step6 재요청 {retry_index}회차",
                            current_step="Step6 재요청",
                            scene_range=micro_label.replace("_", " ~ "),
                            batch_index=batch.batch_index,
                            batch_total=total_batches,
                            micro_index=completed_micro_batches + 1,
                            micro_total=total_micro_batches,
                            batch_micro_index=micro_index,
                            batch_micro_total=len(batch.micro_batches),
                            scene_done=completed_scenes,
                            scene_total=total_scenes,
                        )
                        step6_text = self._send_prompt_resilient(step6_prompt, step_label=f"{micro_label}_step6_retry{retry_index}")
                        writer.write_raw(f"{micro_label}_step6_retry{retry_index}.txt", step6_text)
                        draft_validation = self.validator.validate(step6_text, micro_scenes)
                        if draft_validation.blocks:
                            break
                    if not draft_validation.blocks:
                        writer.write_report(
                            f"{micro_label}_step6_validation.json",
                            {"ok": False, "errors": draft_validation.errors},
                        )
                        raise RuntimeError(
                            f"{micro_label} Step6 응답에서 프롬프트를 찾지 못했습니다. 현재 응답: {step6_text[:120].strip() or '(비어 있음)'}"
                        )
                writer.write_report(
                    f"{micro_label}_step6_validation.json",
                    {"ok": draft_validation.ok, "errors": draft_validation.errors},
                )
                if draft_validation.ok:
                    self.log(f"✅ Step6 1차 형식 검수 통과 | {micro_label}")
                else:
                    self.log(f"⚠️ Step6 1차 형식 이슈 {len(draft_validation.errors)}개 | {micro_label}")

                self._status(
                    status="Step7 검수",
                    detail=f"{micro_label} 검수 요청",
                    current_step="Step7",
                    scene_range=micro_label.replace("_", " ~ "),
                    batch_index=batch.batch_index,
                    batch_total=total_batches,
                    micro_index=completed_micro_batches + 1,
                    micro_total=total_micro_batches,
                    batch_micro_index=micro_index,
                    batch_micro_total=len(batch.micro_batches),
                    scene_done=completed_scenes,
                    scene_total=total_scenes,
                )
                if self.cfg.pipeline_mode == "manual_style":
                    step7_prompt = self.composer.build_manual_style_step7_prompt(
                        micro_scenes,
                        current_text=step6_text,
                        validation_errors=draft_validation.errors,
                    )
                else:
                    step7_prompt = self.composer.build_step7_prompt(micro_scenes, step6_text, draft_validation.errors)
                step7_text = self._send_prompt_resilient(step7_prompt, step_label=f"{micro_label}_step7")
                writer.write_raw(f"{micro_label}_step7_review.txt", step7_text)

                final_candidate = self.validator.extract_final_prompt_text(step7_text)
                final_validation = self.validator.validate(final_candidate, micro_scenes)
                if not final_validation.ok:
                    merged_candidate = self.validator.merge_partial_with_draft(final_validation, draft_validation, micro_scenes)
                    merged_validation = self.validator.validate(merged_candidate, micro_scenes)
                    if merged_validation.ok or len(merged_validation.errors) < len(final_validation.errors):
                        final_candidate = merged_candidate
                        final_validation = merged_validation

                if not final_validation.ok:
                    if self.cfg.pipeline_mode == "manual_style":
                        for retry_index in range(1, 3):
                            self.log(f"🔁 Step7 다시 요청 {retry_index}회차 | {micro_label}")
                            self._status(
                                status="Step7 다시 요청",
                                detail=f"{micro_label} Step7 재검수 {retry_index}회차",
                                current_step="Step7 재검수",
                                scene_range=micro_label.replace("_", " ~ "),
                                batch_index=batch.batch_index,
                                batch_total=total_batches,
                                micro_index=completed_micro_batches + 1,
                                micro_total=total_micro_batches,
                                batch_micro_index=micro_index,
                                batch_micro_total=len(batch.micro_batches),
                                scene_done=completed_scenes,
                                scene_total=total_scenes,
                            )
                            retry_prompt = self.composer.build_manual_style_step7_prompt(
                                micro_scenes,
                                current_text=final_candidate,
                                validation_errors=final_validation.errors,
                            )
                            retry_text = self._send_prompt_resilient(retry_prompt, step_label=f"{micro_label}_step7_retry{retry_index}")
                            writer.write_raw(f"{micro_label}_step7_retry{retry_index}.txt", retry_text)
                            if self.validator.is_no_change_response(retry_text):
                                self.log(f"✅ Step7 재검수 응답: 추가 수정 없음 | {micro_label}")
                                break
                            retry_candidate = self.validator.extract_final_prompt_text(retry_text)
                            retry_validation = self.validator.validate(retry_candidate, micro_scenes)
                            if retry_validation.ok:
                                final_candidate = retry_candidate
                                final_validation = retry_validation
                            else:
                                merged_candidate = self.validator.merge_partial_with_draft(
                                    retry_validation,
                                    final_validation,
                                    micro_scenes,
                                )
                                merged_validation = self.validator.validate(merged_candidate, micro_scenes)
                                if merged_validation.ok or len(merged_validation.errors) < len(final_validation.errors):
                                    final_candidate = merged_candidate
                                    final_validation = merged_validation
                            if final_validation.ok:
                                break
                    else:
                        self.log(f"🩹 Step7 결과 보정 시도 | {micro_label}")
                        self._status(
                            status="자동 보정",
                            detail=f"{micro_label} 형식 보정 중",
                            current_step="보정",
                            scene_range=micro_label.replace("_", " ~ "),
                            batch_index=batch.batch_index,
                            batch_total=total_batches,
                            micro_index=completed_micro_batches + 1,
                            micro_total=total_micro_batches,
                            batch_micro_index=micro_index,
                            batch_micro_total=len(batch.micro_batches),
                            scene_done=completed_scenes,
                            scene_total=total_scenes,
                        )
                        repair_prompt = self.composer.build_repair_prompt(micro_scenes, step7_text, final_validation.errors)
                        repair_text = self._send_prompt_resilient(repair_prompt, step_label=f"{micro_label}_repair")
                        writer.write_raw(f"{micro_label}_repair.txt", repair_text)
                        repaired_candidate = self.validator.extract_final_prompt_text(repair_text)
                        repaired_validation = self.validator.validate(repaired_candidate, micro_scenes)
                        if repaired_validation.ok:
                            final_candidate = repaired_candidate
                            final_validation = repaired_validation

                if not final_validation.ok:
                    missing_items = self.validator.missing_items_from_errors(final_validation.errors)
                    if missing_items:
                        for refill_index in range(1, 3):
                            self.log(f"🧩 누락 프롬프트 보완 {refill_index}회차 | {micro_label}")
                            self._status(
                                status="누락 프롬프트 보완",
                                detail=f"{micro_label} 빠진 번호 보완 {refill_index}회차",
                                current_step="누락 보완",
                                scene_range=micro_label.replace("_", " ~ "),
                                batch_index=batch.batch_index,
                                batch_total=total_batches,
                                micro_index=completed_micro_batches + 1,
                                micro_total=total_micro_batches,
                                batch_micro_index=micro_index,
                                batch_micro_total=len(batch.micro_batches),
                                scene_done=completed_scenes,
                                scene_total=total_scenes,
                            )
                            refill_prompt = self.composer.build_missing_blocks_prompt(
                                micro_scenes,
                                final_candidate,
                                missing_items,
                            )
                            refill_text = self._send_prompt_resilient(refill_prompt, step_label=f"{micro_label}_missing_refill{refill_index}")
                            writer.write_raw(f"{micro_label}_missing_refill{refill_index}.txt", refill_text)
                            refill_candidate = self.validator.extract_final_prompt_text(refill_text)
                            refill_validation = self.validator.validate(refill_candidate, micro_scenes)
                            if refill_validation.blocks:
                                merged_candidate = self.validator.merge_partial_with_draft(
                                    refill_validation,
                                    final_validation,
                                    micro_scenes,
                                )
                                merged_validation = self.validator.validate(merged_candidate, micro_scenes)
                                if merged_validation.ok or len(merged_validation.errors) < len(final_validation.errors):
                                    final_candidate = merged_candidate
                                    final_validation = merged_validation
                            if final_validation.ok:
                                break

                if not final_validation.ok:
                    writer.write_raw(f"{micro_label}_최종후보_실패직전.txt", final_candidate)
                    writer.write_report(
                        f"{micro_label}_final_validation_failed.json",
                        {"ok": False, "errors": final_validation.errors},
                    )
                    raise RuntimeError(f"{micro_label} 최종 검수 결과를 기계적으로 확정하지 못했습니다: {' | '.join(final_validation.errors)}")

                normalized_final = self.validator.normalize_text(final_validation.blocks, micro_scenes)
                writer.append_validated_prompts(micro_label, normalized_final)
                if not self.live_file_opened:
                    self._open_live_file_if_needed(writer.final_live_txt)
                    self.live_file_opened = True
                writer.write_raw(f"{micro_label}_final_validated.txt", normalized_final)
                writer.write_report(
                    f"{micro_label}_final_validation.json",
                    {"ok": True, "errors": [], "count": len(final_validation.blocks)},
                )
                writer.append_manifest_step(
                    {
                        "batch": batch.label,
                        "micro_label": micro_label,
                        "step": "validated",
                        "scene_start": micro_scenes[0].number,
                        "scene_end": micro_scenes[-1].number,
                        "final_file": f"{micro_label}_final_validated.txt",
                    }
                )
                self.log(f"💾 검수 통과 저장 | {micro_label}")
                completed_micro_batches += 1
                completed_scenes += len(micro_scenes)
                self._status(
                    status="저장 완료",
                    detail=f"{micro_label} 저장됨",
                    current_step="저장 완료",
                    scene_range=micro_label.replace("_", " ~ "),
                    batch_index=batch.batch_index,
                    batch_total=total_batches,
                    micro_index=completed_micro_batches,
                    micro_total=total_micro_batches,
                    batch_micro_index=micro_index,
                    batch_micro_total=len(batch.micro_batches),
                    scene_done=completed_scenes,
                    scene_total=total_scenes,
                    countdown_label="대기 없음",
                    countdown_remaining_seconds=0.0,
                )
                self._take_random_break_if_needed(
                    completed_micro_batches=completed_micro_batches,
                    total_micro_batches=total_micro_batches,
                    total_batches=total_batches,
                    batch=batch,
                    micro_index=micro_index,
                    completed_scenes=completed_scenes,
                    total_scenes=total_scenes,
                    current_range=micro_label,
                )

        self.log("🏁 전체 자동화 흐름 완료")
        self._status(
            status="전체 완료",
            detail=f"{scene_range_label} 처리 완료",
            current_step="완료",
            scene_range=scene_range_label.replace("_", " ~ "),
            batch_index=total_batches,
            batch_total=total_batches,
            micro_index=total_micro_batches,
            micro_total=total_micro_batches,
            scene_done=total_scenes,
            scene_total=total_scenes,
            countdown_label="대기 없음",
            countdown_remaining_seconds=0.0,
        )
        return writer.paths
