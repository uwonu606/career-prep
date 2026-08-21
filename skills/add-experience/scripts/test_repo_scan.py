#!/usr/bin/env python3
"""repo_scan.py 가 재료층 밖으로 새지 않는지 고정한다.

    python3 test_repo_scan.py

내용층(파일 경로·커밋 메시지·문서 본문)이 stdout 에 한 글자도 나오지 않는 것이
이 파일의 첫 번째 일이다. 같은 내용층이 정리 파일에는 들어 있어야 한다 — 그 둘이
갈리는 자리를 함께 고정한다. 나머지는 재료 자체가 틀리지 않는지 본다.

표준 라이브러리만 쓴다. 매번 임시 저장소와 임시 career 를 만들고 지운다.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "repo_scan.py")
INDEX_SCRIPT = os.path.join(HERE, "build_index.py")

LAST_LINE = "파일 경로·커밋 메시지는 재료가 아니다. 이 출력에 없는 것은 묻지 않는다."
SAVED_PREFIX = "정리를 저장했다: "
TRUNCATED = "만 위에 표시했다"


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


def scan(repo, career, mail=None):
    argv = [sys.executable, SCRIPT, repo, career] + ([mail] if mail else [])
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


def scans_in(career):
    """career 안에 쌓인 정리 파일 목록."""
    return sorted(glob.glob(os.path.join(career, "projects", "*", "artifacts", "repo-scan-*.md")))


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="repo_scan_test_")
        _git(self.repo, "init", "-q")
        self.addCleanup(shutil.rmtree, self.repo, True)
        self.career = tempfile.mkdtemp(prefix="repo_scan_career_")
        self.addCleanup(shutil.rmtree, self.career, True)

    def saved(self, out):
        """stdout 마지막 줄이 알려준 정리 파일 경로."""
        last = out.rstrip().splitlines()[-1]
        self.assertTrue(last.startswith(SAVED_PREFIX), "마지막 줄이 경로가 아니다: %s" % last)
        return last[len(SAVED_PREFIX):]

    def scans(self):
        return scans_in(self.career)


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
        self.out = scan(self.repo, self.career)

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

    def test_프롬프트_표면이_유지되고_경로가_뒤에_붙는다(self):
        # LAST_LINE 은 데이터가 아니라 프롬프트 표면이다. 출력 형식을 고쳐도 남는다.
        # 이제 그 뒤에 정리 파일 경로가 붙으므로 "마지막 줄"이 아니라 "출력에 있다"로 잡는다.
        self.assertIn(LAST_LINE, self.out.splitlines())
        path = self.saved(self.out)
        self.assertTrue(os.path.isfile(path), "정리 파일이 없다: %s" % path)
        self.assertTrue(path.startswith(os.path.join(self.career, "projects") + os.sep), path)


class 정리_파일에는_내용층이_있다(RepoCase):
    """AC: stdout 과 정리 파일이 갈린다. 같은 것이 한쪽에만 있다."""

    PATH_TOKEN = "PlayerHealthQQZZ"
    MSG_TOKEN = "사운드파일을몰아넣었다QQZZ"
    BODY_TOKEN = "코루틴이겹쳐돌아서무적프레임이안먹었다QQZZ"

    def setUp(self):
        super().setUp()
        commit(self.repo, "2026-06-12T13:58:00", "solo@ex.com",
               "src/%s.cs" % self.PATH_TOKEN, "feat: %s" % self.MSG_TOKEN)
        commit(self.repo, "2026-06-12T14:09:00", "solo@ex.com", "src/combat/DamageGate.cs",
               "fix: 피격 판정이 두 번 들어가던 것\n\n%s\n플래그로 잠근다." % self.BODY_TOKEN)
        commit(self.repo, "2026-06-12T21:10:00", "solo@ex.com", "Assets/Fonts/atlas.asset",
               "fix: 빌드에서 폰트 아틀라스가 빠지던 것")
        commit(self.repo, "2026-06-14T10:02:00", "solo@ex.com", "README.md", "docs: 제출용 README")
        self.out = scan(self.repo, self.career)
        self.path = self.saved(self.out)
        with open(self.path, encoding="utf-8") as f:
            self.text = f.read()

    def test_제목과_본문과_경로가_파일에_있다(self):
        self.assertIn(self.MSG_TOKEN, self.text)
        self.assertIn(self.BODY_TOKEN, self.text)
        self.assertIn(self.PATH_TOKEN, self.text)
        self.assertIn("  본문: %s" % self.BODY_TOKEN, self.text)
        self.assertIn("  플래그로 잠근다.", self.text)   # 본문 이어지는 줄은 두 칸 들여쓴다

    def test_같은_것이_stdout_에는_없다(self):
        self.assertNotIn(self.MSG_TOKEN, self.out)
        self.assertNotIn(self.BODY_TOKEN, self.out)
        self.assertNotIn(self.PATH_TOKEN, self.out)

    def test_frontmatter_는_scanned_at_과_head_둘이다(self):
        head = subprocess.run(["git", "-C", self.repo, "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        self.assertIn("\nhead: %s\n" % head, self.text)     # 파일명은 단축, frontmatter 는 전체
        self.assertRegex(self.text, r"\nscanned_at: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\n")
        fm = self.text.split("---")[1]
        self.assertNotIn("prs_upto", fm)                     # #4 가 소유한다
        self.assertNotIn("issues_upto", fm)

    def test_묶음이_전량이고_시간순이다(self):
        got = [line for line in self.text.splitlines() if line.startswith("## ")]
        self.assertEqual(len(got), 3)
        self.assertEqual(got, sorted(got))


class HEAD_가_같으면_덮어쓰고_다르면_새_파일(RepoCase):
    """파일명이 HEAD 라서 같은 판을 다시 스캔해도 쌓이지 않는다."""

    def test_두_번_스캔해도_파일은_하나다(self):
        commit(self.repo, "2026-05-01T10:00:00", "solo@ex.com", "a", "m")
        scan(self.repo, self.career)
        scan(self.repo, self.career)
        self.assertEqual(len(self.scans()), 1, self.scans())

    def test_커밋이_늘면_새_파일이_생긴다(self):
        commit(self.repo, "2026-05-01T10:00:00", "solo@ex.com", "a", "m")
        scan(self.repo, self.career)
        commit(self.repo, "2026-05-02T10:00:00", "solo@ex.com", "b", "m")
        scan(self.repo, self.career)
        self.assertEqual(len(self.scans()), 2, self.scans())


class 영문_밖_이름은_해시로_갈린다(unittest.TestCase):
    """한글·악센트는 [^a-z0-9] 에 걸려 지워진다. 그대로 두면 다른 저장소가 같은 slug 를
    받아 정리가 한 디렉토리에 섞인다. 코드리뷰가 짚었고 실측으로 확인했다."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="repo_scan_nonascii_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.career = os.path.join(self.tmp, "career")
        os.makedirs(self.career)

    def _scan(self, name):
        repo = os.path.join(self.tmp, name)
        os.makedirs(repo)
        _git(repo, "init", "-q")
        commit(repo, "2026-05-01T10:00:00", "solo@ex.com", "a", "m")
        scan(repo, self.career)

    def projects(self):
        return sorted(os.listdir(os.path.join(self.career, "projects")))

    def test_한글_이름_둘이_같은_자리를_쓰지_않는다(self):
        self._scan("늑대인간")
        self._scan("프로젝트")
        self.assertEqual(len(self.projects()), 2, self.projects())
        self.assertNotIn("repo", self.projects())   # 옛 fallback 으로 뭉치지 않는다

    def test_숫자만_남는_이름도_갈린다(self):
        # '게임잼-2026' 은 빈 문자열이 아니라 '2026' 이 되어 fallback 도 안 탔다
        self._scan("게임잼-2026")
        self._scan("설계-2026")
        self.assertEqual(len(self.projects()), 2, self.projects())
        self.assertNotIn("2026", self.projects())

    def test_ASCII_이름은_해시가_안_붙는다(self):
        self._scan("My_Game.Jam")
        self.assertEqual(self.projects(), ["my-game-jam"])


class 시간_표기는_한_곳에서_나온다(unittest.TestCase):
    """재료표와 정리 파일이 같은 문자열을 써야 두 표면이 안 어긋난다."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="repo_scan_span_")
        self.addCleanup(shutil.rmtree, self.repo, True)
        _git(self.repo, "init", "-q")
        self.career = tempfile.mkdtemp(prefix="repo_scan_span_career_")
        self.addCleanup(shutil.rmtree, self.career, True)

    def test_묶음_시간_표기가_표와_파일에서_같다(self):
        commit(self.repo, "2026-05-01T10:05:00", "solo@ex.com", "a", "m1")
        commit(self.repo, "2026-05-01T10:40:00", "solo@ex.com", "a", "m2")
        out = scan(self.repo, self.career)
        f = scans_in(self.career)[0]
        body = open(f, encoding="utf-8").read()
        self.assertIn("10:05~10:40", out)
        self.assertIn("10:05~10:40", body)

    def test_한_커밋_묶음은_양쪽_다_단일_시각이다(self):
        commit(self.repo, "2026-06-01T09:00:00", "solo@ex.com", "b", "m")
        out = scan(self.repo, self.career)
        body = open(scans_in(self.career)[0], encoding="utf-8").read()
        self.assertNotIn("09:00~09:00", out)
        self.assertNotIn("09:00~09:00", body)


class slug_변환_규칙(unittest.TestCase):
    """저장소 디렉토리 이름이 projects/<slug>/ 를 정한다. realpath 기준이다."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="repo_scan_slug_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "My_Game.Jam")
        os.makedirs(self.repo)
        _git(self.repo, "init", "-q")
        commit(self.repo, "2026-05-01T10:00:00", "solo@ex.com", "a", "m")
        self.career = os.path.join(self.tmp, "career")
        os.makedirs(self.career)

    def projects(self):
        return sorted(os.listdir(os.path.join(self.career, "projects")))

    def test_소문자_kebab_이_된다(self):
        scan(self.repo, self.career)
        self.assertEqual(self.projects(), ["my-game-jam"])

    def test_심볼릭_링크로_불러도_한_건이다(self):
        scan(self.repo, self.career)
        link = os.path.join(self.tmp, "링크")
        os.symlink(self.repo, link)
        scan(link, self.career)
        self.assertEqual(self.projects(), ["my-game-jam"])


class 절단_표시(RepoCase):
    """표는 12개에서 잘린다. 잘렸다는 사실이 출력에 없으면 사용자가 그것을 모른다."""

    def test_묶음이_13이면_몇_개가_남았는지_말한다(self):
        for d in range(1, 14):
            commit(self.repo, "2026-09-%02dT10:00:00" % d, "solo@ex.com", "f%d" % d, "m")
        out = scan(self.repo, self.career)
        self.assertIn("묶음 13개 중 12개만 위에 표시했다. 나머지 1개는 정리 파일에 있다.", out)

    def test_묶음이_12_이하면_표시가_없다(self):
        for d in range(1, 5):
            commit(self.repo, "2026-09-%02dT10:00:00" % d, "solo@ex.com", "f%d" % d, "m")
        out = scan(self.repo, self.career)
        self.assertNotIn(TRUNCATED, out)
        self.assertIn(SAVED_PREFIX, out)


class author_가_여럿이면_정리_파일을_쓰지_않는다(RepoCase):
    """목록 분기에는 rows 가 없다. 이메일을 지정한 재실행이 쓴다."""

    def setUp(self):
        super().setUp()
        commit(self.repo, "2026-02-01T10:00:00", "me@ex.com", "a", "m")
        commit(self.repo, "2026-02-02T10:00:00", "you@ex.com", "b", "m")

    def test_목록_분기는_아무것도_안_남긴다(self):
        out = scan(self.repo, self.career)
        self.assertIn("author 가 여럿", out)
        self.assertNotIn(SAVED_PREFIX, out)
        self.assertEqual(self.scans(), [])
        self.assertFalse(os.path.isdir(os.path.join(self.career, "projects")))

    def test_이메일을_주면_그때_쓴다(self):
        out = scan(self.repo, self.career, "me@ex.com")
        self.assertIn(SAVED_PREFIX, out)
        self.assertEqual(len(self.scans()), 1)


class career_인자_검증(RepoCase):
    def _run(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)

    def test_career_를_빼면_쓰임을_낸다(self):
        r = self._run(self.repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("쓰임:", r.stdout)
        self.assertIn("<career 절대경로>", r.stdout)

    def test_없는_career_는_만들지_않고_1_을_낸다(self):
        # 1단계가 이미 만들었어야 한다. 오타 경로에 트리를 통째로 만들지 않는다.
        missing = os.path.join(self.career, "없는", "자리")
        r = self._run(self.repo, missing)
        self.assertEqual(r.returncode, 1)
        self.assertIn("career 디렉토리가 없다", r.stdout)
        self.assertFalse(os.path.exists(missing))


class project_md_없는_디렉토리가_index_를_안_깨뜨린다(RepoCase):
    """스캔이 만든 projects/<slug>/ 에는 project.md 가 없다. index 는 그것을 세지 않는다."""

    def test_스캔만_한_career_로_index_가_만들어진다(self):
        commit(self.repo, "2026-05-01T10:00:00", "solo@ex.com", "a", "m")
        os.makedirs(os.path.join(self.career, "episodes"), exist_ok=True)
        scan(self.repo, self.career)
        self.assertEqual(len(self.scans()), 1)
        r = subprocess.run([sys.executable, INDEX_SCRIPT, self.career],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("projects=0", r.stdout)
        self.assertTrue(os.path.isfile(os.path.join(self.career, "index.md")))


class author_가_한_명이면_묻지_않는다(RepoCase):
    def test_계정을_묻지_않는다(self):
        commit(self.repo, "2026-02-01T10:00:00", "solo@ex.com", "a", "m")
        out = scan(self.repo, self.career)
        self.assertNotIn("author 가 여럿", out)
        self.assertIn("== 재료 ==", out)


class author_가_여럿이면_목록을_내민다(RepoCase):
    def setUp(self):
        super().setUp()
        commit(self.repo, "2026-02-01T10:00:00", "me@ex.com", "a", "m")
        commit(self.repo, "2026-02-02T10:00:00", "you@ex.com", "b", "m")

    def test_목록을_내밀고_재료는_아직_없다(self):
        out = scan(self.repo, self.career)
        self.assertIn("author 가 여럿", out)
        self.assertIn("me@ex.com", out)
        self.assertIn("you@ex.com", out)
        self.assertNotIn("== 재료 ==", out)

    def test_같은_이메일의_이름_표기_여럿을_한_사람으로_센다(self):
        # AC: 그룹은 %ae 로 묶는다
        commit(self.repo, "2026-02-03T10:00:00", "me@ex.com", "c", "m", name="다른표기")
        commit(self.repo, "2026-02-04T10:00:00", "me@ex.com", "d", "m", name="또다른표기")
        out = scan(self.repo, self.career)
        self.assertIn("me@ex.com  커밋 3  (이름 표기 3종)", out)


class 고른_author_의_커밋만_센다(RepoCase):
    """--author 는 앵커 없는 정규식이라 남의 주소를 부분일치로 문다."""

    def test_부분문자열_이메일이_섞이지_않는다(self):
        commit(self.repo, "2026-02-01T10:00:00", "me@ex.com", "a", "m")
        commit(self.repo, "2026-02-02T10:00:00", "me@ex.com", "b", "m")
        for i, day in enumerate(("05", "06", "07")):
            commit(self.repo, "2026-02-%sT14:00:00" % day, "notme@ex.com", "g%d" % i, "m")
        out = scan(self.repo, self.career, "me@ex.com")
        self.assertIn("== 재료 ==  커밋 2 ", out)
        self.assertNotIn("2026-02-05", out)
        self.assertNotIn("2026-02-06", out)
        self.assertNotIn("2026-02-07", out)

    def test_점은_아무_글자가_아니다(self):
        commit(self.repo, "2026-03-01T10:00:00", "a.b@ex.com", "a", "m")
        commit(self.repo, "2026-03-02T10:00:00", "axb@ex.com", "b", "m")
        self.assertIn("== 재료 ==  커밋 1 ", scan(self.repo, self.career, "a.b@ex.com"))

    def test_더하기가_들어간_주소도_그대로_찾는다(self):
        mail = "309063630+uwonu606@users.noreply.github.com"
        commit(self.repo, "2026-03-01T10:00:00", mail, "a", "m")
        commit(self.repo, "2026-03-02T10:00:00", mail, "b", "m")
        commit(self.repo, "2026-03-03T10:00:00", "z@ex.com", "c", "m")
        self.assertIn("== 재료 ==  커밋 2 ", scan(self.repo, self.career, mail))


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
        self.out = scan(self.repo, self.career)

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
        self.out = scan(self.repo, self.career)

    def test_07_01_의_묶음번호가_유일하다(self):
        got = [idx for date, _span, _n, idx in rows(self.out) if date == "2026-07-01"]
        self.assertEqual(len(got), len(set(got)), "묶음번호가 겹친다: %s" % got)

    def test_기간이_07_01에서_07_02다(self):
        self.assertIn("기간 2026-07-01 ~ 2026-07-02", self.out)


class 잘못_부르면_트레이스백_대신_쓰임을_낸다(RepoCase):
    def _run(self, *args):
        done = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
        return done

    def test_인자가_없으면_쓰임과_1_을_낸다(self):
        r = self._run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("쓰임:", r.stdout)
        self.assertNotIn("Traceback", r.stderr)

    def test_저장소가_아니면_1_을_낸다(self):
        r = self._run(tempfile.gettempdir(), self.career)
        self.assertEqual(r.returncode, 1)

    def test_정상_저장소는_0_을_낸다(self):
        commit(self.repo, "2026-04-01T10:00:00", "solo@ex.com", "a", "m")
        self.assertEqual(self._run(self.repo, self.career).returncode, 0)

    def test_import_해도_실행되지_않는다(self):
        # __main__ 가드가 있어야 테스트가 함수를 직접 부를 수 있다
        import importlib.util
        spec = importlib.util.spec_from_file_location("rs_probe", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(callable(mod.commits))


if __name__ == "__main__":
    unittest.main(verbosity=2)
