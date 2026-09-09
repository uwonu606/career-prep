#!/usr/bin/env python3
"""OpenDART에서 회사 하나의 공시 묶음을 내려받는다.

    python3 dart_fetch.py <법인명|corp_code> --out <dir> [--years 5]
    python3 dart_fetch.py <법인명|corp_code> --check

순서: 키 → corpCode 캐시(7일) → 법인명 확정 → company.json → list.json(최신 사업보고서 1건)
→ document.xml(ZIP, 본문은 접미 없는 {rcept_no}.xml) → empSttus(최근 N개 사업연도)
→ exctvSttus(보고서 사업연도) → manifest.json. 요청 간 0.5초, 재시도 없음.
네트워크 함수(fetch_bytes)와 sleep 은 주입할 수 있어 테스트는 합성 응답으로 돈다.

--check: 내려받지 않고 최근 3년 사업보고서(A001)·감사보고서(F001) 건수만 센다 — 파일 생성 0,
stdout 한 줄 `corp_code=… corp_name=… stock_code=… A001=n F001=m latest_A001=… latest_A001_rcept_dt=… report_nm=…`
(없는 값은 ~), A001 0건이면 종료 2. 이 환경은 .env 를 읽는 셸 명령이 막혀 있어 키를 쓰는 확인은
curl 이 아니라 이 모드로 한다.

키: DART_API_KEY 환경변수 → 없으면 현재 디렉토리 .env 의 DART_API_KEY= 줄.
키는 로그·manifest·에러 메시지·stdout 에 절대 찍지 않는다(URL 기록 시 crtfc_key=***).

종료 코드: 0 성공 / 2 사업보고서 없음(--check 면 A001 0건) / 4 법인명 확정 실패(후보 stderr)
/ 5 키 없음(발급 URL 안내) / 6 API 오류(상태코드·메시지) / 7 네트워크 오류.

필드·파라미터명은 OpenDART 개발가이드(2026-09-06 확인)를 따른다. 표준 라이브러리만 쓴다.
"""

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

BASE = "https://opendart.fss.or.kr/api/"
KEY_URL = "https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do"
USER_AGENT = "research-role/0.1 (+python-urllib)"
DELAY = 0.5        # 요청 간 간격(초)
CACHE_DAYS = 7     # corpCode.zip 재다운로드 주기
LIST_YEARS = 3     # list.json 검색 기간(년)
TIMEOUT = 60
REPRT_ANNUAL = "11011"   # 사업보고서. 11012 반기 / 11013 1분기 / 11014 3분기
DETAIL_ANNUAL = "A001"   # 공시상세유형: 사업보고서(정기공시 A)
DETAIL_AUDIT = "F001"    # 공시상세유형: 감사보고서(외부감사관련 F)

EXIT_NO_REPORT, EXIT_NO_CORP, EXIT_NO_KEY, EXIT_API, EXIT_NET = 2, 4, 5, 6, 7

# 가이드 "메시지 설명" 기준. 013(조회 데이터 없음)은 호출자가 처리한다.
KEY_ERRORS = {
    "010": "등록되지 않은 키",
    "011": "사용할 수 없는 키",
    "012": "접근할 수 없는 IP",
    "901": "개인정보 보유기간 만료로 사용할 수 없는 키",
}
LIMIT_ERRORS = {"020": "요청 제한 초과", "021": "조회 가능 회사 개수 초과(최대 100건)"}


class DartError(Exception):
    """비0 종료로 끝날 실패. code 가 종료 코드다. 메시지에 키가 들어가면 안 된다."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def mask(url):
    """URL 의 crtfc_key 값을 *** 로 가린다. 기록·메시지에 나가는 URL 은 전부 이걸 거친다."""
    return re.sub(r"(crtfc_key=)[^&]*", r"\1***", url)


def load_key(env=None, cwd=None):
    """DART_API_KEY 환경변수 → ./.env 의 DART_API_KEY= 줄 순으로 찾는다. 없으면 None."""
    env = os.environ if env is None else env
    key = (env.get("DART_API_KEY") or "").strip()
    if key:
        return key
    dotenv = Path(cwd or ".") / ".env"
    if not dotenv.is_file():
        return None
    for line in dotenv.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if line.startswith("DART_API_KEY="):
            return line.partition("=")[2].strip().strip('"').strip("'") or None
    return None


def build_request(url):
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})


def http_get(url):
    """기본 네트워크 함수. 테스트에서는 같은 서명(url -> bytes)의 가짜로 바꿔 넣는다."""
    with urllib.request.urlopen(build_request(url), timeout=TIMEOUT) as resp:
        return resp.read()


def check_status(status, message, where, allow=("000",)):
    """허용 목록 밖의 상태코드는 DartError(6). 키 문제와 요청 한도는 그렇다고 명시한다."""
    if status in allow:
        return
    if status in KEY_ERRORS:
        raise DartError(EXIT_API, f"API 키 문제(status {status}, {KEY_ERRORS[status]}): {message} — {where}")
    if status in LIMIT_ERRORS:
        raise DartError(EXIT_API, f"요청 한도(status {status}, {LIMIT_ERRORS[status]}): {message} — {where}")
    raise DartError(EXIT_API, f"API 오류(status {status}): {message} — {where}")


def parse_error_xml(raw):
    """document.xml·corpCode.xml 이 실패하면 ZIP 대신 <result><status/><message/></result> 가 온다."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return "?", raw[:200].decode("utf-8", "replace")
    return (root.findtext(".//status") or "?").strip(), (root.findtext(".//message") or "").strip()


class Client:
    """OpenDART 호출기. 요청 사이에 DELAY 초 쉬고, 부른 URL 을 키 가린 채 기록한다."""

    def __init__(self, key, fetch_bytes=http_get, sleep=time.sleep):
        self.key = key
        self.fetch = fetch_bytes
        self.sleep = sleep
        self.requests = []  # 키 가린 URL. manifest 에 그대로 실린다

    def url(self, endpoint, **params):
        return BASE + endpoint + "?" + urllib.parse.urlencode({"crtfc_key": self.key, **params})

    def get(self, endpoint, **params):
        url = self.url(endpoint, **params)
        if self.requests:
            self.sleep(DELAY)
        self.requests.append(mask(url))
        try:
            return self.fetch(url)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise DartError(EXIT_API, f"요청 제한(HTTP 429) — {mask(url)}") from None
            raise DartError(EXIT_NET, f"HTTP {e.code} — {mask(url)}") from None
        except OSError as e:
            # URLError·timeout·연결 거부가 전부 여기로 온다. e.filename 에 원 URL 이 있을 수 있어 str(e) 만 쓴다
            raise DartError(EXIT_NET, f"네트워크 오류: {getattr(e, 'reason', None) or e} — {mask(url)}") from None

    def get_json(self, endpoint, allow_empty=False, **params):
        """(원문 bytes, dict). allow_empty 면 013 을 통과시켜 호출자가 처리한다."""
        raw = self.get(endpoint, **params)
        try:
            data = json.loads(raw)
        except ValueError:
            raise DartError(EXIT_API, f"JSON 이 아닌 응답 — {self.requests[-1]}") from None
        allow = ("000", "013") if allow_empty else ("000",)
        check_status(str(data.get("status", "")), data.get("message", ""), self.requests[-1], allow)
        return raw, data

    def get_zip(self, endpoint, **params):
        """ZIP 을 기대하는 호출. ZIP 이 아니면 에러 XML 로 보고 status 를 읽어 DartError."""
        raw = self.get(endpoint, **params)
        if zipfile.is_zipfile(io.BytesIO(raw)):
            return raw
        status, message = parse_error_xml(raw)
        check_status(status, message, self.requests[-1])
        raise DartError(EXIT_API, f"ZIP 도 에러 XML 도 아닌 응답 — {self.requests[-1]}")


def parse_corp_codes(zip_bytes):
    """corpCode.zip 안 CORPCODE.xml 의 <list> 들을 dict 목록으로."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        name = next((n for n in zf.namelist() if n.lower().endswith(".xml")), None)
        if name is None:
            raise DartError(EXIT_API, f"corpCode.zip 안에 XML 이 없음: {zf.namelist()}")
        root = ET.fromstring(zf.read(name))
    corps = []
    for el in root.iter("list"):
        corps.append({
            "corp_code": (el.findtext("corp_code") or "").strip(),
            "corp_name": (el.findtext("corp_name") or "").strip(),
            "corp_eng_name": (el.findtext("corp_eng_name") or "").strip(),  # 가이드에는 있고 옛 문서에는 없어 없어도 된다
            "stock_code": (el.findtext("stock_code") or "").strip(),  # 비상장은 공백
            "modify_date": (el.findtext("modify_date") or "").strip(),
        })
    return corps


def load_corp_codes(client, cache_dir):
    """캐시가 7일 안이면 그걸 읽고, 아니면 내려받아 캐시에 둔다. 다운로드 실패면 옛 캐시는 건드리지 않는다."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / "corpCode.zip"
    fresh = path.is_file() and time.time() - path.stat().st_mtime < CACHE_DAYS * 86400
    if not fresh:
        path.write_bytes(client.get_zip("corpCode.xml"))
    return parse_corp_codes(path.read_bytes())


def squash(s):
    return re.sub(r"\s+", "", s or "").lower()


def candidates_table(cands):
    if not cands:
        return "부분일치 후보 없음 — 브랜드명이 아닌 법인명으로 다시 시도하거나 corp_code 8자리를 직접 넣어라"
    lines = [
        "부분일치 후보(상장사 먼저, 최대 10개). corp_code 8자리로 다시 실행:",
        "| corp_name | corp_code | stock_code |",
        "|---|---|---|",
    ]
    lines += [f"| {c['corp_name']} | {c['corp_code']} | {c['stock_code'] or '—'} |" for c in cands]
    return "\n".join(lines)


def resolve_corp(query, corps):
    """8자리 숫자면 corp_code, 아니면 법인명 정확일치 1건. 그 외는 후보 표를 담아 DartError(4)."""
    if re.fullmatch(r"\d{8}", query):
        for c in corps:
            if c["corp_code"] == query:
                return c
        raise DartError(EXIT_NO_CORP, f"corp_code {query} 가 corpCode 목록에 없음")
    q = squash(query)
    if not q:
        raise DartError(EXIT_NO_CORP, "법인명이 비어 있음")
    exact = [c for c in corps if squash(c["corp_name"]) == q]
    if len(exact) == 1:
        return exact[0]
    partial = [c for c in corps if q in squash(c["corp_name"]) or (c["corp_eng_name"] and q in squash(c["corp_eng_name"]))]
    partial.sort(key=lambda c: (c not in exact, not c["stock_code"], c["corp_name"]))
    reason = f"정확일치 {len(exact)}건" if exact else "정확일치 없음"
    raise DartError(EXIT_NO_CORP, f"법인명 확정 실패({reason}): {query!r}\n" + candidates_table(partial[:10]))


def latest_report(items):
    return max(items, key=lambda r: (r.get("rcept_dt", ""), r.get("rcept_no", "")))


def report_year(report_nm, rcept_dt):
    """report_nm 의 "(YYYY.MM)" 에서 사업연도. 없으면 접수연도-1 로 두고 그 출처를 함께 돌려준다."""
    m = re.search(r"\((\d{4})\.(\d{2})\)", report_nm or "")
    if m:
        return int(m.group(1)), "report_nm"
    m = re.match(r"\d{4}", rcept_dt or "")
    if not m:
        raise DartError(EXIT_API, f"사업연도를 알 수 없음: report_nm={report_nm!r} rcept_dt={rcept_dt!r}")
    return int(m.group(0)) - 1, "rcept_dt-1"


def save_document(zip_bytes, rcept_no, out):
    """ZIP 의 파일을 전부 저장하고 (본문 파일명, 첨부 파일명 목록). 본문 = 접미 없는 {rcept_no}.xml."""
    body, attachments = None, []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            safe = Path(name).name  # ZIP 안 경로는 버린다(디렉토리 탈출 방지)
            if not safe or name.endswith("/"):
                continue
            (out / safe).write_bytes(zf.read(name))
            if safe == f"{rcept_no}.xml":
                body = safe
            else:
                attachments.append(safe)
    if body is None:
        raise DartError(EXIT_API, f"document.xml ZIP 에 본문 {rcept_no}.xml 이 없음. 들어 있던 파일: {attachments}")
    return body, attachments


def has_rows(data):
    return str(data.get("status")) != "013" and bool(data.get("list"))


def list_reports(client, corp_code, today, detail_ty):
    """list.json 최근 3년, 최종보고서만, 한 상세유형. (원문 bytes, dict). 013 은 통과시킨다."""
    bgn = today - dt.timedelta(days=365 * LIST_YEARS + 1)
    return client.get_json(
        "list.json", allow_empty=True, corp_code=corp_code,
        bgn_de=bgn.strftime("%Y%m%d"), end_de=today.strftime("%Y%m%d"),
        pblntf_ty=detail_ty[0], pblntf_detail_ty=detail_ty, last_reprt_at="Y", page_count="100",
    )


def annual_reports(listing):
    """A001 이면 사업보고서만 오지만, 혹시 섞이면 이름으로 한 번 더 고른다."""
    items = listing.get("list") or []
    return [r for r in items if "사업보고서" in (r.get("report_nm") or "")] or items


def report_count(listing):
    """응답의 total_count. 013 은 0. total_count 가 없으면 list 길이."""
    if str(listing.get("status")) == "013":
        return 0
    try:
        return int(listing.get("total_count"))
    except (TypeError, ValueError):
        return len(listing.get("list") or [])


def check_reports(query, client, cache_dir, today):
    """--check: 내려받지 않고 A001·F001 건수와 최신 사업보고서만 stdout 한 줄. 파일을 만들지 않는다."""
    corp = resolve_corp(query, load_corp_codes(client, cache_dir))
    _, annual = list_reports(client, corp["corp_code"], today, DETAIL_ANNUAL)
    _, audit = list_reports(client, corp["corp_code"], today, DETAIL_AUDIT)
    items = annual_reports(annual)
    latest = latest_report(items) if items else {}
    n_annual = report_count(annual)
    fields = [
        ("corp_code", corp["corp_code"]),
        ("corp_name", corp["corp_name"]),
        ("stock_code", corp["stock_code"] or "~"),
        (DETAIL_ANNUAL, n_annual),
        (DETAIL_AUDIT, report_count(audit)),
        ("latest_A001", latest.get("rcept_no") or "~"),
        ("latest_A001_rcept_dt", latest.get("rcept_dt") or "~"),
        ("report_nm", latest.get("report_nm") or "~"),
    ]
    print(" ".join(f"{k}={v}" for k, v in fields))
    if n_annual < 1:
        print(f"사업보고서(A001) 최근 {LIST_YEARS}년 0건", file=sys.stderr)
        return EXIT_NO_REPORT
    return 0


def fetch_all(query, out, years, client, cache_dir, today):
    """전체 절차. 성공하면 manifest dict, 실패는 DartError."""
    corp = resolve_corp(query, load_corp_codes(client, cache_dir))
    code = corp["corp_code"]
    out.mkdir(parents=True, exist_ok=True)

    raw, _company = client.get_json("company.json", corp_code=code)
    (out / "company.json").write_bytes(raw)

    raw, listing = list_reports(client, code, today, DETAIL_ANNUAL)
    (out / "list.json").write_bytes(raw)
    items = annual_reports(listing)
    if not items:
        raise DartError(EXIT_NO_REPORT, "사업보고서 없음 — 감사보고서만 내는 회사일 수 있음 (company.json 은 저장함)")
    report = latest_report(items)
    rcept_no = report["rcept_no"]
    year, year_source = report_year(report.get("report_nm"), report.get("rcept_dt"))
    if year_source != "report_nm":
        print(f"report_nm {report.get('report_nm')!r} 에 (YYYY.MM) 이 없어 사업연도를 접수연도-1={year} 로 둠", file=sys.stderr)

    body, attachments = save_document(client.get_zip("document.xml", rcept_no=rcept_no), rcept_no, out)

    emp_files, emp_skipped = {}, []
    for y in range(year, year - years, -1):
        raw, data = client.get_json("empSttus.json", allow_empty=True, corp_code=code, bsns_year=str(y), reprt_code=REPRT_ANNUAL)
        if not has_rows(data):
            emp_skipped.append(y)
            continue
        emp_files[str(y)] = f"empSttus-{y}.json"
        (out / emp_files[str(y)]).write_bytes(raw)

    raw, data = client.get_json("exctvSttus.json", allow_empty=True, corp_code=code, bsns_year=str(year), reprt_code=REPRT_ANNUAL)
    exec_file = None
    if has_rows(data):
        exec_file = f"exctvSttus-{year}.json"
        (out / exec_file).write_bytes(raw)
    else:
        print(f"exctvSttus {year}: 조회 데이터 없음(013) — 건너뜀", file=sys.stderr)

    manifest = {
        "corp_code": code,
        "corp_name": corp["corp_name"],
        "stock_code": corp["stock_code"] or None,
        "rcept_no": rcept_no,
        "report_nm": report.get("report_nm"),
        "rcept_dt": report.get("rcept_dt"),
        "bsns_year_of_report": year,
        "bsns_year_source": year_source,
        "emp_years_fetched": sorted(int(y) for y in emp_files),
        "emp_years_skipped": emp_skipped,
        "exec_year_fetched": year if exec_file else None,
        "files": {
            "company": "company.json",
            "list": "list.json",
            "document": body,
            "attachments": attachments,
            "emp": emp_files,
            "exec": exec_file,
        },
        "requests": list(client.requests),
        "fetched_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", help="법인명(정확일치, 브랜드명 아님) 또는 corp_code 8자리")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path, help="산출 디렉토리(예: career/companies/<slug>/roles/<role>/artifacts/dart)")
    mode.add_argument("--check", action="store_true",
                      help="내려받지 않고 최근 3년 사업보고서(A001)·감사보고서(F001) 건수만 stdout 한 줄로. A001 0건이면 종료 2")
    ap.add_argument("--years", type=int, default=5, help="empSttus 를 받을 최근 사업연도 수(기본 5)")
    args = ap.parse_args(argv)
    if args.years < 1:
        ap.error("--years 는 1 이상")
    return args


def main(argv=None, fetch_bytes=http_get, sleep=time.sleep, env=None, cwd=None, today=None):
    args = parse_args(argv)
    env = os.environ if env is None else env
    key = load_key(env, cwd)
    if not key:
        print(
            "DART_API_KEY 가 없습니다. 환경변수 또는 현재 디렉토리 .env 의 DART_API_KEY= 줄로 넣으세요.\n"
            f"발급(무료, 개인 즉시): {KEY_URL}",
            file=sys.stderr,
        )
        return EXIT_NO_KEY
    cache_dir = Path(env.get("ADD_COMPANY_CACHE") or Path.home() / ".cache" / "career-prep")
    client = Client(key, fetch_bytes=fetch_bytes, sleep=sleep)
    try:
        if args.check:
            return check_reports(args.query, client, cache_dir, today or dt.date.today())
        m = fetch_all(args.query, args.out, args.years, client, cache_dir, today or dt.date.today())
    except DartError as e:
        print(str(e), file=sys.stderr)
        return e.code
    print(
        f"{m['corp_name']}({m['corp_code']}) rcept_no={m['rcept_no']} 사업연도={m['bsns_year_of_report']} "
        f"emp={m['emp_years_fetched']} skipped={m['emp_years_skipped']} -> {args.out / 'manifest.json'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
