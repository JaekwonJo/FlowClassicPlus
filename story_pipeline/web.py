from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, List, Optional

from playwright.sync_api import BrowserContext, Page, TimeoutError, sync_playwright


INPUT_SELECTORS = [
    'rich-textarea div[contenteditable="true"]',
    'div[contenteditable="true"][aria-label*="메시지"]',
    'div[contenteditable="true"][aria-label*="Message"]',
    'textarea[aria-label*="메시지"]',
    'textarea[aria-label*="message"]',
    'div[contenteditable="true"]',
]

SEND_SELECTORS = [
    'button[aria-label*="전송"]',
    'button[aria-label*="Send"]',
    'button[aria-label*="메시지 보내기"]',
    'button[aria-label*="Submit"]',
]

NEW_CHAT_SELECTORS = [
    'button[aria-label*="새 채팅"]',
    'button[aria-label*="New chat"]',
    'a[aria-label*="새 채팅"]',
    'a[aria-label*="New chat"]',
]

RESPONSE_SELECTORS = [
    "model-response",
    "message-content",
    '[data-message-author-role="model"]',
    '[data-test-id="model-response"]',
    'div.response-container',
]


class GeminiWebRunner:
    def __init__(
        self,
        start_url: str,
        profile_dir: Path,
        log: Callable[[str], None],
        wait_timeout_ms: int = 300000,
        send_wait_seconds: float = 2.0,
        poll_interval_seconds: float = 2.0,
        stable_rounds_required: int = 2,
    ):
        self.start_url = start_url
        self.profile_dir = profile_dir
        self.log = log
        self.wait_timeout_ms = wait_timeout_ms
        self.send_wait_seconds = max(0.0, float(send_wait_seconds))
        self.poll_interval_seconds = max(0.5, float(poll_interval_seconds))
        self.stable_rounds_required = max(1, int(stable_rounds_required))
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

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
        self.log("🌐 Gemini 웹 브라우저 준비 완료")

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
        for selector in NEW_CHAT_SELECTORS:
            try:
                button = self.page.locator(selector).first
                if button.count() and button.is_visible(timeout=1200):
                    button.click(timeout=1500)
                    self.wait_for_input_ready()
                    return
            except Exception:
                continue
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
        raise RuntimeError("Gemini 입력창을 찾지 못했습니다. 로그인 여부와 Gem URL을 확인해 주세요.")

    def _find_editor(self, timeout_ms: int = 2000):
        assert self.page is not None
        for selector in INPUT_SELECTORS:
            try:
                loc = self.page.locator(selector).first
                if loc.count() and loc.is_visible(timeout=timeout_ms):
                    return loc
            except Exception:
                continue
        return None

    def _collect_response_texts(self) -> List[str]:
        assert self.page is not None
        script = """
        () => {
          const selectors = %s;
          const out = [];
          for (const selector of selectors) {
            const nodes = Array.from(document.querySelectorAll(selector));
            for (const node of nodes) {
              const text = (node.innerText || "").trim();
              if (!text) continue;
              const style = window.getComputedStyle(node);
              if (style.display === "none" || style.visibility === "hidden") continue;
              out.push(text);
            }
          }
          return out;
        }
        """ % (repr(RESPONSE_SELECTORS))
        try:
            texts = self.page.evaluate(script)
            texts = [item.strip() for item in texts if str(item).strip()]
            if texts:
                return texts
        except Exception:
            pass
        try:
            body_text = self.page.locator("main").inner_text(timeout=1500).strip()
            return [body_text] if body_text else []
        except Exception:
            return []

    def _latest_response_text(self) -> str:
        texts = self._collect_response_texts()
        if not texts:
            return ""
        texts.sort(key=len)
        return texts[-1]

    def _set_editor_text(self, text: str) -> None:
        assert self.page is not None
        editor = self._find_editor(timeout_ms=3000)
        if editor is None:
            raise RuntimeError("Gemini 입력창을 찾지 못했습니다.")
        try:
            tag_name = (editor.evaluate("(el) => el.tagName") or "").lower()
        except Exception:
            tag_name = ""
        editor.click()
        if tag_name == "textarea":
            editor.fill(text)
            return
        editor.evaluate(
            """(el, value) => {
                el.focus();
                el.innerHTML = "";
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

    def _submit(self) -> None:
        assert self.page is not None
        for selector in SEND_SELECTORS:
            try:
                loc = self.page.locator(selector).first
                if loc.count() and loc.is_enabled(timeout=1200):
                    loc.click(timeout=1500)
                    return
            except Exception:
                continue
        editor = self._find_editor(timeout_ms=1200)
        if editor is None:
            raise RuntimeError("전송 버튼과 입력창을 모두 찾지 못했습니다.")
        editor.press("Control+Enter")

    def send_prompt(self, prompt: str, step_label: str = "") -> str:
        self.open_browser()
        assert self.page is not None
        self.page.bring_to_front()
        self.wait_for_input_ready()

        baseline = self._latest_response_text()
        self.log(f"📨 Gemini 전송 시작 | {step_label or '-'}")
        self._set_editor_text(prompt)
        self._submit()
        self.log(
            "⏱ 응답 대기 설정 | 입력후 "
            f"{self.send_wait_seconds:.1f}초 | 확인간격 {self.poll_interval_seconds:.1f}초 | "
            f"안정 {self.stable_rounds_required}회 | 최대 {self.wait_timeout_ms / 1000.0:.1f}초"
        )
        result = self._wait_for_new_response(baseline)
        self.log(f"📥 Gemini 응답 확보 | {step_label or '-'}")
        return result

    def _wait_for_new_response(self, baseline: str) -> str:
        deadline = time.time() + (self.wait_timeout_ms / 1000.0)
        if self.send_wait_seconds > 0:
            time.sleep(self.send_wait_seconds)
        stable_count = 0
        last_text = ""
        while time.time() < deadline:
            current = self._latest_response_text()
            if current and current != baseline:
                if current == last_text:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_text = current
                if stable_count >= self.stable_rounds_required:
                    return current
            time.sleep(self.poll_interval_seconds)
        raise RuntimeError("Gemini 응답 대기 시간이 초과되었습니다.")
