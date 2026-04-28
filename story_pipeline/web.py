from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Callable, List, Optional

from playwright.sync_api import BrowserContext, Page, TimeoutError, sync_playwright


DEFAULT_SITE_TARGET = "gemini"
SITE_DEFAULT_URLS = {
    "gemini": "https://gemini.google.com/app",
    "chatgpt": "https://chatgpt.com/",
}
SITE_LABELS = {
    "gemini": "Gemini",
    "chatgpt": "ChatGPT",
}


COMMON_RESPONSE_IGNORE_SNIPPETS = (
    "사용자설정 gem",
    "지금 답변하기",
    "generating visuals",
    "developing visuals further",
    "evaluating text clarity",
    "생각하는 과정 표시",
    "님이 보낸 내용",
)

RESPONSE_VALID_HINTS = (
    " prompt :",
    " video prompt :",
    "|||",
    "[최종프롬프트]",
    "[검수요약]",
    "[검수 브리핑]",
    "[장면 설계 브리핑]",
)

LONG_PROMPT_PASTE_THRESHOLD = 240

SITE_PROFILES = {
    "gemini": {
        "input_selectors": [
            'rich-textarea div[contenteditable="true"]',
            'div[contenteditable="true"][aria-label*="메시지"]',
            'div[contenteditable="true"][aria-label*="Message"]',
            'textarea[aria-label*="메시지"]',
            'textarea[aria-label*="message"]',
            'div[contenteditable="true"]',
        ],
        "send_selectors": [
            'button[aria-label*="전송"]',
            'button[aria-label*="Send"]',
            'button[aria-label*="메시지 보내기"]',
            'button[aria-label*="Submit"]',
        ],
        "stop_selectors": [
            'button[aria-label*="중지"]',
            'button[aria-label*="Stop"]',
            'button[aria-label*="답변 중지"]',
            'button[aria-label*="생성 중지"]',
        ],
        "response_selectors": [
            "model-response",
            '[data-message-author-role="model"]',
            '[data-test-id="model-response"]',
            'div.response-container',
        ],
        "response_ignore_snippets": COMMON_RESPONSE_IGNORE_SNIPPETS,
    },
    "chatgpt": {
        "input_selectors": [
            '#prompt-textarea',
            'div#prompt-textarea[contenteditable="true"]',
            'textarea[placeholder*="Message"]',
            'textarea[placeholder*="메시지"]',
            'div[contenteditable="true"][aria-label*="메시지"]',
            'div[contenteditable="true"][aria-label*="Message"]',
            'div[contenteditable="true"]',
        ],
        "send_selectors": [
            'button[data-testid="send-button"]',
            'button[aria-label*="Send prompt"]',
            'button[aria-label*="전송"]',
            'button[aria-label*="Send"]',
        ],
        "stop_selectors": [
            'button[data-testid="stop-button"]',
            'button[aria-label*="Stop generating"]',
            'button[aria-label*="중지"]',
            'button[aria-label*="생성 중지"]',
        ],
        "response_selectors": [
            '[data-message-author-role="assistant"]',
            'article [data-message-author-role="assistant"]',
            'div[data-message-author-role="assistant"]',
            'main article',
        ],
        "response_ignore_snippets": COMMON_RESPONSE_IGNORE_SNIPPETS
        + (
            "thinking",
            "tools",
            "무엇이든 물어보세요",
            "what can i help with",
            "searching the web",
        ),
    },
}


class GeminiWebRunner:
    def __init__(
        self,
        site_target: str,
        start_url: str,
        profile_dir: Path,
        log: Callable[[str], None],
        wait_timeout_ms: int = 300000,
        pre_input_delay_seconds: float = 4.0,
        send_wait_seconds: float = 2.0,
        poll_interval_seconds: float = 5.0,
        stable_rounds_required: int = 2,
        human_typing_enabled: bool = True,
        typing_speed_level: int = 5,
        status_callback: Optional[Callable[[dict], None]] = None,
    ):
        self.site_target = site_target if site_target in SITE_PROFILES else DEFAULT_SITE_TARGET
        self.start_url = start_url
        self.profile_dir = profile_dir
        self.log = log
        self.wait_timeout_ms = wait_timeout_ms
        self.pre_input_delay_seconds = max(0.0, float(pre_input_delay_seconds))
        self.send_wait_seconds = max(0.0, float(send_wait_seconds))
        self.poll_interval_seconds = max(5.0, float(poll_interval_seconds))
        self.stable_rounds_required = max(1, int(stable_rounds_required))
        self.human_typing_enabled = bool(human_typing_enabled)
        self.typing_speed_level = max(1, min(20, int(typing_speed_level)))
        self.status_callback = status_callback
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def _site_profile(self) -> dict:
        return SITE_PROFILES.get(self.site_target, SITE_PROFILES[DEFAULT_SITE_TARGET])

    def _site_label(self) -> str:
        return SITE_LABELS.get(self.site_target, self.site_target.title())

    def _status(self, **payload) -> None:
        if self.status_callback is None:
            return
        try:
            self.status_callback(payload)
        except Exception:
            pass

    def _wait_with_countdown(self, seconds: float, label: str, step_label: str = "") -> None:
        total_seconds = max(0.0, float(seconds))
        if total_seconds <= 0:
            self._status(
                countdown_label="대기 없음",
                countdown_remaining_seconds=0.0,
                countdown_total_seconds=0.0,
                countdown_step=step_label,
            )
            return
        end_at = time.time() + total_seconds
        while True:
            remaining = max(0.0, end_at - time.time())
            self._status(
                countdown_label=label,
                countdown_remaining_seconds=remaining,
                countdown_total_seconds=total_seconds,
                countdown_step=step_label,
            )
            if remaining <= 0:
                break
            time.sleep(min(0.2, remaining))

    def open_browser(self) -> None:
        if self.page and not self.page.is_closed():
            self.page.bring_to_front()
            return
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        if self.playwright is None:
            self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            channel="msedge",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1380, "height": 980},
        )
        pages = self.context.pages
        self.page = pages[0] if pages else self.context.new_page()
        self.page.goto(self.start_url, wait_until="domcontentloaded")
        self.wait_for_input_ready()
        self.log(f"🌐 {self._site_label()} 웹 브라우저 준비 완료")

    def close(self) -> None:
        try:
            if self.context:
                self.context.close()
        finally:
            self.context = None
            self.page = None
            if self.playwright:
                self.playwright.stop()
            self.playwright = None

    def reset_conversation(self) -> None:
        self.open_browser()
        assert self.page is not None
        self.log("🧭 대상 URL로 다시 이동해 초기 채팅 상태를 맞춥니다.")
        self.page.goto(self.start_url, wait_until="domcontentloaded")
        self.wait_for_input_ready()

    def wait_for_input_ready(self) -> None:
        assert self.page is not None
        deadline = time.time() + (self.wait_timeout_ms / 1000.0)
        while time.time() < deadline:
            editor = self._find_editor(timeout_ms=1200)
            if editor is not None:
                return
            time.sleep(1.0)
        raise RuntimeError(f"{self._site_label()} 입력창을 찾지 못했습니다. 로그인 여부와 대상 URL을 확인해 주세요.")

    def _find_editor(self, timeout_ms: int = 2000):
        assert self.page is not None
        for selector in self._site_profile().get("input_selectors", []):
            try:
                loc = self.page.locator(selector).first
                if loc.count() and loc.is_visible(timeout=timeout_ms):
                    return loc
            except Exception:
                continue
        return None

    def _collect_response_entries(self) -> List[dict]:
        assert self.page is not None
        script = """
        () => {
          const selectors = %s;
          const out = [];
          let order = 0;
          for (const selector of selectors) {
            const nodes = Array.from(document.querySelectorAll(selector));
            for (const node of nodes) {
              if (node.closest('rich-textarea, textarea, [contenteditable="true"]')) continue;
              if (node.closest('[data-message-author-role="user"], user-query, user-message')) continue;
              const text = (node.innerText || "").trim();
              if (!text) continue;
              const style = window.getComputedStyle(node);
              if (style.display === "none" || style.visibility === "hidden") continue;
              const rect = node.getBoundingClientRect();
              out.push({
                text,
                top: Number(rect.top || 0),
                bottom: Number(rect.bottom || 0),
                order: order++,
              });
            }
          }
          return out;
        }
        """ % (repr(self._site_profile().get("response_selectors", [])))
        try:
            entries = self.page.evaluate(script)
            normalized = []
            for item in entries or []:
                text = str((item or {}).get("text") or "").strip()
                if not text:
                    continue
                lowered = text.lower()
                ignore_snippets = self._site_profile().get("response_ignore_snippets", COMMON_RESPONSE_IGNORE_SNIPPETS)
                if any(snippet in lowered for snippet in ignore_snippets) and not any(
                    hint in lowered for hint in RESPONSE_VALID_HINTS
                ):
                    continue
                normalized.append(
                    {
                        "text": text,
                        "top": float((item or {}).get("top") or 0.0),
                        "bottom": float((item or {}).get("bottom") or 0.0),
                        "order": int((item or {}).get("order") or 0),
                    }
                )
            if normalized:
                normalized.sort(key=lambda item: (item["bottom"], item["top"], item["order"]))
                return normalized
        except Exception:
            pass
        try:
            body_text = self.page.locator("main").inner_text(timeout=1500).strip()
            return [{"text": body_text, "top": 0.0, "bottom": 999999.0, "order": 0}] if body_text else []
        except Exception:
            return []

    def _latest_response_text(self) -> str:
        entries = self._collect_response_entries()
        if not entries:
            return ""
        return str(entries[-1].get("text") or "").strip()

    def _human_type_text(self, editor, text: str, tag_name: str) -> None:
        assert self.page is not None
        speed = max(1, min(20, int(self.typing_speed_level)))
        speed_factor = 1.0 / max(0.6, speed / 4.0)
        for ch in str(text or ""):
            try:
                if ch == "\n":
                    if tag_name == "textarea":
                        editor.press("Shift+Enter")
                    else:
                        self.page.keyboard.press("Shift+Enter")
                else:
                    if tag_name == "textarea":
                        editor.type(ch, delay=1)
                    else:
                        self.page.keyboard.type(ch, delay=1)
            except Exception:
                self.page.keyboard.insert_text(ch)

            if ch in (" ", "\t"):
                base_min, base_max = 0.010, 0.040
            elif ch == "\n":
                base_min, base_max = 0.080, 0.180
            elif ch in (".", ",", "!", "?", ":", ";"):
                base_min, base_max = 0.030, 0.090
            else:
                base_min, base_max = 0.018, 0.065

            delay = random.uniform(base_min, base_max) * speed_factor
            time.sleep(max(0.003, min(delay, 0.22)))

        if self.human_typing_enabled and len(text) > 40:
            time.sleep(random.uniform(0.08, 0.22))

    def _set_editor_text(self, text: str) -> None:
        assert self.page is not None
        editor = self._find_editor(timeout_ms=3000)
        if editor is None:
            raise RuntimeError(f"{self._site_label()} 입력창을 찾지 못했습니다.")
        try:
            tag_name = (editor.evaluate("(el) => el.tagName") or "").lower()
        except Exception:
            tag_name = ""
        self._focus_editor(editor)
        use_human_typing = self.human_typing_enabled and len(str(text or "")) < LONG_PROMPT_PASTE_THRESHOLD
        if use_human_typing:
            try:
                if tag_name == "textarea":
                    editor.fill("")
                else:
                    editor.evaluate(
                        """(el) => {
                            el.focus();
                            while (el.firstChild) el.removeChild(el.firstChild);
                            el.dispatchEvent(new Event("input", {bubbles: true}));
                        }"""
                    )
            except Exception:
                pass
            self.log(f"⌨️ 사람형 타이핑 입력 | 속도 x{self.typing_speed_level}")
            self._human_type_text(editor, text, tag_name)
            return
        if self.human_typing_enabled:
            self.log("📋 긴 프롬프트라 전체 붙여넣기 입력으로 전환")
        else:
            self.log("📋 전체 붙여넣기 입력")
        if tag_name == "textarea":
            editor.fill(text)
            return
        editor.evaluate(
            """(el, value) => {
                el.focus();
                while (el.firstChild) el.removeChild(el.firstChild);
                const lines = String(value).split(/\\n/);
                lines.forEach((line, idx) => {
                    if (idx > 0) el.appendChild(document.createElement("br"));
                    el.appendChild(document.createTextNode(line));
                });
                el.dispatchEvent(new InputEvent("input", {bubbles: true, inputType: "insertText", data: value}));
                el.dispatchEvent(new Event("change", {bubbles: true}));
            }""",
            text,
        )

    def _focus_editor(self, editor) -> None:
        assert self.page is not None
        last_error = ""
        try:
            editor.scroll_into_view_if_needed(timeout=1200)
        except Exception:
            pass
        try:
            editor.click(timeout=2500)
            return
        except Exception as exc:
            last_error = str(exc)
        try:
            editor.focus(timeout=1200)
            return
        except Exception as exc:
            last_error = str(exc)
        try:
            editor.evaluate(
                """(el) => {
                    el.scrollIntoView({block: "center", inline: "nearest"});
                    if (typeof el.focus === "function") el.focus();
                    el.dispatchEvent(new FocusEvent("focus", {bubbles: false}));
                    return true;
                }"""
            )
            return
        except Exception as exc:
            last_error = str(exc)
        raise RuntimeError(f"{self._site_label()} 입력창 포커스 실패: {last_error}")

    def _find_send_button(self, timeout_ms: int = 1200):
        assert self.page is not None
        candidates = []
        editor_box = None
        try:
            editor = self._find_editor(timeout_ms=500)
            if editor is not None:
                editor_box = editor.bounding_box(timeout=700)
        except Exception:
            editor_box = None
        for selector in self._site_profile().get("send_selectors", []):
            try:
                loc = self.page.locator(selector)
                count = min(loc.count(), 12)
                for idx in range(count):
                    button = loc.nth(idx)
                    if not button.is_visible(timeout=timeout_ms):
                        continue
                    if not button.is_enabled(timeout=timeout_ms):
                        continue
                    box = button.bounding_box(timeout=700)
                    if not box or box.get("width", 0) < 5 or box.get("height", 0) < 5:
                        continue
                    score = float(box.get("y", 0)) * 10 + float(box.get("x", 0))
                    if editor_box:
                        center_x = float(box.get("x", 0)) + float(box.get("width", 0)) / 2.0
                        center_y = float(box.get("y", 0)) + float(box.get("height", 0)) / 2.0
                        editor_right = float(editor_box.get("x", 0)) + float(editor_box.get("width", 0))
                        editor_bottom = float(editor_box.get("y", 0)) + float(editor_box.get("height", 0))
                        distance = abs(editor_right - center_x) + abs(editor_bottom - center_y)
                        score = 100000.0 - distance
                    candidates.append((score, button))
            except Exception:
                continue
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _submit(self, attempt: int = 1) -> None:
        assert self.page is not None
        button = self._find_send_button()
        if button is not None:
            if attempt == 1:
                button.click(timeout=1800)
                return
            box = None
            try:
                box = button.bounding_box(timeout=700)
            except Exception:
                box = None
            if attempt == 2 and box:
                self.page.mouse.click(
                    float(box.get("x", 0)) + float(box.get("width", 0)) / 2.0,
                    float(box.get("y", 0)) + float(box.get("height", 0)) / 2.0,
                )
                return
            button.click(timeout=1800, force=True)
            return
        editor = self._find_editor(timeout_ms=1200)
        if editor is None:
            raise RuntimeError("전송 버튼과 입력창을 모두 찾지 못했습니다.")
        if attempt >= 3:
            editor.press("Enter")
        else:
            editor.press("Control+Enter")

    def _composer_text(self) -> str:
        editor = self._find_editor(timeout_ms=700)
        if editor is None:
            return ""
        try:
            tag_name = (editor.evaluate("(el) => el.tagName") or "").lower()
        except Exception:
            tag_name = ""
        try:
            if tag_name == "textarea":
                return str(editor.input_value(timeout=700) or "").strip()
            return str(editor.evaluate("(el) => (el.innerText || el.textContent || '').trim()") or "").strip()
        except Exception:
            return ""

    def _submission_started(self, baseline: str, expected_prompt: str) -> bool:
        if self._has_visible_button(self._site_profile().get("stop_selectors", []), timeout_ms=250):
            return True
        if self._find_send_button(timeout_ms=250) is not None:
            return False
        composer_text = self._composer_text()
        if not composer_text:
            return True
        # If the prompt is still sitting in the composer, the send click did not take.
        expected = " ".join(str(expected_prompt or "").split())
        current_composer = " ".join(composer_text.split())
        if len(current_composer) > 20:
            if not expected:
                return False
            head = expected[: min(80, len(expected))]
            tail = expected[-min(80, len(expected)) :]
            if head and head in current_composer:
                return False
            if tail and tail in current_composer:
                return False
            return False
        current = self._latest_response_text()
        if current and current != baseline and composer_text not in current and current not in composer_text:
            return True
        return False

    def _submit_and_confirm(self, baseline: str, prompt: str, step_label: str = "") -> None:
        last_error = None
        for attempt in range(1, 4):
            try:
                self._submit(attempt=attempt)
            except Exception as exc:
                last_error = exc
            end_at = time.time() + 2.0
            while time.time() < end_at:
                if self._submission_started(baseline, prompt):
                    if attempt > 1:
                        self.log(f"🔁 전송 재시도 성공 | {step_label or '-'} | {attempt}회차")
                    return
                time.sleep(0.2)
            left_text = self._composer_text()
            if left_text:
                self.log(f"🔁 화살표 버튼이 그대로라 다시 전송 시도 | {step_label or '-'} | {attempt}/3")
            else:
                self.log(f"🔁 전송 확인 안됨, 다시 전송 시도 | {step_label or '-'} | {attempt}/3")
        if last_error is not None:
            raise RuntimeError(f"{self._site_label()} 전송 버튼 클릭 실패: {last_error}")
        raise RuntimeError(f"{self._site_label()} 전송이 시작되지 않았습니다. 입력창의 전송 버튼을 확인해 주세요.")

    def _has_visible_button(self, selectors: List[str], timeout_ms: int = 300) -> bool:
        assert self.page is not None
        for selector in selectors:
            try:
                loc = self.page.locator(selector)
                count = min(loc.count(), 4)
                for idx in range(count):
                    button = loc.nth(idx)
                    if button.is_visible(timeout=timeout_ms):
                        return True
            except Exception:
                continue
        return False

    def _composer_is_ready_for_next_prompt(self) -> bool:
        if self._has_visible_button(self._site_profile().get("stop_selectors", [])):
            return False
        return self._has_visible_button(self._site_profile().get("send_selectors", []))

    def _button_state_label(self, stop_visible: bool, send_visible: bool) -> str:
        if stop_visible:
            return "네모 답변중"
        if send_visible:
            return "세모 입력가능"
        return "화면 확인 대기"

    def _status_next_check(self, seconds: float, state: str) -> None:
        self._status(
            poll_check_state=state,
            poll_check_remaining_seconds=max(0.0, float(seconds)),
        )

    def send_prompt(self, prompt: str, step_label: str = "") -> str:
        self.open_browser()
        assert self.page is not None
        self.page.bring_to_front()
        self.wait_for_input_ready()

        baseline = self._latest_response_text()
        self.log(f"📨 {self._site_label()} 전송 시작 | {step_label or '-'}")
        if self.pre_input_delay_seconds > 0:
            self.log(f"🕒 창 안정화 대기 | 입력 전 {self.pre_input_delay_seconds:.1f}초 | {step_label or '-'}")
        self._status(
            status="입력 준비",
            detail=f"{step_label or '-'} 입력창 안정화 대기",
            current_step="입력 준비",
        )
        self._wait_with_countdown(self.pre_input_delay_seconds, "입력 시작까지", step_label=step_label)
        self._set_editor_text(prompt)
        time.sleep(0.15)
        self._submit_and_confirm(baseline, prompt, step_label=step_label)
        self.log(
            "⏱ 응답 대기 설정 | 답변 안정 대기 "
            f"{self.send_wait_seconds:.1f}초 | 확인간격 {self.poll_interval_seconds:.1f}초 | "
            f"같은 응답 확인 {self.stable_rounds_required}회 | 최대 {self.wait_timeout_ms / 1000.0:.1f}초"
        )
        result = self._wait_for_new_response(baseline, step_label=step_label)
        self.log(f"📥 {self._site_label()} 응답 확보 | {step_label or '-'}")
        self._status(
            countdown_label="응답 확보",
            countdown_remaining_seconds=0.0,
            countdown_total_seconds=0.0,
            countdown_step=step_label,
        )
        return result

    def _wait_for_new_response(self, baseline: str, step_label: str = "") -> str:
        deadline = time.time() + (self.wait_timeout_ms / 1000.0)
        self._status(
            status="응답 대기",
            detail=f"{step_label or '-'} 응답 확인 중",
            current_step="응답 대기",
        )
        wait_until = time.time() + self.send_wait_seconds
        stable_count = 0
        last_text = ""
        button_ready_logged = False
        stop_gone_logged = False
        stop_selectors = self._site_profile().get("stop_selectors", [])
        send_selectors = self._site_profile().get("send_selectors", [])
        while time.time() < deadline:
            remaining = max(0.0, deadline - time.time())
            self._status(
                countdown_label="응답 기다리는 중",
                countdown_remaining_seconds=remaining,
                countdown_total_seconds=self.wait_timeout_ms / 1000.0,
                countdown_step=step_label,
            )
            current = self._latest_response_text()
            stop_visible = self._has_visible_button(stop_selectors)
            send_visible = False if stop_visible else self._has_visible_button(send_selectors)
            button_state = self._button_state_label(stop_visible, send_visible)
            if time.time() < wait_until:
                if not (current and current != baseline and not stop_visible):
                    sleep_for = min(self.poll_interval_seconds, max(0.5, wait_until - time.time()))
                    self._status_next_check(sleep_for, button_state)
                    time.sleep(sleep_for)
                    continue
            if current and current != baseline and not stop_visible and send_visible:
                if not button_ready_logged:
                    self.log(f"⏭ 화살표 버튼 복귀 확인 | {step_label or '-'}")
                    button_ready_logged = True
                sleep_for = min(3.0, max(1.0, self.poll_interval_seconds / 2.0))
                self._status_next_check(sleep_for, "세모 입력가능 확인중")
                time.sleep(sleep_for)
                followup = self._latest_response_text()
                if followup and followup != baseline and self._composer_is_ready_for_next_prompt():
                    self._status_next_check(0.0, "세모 입력가능")
                    return followup
            if current and current != baseline and not stop_visible:
                if not stop_gone_logged:
                    self.log(f"⏭ 네모 버튼 종료 확인 | {step_label or '-'}")
                    stop_gone_logged = True
                sleep_for = min(3.0, max(1.0, self.poll_interval_seconds / 2.0))
                self._status_next_check(sleep_for, "답변 종료 확인중")
                time.sleep(sleep_for)
                followup = self._latest_response_text()
                if followup and followup != baseline and not self._has_visible_button(stop_selectors):
                    self._status_next_check(0.0, "세모 입력가능")
                    return followup
            if current and current != baseline:
                if current == last_text:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_text = current
                if stable_count >= self.stable_rounds_required:
                    self._status_next_check(0.0, "답변 안정 확인")
                    return current
            self._status_next_check(self.poll_interval_seconds, button_state)
            time.sleep(self.poll_interval_seconds)
        self._status_next_check(0.0, "시간 초과")
        raise RuntimeError(f"{self._site_label()} 응답 대기 시간이 초과되었습니다.")
