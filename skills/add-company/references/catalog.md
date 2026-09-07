# 자료 카탈로그 — 18각도 × 5묶음

회사 하나를 조사할 때 볼 **각도(자료 유형)의 목록**이다. 각 행의 사이트 이름은 예시일 뿐 각도의 정의가 아니다 — "채용공고 전체"라는 각도가 있고, 회사 채용 페이지·채용 플랫폼은 그 예시다. **표는 바닥이지 천장이 아니다**(불변 원칙 4): 18각도를 전부 점검한 뒤 #7의 탐색 단계로 이 회사에만 있는 자료를 한 번 더 찾고, 새 유형은 이 파일에 추가한다. 지도 에이전트는 #1 → #2~#6의 "확인 절차" 열 → #9 형식으로 반환하고, 묶음 에이전트는 자기 묶음 표의 행만 읽고 #10 형식으로 반환한다.

## 0. 읽는 법

**접근 등급** — 그 서버를 스크립트·curl·WebFetch로 직접 부를 수 있는지의 등급.
- **A** 직접 접근 가능. 공식 API이거나, robots.txt(사이트가 자동 접근 허용 범위를 적어 둔 파일)가 그 경로를 허용하고 **그리고** 이용약관에 자동화 접근 금지 조항이 없음을 실제로 읽어 확인한 곳. 확정 목록은 #8 첫 단락.
- **B** WebSearch(검색 도구)가 돌려준 결과와, 그 결과의 링크·사용자가 준 URL을 WebFetch(주소 하나를 읽어 오는 도구)로 읽은 것까지 — 각도당 깊이 한도(아래, 기본 5건) 안에서, 한 주소에 한 번. 스크립트·curl로 그 서버를 부르거나 페이지를 따라 기어 들어가지 않는다.
- **C** 링크만 제시하고 내용은 사람이 본다. #8 금지 목록의 소스는 WebFetch도 하지 않는다 — WebSearch 스니펫과 링크뿐이다.

공통 규칙: 호스트당 요청 사이에 간격을 두고, 403·429가 오면 그 호스트는 즉시 중단하며, 실패한 요청은 재시도하지 않는다.

**깊이 기본값** — 각도당 대표 자료 최대 5건, 최근 2년 우선. 예외는 5번 채용공고만 **전체**(스택 분포 계산에 필요).

**표 읽는 법** — 열은 `# | 각도 | 답하는 질문 | 어디에(예시) | 있는지 확인하는 절차 | 등급 | 주의`. "확인 절차"가 지도 에이전트의 실행 문장이다. 절차 안의 `D1`·`D2`·`R0`·`H1`·`H2`·`R1`·`G1`·`G2` 표지는 표 아래 명령 블록의 주석 표지다. 사실 뒤의 ①②③은 근거 등급 — ① 실행으로 확인 ② 출처(공식 문서·약관) ③ 감(미확인).

## 1. 법인명 확정 (절차 0)

입력은 브랜드명일 수 있고, 브랜드명 ≠ 법인명이다 — 토스→비바리퍼블리카, 배민→우아한형제들. 공시 검색·뉴스 필터·GitHub 판별의 기준이 전부 법인명이라 이것을 먼저 못 박는다. 세 경로를 순서대로 밟는다.

1. **키가 있으면** `D2`(`dart_fetch.py <이름> --check`) 한 번으로 끝난다 — 스크립트가 키를 스스로 읽고(`.env`), `corpCode.xml`(캐시 7일)에서 `corp_name` 정확일치로 확정한 뒤 사업보고서(A001)·감사보고서(F001) 건수를 한 줄로 돌려준다. 여럿이거나 0건이면 부분일치 후보 최대 10개를 stderr에 찍고 종료 4 → 아래 "확정 못 하면". **키는 셸 명령에 등장하지 않는다** — 이 환경은 `.env`를 읽는 셸 명령을 권한 규칙으로 거부하므로 curl에 `$DART_API_KEY`를 넣는 방식은 쓰지 않는다.
2. **상장사면** KIND(거래소 상장법인 검색)는 쓰지 않는다 — robots.txt가 WAF 차단 페이지라 허용 여부를 확인할 수 없다(#8). 대신 1의 corp_code로 OpenDART `company.json`을 받아 `corp_name`·`corp_name_eng`·`stock_code`·`ceo_nm`·`hm_url`·`ir_url`을 확보한다 — 각도 4·9·11·13이 이 값을 쓴다.
3. **키가 없으면** WebSearch "<브랜드명> 법인명" / "<브랜드명> 운영사"로 후보 법인명을 얻고, 후보마다 `D1`(#2 명령 블록)로 정확일치를 확인한다. 0건이면 표기를 바꿔 다시 — '(주)'·'주식회사' 제거, 띄어쓰기 제거. '토스'·'(주)카카오'·'Kakao'는 전부 0건이고 카카오≠카카오뱅크다 ①.

**확정 못 하면** 후보 목록(법인명, 있으면 corp_code·stock_code)을 사용자에게 보여 주고 고르게 한다. 지어내서 진행하지 않는다. 실제로 일어난다 — `'카카오'`는 corpCode에 **정확일치가 2건**(상장 `00258801`/035720, 비상장 `00918444`)이라 `--check`가 종료 4를 냈다 ①; 상장사를 찾는 상황이면 `stock_code`가 있는 쪽이다. 표기 주의: corpCode의 `corp_name`은 `카카오`, `company.json`의 `corp_name`은 `(주)카카오` ① — **검색·필터·D1의 기준은 corpCode 표기**, 파일 `title`에는 company.json 표기를 쓴다.
확정 결과로 넘기는 것: 법인명 · 브랜드명(없으면 `~`) · corp_code(`~` 가능) · stock_code(`~` 가능) · 영문명(`~` 가능) · 홈페이지 URL(`~` 가능). 해외 법인이면 각도 1~3은 `없음`, 사유 "한국 법인 아님(DART 해당 없음)".

## 2. 묶음 ① DART (등급 A — OpenDART 공식 API, 키 필요)

키가 없으면 `D1`로 유무만 확인할 수 있다. 본문 수집(`dart_fetch.py`)은 종료 5(키 없음, 발급 https://opendart.fss.or.kr) → 이 묶음은 `실패`로 보고한다. 필드명은 개발가이드 https://opendart.fss.or.kr/guide/main.do 에서 재확인한다.

| # | 각도 | 답하는 질문 | 어디에(예시) | 있는지 확인하는 절차 | 등급 | 주의 |
|---|---|---|---|---|---|---|
| 1 | 공시 문서 | 무슨 사업을 어떻게 하나 — 「II. 사업의 내용」 하위 1~7(1 개요 / 2 주요 제품·서비스 / 3 원재료·생산설비 / 4 매출·수주 / 5 위험관리·파생거래 / **6 주요계약 및 연구개발활동** / 7 기타), 부문별 매출 | OpenDART `list.json`→`document.xml`; 키 없으면 DART 공시검색 | 키 있으면 `D2`(`--check`)의 `A001=<n>`이 1 이상이면 있음(종료 0), 0이면 종료 2 — `F001>0`이면 "감사보고서만"→없음. 키 없으면 `D1`을 A001·F001 각각 돌려 `[총 N건]`을 읽는다: A001>0 있음 / A001=0·F001>0 "감사보고서만"→없음 | A | 법인명 **정확일치**·UTF-8 필수·기간 10년 이내(넘으면 에러 없이 0건) ①. 감사보고서만 내는 회사(우아한형제들·토스뱅크)는 없음. 비상장도 증권 모집·매출 이력이 있으면 제출(당근마켓·비바리퍼블리카·컬리·무신사 ①). **금융업 서식은 하위 5개, 연구개발 항목 없음** ②. 연결에 금융 자회사가 있으면 둘이 나란히 나온다 — 카카오 FY2025는 `(제조서비스업)` 7 + `(금융업)` 5 = II 하위 12 ① |
| 2 | 직원 현황 | 어느 부문이 얼마나 크고 커지나 — 부문별 정규직/계약직/합계, 평균 근속, 1인 평균급여, 최근 5개 사업연도 | OpenDART `empSttus.json` | 1이 있음이면 `empSttus.json?crtfc_key=&corp_code=&bsns_year=YYYY&reprt_code=11011`, 최신 연도 `status` 000이면 있음 / 013이면 그 연도 없음(한 해 전 시도) | A | 필드 `fo_bbm`(부문) `sexdstn`(성별) `rgllbr_co`(정규직) `cnttk_co`(계약직) `sm`(합계) `avrg_cnwk_sdytrn`(평균근속) `fyer_salary_totamt`(급여총액) `jan_salary_am`(1인평균) — 콤마 든 문자열, `-` 가능 ①. 2015년 이후만 |
| 3 | 임원·리더십 | 누가 이끄나 — 임원 명단·담당·주요 경력(CTO 배경) | OpenDART `exctvSttus.json` (+ 인터뷰·링크드인) | 1이 있음이면 `exctvSttus.json` 같은 파라미터, `status` 000이면 있음 | A | 필드는 가이드 재확인(`nm, ofcps, chrg_job, main_career` 등으로 기억 ③). 인터뷰·링크드인은 C → 각도 11로 |

```bash
UA="add-company/0.1 (+python-urllib)"   # 요청자 식별 문자열. 브라우저로 위장하지 않는다 — 이 UA로 DART 검색이 200·[총 6건] 응답함 ①
WORK=<지도 에이전트 작업 디렉토리>   # 메인이 미리 만든다. 임시물(응답 본문·HTML)은 전부 여기
NM="<법인명>"; ENC=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$NM")     # UTF-8 percent-encoding 필수(EUC-KR이면 0건)
# D1 정기공시 유무, 키 없음. finalReport=recent = 정정 반영 최종본만. 응답은 HTML 조각, [총 N건]으로 건수 ①
#    본문을 저장하고 HTTP 상태를 본다 — 파이프로만 넘기면 403·500도 '0건'으로 읽힌다(시운전 ①)
for T in A001 F001; do
  CODE=$(curl -sS -A "$UA" -o "$WORK/d1-$T.html" -w '%{http_code}' -X POST "https://dart.fss.or.kr/dsab007/detailSearch.ax" \
    --data "textCrpNm=${ENC}&publicType=${T}&startDate=$(date -d '-3 years' +%Y%m%d)&endDate=$(date +%Y%m%d)&maxResults=50&finalReport=recent")
  [ "$CODE" = 200 ] || { echo "$T HTTP $CODE — 실패(사유에 기록)"; continue; }
  python3 -c "import re,sys,html;t=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',open(sys.argv[1],encoding='utf-8').read())));print(sys.argv[2],(re.search(r'\[총 \d+건\]',t) or ['0건'])[0])" "$WORK/d1-$T.html" "$T"
done
# D2 키 있음(스크립트가 .env 에서 스스로 읽음 — 키를 셸에 노출하지 않는다). 다운로드·저장 없음, list.json 2회(A001·F001, 최근 3년)
#    stdout: corp_code=… corp_name=… stock_code=…|~ A001=<n> F001=<m> latest_A001=<rcept_no>|~ latest_A001_rcept_dt=… report_nm=<끝까지 한 값>
#    종료 0 = A001≥1 / 2 = A001 0건 / 4 법인명 미확정(후보 stderr) / 5 키 없음 / 6 API 오류 / 7 네트워크
python3 <스킬>/scripts/dart_fetch.py "<법인명 또는 corp_code>" --check
```

## 3. 묶음 ② 회사 발신 (등급: 홈페이지 1회 fetch·RSS 프로빙·GitHub API는 A, 나머지 B)

RSS(글 목록을 기계가 읽게 내보내는 피드)를 프로빙하기 전에 그 블로그 도메인의 robots를 `R0`로 먼저 본다. 홈페이지 1회 fetch도 `R0`로 `/` 허용을 본 뒤에.

| # | 각도 | 답하는 질문 | 어디에(예시) | 있는지 확인하는 절차 | 등급 | 주의 |
|---|---|---|---|---|---|---|
| 4 | 회사 자체 소개 | 무엇을 팔고 스스로 어떻게 말하나 — 제품·서비스 라인업, 보도자료, 회사 소개 | 회사 홈페이지 | URL은 `company.json`의 `hm_url`(키) 또는 WebSearch "<법인명> 공식 홈페이지". 그 도메인 `/robots.txt`를 읽고 `H1`로 HTML을 **1회** 받아 둔다 — 5·7·13의 링크는 이 파일에서 찾는다 | A(1회 fetch) | 거의 항상 있음. 두 번 받지 않는다 |
| 5 | 채용공고 **전체** | 지금 어떤 사람을 얼마나 뽑나 — 여는 포지션 전부의 직무·요구 스택 분포 | 회사 채용 페이지 · 채용 플랫폼(원티드·점핏·사람인·잡코리아) | 4의 HTML에서 `H2` — href에 `(career\|recruit\|jobs\|채용)` grep, 3/3 성공 ①(careers.kakao.com / toss.im/career/jobs / career.woowahan.com). 없으면 WebSearch "<법인명> 채용". 플랫폼 공고는 WebSearch 결과로만 | A(링크 발견)→B | 서브도메인 프로빙은 1/3이라 쓰지 않는다 ①. 플랫폼 직접 호출 금지(#8). 사용자가 준 공고 URL은 WebFetch. **이 각도만 전체 수집**. H2는 채용 사이트 루트만 주므로 목록 URL은 루트 WebFetch 1건 또는 `site:<채용도메인>` WebSearch로 확정. 채용 사이트가 JS 셸이면(WebFetch에 제목만, 카카오 실측 ①) 목록은 `site:` 검색으로 보완하고, 관계사 공고가 같은 목록에 섞이면(카카오 S-xxxx ①) 묶음 ②에서 법인명으로 걸러라. **JS 셸이면 그 도메인 robots.txt의 `Sitemap:` 줄을 먼저 본다** — 에이피알은 사이트맵에 job_posting URL 72건이 있어 목록 전체를 얻었고 각 페이지는 `__NEXT_DATA__`에 직군·경력·고용·마감 필드를 담고 있었다(2026-09-06 ①). robots `*` 허용 경로만, 식별 UA, 1.5초 간격 |
| 6 | 채용 브랜딩 | 어떤 사람을 원한다고 말하나 — 인재상·조직문화·팀 소개·복지 | 5의 채용 사이트 안 | 5에서 찾은 채용 사이트를 WebFetch해 인재상·문화·팀·복지 페이지 링크가 있으면 있음 | B | 채용 사이트가 없으면 4의 회사 소개 페이지로 대체. WebFetch가 JS 셸이면 `site:<채용도메인> 인재상 OR 문화 OR 팀` WebSearch로 보완 — `없음` 판정은 그 뒤에 ① |
| 7 | 기술블로그 | 실제 스택, 푸는 문제, 엔지니어링 문화 | 자체 테크블로그 · Medium (toss.tech, techblog.woowahan.com, tech.kakao.com, d2.naver.com, medium.com/daangn, blog.banksalad.com) | 4의 HTML href 중 **호스트명**에 `tech`·`blog`가 들거나 `medium.com`인 링크(경로만 맞는 `/page/service/tech` 같은 제품 페이지는 오탐 ①) → 없으면 각도 9의 GitHub org `blog` 필드(kakao→tech.kakao.com ①) → `R0`로 그 도메인 robots 확인 → `R1` RSS 경로 프로빙 `/rss.xml, /feed/, /feed.xml, /atom.xml, /index.xml`, Medium이면 `medium.com/feed/<handle>` — 9곳 중 6 성공 ①. 못 찾으면 WebSearch "<법인명> 기술 블로그" 보완 | A(RSS 1회)→B | 실패 사례 LINE·컬리 403, 쏘카는 경로가 다름 ① → 블로그 URL만 적고 `수동` |
| 8 | 컨퍼런스 발표 | 공개적으로 자랑하는 기술 문제 | 자체·업계 컨퍼런스(if kakao, SLASH, 우아콘, DEVIEW, NDC) | WebSearch "<법인명 또는 브랜드> 컨퍼런스 발표" — 발표 목록 페이지 링크가 나오면 있음 | B | **YouTube 페이지 직접 fetch 금지**(약관 ②, #8). 회사→컨퍼런스 URL은 연도 패턴·JS 렌더라 프로빙하지 않고 WebSearch |
| 9 | 오픈소스 | 무엇을 공개하고 어떤 언어를 쓰나 — GitHub 조직의 리포·언어·활동 | GitHub 조직 | `G1` `search/users?q=<영문명>+type:org` → 후보마다 `G2` `orgs/<login>`의 `blog`가 회사 도메인과 일치하면 확정 ①(kakao→tech.kakao.com, toss→toss.im, woowabros→woowahan.com) | A | 영문명 필수 — 한글 검색은 0건 ①(`corp_name_eng` 또는 홈페이지에서). 동명 org 주의: `woowahan`은 빈 껍데기, 진짜는 `woowabros` ①. 무키 한도 core 60건/시·search 10건/분 |

```bash
# R0 robots 확인 — 그 호스트의 robots.txt에서 ClaudeBot → anthropic-ai → * 순으로 첫 번째 있는 블록을 적용해 경로별 허용/차단을 찍는다. 전부 '허용'이어야 다음으로 ①
curl -sS -A "$UA" "https://<host>/robots.txt" -o "$WORK/robots-<host>.txt"
python3 - "$WORK/robots-<host>.txt" / /rss.xml /feed/ /feed.xml /atom.xml /index.xml <<'PY'
import sys
txt = open(sys.argv[1], encoding='utf-8', errors='replace').read(); paths = sys.argv[2:]
blocks, group, in_rules = {}, [], False          # 연속된 User-agent 줄은 한 그룹 — 규칙이 그룹 전체에 적용된다
for line in txt.splitlines():
    line = line.split('#')[0].strip()
    if not line: continue
    k, _, v = line.partition(':'); k, v = k.strip().lower(), v.strip()
    if k == 'user-agent':
        if in_rules: group, in_rules = [], False
        group.append(v.lower()); blocks.setdefault(v.lower(), [])
    elif k in ('disallow', 'allow') and group:
        in_rules = True
        for ua in group: blocks[ua].append((k, v))
for ua in ('claudebot', 'anthropic-ai', '*'):
    if ua not in blocks: continue
    for p in paths:
        dis = [v for k, v in blocks[ua] if k == 'disallow' and v and p.startswith(v)]
        alw = [v for k, v in blocks[ua] if k == 'allow' and v and p.startswith(v)]
        print(ua, p, '차단' if dis and (not alw or max(map(len, dis)) > max(map(len, alw))) else '허용')
    break
else:
    print('robots 블록 없음 → 허용(파일 없음/비어 있음)')
PY
# H1 홈페이지 1회 fetch(R0로 / 허용 확인 후). -L 로 리다이렉트를 따르니 링크 열에는 마지막 줄의 최종 URL을 적는다 → H2 채용 링크 grep ①
curl -sS -L -A "$UA" "https://<홈페이지>/" -o "$WORK/homepage.html" -w '%{url_effective}\n'
grep -o -i -E 'href="[^"]*(career|recruit|jobs|채용)[^"]*"' "$WORK/homepage.html" | sort -u
# R1 RSS 프로빙 — 경로당 1회, 2초 간격. 200이고 본문 앞부분에 <rss 또는 <feed 가 있어야 RSS다(404 본문이 67KB HTML인 곳도 있다 ①)
for p in /rss.xml /feed/ /feed.xml /atom.xml /index.xml; do
  CODE=$(curl -sS -L -A "$UA" -o "$WORK/r1.tmp" -w '%{http_code}' "https://<블로그>$p"); sleep 2
  if [ "$CODE" = 200 ] && head -c 400 "$WORK/r1.tmp" | grep -qE '<(rss|feed)'; then echo "$p RSS 있음"; else echo "$p $CODE"; fi
done
# G1 GitHub org 후보 → G2 blog 필드로 동명 org 판별 ①(공식 API, 무키 60건/시)
curl -sS -A "$UA" "https://api.github.com/search/users?q=<영문명>+type:org&per_page=5" | python3 -c "import json,sys;print([i['login'] for i in json.load(sys.stdin)['items']])"
curl -sS -A "$UA" "https://api.github.com/orgs/<login>" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('name'),d.get('blog'),d.get('public_repos'))"
```

## 4. 묶음 ③ 외부 시선 (등급 B)

| # | 각도 | 답하는 질문 | 어디에(예시) | 있는지 확인하는 절차 | 등급 | 주의 |
|---|---|---|---|---|---|---|
| 10 | 뉴스 | 최근 1~2년 신사업·투자·조직 변화 | 언론 기사 | WebSearch "<법인명> 신사업 / 투자 / 조직" 최근 2년, 관련 기사가 있으면 있음 | B | Google News RSS·빅카인즈·네이버 뉴스 검색 **직접 호출 금지** ②(#8) |
| 11 | 외부 인터뷰·발표 | 대표·CTO가 말하는 "왜 이 사업을 하나", 우선순위 | 언론 인터뷰 · 키노트 | WebSearch "<법인명> <대표명(`ceo_nm`)> 인터뷰" · "<법인명> CTO 인터뷰 / 키노트" | B | **그룹사 이름 겹침 주의** ①: "토스 CTO 인터뷰"→토스랩·토스증권·토스페이먼츠, "카카오 인터뷰"→카카오페이손보·카카오게임즈. 본문의 법인명으로 걸러라 |
| 12 | 개발자 인터뷰·팟캐스트 | 팀이 일하는 방식, 채용 철학 | 개발자 인터뷰 기사 · 팟캐스트 | WebSearch "<법인명> 개발자 인터뷰 / 팟캐스트" | B | 팟캐스트 검색 API는 전부 미확인/차단 → WebSearch만 |

## 5. 묶음 ④ 시장·기술 (등급: IR 링크 발견만 A, 나머지 B/C)

| # | 각도 | 답하는 질문 | 어디에(예시) | 있는지 확인하는 절차 | 등급 | 주의 |
|---|---|---|---|---|---|---|
| 13 | IR 자료 | 경영진이 숫자로 강조하는 방향 — 실적발표 자료 | 회사 IR 페이지 | `company.json`의 `ir_url`(키) → 4의 HTML href `(/ir\|invest)` grep → `https://<홈페이지>/ir` 프로빙(302 포함) — 카카오 3/3 ① | A(링크 발견)→B | 비상장은 대개 없음 → `없음`. 사이트맵에는 /ir이 없었다 ① |
| 14 | 투자 이력 | 누가 얼마에 걸었나 — 라운드·투자자·밸류(비상장에 특히) | THE VC · 혁신의숲 · 기사 | `stock_code`가 있으면(상장사) 라운드 자료가 없는 게 정상 — 기업정보 페이지(THE VC 등) 링크로 `수동`, 없으면 `없음`(사유 "상장사"). 비상장이면 WebSearch "<법인명> 투자 유치 / 시리즈" — 라운드가 언급된 결과가 있으면 있음 ① | B/C | THE VC는 robots 허용이나 회사 URL 발견이 기계적이지 않음 ①; 혁신의숲은 ClaudeBot 차단 ① → 둘 다 링크만(C) |
| 15 | 특허 | 어디에 기술을 걸었나 — 출원 분야 | KIPRIS · 기사 | WebSearch "<법인명> 특허 출원" | C | KIPRIS는 robots `Disallow: /` ①, KIPRIS Plus API는 키·조건 미확인 → 링크만. 사용자가 브라우저 자동화를 허용한 경우 검색식은 `AP=["주식회사 <법인명>"]` — 따옴표 없으면 토큰 일치로 무관 출원인이 섞인다(에이피알 95 vs 108 vs 161건 ①). 결과는 90건/페이지로 넘기며 IPC·행정상태를 직접 센다(분류통계 버튼은 본문에 표를 안 그림 ①) |
| 16 | 제품 직접 사용 | 실제로 뭘 만드나 — 앱·웹, 스토어 리뷰 | 앱스토어 · 서비스 웹 | B2C면 WebSearch "<브랜드> 앱"으로 스토어 링크 확보 → `수동`. B2B면 데모·문서 페이지 링크 | C | 사람이 써 보는 각도. 리뷰 요약은 스토어 페이지 링크와 함께 |
| 19 | 규제 인허가·등록 현황 | 어떤 제품이 규제 대상이고 허가를 받았나 — 의료기기 제조업·품목 허가(인허가 업종에만 해당) | 식약처 의료기기전자민원창구 "업체/제품정보 공개" (https://emedi.mfds.go.kr/search/data/MNU20237) · 공공데이터포털 "의료기기 품목허가 정보" API | WebSearch "<법인명> 의료기기 허가 식약처"로 인허가 보도 유무를 보고, 조회 페이지 URL을 링크로 제시해 `수동`으로 둔다 | C(브라우저 자동화가 있으면 A) | emedi.mfds.go.kr는 robots.txt 없음(/robots.txt 302→/error?p=404 ①)·이용약관에 자동화 금지 조항 없음(② WebFetch 요약)이라 접근은 허용이나 검색 페이지가 JS 셸이라 curl·WebFetch로는 조회 불가 ①. 헤드리스 브라우저로는 품목검색 탭 `#entpName`·업체검색 탭 `#entpName2`에 업체명을 넣고 같은 탭의 `input[value="검색"]`을 누르면 표가 나온다(에이피알 2026-09-06 ①). data.go.kr API(15057456·15057971)는 키 필요·약관 미확인 ③. 2026-09-06 에이피알 조사에서 추가 |

## 6. 묶음 ⑤ 평판·프로세스 (등급 B/C)

| # | 각도 | 답하는 질문 | 어디에(예시) | 있는지 확인하는 절차 | 등급 | 주의 |
|---|---|---|---|---|---|---|
| 17 | 평판·후기 | 안에서는 어떻게 보나 — 재직자 평, 연봉 분포 | 잡플래닛 · 블라인드 · 크레딧잡 · 캐치 | WebSearch "<법인명> 잡플래닛 / 블라인드 / 연봉" 스니펫으로 유무 확인, 링크 제시 | C | 잡플래닛 Cloudflare 챌린지로 전 페이지 403 ①, 블라인드 ClaudeBot·anthropic-ai `Disallow: /` ①, 크레딧잡 `Disallow: /` ①, 캐치 `/Company` 차단 ① → 전부 C |
| 18 | 채용 프로세스 | 어떻게 뽑나 — 코딩테스트·과제·면접 구조 후기 | 블로그 후기 · 커뮤니티 | WebSearch "<법인명> 코딩테스트 / 면접 후기 / 채용 과정" | B | 6의 채용 사이트에 절차 안내가 있으면 그것이 1차 출처 |

## 7. 19번째 행 — 탐색 단계와 성장 규칙

18각도를 다 점검한 뒤 "이 업종·회사에만 있는 자료"를 **한 번** 찾는다. 지도 에이전트는 결과를 19번째 행으로 반환한다(#9). 업종별 출발점:

| 업종·상황 | 자료 유형 | 예시 |
|---|---|---|
| 금융사 | 감독기관 경영공시 | 금감원 경영공시 |
| 게임사 | 플랫폼 이용 통계 | 스팀 통계 |
| 개발자 행사를 여는 회사 | 자체 컨퍼런스·해커톤 아카이브 | 발표 자료 사이트 |
| 인허가 업종 | 규제 인허가·등록 현황 | 주무부처 공시 |

새 소스를 찾았으면 이 파일에 각도로 추가한다:
1. `curl -sS https://<host>/robots.txt`에서 `User-agent: *`·`ClaudeBot`·`anthropic-ai` 블록의 `Disallow`를 읽는다. 그 다음 사이트의 이용약관을 찾아 자동화·크롤링·로봇 금지 조항을 읽는다. **둘 다** 통과해야 A, 아니면 B 또는 C. 약관 페이지를 못 찾으면(404 등, developers.kakao.com 실측 ①) A는 불가다.
2. 각도 이름은 자료 유형으로 짓고(사이트 이름 금지), 사이트는 "어디에(예시)" 열에 적는다.
3. 가장 가까운 묶음 표의 마지막 행에 번호 19부터 이어 붙인다. 어디에도 안 맞으면 묶음 ④ 시장·기술. 확인 절차는 명령형 한 문장, 주의 열에 등급 근거(①②③)와 확인 날짜를 적는다.
4. 접근 금지 판정이 나면 #8 표에도 한 줄 넣는다.

## 8. 직접 접근 금지 목록

**규칙**: 직접 접근(스크립트·curl·WebFetch로 그 서버를 부르는 것)은 등급 A만. **robots 허용 ≠ 약관 허용** — 확인한 4곳 중 2곳(빅카인즈·YouTube)이 robots는 허용인데 약관이 금지였다 ②. 등급 A 확정 소스: OpenDART API(약관 제10조 허용량 내, 제11조 무료 ②) · DART `detailSearch.ax`(robots 미언급=허용, 사이트 약관 없음, 금감원 저작권정책 "비영리 개인 이용 자유" ②) · GitHub REST API(공식) · 회사 홈페이지 1회 fetch(그 도메인 robots 확인 후).

아래 소스는 WebSearch 결과와 링크만 쓴다. WebFetch도 하지 않는다.

| 소스 | 이유 | 대신 |
|---|---|---|
| Google News RSS | robots `Disallow: /` + ClaudeBot 명시 차단 ② | WebSearch(각도 10) |
| 네이버 뉴스 검색 | robots `Disallow: /` ② | WebSearch(10) |
| 빅카인즈 | robots는 `Allow: /`이지만 이용약관 제21조가 자동화 수집 금지 ② | WebSearch(10) |
| YouTube | robots는 `/@handle` 허용이지만 약관이 "robots.txt에 따른 공개 검색엔진 외 자동화 수단 접근 금지" ② | WebSearch로 발표 목록(8), 링크 제시 |
| 원티드·점핏 API | robots.txt 자체가 CloudFront 403 → 허용 여부 확인 불가 ① | WebSearch 결과(5) |
| 사람인 오픈API | 승인 필요 ② | WebSearch 결과(5) |
| 잡코리아 | robots·약관 미확인 ③ — 확인 전까지 금지 | WebSearch 결과(5) |
| KIND(krx) | robots.txt가 WAF 차단 페이지 → 확인 불가 ①. 키가 있으면 필요 없다(`corpCode.xml`·`company.json`이 대체) | #1 경로 1·2 |
| 잡플래닛 | Cloudflare 챌린지, 전 페이지 403 ① | 링크(17) |
| 블라인드 | ClaudeBot·anthropic-ai `Disallow: /` ① | 링크(17) |
| 크레딧잡 | `Disallow: /` ① | 링크(17) |
| 캐치 | `/Company` 경로 차단 ① | 링크(17) |
| 혁신의숲 | ClaudeBot 차단 ① | 링크(14) |
| KIPRIS | `Disallow: /` ①; KIPRIS Plus API는 키·조건 미확인 | 링크(15) |
| 팟캐스트 검색 API | 전부 미확인 또는 차단 | WebSearch(12) |
| image.ninehire.com (나인하이어 채용 사이트 이미지 CDN) | robots `Disallow: /`(예외 `/homepage/`) ① 2026-09-06. 에이피알 조사에서 robots 판정 전에 1회 받아 버린 실수가 있었다 — 공고 이미지는 배너뿐이었다 | 공고 본문 텍스트(5); 이미지는 링크만 |

## 9. 지도 에이전트 반환 형식

각도마다 한 줄, 18행 + 19번째 탐색 행, 번호순. 열 구분은 `|`. 의존(4→5·7·13, R0→R1)만 지키면 독립 각도는 병렬로 확인해도 된다.

    번호 | 각도 | 상태 | 링크 또는 사유

상태 어휘는 네 개뿐이다. 각도 안에 자료 유형이 둘(12 인터뷰/팟캐스트)이면 하나만 있어도 `있음`으로 두고 링크 열 괄호에 없는 쪽을 적는다. **법인 변동 신호**(분할·합병·사명 변경 결의 — 법인명·corp_code의 유효기간이 걸린다)가 보이면 표 **아래** `주의:` 한 줄로 적는다; 메인이 `open_questions`로 옮긴다.
- **있음** — 자료 URL을 확보했다. 링크 열에 URL(여럿이면 대표 1~5건, 채용공고는 목록 페이지 URL).
- **없음** — 확인 절차를 끝까지 밟았는데 없다. 그 자체가 정보다("감사보고서만 제출", "비상장이라 IR 없음"). 사유 열에 밟은 절차를 적는다.
- **수동** — 자료는 있는데 등급 C라 사람이 봐야 한다. 링크 열에 URL 필수.
- **실패** — 확인 절차가 기술적으로 실패했다(파서 종료 2·3, 네트워크 오류, 403·429, API 상태코드 020 등). 사유 열에 원인 필수. `없음`과 섞지 않는다.

예:
`1 | 공시 문서 | 있음 | https://dart.fss.or.kr/... (A001 3건, 최신 사업보고서 (2025.12))`
`13 | IR 자료 | 없음 | ir_url 빈값, href에 /ir 없음, /ir 프로빙 404`
`17 | 평판·후기 | 수동 | https://www.jobplanet.co.kr/companies/...`
`7 | 기술블로그 | 실패 | RSS 5경로 전부 403 (robots는 허용)`
`19 | 탐색: <자료 유형> | 있음 또는 없음 | 링크, 또는 "업종 특유 자료 없음"`

## 10. 묶음 에이전트 반환 형식

묶음 에이전트는 자기 묶음의 `있음`·`수동` 행만 받아 자료를 읽고 **사실만** 돌려준다. 해석·판정·교차점은 메인의 일이다. 반환문은 편집 없이 `artifacts/findings/findings-<묶음>.md`로 저장되므로 아래 형식을 그대로 지킨다.

    # findings-<묶음> <법인명> <조사일 YYYY-MM-DD>     ← <묶음>은 dart·company·external·market·reputation (①~⑤ 순)
    ## 발견
    - [각도 N] <사실 한 문장>. — 출처: <URL 또는 artifacts/… 경로>
    ## 못 찾은 것
    - [각도 N] <무엇을> — <어디서 찾았고 왜 없었는지, 되찾을 경로>

규칙:
- 한 항목 = 사실 한 문장 + 출처 하나 + 각도 번호. 출처 없는 문장은 쓰지 않고 "못 찾은 것"으로 보낸다.
- 숫자·날짜는 출처 표기 그대로(단위 포함) 옮긴다. 계산해 새 숫자를 만들지 않는다.
- 깊이는 #0의 기본값을 따른다. 전체를 세는 5번 채용공고만, 센 값을 "공고 N건 중 Kotlin 요구 M건"처럼 모집단과 함께 쓰고 목록 URL을 출처로 단다.
- **법인명으로 걸러라.** 그룹사 이름이 겹친다 — "토스 CTO"가 토스랩·토스증권·토스페이먼츠일 수 있고, "카카오"가 카카오페이손보·카카오게임즈일 수 있다 ①. 기사 본문·페이지 하단의 법인명이 대상과 다르면 버리고, 애매하면 "못 찾은 것"에 후보로 적는다.
- 접근 등급을 넘지 않는다. B·C 소스를 curl·스크립트로 부르지 않고, #8 목록은 WebFetch도 하지 않는다.
- DART 묶음이 `dart_extract.py` 종료 2·3을 받으면 픽스처 절차를 밟고 `실패`로 보고한다 — 절차는 `agents.md` 묶음 템플릿의 DART 절이 정한다.
