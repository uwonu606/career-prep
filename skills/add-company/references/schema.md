# 저장 형식 — 회사

회사 파일은 `add-experience`의 `references/schema.md`와 **같은 저장소(`career/`)에 공존**한다. slug·`~`·`open_questions`·"비워 두는 것이 지어내는 것보다 항상 낫다"는 그 규약을 그대로 잇는다.

## 레이아웃

```
career/
├── projects/<slug>/{project.md, artifacts/}      add-experience 가 만든다
└── companies/<slug>/
    ├── company.md
    └── artifacts/
        ├── dart/        dart_fetch 산출: manifest.json, company.json, list.json(최신 보고서 선택 근거), {rcept_no}.xml(+첨부), empSttus-YYYY.json, exctvSttus-YYYY.json
        │                dart_extract 산출: business.md(II 절), people-report.md(VIII.1 절 원문) · dart_tables 산출: people-tables.md(empSttus·exctvSttus 표)
        └── findings/    findings-<묶음>.md — 묶음 에이전트가 반환한 원문 그대로. 편집하지 않는다
```

**회사는 프로젝트와 같은 급의 1급 객체다.** `projects/<slug>/{project.md, artifacts/}`와 같은 모양이다. `artifacts/`는 원자료의 자리라 손대지 않고, 해석은 `company.md`에만 쓴다. `<묶음>`은 `dart`·`company`·`external`·`market`·`reputation`(카탈로그 ①~⑤ 순).

`career/index.md`의 회사 표는 `add-experience/scripts/build_index.py`가 `companies/*/company.md`의 frontmatter로 만든다(회사 id·법인명·브랜드·조사일·공고·미해결 수). `companies/`가 없으면 표도 없다.

## slug

영문 kebab이고 그것이 곧 참조 id다. **법인명의 영문 표기를 우선한다** — `company.json`의 `corp_name_eng`가 있으면 거기서(`Kakao Corp.` → `kakao`, `Viva Republica Inc.` → `viva-republica`), 없으면 통용 영문명(`woowa-brothers`). 브랜드명(`toss`, `baemin`)은 slug가 아니라 frontmatter `brand`에 둔다. 한글 법인명은 `title`에 둔다.

## company.md

아래는 형식을 보이기 위한 예시다 — 식별자(카카오)와 실측된 URL(careers.kakao.com·tech.kakao.com·github.com/kakao)만 실제이고 `<…>`는 자리표시, 나머지 값도 조사값이 아니다.

```markdown
---
id: kakao
title: 주식회사 카카오
brand: 카카오                  # 법인명과 다를 때 뜻이 있다(비바리퍼블리카 → 토스). 없으면 ~
corp_code: <8자리>             # DART 고유번호(company.json). 해외 법인·미등록이면 ~
stock_code: <6자리>            # 비상장이면 ~
date: 2026-09-06               # 조사일. 재조사하면 갱신
job_url: ~                     # 사용자가 준 공고 URL. 없으면 ~
open_questions:
  - 채용공고 전체(지도 5, 실패) — WebFetch 결과 0건, JS 렌더
  - 개발자 인터뷰·팟캐스트(지도 12, 없음) — WebSearch 2회 0건
---

## 자료 지도

| 번호 | 각도 | 상태 | 링크/사유 |
|---|---|---|---|
| 1 | 공시 문서 | 있음 | artifacts/dart/business.md (사업보고서 <2025.12>, rcept_no <14자리>) |
| 2 | 직원 현황 | 있음 | artifacts/dart/people-tables.md#직원-현황 (empSttus <2021~2025>) |
| 3 | 임원·리더십 | 있음 | artifacts/dart/people-tables.md#임원-현황 (exctvSttus <2025>) |
| 4 | 회사 자체 소개 | 있음 | <company.json hm_url> |
| 5 | 채용공고 전체 | 실패 | https://careers.kakao.com — WebFetch 결과에 공고 0건(JS 렌더). open_questions 참조 |
| 6 | 채용 브랜딩 | 있음 | artifacts/findings/findings-company.md#채용-브랜딩 |
| 7 | 기술블로그 | 있음 | https://tech.kakao.com (RSS 발견) |
| 8 | 컨퍼런스 발표 | 있음 | artifacts/findings/findings-company.md#컨퍼런스-발표 |
| 9 | 오픈소스 | 있음 | https://github.com/kakao (org blog 필드 = tech.kakao.com) |
| 10 | 뉴스 | 있음 | artifacts/findings/findings-external.md#뉴스 |
| 11 | 외부 인터뷰·발표 | 있음 | artifacts/findings/findings-external.md#외부-인터뷰 |
| 12 | 개발자 인터뷰·팟캐스트 | 없음 | WebSearch 2회(법인명+"개발자 인터뷰" / +"팟캐스트") 0건. 그룹사 결과는 법인명 불일치로 제외 |
| 13 | IR 자료 | 있음 | <company.json ir_url> |
| 14 | 투자 이력 | 없음 | 상장사 — 라운드 자료 대신 13 |
| 15 | 특허 | 수동 | <KIPRIS 검색 URL> — robots 차단, 사람 눈 |
| 16 | 제품 직접 사용 | 수동 | <앱스토어 URL> |
| 17 | 평판·후기 | 수동 | <잡플래닛·블라인드 URL> — 직접 접근 차단 |
| 18 | 채용 프로세스 | 있음 | artifacts/findings/findings-reputation.md#채용-프로세스 |
| 19 | 탐색: <자료 유형> | 있음 | <URL> — catalog.md에 각도로 추가함 |

## 무슨 사업을 하나

**부문별 매출**(연결, 백만원) [artifacts/dart/business.md#4-매출-및-수주상황].

| 기(연도) | 합계 | <부문 A> | <부문 B> |
|---|---|---|---|
| 제<n>기(<연도>) | <값> | <값> | <값> |
| 제<n+1>기(<연도>) | <값> | <값> | <값> |
| 제<n+2>기(<연도>) | <값> | <값> | <값> |

**연구개발.** <담당 조직과 구성, 연구개발 항목이 가리키는 방향> [artifacts/dart/business.md#6-주요계약-및-연구개발활동].

**신사업.** <최근 1년 신사업·투자 사실> [출처](https://<뉴스 URL>). <경영진이 IR에서 강조한 방향> [출처](https://<IR 자료 URL>).

## 어떤 인재를 찾나

**직원 수**(명) [artifacts/dart/people-tables.md#직원-현황].

| 연도 | 정규직 | 계약직 | 합계 |
|---|---|---|---|
| <연도> | <값> | <값> | <값> |

**인재상.** <인재상·조직문화 문장> [출처](https://careers.kakao.com/<페이지>).

**개발 공고.** <N건, 직군 분포 한 문장> [출처](https://<채용 목록 URL>).

- **<공고 이름>** — <필수·스택 한 문장> [출처](https://<공고 URL>)
- **<공고 이름>** — <필수·스택 한 문장> [출처](https://<공고 URL>)

## 교차점

**1. <해석 한 줄>.** <단서·철회가 있으면 한 문장>
<empSttus 2023→2025 <부문> 정규직 +38%> [artifacts/dart/people-tables.md#직원-현황] × <기술블로그 최근 2년 글 12건 중 7건이 같은 부문 문제> [출처](https://tech.kakao.com/<태그>)

**2. <해석 한 줄>.**
<연구개발 항목의 주제> [artifacts/dart/business.md#6-주요계약-및-연구개발활동] × <채용 브랜딩의 팀 소개> [artifacts/findings/findings-company.md#채용-브랜딩]

## open_questions

- **채용공고 전체(지도 5, 실패)** — https://careers.kakao.com 을 WebFetch했으나 목록이 JS 렌더라 0건. 되찾기: 사용자가 브라우저로 열어 목록을 붙여넣으면 스택 분포를 계산한다. 원티드·점핏은 직접 호출 금지라 대체 불가.
- **개발자 인터뷰·팟캐스트(지도 12, 없음)** — WebSearch "주식회사 카카오 개발자 인터뷰" / "카카오 개발자 팟캐스트" 각 1회 0건. 다시 찾을 때 같은 검색어는 쓰지 말 것.
```

**frontmatter에 숫자 모양 필드(직원 수·매출·연봉)를 두지 않는다.** 칸이 숫자 모양이면 모르는 값을 채우게 된다 — "지어내지 말라"가 발동 중인데도 실측에서 일어났다(rationale.md #13). 숫자는 본문에 출처와 함께만 온다. `date`는 조사일이라 항상 `YYYY-MM-DD`다.

frontmatter `open_questions`는 항목당 한 줄이고, 본문 `## open_questions`가 같은 항목의 상세(절차·되찾을 경로·URL)를 든다. **두 목록의 항목 수는 같다** — 하나를 지우면 둘 다 지운다. URL·명령이 든 긴 문장은 YAML 안에서 깨지기 쉬워 본문에 둔다.

## 본문 5섹션 — 고정

순서와 제목을 바꾸지 않는다. 다른 섹션을 추가하지 않는다.

### 자료 지도

18행 + 탐색 행. 순서는 `catalog.md`. 열은 `번호 | 각도 | 상태 | 링크/사유`.

| 상태 | 뜻 | 링크/사유 칸 |
|---|---|---|
| `있음` | 자료를 찾아 `artifacts/`에 두었거나 링크로 잡았다 | 파일 경로 또는 URL |
| `없음` | 확인 절차를 돌렸고 이 회사에 그 자료가 없다(감사보고서만 내는 회사, 비상장의 IR 등) | **어느 절차**를 돌렸는지 |
| `수동` | 자료는 있는데 직접 접근이 막혀(robots·약관·챌린지) 링크만 두고 사람이 본다 | URL + 막힌 이유 |
| `실패` | 있을 텐데 절차가 깨졌다 — 파서 종료 2/3, 403/429, API 오류, JS 렌더 0건 | 사유 + `open_questions` 참조 |

**"없음"도 정보다.** 비상장이라 IR이 없고 감사보고서만 낸다는 사실이 회사의 단계를 말한다. 빈 행은 없다 — 점검하지 않은 각도가 있으면 지도가 아니다.

### 무슨 사업을 하나 / 어떤 인재를 찾나

사실 문장만 온다. **모든 문장은 출처로 끝난다** — `[출처](url)` 또는 `artifacts/dart/business.md#절` 같은 파일 경로(절 앵커는 `dart_extract`가 낸 **실제 제목**에서 만든다 — 예시의 `#4-매출-및-수주상황`은 예시다. 카카오처럼 연결에 금융 자회사가 있으면 제목이 `## 6. (제조서비스업)주요계약 및 연구개발활동`이 되어 앵커는 `#6-제조서비스업주요계약-및-연구개발활동`이고, 같은 번호가 `(금융업)`으로 한 번 더 나온다 ①). **출처 없는 문장은 이 두 섹션에 들어오지 못하고 `open_questions`로 간다.**

각도는 섹션이 아니라 출처로만 드러난다 — `### 뉴스`, `### 기술블로그` 같은 하위 절을 만들지 않는다. 같은 사실을 두 출처가 말하면 둘 다 붙인다.

숫자는 원자료 값을 그대로 옮긴다. 계산한 값(증감률·비중)은 두 원값과 계산식이 보이게 쓴다: "정규직 1,200 → 1,656(+38%)".

**형태는 사실 뭉치의 모양이 정한다.** 위에서부터 맞는 첫 칸을 쓴다.

| 사실 뭉치 | 형태 | 실물 예 |
|---|---|---|
| 같은 종류가 셋 이상 · 칸이 맞는다 | **비교표** | 연도별 매출, 분기 실적, 앱 평점 |
| 같은 종류가 셋 이상 · 칸이 제각각이다 | **라벨 목록** `- **<이름>** — <한 문장> [출처]` | 개발 공고 5건(필수·스택·우대가 다 다름) |
| 한 대상의 사실이 넷 이상 | **속성표** `구분 \| 값` | 특허 집계, 공고 분포, 기술 스택 |
| 그 밖 | **문단** — 굵은 머리말로 열고 출처 셋까지 | 생산, 연구개발 조직 |

표의 출처는 **머리 문장 끝에 한 번**이다. 행마다 출처가 다를 때만 `근거` 열을 만든다(에이피알 표 13개 중 12개가 머리, 1개가 열 ①).

**모르는 값이 생기는 열은 만들지 않는다**(rationale.md #19 — 칸이 숫자 모양이면 채우게 된다). 그 사실은 표에서 빼 문장으로 쓴다 — 에이피알 제10·11기 기타 비중이 그 경우다 ①.

훑히는 규약(제목 깊이·덩어리·중복 금지)은 `doc-style` 스킬이 소유한다. 한 가지만 다르다 — **문단 상한은 260자가 아니라 출처 셋**이다. 이 문서는 출처 하나가 150자쯤을 끌고 와(출처 4개 이상 문단 평균 631자 ①) 260자로 재면 출처 둘도 못 넣는다. 세는 것은 **문단뿐**이다 — 표(`|`)·라벨 목록(`-`)·교차점(` × `)은 항목마다 출처를 다는 게 정상이라 뺀다:

```
awk 'BEGIN{RS="\n\n"} !/^\|/ && !/^- / && !/ × / {n=gsub(/\[출처\]\(|\[artifacts\//,"&"); if(n>3) print n" 출처: "substr($0,1,60)}' company.md
```

찍힌 문단은 셋 중 하나다 — 표로 갈 것, 라벨 목록으로 갈 것, 주제가 둘이라 쪼갤 것.

### 교차점

사업 방향 ↔ 채용의 연결. **해석이 들어가는 유일한 자리다.** 한쪽 출처가 없으면 교차점이 아니라 추측이고, `open_questions`로 간다.

**해석이 먼저 온다** — 굵은 한 줄로 결론을 내고, 그 아래 줄에 `[A] × [B]`로 어느 두 출처를 이었는지 든다. 근거 두 덩이를 다 읽어야 결론이 나오는 순서면 안 읽힌다 ①. 위의 출처 셋 상한은 여기 걸리지 않는다 — `[A] × [B]`는 넷을 넘을 수 있다.

**저장 전에 사용자에게 보여주고 확인받는다**(불변 원칙 3 — 저자성은 사용자에게). 확인 질문은 비유도로 묻는다:

- "교차점 세 항목 중 둘째는 직원 추이와 블로그 주제를 제가 이은 해석입니다. 이대로 둘까요, 고칠까요, 뺄까요?"
- "본문에서 제가 잇지 않은 연결이 보이시나요? 있으면 지금 넣고, 없으면 그대로 저장합니다."

사용자가 빼라면 뺀다. 흔들리면 `open_questions`로 내린다.

### open_questions

못 찾은 것 + **어느 확인 절차를 썼고 어디서 되찾나.** 지도의 `실패` 행은 여기에도 반드시 있어야 하고, 사유와 되찾을 경로(DART 뷰어 `https://dart.fss.or.kr/dsaf001/main.do?rcptNo=<rcept_no>`, 재실행할 명령, 사용자가 브라우저로 열어 줄 URL)를 든다. `없음` 행은 사유가 지도 한 줄로 끝나면 여기 오지 않는다.

이게 없으면 다음 조사가 같은 자리를 다시 파고, 같은 검색어를 네 번째로 돌린다.

## 하지 않는 것

- **사용자에 대한 판정·핏 평가.** "이 회사와 맞다/안 맞다", "지원해라/말아라"를 쓰지 않는다(불변 원칙 1). 회사가 할 스크리닝을 대신 하지 않는다 — 그건 미래 `applications/`의 일이다.
- **회사 문장을 지어내기.** 출처 없는 문장은 `open_questions`다. 모르는 값은 `~`.
- **각도별 섹션.** 각도는 출처로만 등장한다.
- **findings 편집.** 묶음 에이전트의 반환은 원문 그대로 둔다. 정리하고 싶으면 `company.md`에 출처를 달아 쓴다.
- **`add-experience`의 입력으로 흘리기.** 공고·인재상은 채굴 앵커가 아니다(rationale.md #6).

## 갱신

같은 회사를 다시 조사하면 **새 파일이 아니라 같은 `company.md`를 갱신**하고 `date`를 바꾼다. 이전 지도와 달라진 행(상태·링크가 바뀜)은 본문 또는 `open_questions`에 "2026-03 없음 → 2026-09 있음" 꼴로 표시한다 — 달라진 것 자체가 회사의 변화다.

`artifacts/`는 덧붙이고 지우지 않는다. `dart/`의 `{rcept_no}.xml`·`empSttus-YYYY.json`은 이름이 곧 구분이라 그대로 쌓인다. 이름이 겹치는 산출(`manifest.json`, `company.json`, `business.md`, `people-report.md`, `people-tables.md`, `findings-<묶음>.md`)은 이전 것을 `<이름>-<이전 date>.<확장자>`로 옮긴 뒤 새로 쓴다.
