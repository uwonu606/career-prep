---
name: add-company
description: 회사 하나를 공개 자료(DART 공시·채용공고·기술블로그·뉴스·인터뷰 등 18각도)로 조사해 무슨 사업을 하고 어떤 인재를 찾는지 출처와 함께 career/companies/에 기록한다. 지원할 회사가 정해져 자소서·면접 재료가 필요할 때 회사명(과 선택으로 채용공고 URL)을 주면 쓴다.
disable-model-invocation: true
---

# 회사 하나 추가하기

한 번 실행에 **회사 한 곳**을 조사해 기록한다. 사용자에 대해 판정하지 않는다 — "이 회사와 맞다/안 맞다"는 쓰지 않고, 회사가 무슨 사업을 하고 어떤 인재를 찾는지만 출처와 함께 적는다(불변 원칙 1).

어떤 각도로 볼지는 [`references/catalog.md`](references/catalog.md)의 표가 정한다. 표는 바닥이지 천장이 아니다 — 18각도를 전부 점검한 뒤 이 회사에만 있는 자료를 한 번 더 찾는다. 에이전트 프롬프트는 [`references/agents.md`](references/agents.md), 파일 규약은 [`references/schema.md`](references/schema.md)다. `<스킬>`은 이 `SKILL.md`가 있는 디렉토리의 절대 경로다.

## 0. 준비

데이터 디렉토리에서 실행한다 — 작업 디렉토리에 `career/`가 없으면 `~/.config/career-prep/data-dir`의 경로로 옮긴다(`career-setup/references/layout.md` #0). `career/`·`.env`가 거기 있다. `career/companies/`가 없으면 그것만 만든다 — 나머지는 `add-experience`의 것이다.

키 유무는 `./.env` 파일이 **있는지만** 본다 — 내용은 읽지 않는다(이 환경은 `.env`를 읽는 셸 명령을 권한 규칙으로 거부하고, 키는 스크립트가 스스로 읽는다). 파일이 없으면 `career-setup` 1단계(발급 URL은 `career-setup/references/layout.md` #2)를 안내하고 **멈추지 않는다.** 키 없음은 DART 세 각도의 지도 상태(`실패(키 없음)`)로 남을 뿐, 나머지 15각도는 그대로 돈다. 키가 있으면 `python3 <스킬>/scripts/dart_fetch.py "<이름>" --check`가 법인명 확정과 사업보고서 유무를 한 번에 돌려준다(종료 5면 키가 유효하지 않은 것).

법인명을 확정한다 — `catalog.md` #1(키가 있으면 위 `--check`가 곧 1번 경로다). 입력은 브랜드명일 수 있고 브랜드명 ≠ 법인명이다(토스 → 비바리퍼블리카). 확정 못 하면 후보 목록을 보여주고 고르게 한다. 지어내서 진행하지 않는다. 확정값은 법인명·브랜드명·corp_code·stock_code·영문명·홈페이지 URL·대표명 — 모르는 것은 `~`.

slug를 정한다(`schema.md`, 법인명의 영문 표기 우선). `career/companies/<slug>/`가 이미 있으면 **갱신 모드**다 — `schema.md`의 갱신 절대로 같은 `company.md`를 고치고 `date`를 바꾸며, `artifacts/`는 덧붙인다.

사용자가 채용공고 URL을 줬으면 `job_url`로 보관한다 — frontmatter에 들어가고, 2단계에서 묶음 ② 에이전트에 넘어간다.

**완료 조건:** `career/companies/<slug>/artifacts/{dart,findings}/`가 있고, 확정값 일곱과 키 유무가 정해졌고, 새 조사인지 갱신인지 정해졌다.

## 1. 자료 지도

임시물을 둘 작업 디렉토리를 `mkdir -p`로 만든다(예: `/tmp/…/add-company/<slug>/`). 지도 에이전트 **하나**를 띄운다 — `agents.md`의 "지도" 템플릿에 확정값·키 유무·조사일·`catalog.md`와 그 작업 디렉토리의 절대 경로를 채워 넘긴다. 에이전트는 `catalog.md` #2~#6의 "확인 절차" 열을 각도 순으로 밟고 #9 형식으로 18행 + 19번째 탐색 행을 돌려준다. 접근 등급을 넘지 않고, 자료를 해석하지 않고, 있는지만 본다.

받은 19행을 **사용자에게 보여준다.** 답을 기다리지 않고 진행하되, 사용자가 빼라는 행이 있으면 2단계에서 파지 않는다 — 지도에는 상태를 그대로 두고 사유 끝에 "사용자 제외"를 붙인다. 표 아래 `주의:` 줄(법인 변동 신호)이 있으면 `open_questions` 첫 항목으로 옮긴다.

**완료 조건:** 19행 전부에 상태(`있음`·`없음`·`수동`·`실패`)가 있고, `있음`·`수동`은 링크, `없음`·`실패`는 사유가 있다. 빈 행이 없다.

## 2. 파기

`있음`·`수동` 행이 하나라도 있는 묶음만 판다. 묶음당 에이전트 **하나**를 **병렬**로 띄운다("묶음" 템플릿). 각 에이전트에는 그 묶음의 지도 행만·확정값·조사일·`artifacts/`와 `catalog.md`의 절대 경로를 넘기고, 묶음 ②에는 `job_url`과 지도 에이전트가 받아 둔 홈페이지 HTML 경로도 넘긴다. 반환문은 **편집 없이** `artifacts/findings/findings-<묶음>.md`로 저장한다 — 묶음 토큰은 `dart`·`company`·`external`·`market`·`reputation`.

**DART 묶음**은 스크립트 세 개(`dart_fetch.py` → `dart_extract.py` → `dart_tables.py`)를 이 순서로 돌린다 — 인자·종료 코드별 행동·픽스처 절차는 [`references/agents.md`](references/agents.md) "묶음" 템플릿의 DART 절이 정한다. 픽스처 디렉토리 `$ADD_COMPANY_FIXTURES`를 함께 넘긴다(타사 공시 원문이라 툴킷 리포 밖에 둔다; 변수가 없으면 사용자에게 위치를 묻는다).

`dart_extract.py`가 종료 2·3이면 **파서를 고친다, 우회하지 않는다.** 묶음 에이전트가 픽스처를 추가하고 `실패`로 보고하면 메인이 **수정 에이전트** 하나를 띄우고("수정" 템플릿), 전 픽스처가 통과하면 **DART 묶음 에이전트만** 재실행한다. 수정도 실패하면 그 각도는 `수동` + DART 뷰어 링크(`https://dart.fss.or.kr/dsaf001/main.do?rcptNo=<rcept_no>`, 사람이 브라우저로 연다)로 남긴다.

서브에이전트가 없는 환경이면 메인이 같은 템플릿을 자기 절차로 읽고 같은 순서로 **순차** 수행한다 — 서브에이전트는 최적화이지 의존성이 아니다(rationale #12).

**완료 조건:** 판 묶음마다 `findings-<묶음>.md`가 있고 각 항목이 "사실 한 문장 + 출처 하나 + 각도 번호"다. DART 묶음은 `business.md`·`people-report.md`·`people-tables.md`가 있거나, 해당 각도가 `실패`·`수동`으로 사유와 함께 남았다.

## 3. 종합

[`references/schema.md`](references/schema.md) 형식으로 `company.md`를 쓴다 — 자료 지도 → 무슨 사업을 하나 → 어떤 인재를 찾나 → 교차점 → open_questions, 이 다섯만 이 순서로. **모든 문장은 출처로 끝난다** — `[출처](url)` 또는 `artifacts/…` 경로. 출처 없는 문장은 본문에 못 들어오고 `open_questions`로 간다. 숫자 표기·형태(비교표·라벨 목록·속성표·문단)·각도를 섹션으로 만들지 않는 것은 전부 `schema.md`가 정한다 — 형태는 사실 뭉치의 모양을 보고 사다리에서 고른다.

교차점은 해석이 들어가는 유일한 자리다. **쓰기 전에 사용자에게 보여주고** `schema.md`의 비유도 질문으로 확인받는다 — *"둘째 문장은 직원 추이와 블로그 주제를 제가 이은 해석입니다. 이대로 둘까요, 고칠까요, 뺄까요?"* *"제가 잇지 않은 연결이 보이시나요?"* 사용자가 빼라면 뺀다. 흔들리면 `open_questions`로 내린다.

**완료 조건:** frontmatter 각 필드가 값·`[]`·`~` 중 하나, 5섹션이 순서대로 존재, 출처 없는 문장 0, 교차점 밖에 출처 넷 이상인 문단 0(`schema.md`의 검사 명령), 지도의 `실패` 행이 `open_questions`에도 있고, frontmatter와 본문의 `open_questions` 항목 수가 같다.

## 4. 마무리

사용자에게 남은 `open_questions`를 읽어준다 — 어느 각도를 썼고 어디서 되찾는지까지.

지도 19행에 새 자료 유형이 나왔으면 `catalog.md` #7의 성장 규칙대로 각도를 추가하고 사용자에게 알린다. `add-experience`의 `scripts/build_index.py`를 돌린다 — `companies/*/company.md`의 frontmatter로 `index.md`에 회사 표(회사·법인명·브랜드·조사일·공고·미해결 수)를 만든다. 이 결과는 `add-experience`의 채굴 앵커로 쓰지 않는다 — 공고·인재상은 경험을 캐는 입력이 아니다(rationale #6).

**완료 조건:** 사용자가 남은 `open_questions`와 카탈로그 변경을 안다.
