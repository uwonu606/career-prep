# 데이터 디렉토리

스킬을 실행하는 **현재 작업 디렉토리**다. 툴킷 리포(`career-prep`)가 아니라 개인 데이터가 사는 곳이고, 모든 스킬은 여기서 `./career`·`./.env`·`./auth`를 상대 경로로 찾는다. `career-setup`이 만든다.

## 0. 경로

경로는 리포 밖 `~/.config/career-prep/data-dir` 한 줄(절대 경로)이 소유한다 — `career-setup`이 실행된 디렉토리를 거기 적는다. 스킬은 작업 디렉토리에 `career/`가 있으면 거기서 돌고, 없으면 그 파일의 경로로 옮겨 시작한다. 둘 다 없으면 `career-setup`을 안내한다.

## 1. 자리

| 자리 | 무엇 | 쓰는 것 | 읽는 것 |
|---|---|---|---|
| `career/` | 경험·회사·직무 기록 | `add-experience`·`add-company`·`research-role` | 전부 |
| `.env` | 키. 한 줄에 하나, `이름=값` | 사용자가 직접 편집 | 스크립트만 — `dart_fetch.py` |
| `auth/<host>.json` | 로그인 상태(쿠키·스토리지) | `browser.py login` | `browser.py open`만 |
| `fixtures/dart/` | 사업보고서 파서 회귀 픽스처 | `add-company` 수정 에이전트 | `test_extract.py` — `ADD_COMPANY_FIXTURES`가 이 경로 |
| `.gitignore` | `.env`·`auth/`가 커밋되지 않게 | `career-setup` | git |

`.env`와 `auth/`의 **내용은 대화와 셸 명령에 나오지 않는다** — `ls`로 있는지만 본다. 이 환경은 `.env`를 읽는 셸 명령을 권한 규칙으로 거부하고, 그게 맞는 규칙이다.

## 2. 키

| 이름 | 여는 것 | 발급 |
|---|---|---|
| `DART_API_KEY` | `add-company` 각도 1·2·3(공시 문서·직원 현황·임원), `research-role` 뻗기의 DART 행 | https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do — 개인용 즉시 발급, 무료, 1인 1키 |

새 키가 필요해지면 이 표에 행을 붙인다. 읽는 스크립트는 `.env`의 그 줄만 읽는다.

## 3. 로그인 상태

`<career-career-setup 스킬>/scripts/browser.py`가 셋을 한다 — `login <url>`은 창을 열어 사용자가 로그인하고 닫으면 `auth/<host>.json`을 남기고, `list`는 호스트·쿠키 수·가장 이른 만료를 찍고, `open <url>`은 URL의 호스트에 맞는 파일이 있으면 그 상태로 헤드리스로 **페이지 하나**를 읽어 제목·최종 URL·본문 텍스트(`--html`이면 HTML)를 돌려준다. 어느 파일을 썼는지는 stderr에 `auth: …`로 나온다. 호스트는 `www.`를 뗀 이름이고, `linkedin.com` 파일은 `kr.linkedin.com`에도 맞는다.

**로그인은 접근 등급을 올리지 않는다** — 등급과 예외 규칙은 `add-company/references/catalog.md` #8이 소유한다. 요지: 파일이 있는 호스트는 사용자 계정으로 한 페이지씩 열 수 있고 출처 뒤에 `규칙 예외(auth)`를 적는다. 파일이 없는 호스트는 링크만 남기고 사용자에게 `login`을 안내한다. 목록 순회는 하지 않는다 — 실마리가 가리킨 페이지 1건씩이다.

`open`이 로그인 페이지로 돌아오면 만료다 — 같은 URL로 `login`을 다시 한다(있던 상태를 물려받아 열린다).

## 4. 브라우저

크로미움은 `~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome`을 쓰고, 없으면 `CHROMIUM_PATH`, 그것도 없으면 종료 3과 함께 `uv run --with playwright playwright install chromium`을 안내한다. 스크립트는 `uv run`이 PEP 723 머리에서 `playwright`를 스스로 받는다(첫 실행 약 15초 ①). 창은 WSLg의 DISPLAY에 뜬다 ①(2026-09-09).
