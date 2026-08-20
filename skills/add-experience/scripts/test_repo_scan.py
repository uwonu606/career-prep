#!/usr/bin/env python3
"""repo_scan.py 가 재료층 밖으로 새지 않는지 고정한다.

    python3 test_repo_scan.py

내용층(파일 경로·커밋 메시지·문서 본문)이 stdout 에 한 글자도 나오지 않는 것이
이 파일의 첫 번째 일이다. 나머지는 재료 자체가 틀리지 않는지 본다.

표준 라이브러리만 쓴다. 매번 임시 저장소를 만들고 지운다.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "repo_scan.py")

LAST_LINE = "파일 경로·커밋 메시지는 재료가 아니다. 이 출력에 없는 것은 묻지 않는다."


def _git(repo, *args, **env):
    e = dict(os.environ)
    e.update(env)
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, env=e)


def commit(repo, when, mail, path, message, name="T", committed=None):
    """author 시각·author 이메일·건드린 파일·커밋 메시지를 지정해 커밋 하나를 만든다."""
    full = os.path.join(repo, path)
    parent = os.path.dirname(full)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(full, "a", encoding="utf-8") as f:
        f.write("x\n")
    _git(repo, "add", "-A")
    _git(repo, "-c", "commit.gpgsign=false", "commit", "-m", message,
         GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=(committed or when),
         GIT_AUTHOR_NAME=name, GIT_COMMITTER_NAME=name,
         GIT_AUTHOR_EMAIL=mail, GIT_COMMITTER_EMAIL=mail)


def scan(repo, mail=None):
    argv = [sys.executable, SCRIPT, repo] + ([mail] if mail else [])
    done = subprocess.run(argv, capture_output=True, text=True)
    return done.stdout


def rows(out):
    """재료표의 데이터 행만 (날짜, 시각, 커밋수, 묶음번호) 로 돌려준다."""
    got = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 6 and parts[0][:2] == "20" and "/" in parts[3]:
            got.append((parts[0], parts[1], parts[2], parts[3]))
    return got


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="repo_scan_test_")
        _git(self.repo, "init", "-q")
        self.addCleanup(shutil.rmtree, self.repo, True)


class 내용층은_출력되지_않는다(RepoCase):
    """AC: 스캔 출력에 파일 경로·커밋 메시지·문서 본문이 없다."""

    PATH_TOKEN = "PlayerHealthZZZ"
    MSG_TOKEN = "사운드파일을몰아넣었다ZZZ"
    PROSE_TOKEN = "미해결명령이91에서41로준다ZZZ"

    def setUp(self):
        super().setUp()
        commit(self.repo, "2026-01-05T22:42:00", "solo@ex.com",
               "src/%s.cs" % self.PATH_TOKEN, "feat: %s" % self.MSG_TOKEN)
        doc = os.path.join(self.repo, "docs", "adr", "0001.md")
        os.makedirs(os.path.dirname(doc), exist_ok=True)
        with open(doc, "w", encoding="utf-8") as f:
            f.write("# 선택과 기각한 대안\n\n%s\n" % self.PROSE_TOKEN)
        commit(self.repo, "2026-01-06T00:55:00", "solo@ex.com",
               "docs/adr/0001.md", "docs: %s" % self.MSG_TOKEN)
        self.out = scan(self.repo)

    def test_파일_경로가_없다(self):
        self.assertNotIn(self.PATH_TOKEN, self.out)
        self.assertNotIn(".cs", self.out)
        self.assertNotIn("docs/", self.out)

    def test_커밋_메시지가_없다(self):
        self.assertNotIn(self.MSG_TOKEN, self.out)
        self.assertNotIn("feat:", self.out)

    def test_문서_본문이_없다(self):
        self.assertNotIn(self.PROSE_TOKEN, self.out)
        self.assertNotIn("기각한 대안", self.out)

    def test_마지막_줄이_유지된다(self):
        # 이 줄은 데이터가 아니라 프롬프트 표면이다. 출력 형식을 고쳐도 남는다.
        self.assertEqual(self.out.rstrip().splitlines()[-1], LAST_LINE)


class author_가_한_명이면_묻지_않는다(RepoCase):
    def test_계정을_묻지_않는다(self):
        commit(self.repo, "2026-02-01T10:00:00", "solo@ex.com", "a", "m")
        out = scan(self.repo)
        self.assertNotIn("author 가 여럿", out)
        self.assertIn("== 재료 ==", out)


class author_가_여럿이면_목록을_내민다(RepoCase):
    def setUp(self):
        super().setUp()
        commit(self.repo, "2026-02-01T10:00:00", "me@ex.com", "a", "m")
        commit(self.repo, "2026-02-02T10:00:00", "you@ex.com", "b", "m")

    def test_목록을_내밀고_재료는_아직_없다(self):
        out = scan(self.repo)
        self.assertIn("author 가 여럿", out)
        self.assertIn("me@ex.com", out)
        self.assertIn("you@ex.com", out)
        self.assertNotIn("== 재료 ==", out)

    def test_같은_이메일의_이름_표기_여럿을_한_사람으로_센다(self):
        # AC: 그룹은 %ae 로 묶는다
        commit(self.repo, "2026-02-03T10:00:00", "me@ex.com", "c", "m", name="다른표기")
        commit(self.repo, "2026-02-04T10:00:00", "me@ex.com", "d", "m", name="또다른표기")
        out = scan(self.repo)
        self.assertIn("me@ex.com  커밋 3  (이름 표기 3종)", out)


class 고른_author_의_커밋만_센다(RepoCase):
    """--author 는 앵커 없는 정규식이라 남의 주소를 부분일치로 문다."""

    def test_부분문자열_이메일이_섞이지_않는다(self):
        commit(self.repo, "2026-02-01T10:00:00", "me@ex.com", "a", "m")
        commit(self.repo, "2026-02-02T10:00:00", "me@ex.com", "b", "m")
        for i, day in enumerate(("05", "06", "07")):
            commit(self.repo, "2026-02-%sT14:00:00" % day, "notme@ex.com", "g%d" % i, "m")
        out = scan(self.repo, "me@ex.com")
        self.assertIn("== 재료 ==  커밋 2 ", out)
        self.assertNotIn("2026-02-05", out)
        self.assertNotIn("2026-02-06", out)
        self.assertNotIn("2026-02-07", out)

    def test_점은_아무_글자가_아니다(self):
        commit(self.repo, "2026-03-01T10:00:00", "a.b@ex.com", "a", "m")
        commit(self.repo, "2026-03-02T10:00:00", "axb@ex.com", "b", "m")
        self.assertIn("== 재료 ==  커밋 1 ", scan(self.repo, "a.b@ex.com"))

    def test_더하기가_들어간_주소도_그대로_찾는다(self):
        mail = "309063630+uwonu606@users.noreply.github.com"
        commit(self.repo, "2026-03-01T10:00:00", mail, "a", "m")
        commit(self.repo, "2026-03-02T10:00:00", mail, "b", "m")
        commit(self.repo, "2026-03-03T10:00:00", "z@ex.com", "c", "m")
        self.assertIn("== 재료 ==  커밋 2 ", scan(self.repo, mail))


class author_시각이_커밋_순서와_어긋나도_버틴다(RepoCase):
    """리베이스·cherry-pick·--amend --date 를 거친 이력."""

    def setUp(self):
        super().setUp()
        # committer 시각은 단조, author 시각은 뒤섞임
        for author_at, committer_at, path in (
                ("2026-06-15T10:00:00", "2026-08-01T09:00:00", "b1"),
                ("2026-01-01T10:00:00", "2026-08-01T09:01:00", "b2"),
                ("2026-12-31T10:00:00", "2026-08-01T09:02:00", "b3"),
                ("2026-06-20T10:00:00", "2026-08-01T09:03:00", "b4")):
            commit(self.repo, author_at, "solo@ex.com", path, "m", committed=committer_at)
        self.out = scan(self.repo)

    def test_기간은_실제_최소와_최대다(self):
        self.assertIn("기간 2026-01-01 ~ 2026-12-31", self.out)

    def test_묶음번호가_날짜_안에서_유일하다(self):
        seen = {}
        for date, _span, _n, idx in rows(self.out):
            seen.setdefault(date, []).append(idx)
        for date, got in seen.items():
            self.assertEqual(len(got), len(set(got)), "%s 의 묶음번호가 겹친다: %s" % (date, got))


class 같은_날이_두_번_끊겨도_묶음번호가_겹치지_않는다(RepoCase):
    """리베이스로 같은 날짜가 이력에서 두 번 떨어져 나타나는 경우."""

    def setUp(self):
        super().setUp()
        for author_at, committer_at, path in (
                ("2026-07-01T10:00:00", "2026-07-10T09:00:00", "a1"),
                ("2026-07-02T12:00:00", "2026-07-10T09:01:00", "a2"),
                ("2026-07-01T10:00:00", "2026-07-10T09:02:00", "a3")):
            commit(self.repo, author_at, "solo@ex.com", path, "m", committed=committer_at)
        self.out = scan(self.repo)

    def test_07_01_의_묶음번호가_유일하다(self):
        got = [idx for date, _span, _n, idx in rows(self.out) if date == "2026-07-01"]
        self.assertEqual(len(got), len(set(got)), "묶음번호가 겹친다: %s" % got)

    def test_기간이_07_01에서_07_02다(self):
        self.assertIn("기간 2026-07-01 ~ 2026-07-02", self.out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
