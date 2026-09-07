# career-prep

[![test](https://github.com/uwonu606/career-prep/actions/workflows/test.yml/badge.svg)](https://github.com/uwonu606/career-prep/actions/workflows/test.yml)

경험을 인지면접으로 캐내 구조화해 쌓고, 면접관 시점으로 검증하는 취업 준비 툴킷.

## 무엇을 하는가

자소서의 품질은 글솜씨가 아니라 **원재료**에서 결정된다. 그래서 이 툴킷은 자소서를 써주지 않는다. 대신

1. **적는다** — 형식 없이 일기로 쌓는다. 여기서는 아무것도 묻지 않는다
2. **캐낸다** — 인지면접 프로토콜로 기억에서 장면을 인출한다
3. **쌓는다** — 면접에서 실제로 질문되는 형태로 구조화해 저장한다
4. **검증한다** — 격리된 면접관이 파일만 보고 무너질 지점과 깎여 적힌 자리를 짚고, 그 자리를 다시 캔다. 채워지면 강화하고, 못 버티는 문장은 빼고, 그때 없었던 것은 다음에 획득할 것으로 넘긴다

원재료가 도메인이고 지원은 그 투영이다. 최종 산출물은 자소서가 아니라 **갱신되는 자기 모델**이다. 자소서는 회사마다 버려지지만 그 모델은 남아서 계속 굴러간다.

설계 근거와 그 근거가 된 연구는 [`docs/rationale.md`](docs/rationale.md)에 있다. **결정을 뒤집기 전에 그 문서를 먼저 읽는 것을 권한다** — 근거 없이 "더 자연스러워 보여서" 바꾸면 이미 검토해서 기각한 설계로 되돌아가게 된다. #11에는 실제 시뮬레이션에서 무너져서 고친 것들이 적혀 있다.

## 쓰는 법

```
/add-note                일기 한 줄을 붙인다. 매일이든 심심할 때든
/add-experience          경험 하나를 캐내 기록한다
```

`/add-experience` 는 재료를 셋 중 하나로 받는다 — **말 · 저장소 · 일기.** 캘 장면이 떠오르면 말로 시작하고, 안 떠오르면 저장소나 `/add-note` 로 쌓아둔 일기에서 후보를 골라 시작한다.

**저장소는 여러 번에 걸쳐 소진된다.** 스캔이 후보로 낸 묶음을 커서에 적어두므로 다시 실행하면 남은 후보부터 난다 — 같은 밤이 두 번 후보로 오지 않는다. 한 실행은 언제나 에피소드 한 건이다.

끝나면 **새 대화를 열어서:**

```
/review-experience       그 기록을 면접관 시점으로 검증하고 되캔다
```

**새 대화여야 하는 이유** — 채굴 대화를 본 상태로 검토하면 파일의 빈 곳을 대화 기억으로 메워버리고, 검토가 아무것도 드러내지 못한다. 격리를 서브에이전트가 아니라 **세션 경계**로 얻는다. 그래서 서브에이전트가 없는 환경에서도 똑같이 작동한다.

지원할 회사가 정해졌으면:

```
/add-company <회사명> [채용공고 URL]   회사 하나를 공개 자료 18각도로 조사해 기록한다
```

회사가 무슨 사업을 하고 어떤 인재를 찾는지를 **문장마다 출처를 달아** `career/companies/`에 쌓는다. 사용자에 대해 판정하지 않고("맞다/안 맞다"를 쓰지 않는다), 그 결과를 `add-experience`의 채굴 입력으로 흘리지도 않는다([`docs/rationale.md`](docs/rationale.md) #6). 근거는 #17~#22.

그 회사만 겨눈 것을 만들려면:

```
/plan-portfolio <회사명>   그 회사가 스스로 말한 문제를 캐, 만들 것 하나를 정한다
```

**문제는 지어내지 않는다.** 밖에서는 회사의 진짜 문제를 알 수 없고, 근거 없이 고른 문제는 면접에서 제일 먼저 터진다. 그래서 회사가 **자백한 자리**(공고의 반복되는 요건, 기술블로그 글 끝의 남은 과제, 문서의 "지원 예정")와 내가 **관측한 값**(직접 써 보고 잰 것)에서만 만들 것을 뽑고, 내가 이은 **추측**은 후보로만 둔다.

그리고 **밖에서 작게 되살리지 못하는 문제는 만들 것이 아니다** — 재현이 게이트다. 이 스킬은 포트폴리오를 만들지 않고 **무엇을 만들지**를 `career/applications/`에 정한다. 만드는 것은 다른 세션이고, 만든 뒤에는 `/add-experience`가 그것을 에피소드로 받는다. 근거는 #26.

## 데이터

사용자 작업 디렉토리의 `career/`에 쌓인다. **툴킷 저장소에는 들어오지 않는다** — 개인의 실패·갈등 기록이라 배포 대상이 아니다. 첫 실행 때 `.gitignore` 등록을 안내한다.

```
career/
├── index.md          자동 생성 (파생 캐시)
├── backlog.md        다음에 캘 장면 후보
├── self.md           역량 주장 — 근거와 반례를 함께 담는다
├── projects/<slug>/{project.md, .harvested, artifacts/}   훑은 묶음과 repo-scan 정리
├── episodes/<slug>.md
├── journal/          일기 — 쓴 날로 나뉜다. frontmatter 없음
├── companies/<slug>/{company.md, artifacts/}  회사 조사 — add-company 가 만든다. 원자료(DART 추출·에이전트 반환)는 artifacts/
└── applications/<slug>/{portfolio.md, artifacts/}  회사×나 — plan-portfolio 가 만든다
```

## 구성

| | |
|---|---|
| `skills/add-note/` | 붙이고 침묵한다 |
| `skills/add-experience/` | 캐내고 기록한다 |
| `└ references/frames.md` | 칸별 질문 18개(바닥), 도달 판정, 특수 상황 셋 |
| `└ references/schema.md` | 파일 레이아웃과 frontmatter |
| `└ references/vocabulary.md` | 역량 태그와 여는 질문 (같은 표에서 나온다) |
| `└ scripts/build_index.py` | `index.md` 재생성 |
| `└ scripts/repo_scan.py` | 재료층(시각·개수·묶음)과 후보(큰 묶음 4개의 커밋 제목 원문)는 화면으로, 내용층(커밋 본문·경로)은 `artifacts/` 의 정리 파일로. 후보로 낸 묶음은 `.harvested` 에 적혀 다음 실행에서 빠진다 |
| `└ scripts/test_repo_scan.py` | 층이 갈리는 자리를 고정한다 — 화면에 본문·경로가 없고, 제목은 후보 절에만 있고, 파일에는 전량이 있고, 커서에 SHA 가 없다 |
| `skills/review-experience/` | 검증하고 되캔다 |
| `└ references/interviewer.md` | 면접관 판정 기준과 반환 형식 |
| `skills/add-company/` | 회사 하나를 조사하고 기록한다 |
| `└ references/catalog.md` | 18각도 × 5묶음 — 각도별 "있는지 확인하는 절차", 접근 등급(robots 허용 AND 약관 무금지만 직접 접근), 명령 블록 |
| `└ references/schema.md` | 회사 파일 규약 — 자료 지도 / 무슨 사업 / 어떤 인재 / 교차점 / open_questions, 문장마다 출처 |
| `└ references/agents.md` | 지도·묶음·수정 에이전트 프롬프트 템플릿 — 파서가 깨지면 픽스처를 더하고 고친다 |
| `└ scripts/dart_fetch.py` `dart_extract.py` `dart_tables.py` | OpenDART 수집(키는 스크립트만 읽는다) · 사업보고서 원문 절 추출 · 직원·임원 표. 표준 라이브러리만 |
| `└ scripts/test_extract.py` `test_fetch.py` | 파서 회귀(픽스처는 리포 밖, `ADD_COMPANY_FIXTURES`) · 수집기 합성 응답 테스트 |
| `skills/plan-portfolio/` | 회사 하나를 겨눈 만들 것을 정한다 |
| `└ references/catalog.md` | 문제 각도 14개 × 4묶음 — 회사가 자기 문제를 드러내는 자리, 재현 세 경로, 만들 것이 받을 질문 세 각도 |
| `└ references/schema.md` | 만들 것 파일 규약 — 문제 지도 / 후보 / 재현 / 만들 것 / open_questions, 등급과 출처가 없으면 후보가 아니다 |
| `docs/rationale.md` | 설계 근거 — 뒤집기 전에 읽을 것 |
| `docs/market-research.md` | 채용 프로세스 모델의 근거와 출처 |
| `docs/company-research.md` | 회사 조사 소스·파서 실측 — robots·약관 판정, 사업보고서 XML 구조, 첫 수정 루프 |
| `agents/tech-interviewer.md` | 격리 판정자 (Claude Code 전용, 읽기 전용) |

## 설치

`SKILL.md` 형식은 [Agent Skills 공개 표준](https://agentskills.io)이고 ChatGPT·Codex·Cursor·Copilot 등 40여 개 제품이 읽는다. 플러그인 구조는 [Agent Plugins v1.0.0](https://agent-plugins.org)을 따른다.

```bash
npx skills add uwonu606/career-prep
```

Claude Code에서는 플러그인으로 설치하면 `agents/tech-interviewer.md`까지 함께 들어간다. 그 밖의 환경에서는 `skills/` 다섯만 들어가고, 검증은 새 대화로 격리한다.

`add-company`의 DART 각도(공시 문서·직원 현황·임원)는 OpenDART 인증키가 있을 때 돈다 — 개인용 즉시 발급, 무료. 작업 디렉토리의 `.env`에 `DART_API_KEY=…` 한 줄로 두면 스크립트만 그것을 읽는다(대화나 셸 명령에 키가 나오지 않는다). 키가 없어도 나머지 15각도는 그대로 돈다.

## 아직 없는 것

- `applications/`의 **격차 서술** 전용 스킬 — 지금은 `plan-portfolio`의 2단계가 후보마다 잇는다·획득·비운다를 붙이는 만큼만 한다. 지원 한 건을 통째로 대조하는 자리는 아직 비어 있다
- 인사담당자(5~10초 예산)·임원(컬처핏) 페르소나 — 다만 기술면접관이 프로젝트 밖 에피소드(알바 갈등·혼자 공부)에도 그대로 작동하는 것이 측정됐다. 급하지 않다
- 자소서 양식 제안. 포트폴리오는 무엇을 만들지까지만 정해지고(#26), 어떻게 보일지의 양식은 아직 없다
- 여는 질문을 직무별로 생성하는 앵커 생성기

## 불변 원칙

기능은 계속 붙지만 아래는 고정이다. **새 기능이 이 중 하나를 어기면 그 기능이 잘못된 것이다.** 근거는 [`docs/rationale.md`](docs/rationale.md) #2.

**3·5 는 2026-09-07 에 뒤집혔다 — rationale #25.**

1. 판정하지 않고 **격차를 서술**한다
2. 역량 주장은 **에피소드 근거를 참조**한다
3. **저자성은 확인에서** 나온다 — 에이전트가 초안을 쓰고 사용자가 고친다 (2026-09-07 변경 — rationale #25)
4. **어떤 각도로 물을지는 표가 정한다** — 문장은 바닥이고, 전제가 거짓이면 같은 틀로 다시 만든다
5. **앞문만 막는다** — JD를 채굴 앵커로 쓰지 않는다. 면접관 지적·재료 내용은 그대로 전달한다 (2026-09-07 변경 — rationale #25)
6. 미완성을 **데이터로 남기고** 넘어간다
