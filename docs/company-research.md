# 회사 조사 소스·파서 실측

`add-company`가 어느 소스를 직접 부르고 어느 소스는 검색·사람 눈으로 넘기는지, 사업보고서 원문을 왜 그렇게 파싱하는지의 **실측 기록**이다. 결정은 [`rationale.md`](rationale.md) #17~#22에 있고, 여기는 그 결정이 딛고 선 숫자다. 근거 등급은 ① 실행 결과 ② 출처 ③ 감. 측정일 2026-09-04~06.

## 한계 — 먼저 읽을 것

- **표본이 작다.** 사업보고서 원문 XML 4건(dart3 세대 3, dart4 세대 1), 인코딩 선언 5건, RSS 프로빙 9곳, 채용 링크 grep 3곳, 지도 단계 시운전 1회사. 통계가 아니라 사례다.
- **대형 IT 회사 기준이다.** 카카오·토스(비바리퍼블리카)·우아한형제들에서 통한 확인법이 중소 회사에서 같은 성공률을 보이는지는 모른다.
- **약관은 읽은 시점의 문면이다.** 빅카인즈 약관은 2025-06-01 시행판, YouTube는 2022-01-05판. 바뀌면 판정도 바뀐다.
- **dart4 실물은 1건이다**(카카오 FY2025). 골격이 dart3과 같다는 것과 홑 `&`가 문제였다는 것까지만 확인됐다.
- 전 절차(지도 → 묶음 5개 → 교차점 → 저장)를 한 회사로 끝까지 돌린 기록은 아직 없다. 지도 단계와 DART 묶음만 실측했다.

## 1. TypeScript vs Python (#21, ①)

정적 타입을 원해 스크립트를 TypeScript로 쓰자는 제안을 같은 과제(KIND 상장사 목록 EUC-KR HTML 2,802행 파싱, ZIP + cp949 XML 읽기, OpenDART 응답 다루기)로 양쪽 실행해 비교했다.

| 재본 것 | TypeScript / Node | Python 표준 라이브러리 |
|---|---|---|
| 단일 파일 + 의존성 | PEP 723 대응물 없음 — `npx tsx` → `ERR_MODULE_NOT_FOUND`, 설치 시 `node_modules` 58MB | PEP 723 있음(이 스킬은 의존성 0이라 쓸 일도 없다) |
| 실행 시 타입 검사 | `node --experimental-strip-types`: 0 — `const wrong: number = r.sm` 통과 | 타입힌트 + `mypy --strict`(정적) |
| 정적 검사기 엄격 모드 | `tsc --strict` 3 | `mypy --strict` 3 — 무승부(서로 다른 실수를 잡는다) |
| cp949 디코딩 | `TextDecoder('euc-kr')`: 확장문자 → U+FFFD, 2글자 손실, 예외 없음(`windows-949`·`ks_c_5601-1987` 라벨도 같음) | `cp949` 코덱, 손상 없음 |
| `'71,432'` → 정수 | `Number()` → `NaN`, 조용히 전파 | `int()` → `ValueError`, 멈춤 |
| 웜 실행(무의존 구현) | **1.51s** | 1.84s |
| ZIP + cp949 XML 파싱 | ZIP 리더·XML 파서·cp949 셋 다 외부 패키지 필요 | 표준 라이브러리 24줄, 0.087s |
| 파싱 시간(픽스처 3건) | — | 10~15ms, 3/3 성공 |

줄 수는 세 구현(의존성 있는 TS·무의존 TS·Python) 40·40·38로 동률 수준이다. **속도·간결함에서 TS는 지지 않는다.** 결론을 가른 건 "조용히 틀리는" 칸 둘(cp949, NaN)과 단일 파일 유지다. 런타임 실측: node v22.17.0, npm 10.9.2, `bun`·`deno`·`pnpm`·`tsc` 전역 없음, `npx` 콜드 실행이 이 환경에서 240초 타임아웃 2/2.

## 2. 소스별 robots·약관 판정 (#20)

**규칙**: 직접 접근(스크립트·curl·WebFetch로 그 서버를 부르는 것)은 robots 허용 **그리고** 약관 무금지를 둘 다 읽어 확인한 곳만. robots 허용 ≠ 약관 허용 — 4곳 중 2곳이 갈렸다.

| 소스 | robots | 약관 | 판정 | 근거 |
|---|---|---|---|---|
| OpenDART API | 공식 API | 제10조 허용량 내, 제11조 무료 | A 직접 | ② |
| DART 공시검색 `detailSearch.ax` | 미언급 = 허용 | 사이트 약관 없음, 금감원 저작권정책 "비영리 개인 이용 자유" | A 직접(키 없을 때 유무 판별) | ② |
| GitHub REST API | 공식 API | — | A 직접(무키 60건/시, search 10건/분) | ② |
| 회사 홈페이지 | 그 도메인 robots 확인 후 | — | A 1회 fetch | ① |
| 원티드·점핏 API | robots.txt 자체가 CloudFront 403 → 확인 불가 | — | 직접 호출 안 함 | ① |
| KIND(krx) | robots.txt가 WAF 차단 페이지 → 확인 불가 | 법적고지에 재배포 금지만 | 직접 호출 안 함(키 있으면 불필요) | ①② |
| Google News RSS | `Disallow: /` + ClaudeBot·anthropic-ai 명시 차단 | — | 금지 | ① |
| 네이버 뉴스 검색 | `Disallow: /` | — | 금지 | ① |
| 빅카인즈 | `Allow: /` | 제21조(2025-06-01) 자동화 접근·수집 불허, 소프트웨어 개발 목적 이용 금지 | **금지** — robots만 봤으면 통과했을 곳 | ② |
| YouTube | `/@handle` 허용, RSS·검색 차단 | 공개 검색엔진 외 자동화 접근 금지 | **금지** — 같음 | ② |
| 블라인드 | ClaudeBot·anthropic-ai `Disallow: /` | — | 금지 | ① |
| 크레딧잡 | `Disallow: /` | — | 금지 | ① |
| 캐치 | `/Company` 차단 | — | 금지 | ① |
| 잡플래닛 | robots는 회사 페이지 허용이나 Cloudflare 챌린지로 전 페이지 403 | — | 금지(링크만) | ① |
| 혁신의숲 | ClaudeBot 차단(Claude-User만 허용) | — | 링크만(C) | ① |
| KIPRIS | `Disallow: /`; KIPRIS Plus API는 키·조건 미확인 | — | 링크만(C) | ① |
| 사람인 오픈API | — | 신청·승인 필요 | 직접 호출 안 함 | ② |
| THE VC | `Allow: /`, `/api` 차단 | — | 회사 URL 발견이 기계적이지 않아 WebSearch | ① |

DART 공시검색은 브라우저 UA 없이 식별 문자열 `add-company/0.1 (+python-urllib)`로 200·`[총 6건]`을 돌려줬다 ①. 브라우저 UA와 Referer를 둘 다 요구하는 소스(빅카인즈)는 그 요구 자체가 직접 접근에서 빠지는 이유다.

**사업보고서 제출 대상은 상장 여부가 아니다** ①(DART 공시검색 실측): 당근마켓 사업보고서 2건, 비바리퍼블리카 4, 컬리 4, 무신사 2 — 전부 비상장. 우아한형제들·토스뱅크는 감사보고서만. 근거 법령은 자본시장법 159조("증권을 모집·매출한 적 있는 발행인") ②. 공시검색은 법인명 **정확일치**만 받는다('토스'·'(주)카카오'·'Kakao' 0건, 카카오≠카카오뱅크), UTF-8 필수, 기간 10년 초과면 에러 없이 0건 ①. OpenDART `corpCode.xml`에서 '카카오' 정확일치는 2건(상장 `00258801`/035720, 비상장 `00918444`) ①.

## 3. 사업보고서 XML 실측 (#21)

| 재본 것 | 결과 | 근거 |
|---|---|---|
| 인코딩 선언 | utf-8 5/5(2012·2020·2022 사업보고서, 2024 증권신고서, 2026 주요사항보고서) | ① |
| 스키마 세대 | `dart3.xsd`(~2023.03 제출) / `dart4.xsd`(2024.03 제출~). dart4는 TITLE에 `ATOCID`·`ENG` 등 속성만 추가, 태그 신설 0 | ① |
| 미정의 엔티티 `&cr;` | dart3 파일당 518~1,172회 | ① |
| 한글 의사 태그(`<당기>` 등) | 파일당 0~70개 | ① |
| **홑 `&`**(이스케이프 안 된 `F&B`·`M&A`) | dart3 3건 0개, **dart4 카카오 84개**(속성값 안에도) — 첫 라이브에서 파서를 깨뜨린 원인 | ① |
| 전처리 뒤 strict 파싱 | 3줄로 dart3 3/3, 홑 `&` 규칙을 더한 4줄로 4/4 | ① |
| recover 모드 | SECTION-2가 TABLE 아래로 잘못 들어감 → 불채택 | ① |
| 「II. 사업의 내용」 텍스트 첫 매치가 절 머리글인 비율 | 172/294 = 59% (CVC-project/DiscloseAI, 2,570사 실측 주석) | ② |
| 2022 실물의 첫 매치 | `<P>` 안의 참조 문장 | ① |
| `AASSOCNOTE` 앵커 | I·VI·VIII·전문가확인·상세표 하위에 없음 → 식별 키 불가 | ① |
| 직계 자식만 탐색할 때 II 하위 절 | 7개 → 0개(`LIBRARY` 안) — 후손 탐색 필수 | ① |
| 사업보고서 ZIP 구성 | 3파일: `{rcept_no}.xml` 본문 + `_00760`·`_00761` 첨부 감사보고서 (4,204건 실측 자료) | ② |
| 법정 목차 | 별지 제35호(2026-07-28 시행): I 회사의 개요 … II 사업의 내용(하위 1~7, 금융업은 1~5) … VIII 임원 및 직원 등에 관한 사항(하위 2) … XII 상세표. 연구개발활동은 II 하위 6 | ② |
| 목차 개정 | 2021-07-13 개정·07-16 시행 한 번(II 하위 1~7 신설). 이후 목차 불변, dart3→dart4는 목차 변화 없음 | ①② |
| 픽스처 4건 기대값(원문에서 독립 산정) | II 하위 SECTION-2 0 / 0 / 7 / **12**(카카오: 제조서비스업 7 + 금융업 5), VIII 하위 2 / 2 / 2 / 2 | ① |
| 파싱 시간(`xml.etree.ElementTree`) | 10~15ms(dart3), 14MB dart4도 수 초 안 | ① |

II 하위 0은 파서 실패가 아니다 — 2021.7.16 이전 제출분은 II 하위 절이 없고 본문 머리글로만 나뉜다 ②. 기성 라이브러리 소스 확인 ①: `dart-fss` 0.4.17은 `download_document`(원문 API)를 테스트에서만 부르고 절 접근은 `dsaf001/main.do`·`report/viewer.do`(robots 차단 경로) 스크래핑 + 인라인 JS 정규식; `OpenDartReader` 0.3.3은 ZIP의 첫 엔트리를 euc-kr 우선으로 디코드해 통째로 돌려줄 뿐 절 파싱이 없다.

## 4. 지도 단계 "있는지 확인" 실측 (#17·#18)

| 각도 | 확인법 | 실측 | 근거 |
|---|---|---|---|
| 1 공시 문서(키 없음) | DART 공시검색, 법인명 정확일치, A001(사업보고서)·F001(감사보고서) 각각 | 카카오 A001 6건·F001 0 / 우아한형제들 A001 0·F001 3 → "감사보고서만" 판별 | ① |
| 5 채용공고 | 홈페이지 HTML `href`에서 `(career\|recruit\|jobs\|채용)` grep | 3/3(careers.kakao.com, toss.im/career/jobs, career.woowahan.com). 서브도메인 프로빙은 1/3이라 불채택. 카카오 채용 사이트는 JS 셸(WebFetch에 제목만) | ① |
| 7 기술블로그 | 홈페이지 `href`(호스트명에 tech·blog, medium.com) + RSS 경로 프로빙 `/rss.xml` `/feed/` `/feed.xml` `/atom.xml` `/index.xml` `medium.com/feed/<handle>` | 9곳 중 6 성공(toss.tech, techblog.woowahan.com, tech.kakao.com, d2.naver.com, medium.com/daangn, blog.banksalad.com). 실패: LINE·컬리 403, 쏘카 경로 다름. 경로만 매치하는 `/page/service/tech`는 오탐 | ① |
| 9 오픈소스 | `api.github.com/search/users?q=<영문명>+type:org` → `orgs/<login>`의 `blog`가 회사 도메인과 일치하면 확정 | kakao→tech.kakao.com, toss→toss.im. 우아한형제들은 `woowahan` org가 빈 껍데기고 진짜는 `woowabros`→woowahan.com. 한글 검색 0건 | ① |
| 13 IR | `company.json` `ir_url` / `href` `(/ir\|invest)` / `/ir` 프로빙 | 카카오 3/3 | ① |
| 회사명→YouTube 채널 | 테크블로그 HTML의 youtube 링크 | 1/3만(핸들 추측 6개 중 3개 404) → WebSearch | ① |

**지도 단계 시운전**(카카오, 키 없음, 2026-09-06) ①: 19행 전부 판정, 벽시계 약 8분(독립 각도 5라운드 병렬). 요청 curl 13회(DART 2·홈페이지 2·GitHub 2·tech.kakao 6·developers 1)·WebSearch 22회·WebFetch 5회, 403·429 0회, 재시도 0회, 식별 UA만 사용. 19번째 탐색 행이 실제로 새 각도(개발자 플랫폼 문서·공지, developers.kakao.com)를 찾았고 이용약관 페이지가 404라 B 등급으로 붙였다. 시운전에서 고친 것: D1의 HTTP 상태 확인(파이프만 넘기면 403도 '0건'으로 읽힘), R1의 본문 확인(404 본문이 67KB HTML인 곳), R0 robots 판정 블록(연속 User-agent 줄은 한 그룹), 각도 7 호스트명 매치, JS 셸 대체 절차, 상장사의 각도 14 분기, 법인 변동 신호 `주의:` 줄.

## 5. 첫 수정 루프 — dart4 실물에서 파서가 깨진 기록 (#21, ①)

2026-09-06, 키 발급 직후 카카오 사업보고서(2025.12, rcept_no 20260318001423, 14MB, `dart4.xsd`)로 첫 라이브 실행. `dart_fetch.py` 6.3초·요청 9건 성공, `dart_tables.py` 성공, **`dart_extract.py` 종료 3** — `not well-formed (invalid token): line 1456, column 52`.

| 단계 | 한 것 | 결과 |
|---|---|---|
| 픽스처 | 원문 그대로 픽스처 디렉토리에 + README 행 + `expect.json` null 항목 | 테스트 `FAILED (failures=1, errors=3)` — 의도된 붉음 |
| 진단(수정 에이전트) | 1456행 `S.M. F&B Development Japan Inc.` — 이스케이프 안 된 **홑 `&`**. 파일 전체 `&` 84개가 전부 홑 `&`(참조 꼴 0). 속성값 안에도. dart3 픽스처 3건엔 이 패턴이 없었다. 다른 dart4 깨짐(제어문자·잘못된 문자참조·`]]>`·태그 아닌 `<`·소문자 태그) 전수 조사 0 | 원인 한 가지 |
| 수정 | `preprocess()`에 규칙 1줄: 참조 꼴(`&이름;` `&#n;` `&#xh;`)을 시작하지 않는 `&` → `&amp;`. 기존 규칙 뒤에 두어 이중 처리 없음 | strict 파싱 유지, recover 없음 |
| 기대값 | 파서가 아니라 원문 grep/awk로 독립 산정: II `SECTION-1`(3487~9686행) 아래 `SECTION-2` **12**(제조서비스업 1~7 + 금융업 1~5 — 연결에 카카오페이증권·손보), VIII 하위 2, 연구개발 제목 1 | `expect.json` 12 / 2 / true |
| 검증 | `test_extract.py` 통과(3.9·3.12·3.14), 기존 3건 출력 `diff -r` 동일, dart4 실행 종료 0: business.md 1063줄·표 53·원시 태그 0, people-report.md 217줄·표 12 | 통과 |
| 남긴 것 | 홑 `&` 단위 테스트 추가. 앵커는 실제 제목에서 만든다는 주의(카카오는 `## 6. (제조서비스업)주요계약 및 연구개발활동`) | — |

교훈 둘. ① "전처리 3줄로 3/3 통과"는 표본 3의 결론이었고 네 번째 실물이 바로 깨뜨렸다 — 그래서 픽스처가 자산이다. ② 기대값을 파서 출력으로 채웠으면 12가 아니라 7을 기대했을 것이다(2021.7 서식 = 7개라는 선입견). 원문에서 독립적으로 센 것이 맞았다.

**급여 단위**: OpenDART 개발가이드는 `fyer_salary_totamt`·`jan_salary_am`의 단위를 적지 않는다. 같은 보고서 원문 VIII.1 직원 표는 `(단위 : 백만원)` 캡션에 연간급여총액 `277,251`·1인평균 `122`, API는 `277,251,000,000`·`122,000,000` — API가 **원**으로 환산해 준다 ①.

## 6. 뺀 것과 이유

| 뺀 것 | 왜 | 넣을 조건 |
|---|---|---|
| 특정 사이트를 스킬에 고정 | 체크리스트가 되어 거기서 멈춘다(#18). 사이트는 예시로만 ③ | — |
| `dart-fss` | 절 추출을 robots 차단 경로 스크래핑으로 한다 ① | 절 추출이 공식 API 경로로 바뀌면 |
| `OpenDartReader` | 원문을 통째로 돌려줄 뿐 절 파싱이 없다 ① | — |
| 정규식 텍스트 컷 | 첫 매치의 41%가 목차 셀·참조 문장 ② | — |
| recover 모드 파싱 | SECTION-2를 TABLE 아래로 잘못 넣는다 ① | — |
| 각도별 에이전트 18개 | 법인 판별이 에이전트 사이에 공유되지 않는다 ③ | — |
| 각도별 섹션 18개 | 빈칸 18개를 채우라고 부른다(#13) ① | — |
| TypeScript | #1 — 의존성 있으면 단일 파일 깨짐, 런타임 타입검사 0, cp949 손상, NaN 전파 ① | PEP 723 대응물이 생기고 `TextDecoder`의 cp949가 고쳐지면 |
| `uv` / PEP 723 | 의존성이 0이라 필요 없다 ① | 표준 라이브러리 밖 패키지가 필요해지면 |
| 점핏 `techStacks` 직접 호출 | robots.txt가 CloudFront 403이라 확인 불가 ① | robots·약관 둘 다 확인되면 |
| 뉴스 API 키(네이버 등) | WebSearch로 열댓 건이면 충분하다 ③ | — |
| 픽스처를 리포 안에 | 타사 공시 전문 재배포 ② | 구조만 남긴 축약본으로 바꾸면 |

## 출처

- OpenDART 개발가이드 https://opendart.fss.or.kr/guide/main.do · 이용약관 https://opendart.fss.or.kr/intro/terms.do · 인증키 신청 https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do
- 금융감독원 기업공시서식 작성기준(2026-08-03 시행) https://dart.fss.or.kr/dsaa003/selectGuideMain.ax?seqno=448 · 별지서식(2026-07-28 시행) seqno=447 · 2021-07-13 개정 요약
- DART robots.txt https://dart.fss.or.kr/robots.txt · 금융감독원 저작권 정책 https://www.fss.or.kr/fss/main/contents.do?menuNo=200701
- 빅카인즈 이용약관(2025-06-01) 제21조 · YouTube 서비스 약관(2022-01-05) https://www.youtube.com/t/terms?hl=ko&gl=KR · KRX 법적고지 http://info.krx.co.kr/contents/KRX/06/06070200/KRX06070200.jsp
- 자본시장과 금융투자업에 관한 법률 제159조
- CVC-project/DiscloseAI `sectioner.py`(2,570사 실측 주석) · dart-fss 0.4.17 · OpenDartReader 0.3.3 · GongZen/disclosure-agent `docs/DATASET.md`(ZIP 구성 4,204건)
