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

처음 한 번, 개인 데이터를 둘 디렉토리에서 — 스킬은 전부 그 디렉토리에서 실행한다:

```
/career-setup                   career/·키(.env)·로그인 상태(auth/)를 만든다
```

지원할 직무의 공고가 있으면:

```
/research-role <채용공고 URL>          공고에서 출발해 그 직무 주변을 파고, 안 풀리는 질문만 바깥으로 뻗는다
```

공고 한 장에서 깊게 판다. 공고의 줄마다 **실마리**(팀·제품·기술·사람의 이름과 공고가 답하지 않는 질문)를 뽑아 팀·리더·대표의 말·스택·제품을 파고, 공고만으로 안 풀리는 질문이 남을 때만 DART·전체 공고·뉴스로 뻗는다. **문장마다 출처를 달아** `career/companies/<slug>/roles/<role>/`에 쌓고, 사용자에 대해 판정하지 않는다("맞다/안 맞다"를 쓰지 않는다). 근거는 #28.

## 데이터

데이터 디렉토리의 `career/`에 쌓인다. **툴킷 저장소에는 들어오지 않는다** — 개인 기록이라 배포 대상이 아니다.

```
career/
└── companies/<slug>/roles/<role>/{role.md, artifacts/}   직무 조사 — research-role 이 만든다. 공고 원문·에이전트 반환·DART 산출은 artifacts/
```

## 구성

| | |
|---|---|
| `skills/research-role/` | 직무 하나를 공고에서 출발해 조사한다 |
| `└ references/leads.md` | 실마리 여섯 종류와 정체가 드러나는 자리, 질문 실마리의 네 무늬, 뻗는 조건 다섯, 에이전트에 넘기는 것과 반환 형식 |
| `└ references/role.md` | 직무 파일 모양 — 공고와 실마리 / 실마리가 닿은 것 / 공고 밖에서 온 것, 실마리 줄이 곧 상태. slug 규칙 |
| `└ references/access.md` | 접근 등급(robots 허용 AND 약관 무금지만 직접 접근), 직접 접근 금지 목록, 로그인 예외 |
| `└ references/angles.md` | 뻗기 각도 일곱 — 각도별 절차, 명령 블록(DART 유무 확인·robots 판정·홈페이지 1회 fetch) |
| `└ scripts/dart_fetch.py` `dart_extract.py` `dart_tables.py` | OpenDART 수집(키는 스크립트만 읽는다) · 사업보고서 원문 절 추출 · 직원·임원 표. 표준 라이브러리만 |
| `└ scripts/test_extract.py` `test_fetch.py` | 파서 회귀(픽스처는 리포 밖, `ADD_COMPANY_FIXTURES`) · 수집기 합성 응답 테스트 |
| `skills/career-setup/` | 데이터 디렉토리·키·로그인 상태를 준비한다 |
| `└ references/layout.md` | 데이터 디렉토리의 자리 — `career/`·`.env`·`auth/`·`fixtures/`, 키 표, 로그인 상태 규약 |
| `└ scripts/browser.py` | `login`(창에서 로그인해 상태 저장) · `list` · `open`(그 상태로 페이지 하나 읽기). `uv run` |
| `docs/rationale.md` | 설계 근거 — 뒤집기 전에 읽을 것 |
| `docs/market-research.md` | 채용 프로세스 모델의 근거와 출처 |
| `docs/company-research.md` | 회사 조사 소스·파서 실측 — robots·약관 판정, 사업보고서 XML 구조, 첫 수정 루프 |

## 설치

`SKILL.md` 형식은 [Agent Skills 공개 표준](https://agentskills.io)이고 ChatGPT·Codex·Cursor·Copilot 등 40여 개 제품이 읽는다. 플러그인 구조는 [Agent Plugins v1.0.0](https://agent-plugins.org)을 따른다.

```bash
npx skills add uwonu606/career-prep
```

어느 환경에서든 `skills/` 둘이 들어간다.

처음 한 번 개인 데이터 디렉토리에서 `/career-setup`을 돈다 — `career/`·키(`.env`)·로그인 상태(`auth/`)가 거기 생기고, 무엇이 어디에 있는지는 [`skills/career-setup/references/layout.md`](skills/career-setup/references/layout.md)가 정한다. 키와 로그인 상태의 내용은 스크립트만 읽는다(대화나 셸 명령에 나오지 않는다). OpenDART 키가 없으면 `research-role` 뻗기의 DART 행만 비고 나머지는 그대로 돈다.

## 불변 원칙

기능은 계속 붙지만 아래는 고정이다. **새 기능이 이 중 하나를 어기면 그 기능이 잘못된 것이다.** 근거는 [`docs/rationale.md`](docs/rationale.md) #2.

**3·5 는 2026-09-07 에 뒤집혔다 — rationale #25.**

1. 판정하지 않고 **격차를 서술**한다
2. 역량 주장은 **에피소드 근거를 참조**한다
3. **저자성은 확인에서** 나온다 — 에이전트가 초안을 쓰고 사용자가 고친다. 확인하는 것은 저자가 아니라 면접에서 말할 수 있는지다 (2026-09-07 변경 — rationale #25·#27)
4. **어떤 각도로 물을지는 표가 정한다** — 문장은 바닥이고, 전제가 거짓이면 같은 틀로 다시 만든다
5. **앞문만 막는다** — JD를 채굴 앵커로 쓰지 않는다. 면접관 지적·재료 내용은 그대로 전달한다 (2026-09-07 변경 — rationale #25)
6. 미완성을 **데이터로 남기고** 넘어간다
