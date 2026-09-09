# 접근 규칙

그 서버를 스크립트·curl·WebFetch로 직접 불러도 되는지의 규칙이다. robots.txt와 이용약관을 읽어 등급을 판정한 **뒤에** 부른다. 판정과 호출이 한 명령에 있으면 조건문으로 막고, 어겼으면 사용자에게 밝힌다.

## 1. 접근 등급

**접근 등급** — 그 서버를 스크립트·curl·WebFetch로 직접 부를 수 있는지의 등급.
- **A** 직접 접근 가능. 공식 API이거나, robots.txt(사이트가 자동 접근 허용 범위를 적어 둔 파일)가 그 경로를 허용하고 **그리고** 이용약관에 자동화 접근 금지 조항이 없음을 실제로 읽어 확인한 곳. 확정 목록은 #2 첫 단락.
- **B** WebSearch(검색 도구)가 돌려준 결과와, 그 결과의 링크·사용자가 준 URL을 WebFetch(주소 하나를 읽어 오는 도구)로 읽은 것까지 — 깊이 한도(아래) 안에서, 한 주소에 한 번. 스크립트·curl로 그 서버를 부르거나 페이지를 따라 기어 들어가지 않는다.
- **C** 링크만 제시하고 내용은 사람이 본다. #2 금지 목록의 소스는 WebFetch도 하지 않는다 — WebSearch 스니펫과 링크뿐이다.

공통 규칙: 호스트당 요청 사이에 간격을 두고, 403·429가 오면 그 호스트는 즉시 중단하며, 실패한 요청은 재시도하지 않는다.

**깊이 기본값** — 실마리는 `leads.md` #1의 깊이(검색 두 번, 결과 링크 WebFetch 1건씩)를 따른다. 뻗기 각도는 각도당 대표 자료 최대 5건, 최근 2년 우선. 예외는 채용공고 전체 각도(`angles.md` 3행)만 **전체**(분포 계산에 필요).

사실 뒤의 ①②③은 근거 등급 — ① 실행으로 확인 ② 출처(공식 문서·약관) ③ 감(미확인).

## 2. 직접 접근 금지 목록

**규칙**: 직접 접근(스크립트·curl·WebFetch로 그 서버를 부르는 것)은 등급 A만. **robots 허용 ≠ 약관 허용** — 확인한 4곳 중 2곳(빅카인즈·YouTube)이 robots는 허용인데 약관이 금지였다 ②. 등급 A 확정 소스: OpenDART API(약관 제10조 허용량 내, 제11조 무료 ②) · DART `detailSearch.ax`(robots 미언급=허용, 사이트 약관 없음, 금감원 저작권정책 "비영리 개인 이용 자유" ②) · GitHub REST API(공식) · 회사 홈페이지 1회 fetch(그 도메인 robots 확인 후).

**예외는 사용자의 로그인이다** — 사용자가 `career-setup`으로 로그인해 둔 호스트(데이터 디렉토리 `auth/<host>.json`, `career-setup/references/layout.md` #3)는 그 계정으로 `career-setup/scripts/browser.py open` 한 페이지씩 열 수 있고, 출처 뒤에 `규칙 예외(auth)`를 적는다. 등급은 그대로다 — 로그인 ≠ 약관 허용. 목록 순회는 없다. 에지 차단(잡플래닛·블라인드·원티드)은 로그인 없는 헤드리스로 403이었고 ① 로그인 상태로는 미확인 ③.

아래 소스는 WebSearch 결과와 링크만 쓴다. WebFetch도 하지 않는다.

| 소스 | 이유 | 대신 |
|---|---|---|
| Google News RSS | robots `Disallow: /` + ClaudeBot 명시 차단 ② | WebSearch |
| 네이버 뉴스 검색 | robots `Disallow: /` ② | WebSearch |
| 빅카인즈 | robots는 `Allow: /`이지만 이용약관 제21조가 자동화 수집 금지 ② | WebSearch |
| YouTube | robots는 `/@handle` 허용이지만 약관이 "robots.txt에 따른 공개 검색엔진 외 자동화 수단 접근 금지" ② | WebSearch로 발표 목록, 링크 제시 |
| 원티드·점핏 API | robots.txt 자체가 CloudFront 403 → 허용 여부 확인 불가 ① | WebSearch 결과 |
| 사람인 오픈API | 승인 필요 ② | WebSearch 결과 |
| 잡코리아 | robots·약관 미확인 ③ — 확인 전까지 금지 | WebSearch 결과 |
| KIND(krx) | robots.txt가 WAF 차단 페이지 → 확인 불가 ①. 키가 있으면 필요 없다(`corpCode.xml`·`company.json`이 대체) | `dart_fetch.py --check`(키) · WebSearch "<브랜드명> 법인명" + `D1`(`angles.md` #2) |
| 잡플래닛 | Cloudflare 챌린지, 전 페이지 403 ① | 링크 |
| 블라인드 | ClaudeBot·anthropic-ai `Disallow: /` ① | 링크 |
| 크레딧잡 | `Disallow: /` ① | 링크 |
| 캐치 | `/Company` 경로 차단 ① | 링크 |
| 혁신의숲 | ClaudeBot 차단 ① | 링크 |
| KIPRIS | `Disallow: /` ①; KIPRIS Plus API는 키·조건 미확인 | 링크 |
| 팟캐스트 검색 API | 전부 미확인 또는 차단 | WebSearch |
| 한경컨센서스 | robots `Disallow: /` ① 2026-09-07 | WebSearch 결과와 리포트 브리핑 기사 |
| FnGuide Company Guide | robots·약관 미확인 ③ — 확인 전까지 금지 | WebSearch 결과 |
| image.ninehire.com (나인하이어 채용 사이트 이미지 CDN) | robots `Disallow: /`(예외 `/homepage/`) ① 2026-09-06. 에이피알 조사에서 robots 판정 전에 1회 받아 버린 실수가 있었다 — 공고 이미지는 배너뿐이었다 | 공고 본문 텍스트; 이미지는 링크만 |

새 소스를 직접 부르려면 먼저 `curl -sS https://<host>/robots.txt`에서 `User-agent: *`·`ClaudeBot`·`anthropic-ai` 블록의 `Disallow`를 읽고, 그 다음 사이트의 이용약관에서 자동화·크롤링·로봇 금지 조항을 읽는다. **둘 다** 통과해야 A, 아니면 B 또는 C. 약관 페이지를 못 찾으면(404 등, developers.kakao.com 실측 ①) A는 불가다. 접근 금지 판정이 나면 위 표에 한 줄 넣는다.
