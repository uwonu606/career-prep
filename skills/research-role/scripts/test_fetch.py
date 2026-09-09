#!/usr/bin/env python3
"""dart_fetch.py · dart_tables.py 테스트. 네트워크 없이 합성 응답으로 돈다.

    python3 test_fetch.py            또는        python3 -m unittest test_fetch

합성 응답: corpCode.zip(정확일치 1건·부분일치 여럿·0건·정확일치 2건), list.json(사업보고서 2건 중 최신),
document.xml ZIP(본문 + _00760·_00761), empSttus/exctvSttus(콤마 든 숫자·'-'), 상태코드 010/013/014/020.
"""

import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dart_fetch  # noqa: E402
import dart_tables  # noqa: E402

KEY = "k" * 40
RCEPT = "20250317000123"
TODAY = dt.date(2026, 9, 6)

CORPS = [
    ("00256598", "카카오", "Kakao Corp.", "035720"),
    ("00612345", "카카오뱅크", "KakaoBank Corp.", "323410"),
    ("01234567", "카카오엔터테인먼트", "Kakao Entertainment Corp.", " "),
    ("00126380", "삼성전자", "SAMSUNG ELECTRONICS CO,.LTD", "005930"),
    ("00999001", "동일상사", "Dongil Corp.", " "),
    ("00999002", "동일상사", "Dongil Trading Co.", "999002"),
]


def zip_bytes(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def corpcode_zip():
    items = "".join(
        f"<list><corp_code>{c}</corp_code><corp_name>{n}</corp_name><corp_eng_name>{e}</corp_eng_name>"
        f"<stock_code>{s}</stock_code><modify_date>20250101</modify_date></list>\n"
        for c, n, e, s in CORPS
    )
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<result>\n' + items + "</result>\n"
    return zip_bytes({"CORPCODE.xml": xml.encode("utf-8")})


def error_xml(status, message):
    return f'<?xml version="1.0" encoding="UTF-8"?><result><status>{status}</status><message>{message}</message></result>'.encode("utf-8")


def status_json(status, message):
    return json.dumps({"status": status, "message": message}, ensure_ascii=False).encode("utf-8")


def company_json():
    return json.dumps({
        "status": "000", "message": "정상", "corp_code": "00256598", "corp_name": "주식회사 카카오",
        "corp_name_eng": "Kakao Corp.", "stock_name": "카카오", "stock_code": "035720", "ceo_nm": "정신아",
        "corp_cls": "Y", "jurir_no": "1101111111111", "bizr_no": "1208100000", "adres": "제주",
        "hm_url": "www.kakaocorp.com", "ir_url": "www.kakaocorp.com/ir", "phn_no": "02-0000-0000", "fax_no": "",
        "induty_code": "63999", "est_dt": "19950216", "acc_mt": "12",
    }, ensure_ascii=False).encode("utf-8")


def list_json():
    return json.dumps({
        "status": "000", "message": "정상", "page_no": 1, "page_count": 100, "total_count": 2, "total_page": 1,
        "list": [
            {"corp_code": "00256598", "corp_name": "카카오", "stock_code": "035720", "corp_cls": "Y",
             "report_nm": "사업보고서 (2023.12)", "rcept_no": "20240320000456", "flr_nm": "카카오", "rcept_dt": "20240320", "rm": "연"},
            {"corp_code": "00256598", "corp_name": "카카오", "stock_code": "035720", "corp_cls": "Y",
             "report_nm": "[기재정정]사업보고서 (2024.12)", "rcept_no": RCEPT, "flr_nm": "카카오", "rcept_dt": "20250317", "rm": "연"},
        ],
    }, ensure_ascii=False).encode("utf-8")


def audit_json(n, total_count=None):
    """F001 감사보고서 n건. total_count 는 기본 n."""
    items = [
        {"corp_code": "00256598", "corp_name": "카카오", "stock_code": "035720", "corp_cls": "Y",
         "report_nm": f"감사보고서 ({2024 - i}.12)", "rcept_no": f"2025040100{i:04d}", "flr_nm": "회계법인", "rcept_dt": f"202{5 - i}0401", "rm": ""}
        for i in range(n)
    ]
    return json.dumps({"status": "000", "message": "정상", "page_no": 1, "page_count": 100,
                       "total_count": n if total_count is None else total_count, "total_page": 1, "list": items}, ensure_ascii=False).encode("utf-8")


def list_by_type(annual, audit):
    """list.json 가짜: pblntf_detail_ty 로 A001/F001 응답을 고른다."""
    def pick(params):
        return annual if params["pblntf_detail_ty"] == "A001" else audit
    return pick


def document_zip(rcept=RCEPT):
    return zip_bytes({
        f"{rcept}.xml": b'<?xml version="1.0" encoding="utf-8"?><DOCUMENT><BODY>body</BODY></DOCUMENT>',
        f"{rcept}_00760.xml": b"<DOCUMENT>audit-1</DOCUMENT>",
        f"{rcept}_00761.xml": b"<DOCUMENT>audit-2</DOCUMENT>",
    })


def emp_rows(year, with_total=False, mismatch=False):
    base = {"rcept_no": RCEPT, "corp_cls": "Y", "corp_code": "00256598", "corp_name": "카카오", "stlm_dt": f"{year}-12-31", "rm": "-"}
    rows = [
        dict(base, fo_bbm="전사", sexdstn="남", rgllbr_co="2,345", cnttk_co="120", sm="2,465", avrg_cnwk_sdytrn="5.3",
             fyer_salary_totamt="250,000,000,000", jan_salary_am="101,000,000"),
        dict(base, fo_bbm="전사", sexdstn="여", rgllbr_co="1,200", cnttk_co="-", sm="1,200" if not mismatch else "1,250",
             avrg_cnwk_sdytrn="4.1", fyer_salary_totamt="100,000,000,000", jan_salary_am="83,000,000"),
        dict(base, fo_bbm="해외", sexdstn="남", rgllbr_co="-", cnttk_co="-", sm="-", avrg_cnwk_sdytrn="-",
             fyer_salary_totamt="-", jan_salary_am="해당사항없음"),
        dict(base, fo_bbm="해외", sexdstn="여", rgllbr_co="", cnttk_co="", sm="", avrg_cnwk_sdytrn="", fyer_salary_totamt="", jan_salary_am=""),
    ]
    if with_total:
        rows.append(dict(base, fo_bbm="합계", sexdstn="-", rgllbr_co="3,545", cnttk_co="120", sm="3,665", avrg_cnwk_sdytrn="4.9",
                         fyer_salary_totamt="350,000,000,000", jan_salary_am="95,000,000"))
    return rows


def emp_json(year, **kw):
    return json.dumps({"status": "000", "message": "정상", "list": emp_rows(year, **kw)}, ensure_ascii=False).encode("utf-8")


def exec_rows():
    base = {"rcept_no": RCEPT, "corp_cls": "Y", "corp_code": "00256598", "corp_name": "카카오", "stlm_dt": "2024-12-31"}
    return [
        dict(base, nm="정신아", sexdstn="여", birth_ym="1975년 04월", ofcps="대표이사", rgist_exctv_at="등기임원", fte_at="상근",
             chrg_job="대표이사", main_career="카카오벤처스 대표\n보스턴컨설팅그룹", mxmm_shrholdr_relate="-", hffc_pd="1년", tenure_end_on="2027년 03월 28일"),
        dict(base, nm="홍길동", sexdstn="남", birth_ym="1980년 01월", ofcps="부사장|CTO", rgist_exctv_at="미등기임원", fte_at="상근",
             chrg_job="기술총괄", main_career="-", mxmm_shrholdr_relate="-", hffc_pd="3년", tenure_end_on="-"),
    ]


def exec_json():
    return json.dumps({"status": "000", "message": "정상", "list": exec_rows()}, ensure_ascii=False).encode("utf-8")


class FakeNet:
    """URL 을 endpoint·파라미터로 풀어 미리 정한 응답을 돌려준다. 값은 bytes, 예외, 또는 params -> bytes 함수."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        path, _, query = url.partition("?")
        assert path.startswith(dart_fetch.BASE), path
        params = dict(urllib.parse.parse_qsl(query))
        assert params.get("crtfc_key") == KEY, "키가 URL 에 없다"
        resp = self.responses[path.rsplit("/", 1)[1]]
        if callable(resp):
            resp = resp(params)
        if isinstance(resp, Exception):
            raise resp
        return resp

    def endpoints(self):
        return [u.partition("?")[0].rsplit("/", 1)[1] for u in self.calls]

    def params(self, endpoint):
        return [dict(urllib.parse.parse_qsl(u.partition("?")[2])) for u in self.calls if u.partition("?")[0].endswith("/" + endpoint)]


def happy():
    def emp(params):
        if params["bsns_year"] == "2022":
            return status_json("013", "조회된 데이타가 없습니다.")
        return emp_json(params["bsns_year"], with_total=(params["bsns_year"] == "2023"))

    return {
        "corpCode.xml": corpcode_zip(),
        "company.json": company_json(),
        "list.json": list_json(),
        "document.xml": document_zip(),
        "empSttus.json": emp,
        "exctvSttus.json": exec_json(),
    }


class FetchCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "out"
        self.cache = self.root / "cache"

    def tearDown(self):
        self.tmp.cleanup()

    def run_fetch(self, argv, responses, env=None, cwd=None):
        net = FakeNet(responses)
        sleeps = []
        out, err = io.StringIO(), io.StringIO()
        env = {"DART_API_KEY": KEY, "ADD_COMPANY_CACHE": str(self.cache)} if env is None else env
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = dart_fetch.main(argv, fetch_bytes=net, sleep=sleeps.append, env=env, cwd=cwd, today=TODAY)
        self.assertNotIn(KEY, out.getvalue() + err.getvalue(), "키가 출력에 새면 안 된다")
        return code, out.getvalue(), err.getvalue(), net, sleeps

    def argv(self, query="카카오", *extra):
        return [query, "--out", str(self.out), *extra]

    # --- 정상 경로 ---

    def test_happy_path_writes_everything(self):
        code, out, err, net, sleeps = self.run_fetch(self.argv(), happy())
        self.assertEqual(code, 0, err)
        self.assertEqual(net.endpoints(), [
            "corpCode.xml", "company.json", "list.json", "document.xml",
            "empSttus.json", "empSttus.json", "empSttus.json", "empSttus.json", "empSttus.json", "exctvSttus.json",
        ])
        self.assertEqual(sleeps, [0.5] * (len(net.calls) - 1), "첫 요청 뒤부터 요청마다 0.5초")

        names = sorted(p.name for p in self.out.iterdir())
        self.assertEqual(names, sorted([
            "company.json", "list.json", f"{RCEPT}.xml", f"{RCEPT}_00760.xml", f"{RCEPT}_00761.xml",
            "empSttus-2024.json", "empSttus-2023.json", "empSttus-2021.json", "empSttus-2020.json",
            "exctvSttus-2024.json", "manifest.json",
        ]))
        self.assertTrue((self.out / f"{RCEPT}.xml").read_bytes().startswith(b"<?xml"))
        self.assertEqual((self.out / "company.json").read_bytes(), company_json(), "응답 원문을 그대로 저장")

        m = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual((m["corp_code"], m["corp_name"], m["stock_code"]), ("00256598", "카카오", "035720"))
        self.assertEqual((m["rcept_no"], m["rcept_dt"], m["report_nm"]), (RCEPT, "20250317", "[기재정정]사업보고서 (2024.12)"))
        self.assertEqual((m["bsns_year_of_report"], m["bsns_year_source"]), (2024, "report_nm"))
        self.assertEqual(m["emp_years_fetched"], [2020, 2021, 2023, 2024])
        self.assertEqual(m["emp_years_skipped"], [2022])
        self.assertEqual(m["exec_year_fetched"], 2024)
        self.assertEqual(m["files"]["document"], f"{RCEPT}.xml")
        self.assertEqual(sorted(m["files"]["attachments"]), [f"{RCEPT}_00760.xml", f"{RCEPT}_00761.xml"])
        self.assertEqual(m["files"]["emp"], {"2020": "empSttus-2020.json", "2021": "empSttus-2021.json", "2023": "empSttus-2023.json", "2024": "empSttus-2024.json"})
        self.assertEqual(m["files"]["exec"], "exctvSttus-2024.json")
        self.assertEqual(len(m["requests"]), len(net.calls))
        for u in m["requests"]:
            self.assertIn("crtfc_key=***", u)
        self.assertNotIn(KEY, (self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertRegex(m["fetched_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")
        self.assertIn("rcept_no=" + RCEPT, out)
        self.assertTrue((self.cache / "corpCode.zip").is_file())

    def test_request_params_follow_guide(self):
        code, _, err, net, _ = self.run_fetch(self.argv("카카오", "--years", "2"), happy())
        self.assertEqual(code, 0, err)
        (lst,) = net.params("list.json")
        self.assertEqual(lst["corp_code"], "00256598")
        self.assertEqual((lst["pblntf_ty"], lst["pblntf_detail_ty"], lst["last_reprt_at"], lst["page_count"]), ("A", "A001", "Y", "100"))
        self.assertEqual((lst["bgn_de"], lst["end_de"]), ("20230906", "20260906"), "최근 3년")
        (doc,) = net.params("document.xml")
        self.assertEqual(doc["rcept_no"], RCEPT)
        emp = net.params("empSttus.json")
        self.assertEqual([p["bsns_year"] for p in emp], ["2024", "2023"], "--years 2")
        self.assertTrue(all(p["reprt_code"] == "11011" and p["corp_code"] == "00256598" for p in emp))
        (ex,) = net.params("exctvSttus.json")
        self.assertEqual((ex["bsns_year"], ex["reprt_code"]), ("2024", "11011"))
        self.assertEqual(net.params("corpCode.xml"), [{"crtfc_key": KEY}])

    def test_corp_code_query_skips_name_matching(self):
        code, _, err, net, _ = self.run_fetch(self.argv("00126380"), happy())
        self.assertEqual(code, 0, err)
        self.assertEqual(net.params("company.json")[0]["corp_code"], "00126380")
        m = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["corp_name"], "삼성전자")

    def test_unlisted_company_has_null_stock_code(self):
        code, _, err, _, _ = self.run_fetch(self.argv("카카오엔터테인먼트"), happy())
        self.assertEqual(code, 0, err)
        m = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertIsNone(m["stock_code"])

    def test_exec_013_is_skipped_not_fatal(self):
        r = happy()
        r["exctvSttus.json"] = status_json("013", "조회된 데이타가 없습니다.")
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 0, err)
        self.assertIn("exctvSttus", err)
        m = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertIsNone(m["exec_year_fetched"])
        self.assertIsNone(m["files"]["exec"])

    # --- --check ---

    def check_argv(self, query="카카오"):
        return [query, "--check"]

    def assert_no_files(self):
        self.assertFalse(self.out.exists(), "--check 는 산출 디렉토리를 만들지 않는다")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["cache"], "캐시 말고는 파일 생성 0")

    def test_check_found_exit_0(self):
        r = happy()
        r["list.json"] = list_by_type(list_json(), audit_json(3))
        code, out, err, net, sleeps = self.run_fetch(self.check_argv(), r)
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "corp_code=00256598 corp_name=카카오 stock_code=035720 A001=2 F001=3 "
                              f"latest_A001={RCEPT} latest_A001_rcept_dt=20250317 report_nm=[기재정정]사업보고서 (2024.12)\n")
        self.assertEqual(net.endpoints(), ["corpCode.xml", "list.json", "list.json"], "다운로드 없음")
        a, f = net.params("list.json")
        self.assertEqual((a["pblntf_ty"], a["pblntf_detail_ty"]), ("A", "A001"))
        self.assertEqual((f["pblntf_ty"], f["pblntf_detail_ty"]), ("F", "F001"))
        for p in (a, f):
            self.assertEqual((p["corp_code"], p["last_reprt_at"], p["page_count"], p["bgn_de"], p["end_de"]),
                             ("00256598", "Y", "100", "20230906", "20260906"))
        self.assertEqual(sleeps, [0.5, 0.5])
        self.assert_no_files()

    def test_check_audit_only_exit_2(self):
        r = happy()
        r["list.json"] = list_by_type(status_json("013", "조회된 데이타가 없습니다."), audit_json(5))
        code, out, err, net, _ = self.run_fetch(self.check_argv(), r)
        self.assertEqual(code, 2)
        self.assertEqual(out, "corp_code=00256598 corp_name=카카오 stock_code=035720 A001=0 F001=5 "
                              "latest_A001=~ latest_A001_rcept_dt=~ report_nm=~\n")
        self.assertIn("A001", err)
        self.assertNotIn("감사보고서만", err + out, "판정은 호출자가 한다")
        self.assert_no_files()

    def test_check_nothing_exit_2(self):
        r = happy()
        r["list.json"] = list_by_type(status_json("013", "없음"), status_json("013", "없음"))
        code, out, err, _, _ = self.run_fetch(self.check_argv(), r)
        self.assertEqual(code, 2)
        self.assertIn(" A001=0 F001=0 latest_A001=~ ", out)
        self.assert_no_files()

    def test_check_unlisted_stock_code_is_tilde(self):
        r = happy()
        r["list.json"] = list_by_type(list_json(), status_json("013", "없음"))
        code, out, err, _, _ = self.run_fetch(self.check_argv("카카오엔터테인먼트"), r)
        self.assertEqual(code, 0, err)
        self.assertIn(" corp_name=카카오엔터테인먼트 stock_code=~ A001=2 F001=0 ", out)

    def test_check_uses_total_count_over_page_length(self):
        r = happy()
        r["list.json"] = list_by_type(list_json(), audit_json(2, total_count=150))
        code, out, _, _, _ = self.run_fetch(self.check_argv(), r)
        self.assertEqual(code, 0)
        self.assertIn(" F001=150 ", out)

    def test_check_api_error_keeps_exit_6(self):
        r = happy()
        r["list.json"] = list_by_type(list_json(), status_json("020", "요청 제한을 초과하였습니다."))
        code, out, err, _, _ = self.run_fetch(self.check_argv(), r)
        self.assertEqual(code, 6)
        self.assertEqual(out, "", "오류면 stdout 줄을 내지 않는다")
        self.assertIn("020", err)

    def test_check_unresolved_name_exit_4(self):
        code, out, err, net, _ = self.run_fetch(self.check_argv("카카"), happy())
        self.assertEqual(code, 4)
        self.assertEqual(net.endpoints(), ["corpCode.xml"])
        self.assert_no_files()

    def test_check_and_out_are_mutually_exclusive(self):
        for argv in (["카카오", "--check", "--out", str(self.out)], ["카카오"]):
            with self.assertRaises(SystemExit):
                with contextlib.redirect_stderr(io.StringIO()):
                    dart_fetch.parse_args(argv)

    # --- 법인명 확정 ---

    def test_partial_matches_listed_first_exit_4(self):
        code, _, err, net, _ = self.run_fetch(self.argv("카카"), happy())
        self.assertEqual(code, 4)
        self.assertEqual(net.endpoints(), ["corpCode.xml"], "확정 실패면 더 부르지 않는다")
        self.assertIn("정확일치 없음", err)
        rows = [l for l in err.splitlines() if l.startswith("| ") and "corp_name" not in l]
        self.assertEqual([r.split("|")[1].strip() for r in rows], ["카카오", "카카오뱅크", "카카오엔터테인먼트"], "상장사 먼저")
        self.assertIn("| 카카오 | 00256598 | 035720 |", err)
        self.assertIn("| 카카오엔터테인먼트 | 01234567 | — |", err)
        self.assertFalse(self.out.exists(), "확정 전에는 산출 디렉토리를 만들지 않는다")

    def test_duplicate_exact_matches_exit_4(self):
        code, _, err, _, _ = self.run_fetch(self.argv("동일상사"), happy())
        self.assertEqual(code, 4)
        self.assertIn("정확일치 2건", err)
        rows = [l for l in err.splitlines() if l.startswith("| 동일상사")]
        self.assertEqual(len(rows), 2)
        self.assertIn("999002", rows[0], "상장된 쪽이 위")

    def test_no_candidates_exit_4(self):
        code, _, err, _, _ = self.run_fetch(self.argv("없는회사"), happy())
        self.assertEqual(code, 4)
        self.assertIn("후보 없음", err)

    def test_unknown_corp_code_exit_4(self):
        code, _, err, _, _ = self.run_fetch(self.argv("00000001"), happy())
        self.assertEqual(code, 4)
        self.assertIn("00000001", err)

    def test_english_name_partial_match(self):
        code, _, err, _, _ = self.run_fetch(self.argv("Dongil"), happy())
        self.assertEqual(code, 4)
        self.assertEqual(err.count("| 동일상사"), 2)

    def test_whitespace_insensitive_exact_match(self):
        code, _, err, _, _ = self.run_fetch(self.argv(" 카카오 뱅크"), happy())
        self.assertEqual(code, 0, err)

    # --- 사업보고서 없음 ---

    def test_no_annual_report_exit_2_keeps_company_json(self):
        r = happy()
        r["list.json"] = status_json("013", "조회된 데이타가 없습니다.")
        code, _, err, net, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 2)
        self.assertIn("사업보고서 없음 — 감사보고서만 내는 회사일 수 있음", err)
        self.assertTrue((self.out / "company.json").is_file())
        self.assertFalse((self.out / "manifest.json").exists())
        self.assertNotIn("document.xml", net.endpoints())

    def test_empty_list_exit_2(self):
        r = happy()
        r["list.json"] = json.dumps({"status": "000", "message": "정상", "list": []}).encode()
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 2)

    # --- API 오류 ---

    def test_status_020_exit_6(self):
        r = happy()
        r["list.json"] = status_json("020", "요청 제한을 초과하였습니다.")
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 6)
        self.assertIn("020", err)
        self.assertIn("요청 한도", err)

    def test_status_010_json_says_key_problem(self):
        r = happy()
        r["company.json"] = status_json("010", "등록되지 않은 키입니다.")
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 6)
        self.assertIn("키 문제", err)
        self.assertIn("010", err)
        self.assertIn("crtfc_key=***", err)

    def test_corpcode_error_xml_instead_of_zip(self):
        r = happy()
        r["corpCode.xml"] = error_xml("010", "등록되지 않은 키입니다.")
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 6)
        self.assertIn("키 문제", err)
        self.assertFalse((self.cache / "corpCode.zip").exists(), "에러 XML 을 캐시하면 안 된다")

    def test_document_error_xml_reads_status(self):
        r = happy()
        r["document.xml"] = error_xml("014", "파일이 존재하지 않습니다.")
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 6)
        self.assertIn("014", err)
        self.assertIn("파일이 존재하지 않습니다", err)

    def test_document_zip_without_body_exit_6(self):
        r = happy()
        r["document.xml"] = zip_bytes({f"{RCEPT}_00760.xml": b"<x/>"})
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 6)
        self.assertIn("본문", err)

    def test_status_901_exit_6(self):
        r = happy()
        r["company.json"] = status_json("901", "만료")
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 6)
        self.assertIn("키 문제", err)

    def test_non_json_response_exit_6(self):
        r = happy()
        r["company.json"] = b"<html>maintenance</html>"
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 6)
        self.assertIn("JSON", err)

    # --- 네트워크 ---

    def test_url_error_exit_7(self):
        r = happy()
        r["list.json"] = urllib.error.URLError("Name or service not known")
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 7)
        self.assertIn("네트워크 오류", err)
        self.assertIn("crtfc_key=***", err)

    def test_timeout_exit_7(self):
        r = happy()
        r["document.xml"] = TimeoutError("timed out")
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 7)

    def test_http_429_exit_6_and_other_http_exit_7(self):
        r = happy()
        r["list.json"] = urllib.error.HTTPError("https://x", 429, "Too Many Requests", {}, None)
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 6)
        self.assertIn("429", err)
        r["list.json"] = urllib.error.HTTPError("https://x", 503, "Service Unavailable", {}, None)
        code, _, err, _, _ = self.run_fetch(self.argv(), r)
        self.assertEqual(code, 7)
        self.assertIn("503", err)

    # --- 키 ---

    def test_no_key_exit_5_with_signup_url(self):
        code, _, err, net, _ = self.run_fetch(self.argv(), happy(), env={}, cwd=str(self.root))
        self.assertEqual(code, 5)
        self.assertIn(dart_fetch.KEY_URL, err)
        self.assertEqual(net.calls, [])

    def test_key_from_dotenv(self):
        (self.root / ".env").write_text(f'OTHER=1\nexport DART_API_KEY="{KEY}"\n', encoding="utf-8")
        self.assertEqual(dart_fetch.load_key({}, str(self.root)), KEY)
        code, _, err, _, _ = self.run_fetch(self.argv(), happy(), env={"ADD_COMPANY_CACHE": str(self.cache)}, cwd=str(self.root))
        self.assertEqual(code, 0, err)

    def test_env_key_wins_over_dotenv(self):
        (self.root / ".env").write_text("DART_API_KEY=fromfile\n", encoding="utf-8")
        self.assertEqual(dart_fetch.load_key({"DART_API_KEY": "fromenv"}, str(self.root)), "fromenv")

    def test_mask(self):
        self.assertEqual(dart_fetch.mask(f"https://x/api/list.json?crtfc_key={KEY}&corp_code=1"), "https://x/api/list.json?crtfc_key=***&corp_code=1")
        self.assertEqual(dart_fetch.mask("https://x/api/corpCode.xml?crtfc_key=abc"), "https://x/api/corpCode.xml?crtfc_key=***")

    def test_user_agent_header(self):
        req = dart_fetch.build_request("https://opendart.fss.or.kr/api/list.json?crtfc_key=x")
        self.assertEqual(req.get_header("User-agent"), "research-role/0.1 (+python-urllib)")

    # --- 캐시 ---

    def test_corpcode_cache_reused_then_expires(self):
        code, _, err, net, _ = self.run_fetch(self.argv(), happy())
        self.assertEqual(code, 0, err)
        self.assertIn("corpCode.xml", net.endpoints())
        code, _, err, net, _ = self.run_fetch(self.argv(), happy())
        self.assertEqual(code, 0, err)
        self.assertNotIn("corpCode.xml", net.endpoints(), "7일 안이면 캐시")
        old = time.time() - 8 * 86400
        os.utime(self.cache / "corpCode.zip", (old, old))
        code, _, err, net, _ = self.run_fetch(self.argv(), happy())
        self.assertEqual(code, 0, err)
        self.assertEqual(net.endpoints()[0], "corpCode.xml", "7일 지나면 다시 받는다")

    # --- 단위 ---

    def test_report_year(self):
        self.assertEqual(dart_fetch.report_year("사업보고서 (2024.12)", "20250317"), (2024, "report_nm"))
        self.assertEqual(dart_fetch.report_year("[기재정정]사업보고서 (2023.03)", "20230630"), (2023, "report_nm"))
        self.assertEqual(dart_fetch.report_year("사업보고서", "20250317"), (2024, "rcept_dt-1"))
        with self.assertRaises(dart_fetch.DartError):
            dart_fetch.report_year(None, None)

    def test_latest_report_by_rcept_dt(self):
        items = json.loads(list_json())["list"]
        self.assertEqual(dart_fetch.latest_report(items)["rcept_no"], RCEPT)

    def test_save_document_strips_zip_paths(self):
        out = self.root / "doc"
        out.mkdir()
        zb = zip_bytes({f"sub/../{RCEPT}.xml": b"<a/>", f"dir/{RCEPT}_00760.xml": b"<b/>"})
        body, atts = dart_fetch.save_document(zb, RCEPT, out)
        self.assertEqual(body, f"{RCEPT}.xml")
        self.assertEqual(atts, [f"{RCEPT}_00760.xml"])
        self.assertEqual(sorted(p.name for p in out.iterdir()), [f"{RCEPT}.xml", f"{RCEPT}_00760.xml"])

    def test_parse_corp_codes_without_eng_name(self):
        xml = b'<result><list><corp_code>00000001</corp_code><corp_name>A</corp_name><stock_code> </stock_code><modify_date>20200101</modify_date></list></result>'
        corps = dart_fetch.parse_corp_codes(zip_bytes({"CORPCODE.xml": xml}))
        self.assertEqual(corps, [{"corp_code": "00000001", "corp_name": "A", "corp_eng_name": "", "stock_code": "", "modify_date": "20200101"}])


class TablesCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        p = self.root / name
        p.write_bytes(data)
        return str(p)

    def run_tables(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = dart_tables.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_parse_num(self):
        self.assertEqual(dart_tables.parse_num("2,345"), 2345)
        self.assertEqual(dart_tables.parse_num("5.3"), 5.3)
        self.assertEqual(dart_tables.parse_num(" 101,000,000 "), 101000000)
        for v in ["-", "", None, "해당사항없음", "abc", "3년 2개월"]:
            self.assertIsNone(dart_tables.parse_num(v), v)

    def test_emp_table_merges_sexes_and_computes_total(self):
        tbl, notes = dart_tables.emp_table(emp_rows("2024"))
        self.assertEqual(tbl[0], "| 부문 | 정규직 | 계약직 | 합계 | 평균근속(년) | 1인평균급여(원) |")
        self.assertEqual(tbl[2], "| 전사 | 3,545 | 120 | 3,665 | 남 5.3 / 여 4.1 | 남 101,000,000 / 여 83,000,000 |")
        self.assertEqual(tbl[3], "| 해외 |  |  |  |  |  |", "'-'·빈값·해당사항없음은 빈 셀")
        self.assertEqual(tbl[4], "| 합계 (계산) | 3,545 | 120 | 3,665 |  |  |")
        self.assertEqual(len(tbl), 5)
        self.assertTrue(any("계산" in n for n in notes))
        self.assertTrue(any("성별 행을 더한 값" in n for n in notes))

    def test_emp_table_uses_total_row_from_data(self):
        tbl, notes = dart_tables.emp_table(emp_rows("2023", with_total=True))
        self.assertEqual(tbl[-1], "| 합계 | 3,545 | 120 | 3,665 | 4.9 | 95,000,000 |")
        self.assertFalse(any("계산" in l for l in tbl))
        self.assertFalse(any("계산" in n for n in notes))

    def test_sum_mismatch_shows_both(self):
        tbl, _ = dart_tables.emp_table(emp_rows("2024", mismatch=True))
        self.assertIn("| 전사 | 3,545 | 120 | 3,715 (정규직+계약직=3,665) |", tbl[2])

    def test_non_numeric_count_is_kept_verbatim_not_summed(self):
        rows = emp_rows("2024")
        rows[0]["rgllbr_co"] = "약 2,000명"
        tbl, _ = dart_tables.emp_table(rows)
        self.assertIn("| 전사 | 약 2,000명 / 1,200 |", tbl[2])

    def test_sex_total_row_inside_group_is_used_not_added(self):
        rows = emp_rows("2024")[:2] + [dict(emp_rows("2024")[0], sexdstn="합계", rgllbr_co="3,545", cnttk_co="120", sm="3,665", avrg_cnwk_sdytrn="4.9", jan_salary_am="95,000,000")]
        tbl, _ = dart_tables.emp_table(rows)
        self.assertEqual(tbl[2], "| 전사 | 3,545 | 120 | 3,665 | 4.9 | 95,000,000 |")

    def test_render_years_ascending_with_sources(self):
        a = self.write("empSttus-2024.json", emp_json("2024"))
        b = self.write("empSttus-2023.json", emp_json("2023", with_total=True))
        md = dart_tables.render([a, b], None)
        self.assertLess(md.index("### 2023\n"), md.index("### 2024\n"))
        self.assertIn(f"출처: OpenDART empSttus, 사업연도 2023, rcept_no {RCEPT} (결산기준일 2023-12-31)", md)
        self.assertIn(f"출처: OpenDART empSttus, 사업연도 2024, rcept_no {RCEPT} (결산기준일 2024-12-31)", md)
        self.assertTrue(md.startswith("## 직원 현황\n"))

    def test_fixed_headings_for_role_anchor(self):
        a = self.write("empSttus-2024.json", emp_json("2024"))
        e = self.write("exctvSttus-2024.json", exec_json())
        lines = dart_tables.render([a], e).splitlines()
        self.assertEqual([l for l in lines if l.startswith("#")], ["## 직원 현황", "### 2024", "## 임원 현황"])

    def test_year_falls_back_to_stlm_dt(self):
        p = self.write("whatever.json", emp_json("2021"))
        self.assertIn("### 2021\n", dart_tables.render([p], None))

    def test_exec_table(self):
        p = self.write("exctvSttus-2024.json", exec_json())
        md = dart_tables.render([], p)
        lines = md.splitlines()
        self.assertEqual(lines[0], "## 임원 현황")
        self.assertEqual(lines[2], "| 이름 | 직위 | 등기여부 | 상근여부 | 담당업무 | 주요경력 |")
        self.assertEqual(lines[4], "| 정신아 | 대표이사 | 등기임원 | 상근 | 대표이사 | 카카오벤처스 대표 / 보스턴컨설팅그룹 |")
        self.assertEqual(lines[5], "| 홍길동 | 부사장\\|CTO | 미등기임원 | 상근 | 기술총괄 |  |")
        self.assertIn(f"출처: OpenDART exctvSttus, 사업연도 2024, rcept_no {RCEPT}", md)

    def test_cli_writes_out_file(self):
        a = self.write("empSttus-2024.json", emp_json("2024"))
        e = self.write("exctvSttus-2024.json", exec_json())
        out = self.root / "sub" / "people-tables.md"
        code, so, err = self.run_tables(["--emp", a, "--exec", e, "--out", str(out)])
        self.assertEqual(code, 0, err)
        md = out.read_text(encoding="utf-8")
        self.assertIn("## 직원 현황", md)
        self.assertIn("## 임원 현황", md)
        self.assertIn(str(out), so)

    def test_cli_skips_013_and_exits_2_when_nothing_left(self):
        a = self.write("empSttus-2022.json", status_json("013", "조회된 데이타가 없습니다."))
        b = self.write("empSttus-2024.json", emp_json("2024"))
        code, so, err = self.run_tables(["--emp", a, b])
        self.assertEqual(code, 0, err)
        self.assertIn("건너뜀", err)
        self.assertIn("### 2024\n", so)
        code, so, err = self.run_tables(["--emp", a])
        self.assertEqual(code, 2)
        self.assertIn("없음", err)

    def test_cli_bad_json_exit_3(self):
        a = self.write("empSttus-2024.json", b"{not json")
        code, _, err = self.run_tables(["--emp", a])
        self.assertEqual(code, 3)
        self.assertIn("JSON 읽기 실패", err)

    def test_cli_requires_some_input(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                dart_tables.main(["--out", "x.md"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
