#!/usr/bin/env python3
"""repo_facts.py 의 출력 형식 테스트. 임시 git 저장소를 만들어 돌린다. 표준 라이브러리만."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "repo_facts.py")
ME = "me@example.com"
OTHER = "other@example.com"


def sh(cwd, *args, email=ME, name="Me"):
    env = dict(os.environ, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email,
               GIT_AUTHOR_DATE="2026-01-01T00:00:00+09:00", GIT_COMMITTER_DATE="2026-01-01T00:00:00+09:00")
    return subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, text=True, env=env).stdout


def write(cwd, rel, text):
    path = os.path.join(cwd, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def commit(cwd, rel, text, msg, email=ME, name="Me"):
    write(cwd, rel, text)
    sh(cwd, "add", "-A")
    sh(cwd, "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg, email=email, name=name)
    return sh(cwd, "rev-parse", "HEAD").strip()


def run(repo, out, *extra):
    return subprocess.run([sys.executable, SCRIPT, repo, "--out", out, *extra], capture_output=True, text=True)


class RepoFactsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.repo = os.path.join(cls.tmp.name, "repo")
        os.makedirs(cls.repo)
        sh(cls.repo, "init", "-q")
        cls.c1 = commit(cls.repo, "README.md", "# demo\n\n주문 도메인 예제\n", "init: 프로젝트를 연다")
        cls.c2 = commit(cls.repo, "src/app.py", "def f():\n    return 1\n", "app: 주문 계산을 더한다\n\n왜: 정산 오류 재현.\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
        cls.c3 = commit(cls.repo, "tests/test_app.py", "def test_f():\n    assert True\n", "app: 정산 회귀 테스트를 붙인다")
        cls.c4 = commit(cls.repo, "src/other.py", "x = 1\n", "other: 다른 사람 작업", email=OTHER, name="Other")
        write(cls.repo, "CLAUDE.md", "# 규칙\n")
        write(cls.repo, ".github/workflows/test.yml", "name: test\n")
        write(cls.repo, "Dockerfile", "FROM python\n")
        cls.c5 = commit(cls.repo, "evals/cases.json", "[]\n", "ci: 워크플로와 에이전트 설정을 둔다")
        sh(cls.repo, "-c", "commit.gpgsign=false", "revert", "--no-edit", cls.c4)
        cls.c6 = sh(cls.repo, "rev-parse", "HEAD").strip()
        sh(cls.repo, "tag", "v0.1.0")
        cls.out = os.path.join(cls.tmp.name, "out")
        proc = run(cls.repo, cls.out, "--author", ME)
        assert proc.returncode == 0, proc.stderr
        cls.stdout = proc.stdout
        with open(os.path.join(cls.out, "summary.json"), encoding="utf-8") as fh:
            cls.summary = json.load(fh)
        with open(os.path.join(cls.out, "commits.json"), encoding="utf-8") as fh:
            cls.commits = json.load(fh)
        cls.by_sha = {c["sha"]: c for c in cls.commits}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_stdout_is_one_line_summary(self):
        self.assertEqual(len(self.stdout.strip().splitlines()), 1)
        self.assertIn("커밋 6", self.stdout)

    def test_summary_counts(self):
        s = self.summary
        self.assertEqual(s["commit_count"], 6)
        self.assertEqual(s["mine_count"], 5)
        self.assertEqual(s["revert_count"], 1)
        self.assertEqual(s["identities"], [ME])
        self.assertEqual(s["head"], self.c6)
        self.assertEqual([a["email"] for a in s["authors"]], [ME, OTHER])
        self.assertEqual(s["authors"][0]["commits"], 5)
        self.assertEqual([t["name"] for t in s["tags"]], ["v0.1.0"])

    def test_summary_markers(self):
        m = self.summary["markers"]
        self.assertEqual(m["readme"], "README.md")
        self.assertIn("주문 도메인 예제", self.summary["readme_head"])
        self.assertEqual(m["agent_config"], ["CLAUDE.md"])
        self.assertEqual(m["ci"], [".github/workflows/test.yml"])
        self.assertEqual(m["evals"], ["evals/cases.json"])
        self.assertEqual(m["deploy"], ["Dockerfile"])
        self.assertEqual(m["tests"], 1)
        self.assertEqual(self.summary["files"]["by_ext"][".py"], 2, "되돌림이 other.py 를 지웠다")

    def test_commit_fields(self):
        c = self.by_sha[self.c2]
        for key in ("sha", "short", "date", "author_name", "author_email", "parents", "is_merge", "is_revert",
                    "subject", "body", "trailers", "mine", "stats", "touches", "files"):
            self.assertIn(key, c)
        self.assertEqual(c["subject"], "app: 주문 계산을 더한다")
        self.assertIn("정산 오류 재현", c["body"])
        self.assertEqual(c["trailers"]["Co-Authored-By"], ["Claude <noreply@anthropic.com>"])
        self.assertTrue(c["mine"])
        self.assertEqual(c["files"], [{"path": "src/app.py", "added": 2, "deleted": 0}])
        self.assertEqual(c["stats"], {"files": 1, "added": 2, "deleted": 0})

    def test_touches_and_flags(self):
        self.assertEqual(self.by_sha[self.c3]["touches"]["tests"], 1)
        self.assertFalse(self.by_sha[self.c4]["mine"])
        c5 = self.by_sha[self.c5]
        self.assertEqual(c5["touches"]["ci"], 1)
        self.assertEqual(c5["touches"]["agent_config"], 1)
        self.assertEqual(c5["touches"]["evals"], 1)
        self.assertEqual(c5["touches"]["deploy"], 1)
        self.assertTrue(self.by_sha[self.c6]["is_revert"])
        self.assertEqual(self.commits[0]["sha"], self.c6, "최신 커밋이 앞이다")

    def test_since_limits_range(self):
        out = os.path.join(self.tmp.name, "out-since")
        proc = run(self.repo, out, "--since", self.c3)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(os.path.join(out, "summary.json"), encoding="utf-8") as fh:
            s = json.load(fh)
        self.assertEqual(s["range"], f"{self.c3}..HEAD")
        self.assertEqual(s["commit_count"], 3)
        self.assertIsNone(s["mine_count"], "--author 없으면 null")
        with open(os.path.join(out, "commits.json"), encoding="utf-8") as fh:
            self.assertTrue(all(c["mine"] is None for c in json.load(fh)))

    def test_errors_exit_2(self):
        self.assertEqual(run(self.tmp.name, os.path.join(self.tmp.name, "x")).returncode, 2)
        self.assertEqual(run(self.repo, os.path.join(self.tmp.name, "y"), "--since", "deadbeef").returncode, 2)
        self.assertEqual(run(os.path.join(self.tmp.name, "nope"), os.path.join(self.tmp.name, "z")).returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
