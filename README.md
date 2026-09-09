# career-prep

[![test](https://github.com/uwonu606/career-prep/actions/workflows/test.yml/badge.svg)](https://github.com/uwonu606/career-prep/actions/workflows/test.yml)

내 저장소에서 소재를 뽑고 지원할 직무를 공고에서 조사해, 자소서·이력서·포트폴리오의 **재료**를 파일로 쌓는 툴킷.

## 무엇을 하는가

자소서의 품질은 글솜씨가 아니라 **재료**에서 결정된다. 그래서 이 툴킷은 자소서를 써주지 않는다. 재료 둘을 파일로 쌓는다.

1. **뽑는다** — 내 저장소를 끝까지 읽고 소재가 될 가능성이 있는 모든 것을 근거(커밋·PR·이슈·경로)와 함께 적는다. 고르지 않고 순위를 매기지 않고, 실행 중 묻지 않는다
2. **판다** — 지원할 직무의 공고 한 장에서 출발해 그 직무 주변을 조사하고, 문장마다 출처를 단다

재료에서 무엇을 고르고 어느 문서에 어떻게 쓸지는 이 툴킷 밖의 일이다.

설계 근거는 [`docs/rationale.md`](docs/rationale.md)에 있다. **결정을 뒤집기 전에 그 문서를 먼저 읽는 것을 권한다** — 근거 없이 "더 자연스러워 보여서" 바꾸면 이미 검토해서 기각한 설계로 되돌아가게 된다. 2026-09-09 이전의 인지면접 툴킷을 왜 버렸는지는 #10 에 있다.

## 쓰는 법

처음 한 번, 개인 데이터를 둘 디렉토리에서 — 스킬은 전부 그 디렉토리에서 실행한다:

```
/career-setup                   career/·키(.env)·로그인 상태(auth/)·GitHub 로그인을 준비한다
```

내 저장소가 있으면:

```
/extract-repo <디렉토리 또는 원격 주소>   리포 하나를 끝까지 읽고 재료를 뽑는다
```

리포에 남은 흔적을 일곱 축(도메인·문제 / 구조·기술 선택과 대안 / 장애·버그와 수정 / 성과·수치 / 과정·협업 / 에이전트 활용과 검증 / 그 밖)으로 훑어 **사건 단위**로 재료를 적는다. 재료마다 근거·종류(직접/정황)·리포로 못 밝힌 `확인 필요`가 붙고, 본인이 저자·리뷰어·이슈 작성자인 것을 뽑되 함께 만든 사람의 이어진 작업은 `함께 한 것`에 둔다. 다시 돌리면 마지막으로 훑은 커밋 뒤만 덧붙인다. 근거는 #9.

지원할 직무의 공고가 있으면:

```
/research-role <채용공고 URL>          공고에서 출발해 그 직무 주변을 파고, 안 풀리는 질문만 바깥으로 뻗는다
```

공고 한 장에서 깊게 판다. 공고의 줄마다 **실마리**(팀·제품·기술·사람의 이름과 공고가 답하지 않는 질문)를 뽑아 팀·리더·대표의 말·스택·제품을 파고, 공고만으로 안 풀리는 질문이 남을 때만 DART·전체 공고·뉴스로 뻗는다. **문장마다 출처를 달아** `career/companies/<slug>/roles/<role>/`에 쌓고, 사용자에 대해 판정하지 않는다("맞다/안 맞다"를 쓰지 않는다). 근거는 #7.

## 데이터

데이터 디렉토리의 `career/`에 쌓인다. **툴킷 저장소에는 들어오지 않는다** — 개인 기록이라 배포 대상이 아니다.

```
career/
├── repos/<slug>/{repo.md, candidates.md, artifacts/}      리포 재료 — extract-repo 가 만든다. 스크립트·gh 원자료는 artifacts/
└── companies/<slug>/roles/<role>/{role.md, artifacts/}   직무 조사 — research-role 이 만든다. 공고 원문·에이전트 반환·DART 산출은 artifacts/
cache/repos/<slug>/                                        원격 리포의 클론. 지워도 다시 받는다
```

## 구성

| | |
|---|---|
| `skills/extract-repo/` | 저장소 하나에서 재료를 뽑는다 |
| `└ references/axes.md` | 축 일곱과 어디에 남나, 사건으로 묶는 규칙, 칸 일곱, 누구의 것을 뽑나 |
| `└ references/files.md` | `repo.md`·`candidates.md` 모양 |
| `└ scripts/repo_facts.py` | git 사실을 `summary.json`·`commits.json`으로. 표준 라이브러리 + git |
| `└ scripts/test_repo_facts.py` | 출력 형식 테스트 — 임시 저장소를 만들어 돈다 |
| `skills/research-role/` | 직무 하나를 공고에서 출발해 조사한다 |
| `└ references/leads.md` | 실마리 여섯 종류와 정체가 드러나는 자리, 질문 실마리의 네 무늬, 뻗는 조건 다섯, 에이전트에 넘기는 것과 반환 형식 |
| `└ references/role.md` | 직무 파일 모양 — 공고와 실마리 / 실마리가 닿은 것 / 공고 밖에서 온 것, 실마리 줄이 곧 상태. slug 규칙 |
| `└ references/access.md` | 접근 등급(robots 허용 AND 약관 무금지만 직접 접근), 직접 접근 금지 목록, 로그인 예외 |
| `└ references/angles.md` | 뻗기 각도 일곱 — 각도별 절차, 명령 블록(DART 유무 확인·robots 판정·홈페이지 1회 fetch) |
| `└ scripts/dart_fetch.py` `dart_extract.py` `dart_tables.py` | OpenDART 수집(키는 스크립트만 읽는다) · 사업보고서 원문 절 추출 · 직원·임원 표. 표준 라이브러리만 |
| `└ scripts/test_extract.py` `test_fetch.py` | 파서 회귀(픽스처는 리포 밖, `ADD_COMPANY_FIXTURES`) · 수집기 합성 응답 테스트 |
| `skills/career-setup/` | 데이터 디렉토리·키·로그인 상태를 준비한다 |
| `└ references/layout.md` | 데이터 디렉토리의 자리 — `career/`·`cache/`·`.env`·`auth/`·`fixtures/`, 키 표, 로그인 상태 규약, GitHub 로그인 |
| `└ scripts/browser.py` | `login`(창에서 로그인해 상태 저장) · `list` · `open`(그 상태로 페이지 하나 읽기). `uv run` |
| `docs/rationale.md` | 설계 근거 — 뒤집기 전에 읽을 것 |
| `docs/research/appeal-criteria/` | 무엇이 소재가 되나 — 2026-09 공고 원문 20건과 출처 26건, 리포에서 뽑을 수 있는 증거 표 |
| `docs/market-research.md` | 채용 프로세스 모델의 근거와 출처 |
| `docs/company-research.md` | 회사 조사 소스·파서 실측 — robots·약관 판정, 사업보고서 XML 구조, 첫 수정 루프 |

## 설치

`SKILL.md` 형식은 [Agent Skills 공개 표준](https://agentskills.io)이고 ChatGPT·Codex·Cursor·Copilot 등 40여 개 제품이 읽는다. 플러그인 구조는 [Agent Plugins v1.0.0](https://agent-plugins.org)을 따른다.

```bash
npx skills add uwonu606/career-prep
```

어느 환경에서든 `skills/` 셋이 들어간다.

처음 한 번 개인 데이터 디렉토리에서 `/career-setup`을 돈다 — `career/`·키(`.env`)·로그인 상태(`auth/`)가 거기 생기고 `gh` 로그인을 확인하며, 무엇이 어디에 있는지는 [`skills/career-setup/references/layout.md`](skills/career-setup/references/layout.md)가 정한다. 키와 로그인 상태의 내용은 스크립트만 읽는다(대화나 셸 명령에 나오지 않는다). OpenDART 키가 없으면 `research-role` 뻗기의 DART 행만 비고, `gh` 로그인이 없으면 `extract-repo`가 비공개 리포와 PR·이슈만 못 읽고 나머지는 그대로 돈다.

## 불변 원칙

기능은 계속 붙지만 아래는 고정이다. **새 기능이 이 중 하나를 어기면 그 기능이 잘못된 것이다.** 근거는 [`docs/rationale.md`](docs/rationale.md) #2.

1. 판정하지 않고 **격차를 서술**한다 — 재료에 점수·순위가 없고, 직무 파일에 "맞다/안 맞다"가 없다
2. 재료마다 **저장소 안 근거**가 붙는다 — 커밋·PR·이슈·`경로:줄`. 직무 파일의 문장은 출처로 끝난다
3. **해석이 들어가는 저장만 확인**을 거친다 — `research-role`의 "공고 밖에서 온 것". 재료 파일은 사실의 나열이라 확인 없이 저장한다
4. 미완성을 **데이터로 남기고** 넘어간다 — `확인 필요`·`open_questions`
