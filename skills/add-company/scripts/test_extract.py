#!/usr/bin/env python3
"""dart_extract.py 회귀 테스트.

    python3 test_extract.py [fixtures_dir]
    python3 -m unittest test_extract        # scripts/ 디렉토리에서

픽스처 디렉토리는 인자 > $ADD_COMPANY_FIXTURES 로 정한다. 둘 다 없으면 픽스처 테스트는 건너뛰고(합성 테스트만 돈다)
이유를 출력한다 — 픽스처(타사 공시 원문, 수십 MB)는 이 공개 리포 밖에 두고 setup 스킬이 위치를 정한다.
기대값은 픽스처 옆 expect.json — 파일명 → {"ii_subsections", "viii_subsections", "has_rnd"}.
픽스처를 추가하면 expect.json 에도 한 줄 넣어야 한다(없으면 여기서 실패한다).
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dart_extract as dx  # noqa: E402

RAW_TAG = re.compile(r"<[A-Z][A-Z0-9-]*>")
SCRIPT = HERE / "dart_extract.py"


def default_fixtures():
    env = os.environ.get("ADD_COMPANY_FIXTURES")
    return Path(env) if env else None


FIXTURES = default_fixtures()


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8")


def synthetic_xml(path, body):
    path.write_text('<?xml version="1.0" encoding="utf-8"?>\n<DOCUMENT><BODY>' + body
                    + "</BODY></DOCUMENT>", encoding="utf-8")
    return path


class FixtureTests(unittest.TestCase):
    """픽스처 전부에 대해 파싱·절 식별·하위 개수·출력 위생을 본다."""

    @classmethod
    def setUpClass(cls):
        if FIXTURES is None or not FIXTURES.is_dir():
            raise unittest.SkipTest(
                f"픽스처 디렉토리 없음({FIXTURES}) — 인자 또는 ADD_COMPANY_FIXTURES 로 지정한다. 합성 테스트만 돈다.")
        cls.xmls = sorted(FIXTURES.glob("*.xml"))
        cls.expect = json.loads((FIXTURES / "expect.json").read_text(encoding="utf-8"))

    def test_fixtures_present(self):
        self.assertTrue(self.xmls, f"픽스처 XML 이 없습니다: {FIXTURES}")

    def test_every_fixture_has_expectation(self):
        for xml in self.xmls:
            self.assertIn(xml.name, self.expect, f"expect.json 에 {xml.name} 기대값이 없습니다")

    def test_parse_and_sections(self):
        for xml in self.xmls:
            with self.subTest(fixture=xml.name):
                want = self.expect[xml.name]
                root = dx.load(xml)  # 전처리 뒤 strict 파싱. 실패하면 ParseError 로 여기서 터진다
                ii, viii = dx.section_business(root), dx.section_people(root)
                self.assertIsNotNone(ii, "II. 사업의 내용 못 찾음")
                self.assertIsNotNone(viii, "VIII. 임원 및 직원 등에 관한 사항 못 찾음")
                self.assertEqual(len(dx.subsections(ii)), want["ii_subsections"])
                self.assertEqual(len(dx.subsections(viii)), want["viii_subsections"])
                self.assertEqual(dx.has_rnd(ii), want["has_rnd"])
                self.assertIsNotNone(dx.people_subsection(viii), "VIII 하위 '임원 및 직원 현황' 못 찾음")

    def test_markdown_outputs(self):
        for xml in self.xmls:
            with self.subTest(fixture=xml.name):
                root = dx.load(xml)
                business = dx.business_markdown(dx.section_business(root))
                viii = dx.section_people(root)
                people = dx.people_markdown(viii, dx.people_subsection(viii))
                for name, md in (("business", business), ("people", people)):
                    self.assertTrue(md.strip(), f"{name}.md 가 비었습니다")
                    leak = RAW_TAG.search(md)
                    self.assertIsNone(leak, f"{name}.md 에 원시 태그 누출: {leak}")
                    self.assertNotIn("\r", md)
                    self.assertNotRegex(md, r"\n{3,}", f"{name}.md 에 빈 줄이 연속됩니다")
                self.assertTrue(business.startswith("# II. 사업의 내용\n"))
                self.assertTrue(people.startswith("# VIII. 임원 및 직원 등에 관한 사항\n"))
                # 하위 2(임원의 보수 등) 제목이 들어오면 안 된다
                self.assertNotIn("임원의 보수", people.split("\n", 3)[2])

    def test_heading_format(self):
        """schema.md 가 앵커로 참조하는 형식: H1 은 고정 문자열, H2 는 하위 절 원문 TITLE 그대로."""
        for xml in self.xmls:
            with self.subTest(fixture=xml.name):
                root = dx.load(xml)
                ii, viii = dx.section_business(root), dx.section_people(root)
                sub = dx.people_subsection(viii)
                business = dx.business_markdown(ii)
                people = dx.people_markdown(viii, sub)
                b_heads = [l for l in business.splitlines() if l.startswith("#")]
                self.assertEqual([h for h in b_heads if h.startswith("# ")], ["# II. 사업의 내용"])
                self.assertEqual([h for h in b_heads if h.startswith("## ")],
                                 ["## " + t for t in dx.subsection_titles(ii)])
                p_heads = [l for l in people.splitlines() if l.startswith("#") and not l.startswith("###")]
                self.assertEqual(p_heads, ["# VIII. 임원 및 직원 등에 관한 사항", "## " + dx.heading_text(sub)])

    def test_cli_exit_0_and_rnd_notice(self):
        for xml in self.xmls:
            with self.subTest(fixture=xml.name), tempfile.TemporaryDirectory() as tmp:
                out, people = Path(tmp, "business.md"), Path(tmp, "people.md")
                r = run_cli(xml, "--out", out, "--people", people)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(out.read_text(encoding="utf-8").strip())
                self.assertTrue(people.read_text(encoding="utf-8").strip())
                self.assertEqual("연구개발 절 없음" in r.stderr, not self.expect[xml.name]["has_rnd"], r.stderr)

    def test_cli_stdout_without_out(self):
        r = run_cli(self.xmls[0])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("# II. 사업의 내용"))


class FailureTests(unittest.TestCase):
    """의도적 실패: 절이 없으면 2, 전처리 뒤에도 파싱이 안 되면 3."""

    def test_missing_sections_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml = synthetic_xml(Path(tmp, "no-sections.xml"),
                                '<SECTION-1><TITLE ATOC="Y">I. 회사의 개요</TITLE><P>본문</P></SECTION-1>')
            r = run_cli(xml, "--out", Path(tmp, "b.md"), "--people", Path(tmp, "p.md"))
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("II. 사업의 내용", r.stderr)
            self.assertIn("VIII.", r.stderr)
            self.assertFalse(Path(tmp, "b.md").exists())

    def test_one_section_found_still_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml = synthetic_xml(Path(tmp, "only-ii.xml"),
                                '<SECTION-1><TITLE ATOC="Y">Ⅱ. 사업의 내용</TITLE><P>본문</P></SECTION-1>')
            r = run_cli(xml, "--out", Path(tmp, "b.md"), "--people", Path(tmp, "p.md"))
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertEqual(Path(tmp, "b.md").read_text(encoding="utf-8"), "# II. 사업의 내용\n\n본문\n")
            self.assertFalse(Path(tmp, "p.md").exists())

    def test_parse_failure_exit_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml = Path(tmp, "broken.xml")
            xml.write_text('<?xml version="1.0" encoding="utf-8"?>\n<DOCUMENT><BODY><P>닫히지 않음</BODY>',
                           encoding="utf-8")
            r = run_cli(xml, "--out", Path(tmp, "b.md"))
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn("파싱 실패", r.stderr)


class UnitTests(unittest.TestCase):
    """전처리·표 평탄화의 규칙을 합성 입력으로 고정한다."""

    def test_preprocess_escapes_bare_ampersand(self):
        """dart4 원문은 F&B·M&A 의 홑 & 를 이스케이프하지 않는다(카카오 20260318001423, 속성값 안에서도).
        홑 & 만 &amp; 로 바꾸고, 이미 참조 꼴인 &amp; &#160; &#xA0; &cr; &foo; 는 이중 처리하지 않는다."""
        raw = ('<DOCUMENT><BODY><SECTION-1><TITLE ATOC="Y">II. 사업의 내용</TITLE>'
               '<P>S.M. F&B Development &amp; M&A &cr; &#160; &#xA0; &foo;</P>'
               '<TD ENG="KR Investment & Securities">x</TD></SECTION-1></BODY></DOCUMENT>')
        out = dx.preprocess(raw)
        el = dx.ET.fromstring(out)  # strict 파싱이 되면 일단 통과
        p = el.find(".//P").text
        self.assertIn("F&B", p)
        self.assertIn("M&A", p)
        self.assertIn("&foo;", p)
        self.assertNotIn("&amp;amp;", out)
        self.assertEqual(el.find(".//TD").get("ENG"), "KR Investment & Securities")

    def test_preprocess_makes_strict_parse_possible(self):
        raw = "<P>&cr;당기&nbsp;<당기> 1 &lt; 2 &foo;</P>"
        el = dx.ET.fromstring(dx.preprocess(raw))
        self.assertEqual(el.text, "\r당기\xa0<당기> 1 < 2 &foo;")

    def test_table_spans_flatten(self):
        table = dx.ET.fromstring(
            "<TABLE><THEAD>"
            '<TR><TH ROWSPAN="2">성명</TH><TH COLSPAN="2">직원 수</TH></TR>'
            "<TR><TH>남</TH><TH>여</TH></TR>"
            "</THEAD><TBODY>"
            '<TR><TD ROWSPAN="2">A|B</TD><TD>1</TD><TD>2</TD></TR>'
            "<TR><TD>3</TD></TR>"
            "</TBODY></TABLE>")
        self.assertEqual(dx.markdown_table(table), [
            "| 성명 | 직원 수 남 | 직원 수 여 |",
            "| --- | --- | --- |",
            "| A\\|B | 1 | 2 |",
            "|  | 3 |  |",
        ])

    def test_single_row_table_becomes_line(self):
        table = dx.ET.fromstring(
            '<TABLE><TBODY><TR><TD>(기준일 :</TD><TU AUNIT="BASE_DT">2022년</TU></TR></TBODY></TABLE>')
        self.assertEqual(dx.markdown_table(table), ["(기준일 : 2022년"])

    def test_heading_normalization_and_hash_escape(self):
        root = dx.ET.fromstring(
            "<DOCUMENT><BODY><SECTION-1>"
            "<TITLE ATOC=\"Y\">Ⅱ.  사업의   내용</TITLE>"
            "<SECTION-2><TITLE>4.  매출 및&#13;수주상황</TITLE><P>#1 주석</P></SECTION-2>"
            "</SECTION-1></BODY></DOCUMENT>")
        md = dx.business_markdown(dx.section_business(root))
        self.assertEqual(md, "# II. 사업의 내용\n\n## 4. 매출 및 수주상황\n\n\\#1 주석\n")

    def test_images_and_comments_dropped(self):
        sec = dx.ET.fromstring(
            '<SECTION-2><TITLE>1. 개요</TITLE><P>앞 <SPAN>글</SPAN> 뒤</P>'
            "<IMAGE><IMG>a.jpg</IMG><IMG-CAPTION>캡션</IMG-CAPTION></IMAGE><PGBRK/>"
            "<INSERTION><COMMENT>◆click◆</COMMENT>"
            "<LIBRARY><FILENAME>x</FILENAME><P>본문</P></LIBRARY></INSERTION>"
            "</SECTION-2>")
        blocks = []
        dx.render_section(sec, 2, blocks)
        self.assertEqual(blocks, ["## 1. 개요", "앞 글 뒤", "본문"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        FIXTURES = Path(sys.argv.pop(1))
    unittest.main()
