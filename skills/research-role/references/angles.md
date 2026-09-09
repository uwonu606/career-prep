# 뻗기 각도

`leads.md` #2 조건표의 행이 가리키는 각도(자료 유형)와 그 절차다. 각 행의 사이트 이름은 예시일 뿐 각도의 정의가 아니다. 등급은 `access.md` #1, 금지 목록은 `access.md` #2, 사실 뒤의 ①②③도 거기 적힌 근거 등급이다.

## 1. 각도

열은 `# | 각도 | 답하는 질문 | 어디에(예시) | 절차 | 등급 | 주의`. "절차"가 에이전트의 실행 문장이다. 절차 안의 `D1`·`D2`·`R0`·`H1`·`H2` 표지는 #2 명령 블록의 주석 표지다.

| # | 각도 | 답하는 질문 | 어디에(예시) | 절차 | 등급 | 주의 |
|---|---|---|---|---|---|---|
| 1 | 공시 문서 | 무슨 사업을 어떻게 하나 — 「II. 사업의 내용」 하위 1~7(1 개요 / 2 주요 제품·서비스 / 3 원재료·생산설비 / 4 매출·수주 / 5 위험관리·파생거래 / **6 주요계약 및 연구개발활동** / 7 기타), 부문별 매출 | OpenDART `list.json`→`document.xml`; 키 없으면 DART 공시검색 | 키 있으면 `D2`(`--check`)의 `A001=<n>`이 1 이상이면 있음(종료 0), 0이면 종료 2 — `F001>0`이면 "감사보고서만"→없음. 키 없으면 `D1`을 A001·F001 각각 돌려 `[총 N건]`을 읽는다: A001>0 있음 / A001=0·F001>0 "감사보고서만"→없음 | A | 법인명 **정확일치**·UTF-8 필수·기간 10년 이내(넘으면 에러 없이 0건) ①. 감사보고서만 내는 회사(우아한형제들·토스뱅크)는 없음. 비상장도 증권 모집·매출 이력이 있으면 제출(당근마켓·비바리퍼블리카·컬리·무신사 ①). **금융업 서식은 하위 5개, 연구개발 항목 없음** ②. 연결에 금융 자회사가 있으면 둘이 나란히 나온다 — 카카오 FY2025는 `(제조서비스업)` 7 + `(금융업)` 5 = II 하위 12 ① |
| 2 | 직원 현황 | 어느 부문이 얼마나 크고 커지나 — 부문별 정규직/계약직/합계, 평균 근속, 1인 평균급여, 최근 5개 사업연도 | OpenDART `empSttus.json` | 1이 있음이면 `empSttus.json?crtfc_key=&corp_code=&bsns_year=YYYY&reprt_code=11011`, 최신 연도 `status` 000이면 있음 / 013이면 그 연도 없음(한 해 전 시도) | A | 필드 `fo_bbm`(부문) `sexdstn`(성별) `rgllbr_co`(정규직) `cnttk_co`(계약직) `sm`(합계) `avrg_cnwk_sdytrn`(평균근속) `fyer_salary_totamt`(급여총액) `jan_salary_am`(1인평균) — 콤마 든 문자열, `-` 가능 ①. 2015년 이후만 |
| 3 | 채용공고 **전체** | 지금 어떤 사람을 얼마나 뽑나 — 여는 포지션 전부의 직무·요구 스택 분포 | 회사 채용 페이지 · 채용 플랫폼(원티드·점핏·사람인·잡코리아) | 회사 홈페이지 도메인의 robots를 `R0`로 보고 `H1`로 HTML을 **1회** 받은 뒤 `H2` — href에 `(career\|recruit\|jobs\|채용)` grep, 3/3 성공 ①(careers.kakao.com / toss.im/career/jobs / career.woowahan.com). 없으면 WebSearch "<법인명> 채용". 플랫폼 공고는 WebSearch 결과로만 | A(링크 발견)→B | 서브도메인 프로빙은 1/3이라 쓰지 않는다 ①. 플랫폼 직접 호출 금지(`access.md` #2). 사용자가 준 공고 URL은 WebFetch. **이 각도만 전체 수집**. H2는 채용 사이트 루트만 주므로 목록 URL은 루트 WebFetch 1건 또는 `site:<채용도메인>` WebSearch로 확정. 채용 사이트가 JS 셸이면(WebFetch에 제목만, 카카오 실측 ①) 목록은 `site:` 검색으로 보완하고, 관계사 공고가 같은 목록에 섞이면(카카오 S-xxxx ①) 법인명으로 걸러라. **JS 셸이면 그 도메인 robots.txt의 `Sitemap:` 줄을 먼저 본다** — 에이피알은 사이트맵에 job_posting URL 72건이 있어 목록 전체를 얻었고 각 페이지는 `__NEXT_DATA__`에 직군·경력·고용·마감 필드를 담고 있었다(2026-09-06 ①). robots `*` 허용 경로만, 식별 UA, 1.5초 간격 |
| 4 | 뉴스 | 최근 1~2년 신사업·투자·조직 변화 | 언론 기사 | WebSearch "<법인명> 신사업 / 투자 / 조직" 최근 2년, 관련 기사가 있으면 있음 | B | Google News RSS·빅카인즈·네이버 뉴스 검색 **직접 호출 금지** ②(`access.md` #2) |
| 5 | IR 자료 | 경영진이 숫자로 강조하는 방향 — 실적발표 자료 | 회사 IR 페이지 | `company.json`의 `ir_url`(키) → `H1`로 받은 홈페이지 HTML href `(/ir\|invest)` grep → `https://<홈페이지>/ir` 프로빙(302 포함) — 카카오 3/3 ① | A(링크 발견)→B | 비상장은 대개 없음 → `없음`. 사이트맵에는 /ir이 없었다 ① |
| 6 | 평판·후기 | 안에서는 어떻게 보나 — 재직자 평, 연봉 분포 | 잡플래닛 · 블라인드 · 크레딧잡 · 캐치 | WebSearch "<법인명> 잡플래닛 / 블라인드 / 연봉" 스니펫으로 유무 확인, 링크 제시 | C | 잡플래닛 Cloudflare 챌린지로 전 페이지 403 ①, 블라인드 ClaudeBot·anthropic-ai `Disallow: /` ①, 크레딧잡 `Disallow: /` ①, 캐치 `/Company` 차단 ① → 전부 C |
| 7 | 채용 프로세스 | 어떻게 뽑나 — 코딩테스트·과제·면접 구조 후기 | 블로그 후기 · 커뮤니티 | WebSearch "<법인명> 코딩테스트 / 면접 후기 / 채용 과정" | B | 3의 채용 사이트에 절차 안내가 있으면 그것이 1차 출처 |

DART(1·2)는 OpenDART 공식 API라 등급 A이고 키가 필요하다. 키가 없으면 `D1`로 유무만 확인할 수 있다 — 본문 수집(`dart_fetch.py`)은 종료 5(키 없음 — `career-setup/references/layout.md` #2)이므로 그 실마리는 비워 두고 `open_questions`다. 필드명은 개발가이드 https://opendart.fss.or.kr/guide/main.do 에서 재확인한다.

## 2. 명령 블록

`<스킬>`은 이 스킬의 `SKILL.md`가 있는 디렉토리의 절대 경로다.

```bash
UA="research-role/0.1 (+python-urllib)"   # 요청자 식별 문자열. 브라우저로 위장하지 않는다 — 이 UA로 DART 검색이 200·[총 6건] 응답함 ①
WORK=<에이전트 작업 디렉토리>   # 임시물(응답 본문·HTML)은 전부 여기. artifacts/ 에는 두지 않는다
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
# R0 robots 확인 — 그 호스트의 robots.txt에서 ClaudeBot → anthropic-ai → * 순으로 첫 번째 있는 블록을 적용해 경로별 허용/차단을 찍는다. 전부 '허용'이어야 다음으로 ①
curl -sS -A "$UA" "https://<host>/robots.txt" -o "$WORK/robots-<host>.txt"
python3 - "$WORK/robots-<host>.txt" / <확인할 경로...> <<'PY'
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
# H1 홈페이지 1회 fetch(R0로 / 허용 확인 후). -L 로 리다이렉트를 따르니 출처에는 마지막 줄의 최종 URL을 적는다 → H2 채용 링크 grep ①
curl -sS -L -A "$UA" "https://<홈페이지>/" -o "$WORK/homepage.html" -w '%{url_effective}\n'
grep -o -i -E 'href="[^"]*(career|recruit|jobs|채용)[^"]*"' "$WORK/homepage.html" | sort -u
```
