# 뻗기

2단계 뒤 남은 실마리 — 닿지 않았거나, 닿았는데 크기·방향을 모르는 것 — 를 아래 조건에 댄다. 맞는 절만 판다. 절마다 에이전트 하나이고, 어느 실마리 때문에 파는지를 함께 넘긴다. 맞는 절이 없으면 뻗기는 비어 있고 그것도 기록이다.

에이전트에 넘기는 것은 `leads.md` #2와 같고, 거기에 이 파일의 해당 절과 그 절을 연 실마리를 더한다. 등급은 `access.md`. `<스킬>`은 이 스킬의 `SKILL.md`가 있는 디렉토리의 절대 경로, `$WORK`는 에이전트 작업 디렉토리(임시물은 전부 여기, `artifacts/`에는 두지 않는다), `UA="research-role/0.1 (+python-urllib)"`(식별 문자열, 브라우저 UA로 바꾸지 않는다).

## 1. 팀·제품이 회사 안에서 얼마나 크고 커지는지 모른다 → DART

「II. 사업의 내용」(무슨 사업을 어떻게 하나 — 주요 제품·서비스, 매출, 연구개발, 주요계약)과 직원 현황(부문별 인원·평균 근속·1인 평균급여, 최근 사업연도들)에서 읽는다. 등급 A, 키가 필요하다 — 키는 `dart_fetch.py`가 `.env`에서 스스로 읽는다.

```bash
python3 <스킬>/scripts/dart_fetch.py "<법인명>" --out artifacts/dart
python3 <스킬>/scripts/dart_extract.py artifacts/dart/<rcept_no>.xml --out artifacts/dart/business.md --people artifacts/dart/people.md
python3 <스킬>/scripts/dart_tables.py --emp artifacts/dart/empSttus-*.json --exec artifacts/dart/exctvSttus-*.json --out artifacts/dart/people-tables.md
```

`<rcept_no>`는 첫 명령의 stdout에 있다. `exctvSttus-*.json`이 없으면 `--exec`를 뺀다. 종료 코드는 `--help`가 적는다 — 셋만 분기한다: 2(사업보고서 없음 — 감사보고서만 내는 회사)·5(키 없음)는 그 실마리를 비워 `open_questions`에 두고, 4(법인명 후보 여럿)는 stderr의 후보에서 고른다.

법인명은 **정확일치**다 — 브랜드명이 아니다. 비상장이라도 증권을 모집·매출한 회사는 사업보고서를 낸다(당근마켓·비바리퍼블리카·컬리·무신사). 금융업 서식은 「II. 사업의 내용」에 연구개발 절이 없다 — 없음은 파서 실패가 아니다. 연결에 금융 자회사가 있으면 제조서비스업·금융업 절이 나란히 나온다.

파서가 깨지면 그 실마리에 DART 뷰어 링크를 남기고 다음으로 간다 — 파서는 조사가 끝난 뒤 별도 세션에서 고친다.

## 2. 이 직무가 회사 채용 전체에서 어디쯤인지 모른다 → 전체 공고

여는 포지션 **전부**의 직무·요구 스택 분포를 센다 — `model: haiku`. 유일하게 전체를 모으는 절이다.

```bash
python3 <스킬>/scripts/robots_check.py <홈페이지 호스트> / --save "$WORK/robots.txt" \
  && curl -sS -L -A "$UA" "https://<홈페이지>/" -o "$WORK/homepage.html" -w '%{url_effective}\n'
grep -o -i -E 'href="[^"]*(career|recruit|jobs|채용)[^"]*"' "$WORK/homepage.html" | sort -u
```

`-L`이 리다이렉트를 따르므로 출처에는 마지막 줄의 최종 URL을 적는다. 채용 사이트 루트가 나오면 그 도메인도 `robots_check.py`로 판정한 뒤 WebFetch 1건 또는 `site:<채용도메인>` WebSearch로 목록 URL을 확정한다. 채용 사이트가 JS 셸이라 WebFetch에 제목만 오면 `robots_check.py`가 찍은 `Sitemap:`을 먼저 본다 — 공고 URL이 사이트맵에 전부 있는 회사가 있다. 홈페이지에 채용 링크가 없으면 WebSearch "<법인명> 채용". 플랫폼 공고는 WebSearch 결과로만(`access.md` #3). 관계사 공고가 같은 목록에 섞이면 법인명으로 거른다. 요청 간격 1.5초.

## 3. 회사 질문에 대표의 말이 안 닿았다 → 뉴스·IR

- **뉴스** — WebSearch "<법인명> 신사업 / 투자 / 조직" 최근 2년. 등급 B.
- **IR** — `artifacts/dart/company.json`의 `ir_url`(키 있을 때) → 홈페이지 HTML href의 `(/ir|invest)` grep → `https://<홈페이지>/ir`. 실적발표 자료에서 경영진이 숫자로 강조하는 방향을 읽는다. 비상장은 대개 없고, 없음도 기록이다.

## 4. 전형이 공고에 없다 → 채용 프로세스

WebSearch "<법인명> 코딩테스트 / 면접 후기 / 채용 과정". 채용 사이트에 절차 안내가 있으면 그것이 1차 출처다. 등급 B.

## 5. 이 직군의 처우를 묻는다 → 평판

WebSearch "<법인명> 잡플래닛 / 블라인드 / 연봉" 스니펫으로 유무만 확인하고 링크를 제시한다. 등급 C.

**깊이** — 절당 대표 자료 최대 5건, 최근 2년 우선. 예외는 #2(전체).
