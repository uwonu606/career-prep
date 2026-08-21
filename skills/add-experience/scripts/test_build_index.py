#!/usr/bin/env python3
"""build_index.py 가 무엇을 읽고 무엇을 내는지 고정한다.

    python3 test_build_index.py

frontmatter 가 진실이고 index.md 는 파생 캐시다. 그래서 이 파일은 둘을 고정한다 —
파서가 schema.md 문면을 읽는 것과, index.md 의 출력 형식. 스킬이 index 를 읽고
시작하므로 형식 회귀는 채굴 품질로 전이된다.

어휘는 fixture 로 만든다. 실물 references/vocabulary.md 에 형식 단언을 걸면 태그를
하나 늘리는 무관한 변경이 CI 를 빨갛게 만든다. 실물은 스모크 하나로만 본다.

표준 라이브러리만 쓴다. 매번 임시 career/ 를 만들고 지운다.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "build_index.py")
REAL_VOCAB = Path(HERE).parent / "references" / "vocabulary.md"

_spec = importlib.util.spec_from_file_location("build_index_under_test", SCRIPT)
bi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bi)

VOCABULARY = """# 앵커와 어휘

## 역량

| 태그 | 여는 질문 |
| --- | --- |
| 디버깅 | "원인을 못 찾아서 오래 붙잡고 있었던 에러가 있었나요?" |
| 갈등 | "팀에서 의견이 갈렸던 적이 있었나요?" |

## 기술 주제

| 태그 | |
| --- | --- |
| 동시성 | |
| 성능 | |
"""

# schema.md 의 에피소드 템플릿 문면 그대로 — 인라인 주석 포함
SCHEMA_EPISODE = """---
id: concurrent-payment-lock
title: 동시 결제로 재고가 음수가 된 버그
projects: [secondhand-market]      # 0개(프로젝트 밖) · 1개 · 2개 이상(걸친 사건) 모두 정상
related: []                        # 이어지는 다른 에피소드 id
date: 2025-04
skills: [동시성, 디버깅]            # references/vocabulary.md 의 어휘
evidence: verified                 # verified | recalled | unacquired
evidence_links:
  - https://github.com/x/pull/42
open_questions:
  - 재현 테스트 횟수의 정확한 수치
---

## 맥락
"""


class CareerCase(unittest.TestCase):
    def setUp(self):
        self.career = tempfile.mkdtemp(prefix="build_index_test_")
        self.addCleanup(shutil.rmtree, self.career, True)
        os.makedirs(os.path.join(self.career, "episodes"))
        os.makedirs(os.path.join(self.career, "projects"))
        self.vocab = os.path.join(self.career, "vocabulary.md")
        with open(self.vocab, "w", encoding="utf-8") as f:
            f.write(VOCABULARY)

    def episode(self, slug, body):
        with open(os.path.join(self.career, "episodes", slug + ".md"), "w",
                  encoding="utf-8") as f:
            f.write(body)

    def project(self, slug, body):
        d = os.path.join(self.career, "projects", slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "project.md"), "w", encoding="utf-8") as f:
            f.write(body)

    def build(self, career=None, vocab=None):
        argv = [sys.executable, SCRIPT, career or self.career, vocab or self.vocab]
        done = subprocess.run(argv, capture_output=True, text=True)
        return done.returncode, done.stdout + done.stderr

    def index(self):
        rc, out = self.build()
        self.assertEqual(rc, 0, out)
        with open(os.path.join(self.career, "index.md"), encoding="utf-8") as f:
            return f.read()

    def section(self, text, name):
        """index.md 는 표가 셋이고 id 가 표를 가로질러 겹친다. 절 단위로 자른다."""
        head = "## " + name
        self.assertIn(head, text)
        return text.split(head, 1)[1].split("\n## ", 1)[0]

    def row(self, text, first_cell, section="에피소드"):
        for line in self.section(text, section).splitlines():
            if line.startswith("| " + first_cell + " |"):
                return [c.strip() for c in line.strip("|").split("|")]
        self.fail("%s 절에서 행을 찾지 못했다: %s\n%s" % (section, first_cell, text))

    def coverage(self, text, tag):
        for line in text.splitlines():
            if line.startswith("**") and (tag + " ") in line:
                for cell in line.split(bi.BAR):
                    head, _, count = cell.rpartition(" ")
                    if head.endswith(tag):
                        return int(count)
        self.fail("커버리지에서 %s 를 찾지 못했다\n%s" % (tag, text))


class schema_md_문면_그대로가_읽힌다(CareerCase):
    """schema.md 가 보여주는 템플릿을 복사하면 그대로 동작해야 한다.

    안 받으면 조용히 비는 것이 아니라 값이 글자 단위로 부서진 채 종료 코드 0 이 난다.
    """

    def setUp(self):
        super().setUp()
        self.episode("concurrent-payment-lock", SCHEMA_EPISODE)
        self.project("secondhand-market",
                     "---\nid: secondhand-market\ntitle: 중고거래 플랫폼\n"
                     "period: 2025-03 ~ 2025-04 (6주)\nrole: 백엔드\n---\n")
        self.text = self.index()

    def test_인라인_주석이_붙은_리스트가_리스트로_읽힌다(self):
        fm = bi.parse_frontmatter(SCHEMA_EPISODE)
        self.assertEqual(fm["projects"], ["secondhand-market"])
        self.assertEqual(fm["skills"], ["동시성", "디버깅"])
        self.assertEqual(fm["related"], [])

    def test_인라인_주석이_스칼라_값에_남지_않는다(self):
        self.assertEqual(bi.parse_frontmatter(SCHEMA_EPISODE)["evidence"], "verified")

    def test_주석_본문이_index_로_새지_않는다(self):
        body = self.section(self.text, "에피소드")
        for token in ("프로젝트 밖", "references/vocabulary.md", "recalled | unacquired"):
            self.assertNotIn(token, body)
        self.assertNotIn("\\|", self.text)

    def test_역량이_글자로_쪼개지지_않는다(self):
        cells = self.row(self.text, "concurrent-payment-lock")
        self.assertEqual(cells[2], "secondhand-market")
        self.assertEqual(cells[3], "동시성, 디버깅")

    def test_프로젝트의_에피소드_수가_센다(self):
        self.assertEqual(self.row(self.text, "secondhand-market", "프로젝트")[4], "1")

    def test_캔_축은_커버리지에서_0_이_아니다(self):
        self.assertEqual(self.coverage(self.text, "디버깅"), 1)
        self.assertEqual(self.coverage(self.text, "동시성"), 1)


class 주석_규칙은_따옴표와_URL_을_건드리지_않는다(CareerCase):
    def test_따옴표_안의_우물정은_값이다(self):
        fm = bi.parse_frontmatter('---\nid: a\ntitle: "PR #3 은 왜 닫혔나"\n---\n')
        self.assertEqual(fm["title"], "PR #3 은 왜 닫혔나")

    def test_URL_앵커는_잘리지_않는다(self):
        fm = bi.parse_frontmatter(
            "---\nid: a\nevidence_links:\n  - https://github.com/x/pull/42#c1\n---\n")
        self.assertEqual(fm["evidence_links"], ["https://github.com/x/pull/42#c1"])

    def test_목록_항목_안의_우물정은_주석이_아니다(self):
        """open_questions 는 산문이고 '#42' 는 되찾을 경로다. 여기서 자르면 뜻이 사라진다."""
        fm = bi.parse_frontmatter(
            "---\nid: a\nopen_questions:\n  - 결과 미도달 — PR #42 에서 되찾을 것\n---\n")
        self.assertEqual(fm["open_questions"], ["결과 미도달 — PR #42 에서 되찾을 것"])


class 목록_항목이_여러_줄로_이어진다(CareerCase):
    """schema.md 는 park한 칸에 '어느 각도를 썼는지와 되찾을 경로'를 함께 적게 한다."""

    TEXT = """---
id: a
title: 제목
open_questions:
  - 결과 — 3회 시도 전부 미도달.
    되찾을 경로: git log 2026-01-06
  - 재현 횟수
---
"""

    def test_이어짐_줄이_앞_항목에_붙는다(self):
        fm = bi.parse_frontmatter(self.TEXT)
        self.assertEqual(len(fm["open_questions"]), 2)
        self.assertIn("되찾을 경로: git log 2026-01-06", fm["open_questions"][0])

    def test_이어짐_줄이_가짜_최상위_키를_만들지_않는다(self):
        self.assertNotIn("되찾을 경로", bi.parse_frontmatter(self.TEXT))

    def test_중첩_맵은_이어짐으로_빨려들지_않는다(self):
        fm = bi.parse_frontmatter("---\nid: a\nlinks:\n  repo: ~\n---\n")
        self.assertEqual(fm["links"], {"repo": ""})

    def test_미해결_수가_이어짐_줄에_흔들리지_않는다(self):
        self.episode("a", self.TEXT)
        self.assertEqual(self.row(self.index(), "a")[5], "2")


class 블록_스칼라를_읽는다(CareerCase):
    """schema.md 가 쓰지 않는 문법이지만, YAML 로 보이는 것에 사람이 쓰는 형태다."""

    def test_folded_는_공백으로_잇는다(self):
        fm = bi.parse_frontmatter("---\nid: a\ntitle: >\n  긴 제목이\n  두 줄이다\n---\n")
        self.assertEqual(fm["title"], "긴 제목이 두 줄이다")

    def test_literal_은_개행을_지킨다(self):
        fm = bi.parse_frontmatter("---\nid: a\ntitle: |\n  첫 줄\n  둘째 줄\n---\n")
        self.assertEqual(fm["title"], "첫 줄\n둘째 줄")

    def test_블록이_끝나면_다음_키가_이어진다(self):
        fm = bi.parse_frontmatter("---\nid: a\ntitle: >\n  제목\nskills: [디버깅]\n---\n")
        self.assertEqual(fm["skills"], ["디버깅"])

    def test_표는_한_행이_한_줄이다(self):
        self.episode("a", "---\nid: a\ntitle: |\n  첫 줄\n  둘째 줄\n---\n")
        text = self.index()
        body = self.section(text, "에피소드").strip().splitlines()
        self.assertEqual(len(body), 3, body)  # 머리글 · 구분선 · 행 하나
        self.assertEqual(self.row(text, "a")[1], "첫 줄 둘째 줄")


class 경계_밖은_빈_칸으로_보인다(CareerCase):
    """지원 경계 밖 입력은 사라지는 대신 눈에 보이는 빈 칸(—)으로 남는다."""

    def setUp(self):
        super().setUp()
        self.episode("no-close", "---\nid: no-close\ntitle: 닫는 대시가 없다\n\n## 맥락\n")
        self.episode("deep-nest", "---\nid: deep-nest\ntitle: 두 단계 중첩\n"
                                  "links:\n  repo:\n    url: https://x\n---\n")
        self.episode("unclosed", "---\nid: unclosed\ntitle: 안 닫힘\nskills: [동시성\n---\n")
        self.text = self.index()

    def test_파이썬_None_이_표로_새지_않는다(self):
        self.assertNotIn("None", self.text)

    def test_읽지_못한_파일도_행으로_남는다(self):
        self.assertEqual(self.row(self.text, "no-close")[1], "—")

    def test_두_단계_중첩은_지원하지_않지만_행은_남는다(self):
        self.assertEqual(self.row(self.text, "deep-nest")[1], "두 단계 중첩")

    def test_안_닫힌_대괄호는_역량으로_세지_않는다(self):
        self.assertEqual(self.coverage(self.text, "동시성"), 0)


class index_md_의_형식이_고정된다(CareerCase):
    """스킬이 index 를 읽고 시작하므로 형식 회귀는 채굴 품질로 전이된다."""

    def setUp(self):
        super().setUp()
        self.episode("a", "---\nid: a\ntitle: 첫째\nprojects: [p]\nskills: [디버깅]\n"
                          "evidence: recalled\nrelated: [b]\n---\n")
        self.episode("b", "---\nid: b\ntitle: 둘째\nprojects: [p]\nskills: [디버깅]\n"
                          "evidence: verified\n---\n")
        self.project("p", "---\nid: p\ntitle: 프로젝트\nperiod: 2025\nrole: 백엔드\n---\n")
        self.text = self.index()

    def test_직접_고치지_말라는_경고로_시작한다(self):
        head = self.text.splitlines()[:2]
        self.assertTrue(head[0].startswith("<!--") and "자동 생성" in head[0], head)
        self.assertIn("build_index.py", head[1])

    def test_네_개의_절이_이_순서로_있다(self):
        heads = [l for l in self.text.splitlines() if l.startswith("## ")]
        self.assertEqual(heads,
                         ["## 프로젝트", "## 에피소드", "## 이어지는 사건", "## 역량 커버리지"])

    def test_표_머리글이_고정된다(self):
        self.assertIn("| id | 제목 | 기간 | 역할 | 에피소드 수 |", self.text)
        self.assertIn("| id | 제목 | 프로젝트 | 역량 | 증거 | 미해결 |", self.text)
        self.assertIn("| 에피소드 | 선행 | 후속 |", self.text)

    def test_이어지는_사건은_후속을_역으로_계산한다(self):
        self.assertEqual(self.row(self.text, "b", "이어지는 사건"), ["b", "—", "a"])

    def test_없는_id_를_가리키면_물음표가_붙는다(self):
        self.episode("c", "---\nid: c\ntitle: 셋째\nrelated: [없는것]\n---\n")
        self.assertEqual(self.row(self.index(), "c", "이어지는 사건")[1], "없는것(?)")

    def test_커버리지는_어휘_전체를_0_포함해_나열한다(self):
        line = [l for l in self.text.splitlines() if l.startswith("**역량:**")][0]
        self.assertIn("디버깅 2", line)
        self.assertIn("갈등 0", line)
        self.assertEqual(line.count(bi.BAR), 1)

    def test_어휘_밖의_태그도_커버리지에_남는다(self):
        self.episode("d", "---\nid: d\ntitle: 넷째\nskills: [없는태그]\n---\n")
        self.assertEqual(self.coverage(self.index(), "없는태그"), 1)

    def test_stdout_이_센_것을_말한다(self):
        rc, out = self.build()
        self.assertEqual(rc, 0)
        self.assertIn("episodes=2", out)
        self.assertIn("projects=1", out)


class 저장소가_비어_있어도_만든다(CareerCase):
    def test_에피소드가_0개여도_index_가_생긴다(self):
        text = self.index()
        self.assertIn("## 역량 커버리지", text)
        self.assertEqual(self.coverage(text, "디버깅"), 0)


class 실물_vocabulary_md_가_읽힌다(unittest.TestCase):
    """표 형식이 바뀌면 커버리지가 통째로 비고, 0인 축을 보는 앵커 선택이 무력해진다.

    형식 단언은 fixture 쪽에 있다. 여기서는 실물이 파싱되는지만 본다 —
    태그를 늘리는 변경에 이 파일이 흔들리지 않게.
    """

    def test_소제목별로_태그가_나온다(self):
        groups = bi.load_vocabulary(REAL_VOCAB)
        self.assertGreaterEqual(len(groups), 2)
        for name, tags in groups.items():
            self.assertTrue(tags, name)
            self.assertNotIn("태그", tags)


class 잘못_부르면_트레이스백_대신_쓰임을_낸다(CareerCase):
    def test_인자가_없으면_쓰임과_1_을_낸다(self):
        done = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("쓰임:", done.stdout + done.stderr)
        self.assertNotIn("Traceback", done.stdout + done.stderr)

    def test_career_가_없으면_트레이스백이_아니라_1_이다(self):
        rc, out = self.build(career=os.path.join(self.career, "없는곳"))
        self.assertEqual(rc, 1)
        self.assertNotIn("Traceback", out)

    def test_career_를_대신_만들지_않는다(self):
        """오타 경로에 조용히 두 번째 저장소가 생기면 커버리지가 그만큼 갈라진다."""
        missing = os.path.join(self.career, "없는곳")
        self.build(career=missing)
        self.assertFalse(os.path.exists(missing))

    def test_vocabulary_가_없으면_1_이다(self):
        rc, out = self.build(vocab=os.path.join(self.career, "없다.md"))
        self.assertEqual(rc, 1)
        self.assertNotIn("Traceback", out)

    def test_오류는_한_채널로만_나온다(self):
        done = subprocess.run(
            [sys.executable, SCRIPT, os.path.join(self.career, "없는곳"), self.vocab],
            capture_output=True, text=True)
        self.assertTrue(bool(done.stdout) != bool(done.stderr), (done.stdout, done.stderr))

    def test_import_해도_실행되지_않는다(self):
        done = subprocess.run(
            [sys.executable, "-c",
             "import importlib.util as u;s=u.spec_from_file_location('m',%r);"
             "m=u.module_from_spec(s);s.loader.exec_module(m)" % SCRIPT],
            capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout, "")


if __name__ == "__main__":
    unittest.main(verbosity=1)
