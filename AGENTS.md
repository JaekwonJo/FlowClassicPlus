# AGENTS.md instructions for /mnt/c/Users/jaekw/Documents/autoupload

## 기본 지침
- 작업 시작 전에 반드시 `codex 설명서.md`를 먼저 읽고 그 규칙을 우선 적용한다.
- 새 세션을 시작할 때 사용자가 `새 Codex 시작용 한방 프롬프트.txt` 내용을 붙여넣으면, 그 프롬프트를 현재 작업의 시작 기준으로 삼고 반드시 거기 적힌 문서부터 읽는다.
- 사용자 설명은 최대한 쉬운 한국어로 작성한다.
- 코드/파일 수정 전에는 무엇을 바꿀지 짧게 먼저 알린다.
- `flow/flow_config.json`은 각 컴퓨터별 로컬 설정 파일이므로 GitHub 최신본으로 덮어쓰지 않는다. 코드 업데이트가 필요할 때도 config는 최대한 유지한다.

## 워커 규칙 분리
- `story_pipeline` / `똑똑즈 파이프라인 워커`는 Gemini에게 Grok Worker용 프롬프트를 만들게 하는 도구다.
- `Ext`, `3D text`, `@S800`, `@S901`, `[STRICT FRAME CONSTRAINT...]` 규칙은 Grok Worker 전용이다.
- 위 Grok Worker 규칙을 `C:\Users\jaekw\FlowWorker`의 FlowWorker/Veo 자동화 규칙과 절대 섞지 않는다.
- FlowWorker는 Flow 사이트에서 이미지/동영상 생성, 시작 프레임 첨부, 확장, 다운로드를 다루는 별도 워커다.
- 사용자가 “Flow worker”라고 말하면 FlowWorker 규칙을, “그록워커/Grok Worker/똑똑즈 파이프라인 워커”라고 말하면 Grok Worker 프롬프트 규칙을 적용한다.

## 문서 우선순위
1. 시스템/개발자 상위 지침
2. 이 파일(`AGENTS.md`)
3. `codex 설명서.md`
