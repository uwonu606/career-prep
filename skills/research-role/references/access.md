# 접근 규칙

서버를 스크립트·curl·WebFetch로 직접 부르는 것은 **등급 A**만이다. 등급은 robots.txt와 이용약관을 읽어 판정하고, 판정한 뒤에 부른다.

## 1. 등급

- **A** 직접 접근. 공식 API이거나, robots가 그 경로를 허용하고 **그리고** 약관에 자동화 접근 금지 조항이 없음을 둘 다 읽어 확인한 곳. 확정: OpenDART API · DART `detailSearch.ax` · GitHub REST API · 회사 홈페이지 1회 fetch(그 도메인 robots 확인 뒤).
- **B** WebSearch 결과와, 그 결과의 링크·사용자가 준 URL을 WebFetch로 한 주소에 한 번. 페이지를 따라 기어 들어가는 것은 직접 접근이다.
- **C** 링크만 제시하고 내용은 사람이 본다. #3의 소스가 여기다.

호스트당 요청 사이에 간격을 두고, 403·429가 오면 그 호스트는 즉시 멈추고, 실패한 요청은 그대로 둔다.

**새 호스트를 직접 부르려면** 판정이 먼저다 — `robots_check.py`가 전부 허용을 찍어야 다음으로 가고, 그 다음 사이트의 이용약관에서 자동화·크롤링·로봇 조항을 읽는다. 둘 다 통과해야 A다. robots를 못 받거나(403·WAF) 약관 페이지가 없으면 A가 아니다. 판정과 fetch를 한 명령에 두면 `&&`로 잇는다 — 판정이 차단이면 fetch가 돌지 않는다.

```bash
python3 <스킬>/scripts/robots_check.py <host> / <경로...> --save "$WORK/robots-<host>.txt" && curl -sS -A "$UA" "https://<host>/<경로>" -o "$WORK/<이름>"
```

`<스킬>`은 `research-role/SKILL.md`가 있는 디렉토리, `$WORK`는 작업 디렉토리(임시물 자리), `$UA`는 `research-role/0.1 (+python-urllib)` — 식별 문자열이다.

차단으로 판정한 호스트는 #3 표에 한 줄 넣는다. 판정 전에 받아 버렸으면 사용자에게 밝힌다.

## 2. 로그인 예외

사용자가 `career-setup`으로 로그인해 둔 호스트(데이터 디렉토리 `auth/<host>.json`)는 그 계정으로 **페이지 하나씩** 연다. 등급은 그대로다 — 출처 뒤에 `규칙 예외(auth)`를 적는다. 목록 페이지는 열지 않고 실마리가 가리킨 페이지 1건이다.

```bash
cd <데이터 디렉토리> && uv run <career-setup 스킬>/scripts/browser.py open "<url>"
```

`uv run`으로 부른다 — 스크립트가 PEP 723 머리에서 `playwright`를 스스로 받는다. 로그인 페이지로 돌아오면 만료다 — 링크만 남기고 사용자에게 `career-setup`을 안내한다. 파일이 없는 호스트도 같다. 잡플래닛·블라인드·원티드는 로그인 없는 헤드리스로 403이었고 로그인 상태로는 미확인이다.

## 3. 링크만 쓰는 소스

WebSearch 스니펫과 링크까지다. WebFetch도 하지 않는다.

| 소스 | 대신 |
|---|---|
| Google News RSS · 네이버 뉴스 검색 · 빅카인즈 · 팟캐스트 검색 API | WebSearch |
| YouTube | WebSearch로 발표 목록, 링크 |
| 원티드 · 점핏 · 사람인 오픈API · 잡코리아(미확인) | WebSearch 결과 |
| 한경컨센서스 · FnGuide(미확인) | WebSearch 결과, 리포트 브리핑 기사 |
| KIND(krx) | `dart_fetch.py --check` — `corpCode`·`company.json`이 대체한다 |
| 잡플래닛 · 블라인드 · 크레딧잡 · 캐치 · 혁신의숲 · KIPRIS | 링크 |
| image.ninehire.com(나인하이어 채용 사이트 이미지) | 공고 본문 텍스트, 이미지는 링크 |

빅카인즈·YouTube는 robots가 허용인데 약관이 금지다 — robots 허용은 약관 허용이 아니다.
