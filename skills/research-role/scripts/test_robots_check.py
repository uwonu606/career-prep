#!/usr/bin/env python3
"""robots_check.py 테스트. 네트워크 없이 문자열로 돈다.

    python3 test_robots_check.py            또는        python3 -m unittest test_robots_check
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import robots_check  # noqa: E402


class Judge(unittest.TestCase):
    def test_claudebot_block_wins_over_star(self):
        txt = "User-agent: *\nAllow: /\n\nUser-agent: ClaudeBot\nDisallow: /\n"
        ua, v = robots_check.judge(txt, ["/", "/jobs"])
        self.assertEqual(ua, "claudebot")
        self.assertEqual(v, [("/", False), ("/jobs", False)])

    def test_group_of_agents_shares_rules(self):
        txt = "User-agent: anthropic-ai\nUser-agent: GPTBot\nDisallow: /private\n\nUser-agent: *\nDisallow:\n"
        ua, v = robots_check.judge(txt, ["/private/x", "/public"])
        self.assertEqual(ua, "anthropic-ai")
        self.assertEqual(v, [("/private/x", False), ("/public", True)])

    def test_longest_match_and_allow_tie(self):
        txt = "User-agent: *\nDisallow: /\nAllow: /homepage/\n"
        _, v = robots_check.judge(txt, ["/", "/homepage/a.png", "/x"])
        self.assertEqual(v, [("/", False), ("/homepage/a.png", True), ("/x", False)])

    def test_empty_disallow_means_allow(self):
        _, v = robots_check.judge("User-agent: *\nDisallow:\n", ["/"])
        self.assertEqual(v, [("/", True)])

    def test_no_block_allows(self):
        ua, v = robots_check.judge("", ["/a"])
        self.assertIsNone(ua)
        self.assertEqual(v, [("/a", True)])

    def test_sitemaps_and_comments(self):
        txt = "# c\nSitemap: https://h/s.xml\nUser-agent: * # x\nDisallow: /p # y\n"
        self.assertEqual(robots_check.sitemaps(txt), ["https://h/s.xml"])
        _, v = robots_check.judge(txt, ["/p/1"])
        self.assertEqual(v, [("/p/1", False)])


class Cli(unittest.TestCase):
    def run_file(self, text, paths):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "robots.txt")
            Path(p).write_text(text, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = robots_check.main(["--file", p] + paths)
            return code, out.getvalue()

    def test_exit_1_when_any_blocked(self):
        code, out = self.run_file("User-agent: *\nDisallow: /jobs\n", ["/", "/jobs"])
        self.assertEqual(code, 1)
        self.assertIn("/ 허용", out)
        self.assertIn("/jobs 차단", out)

    def test_exit_0_when_all_allowed(self):
        code, out = self.run_file("User-agent: *\nDisallow:\nSitemap: https://h/s.xml\n", ["/"])
        self.assertEqual(code, 0)
        self.assertIn("Sitemap: https://h/s.xml", out)

    def test_default_path_is_root(self):
        code, out = self.run_file("User-agent: *\nDisallow: /\n", [])
        self.assertEqual(code, 1)
        self.assertIn("/ 차단", out)


if __name__ == "__main__":
    unittest.main()
