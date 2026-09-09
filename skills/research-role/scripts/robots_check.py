#!/usr/bin/env python3
"""호스트의 robots.txt 를 받아 경로마다 허용/차단을 찍는다. 전부 허용일 때만 종료 0.

    python3 robots_check.py <host> <path>... [--save FILE]
    python3 robots_check.py --file robots.txt <path>...

`ClaudeBot` → `anthropic-ai` → `*` 순으로 첫 번째 있는 블록 하나를 적용한다. 연속된 User-agent 줄은
한 그룹이고 규칙은 그룹 전체에 붙는다. 경로는 가장 긴 매치가 이기고, 같은 길이면 Allow 가 이긴다.
robots.txt 가 없으면(404) 허용이다. 403·WAF 페이지처럼 받지 못한 경우는 확인 불가로 종료 2 —
확인 못 한 호스트는 직접 접근하지 않는다.

stdout: 적용한 UA 블록, 경로마다 `<path> 허용|차단`, 있으면 `Sitemap:` 줄. 표준 라이브러리만 쓴다.

종료 코드: 0 전부 허용 / 1 하나라도 차단 / 2 robots.txt 를 받지 못함(상태코드 stderr) / 5 인자 오류.
fetch 를 뒤에 `&&` 로 이으면 판정이 fetch 를 막는다.
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request

UA = "research-role/0.1 (+python-urllib)"
AGENTS = ("claudebot", "anthropic-ai", "*")


def parse(text: str) -> dict:
    """UA(소문자) → [(allow|disallow, 경로)] 목록. 연속된 User-agent 줄은 한 그룹."""
    blocks: dict = {}
    group: list = []
    in_rules = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if in_rules:
                group, in_rules = [], False
            group.append(value.lower())
            blocks.setdefault(value.lower(), [])
        elif key in ("allow", "disallow") and group:
            in_rules = True
            for ua in group:
                blocks[ua].append((key, value))
    return blocks


def sitemaps(text: str) -> list:
    return [
        line.split(":", 1)[1].strip()
        for line in text.splitlines()
        if line.split("#", 1)[0].strip().lower().startswith("sitemap:")
    ]


def judge(text: str, paths: list) -> tuple:
    """(적용한 UA 또는 None, [(path, 허용 여부)]). 블록이 없으면 전부 허용."""
    blocks = parse(text)
    ua = next((a for a in AGENTS if a in blocks), None)
    if ua is None:
        return None, [(p, True) for p in paths]
    rules = blocks[ua]
    verdicts = []
    for p in paths:
        dis = max((len(v) for k, v in rules if k == "disallow" and v and p.startswith(v)), default=-1)
        alw = max((len(v) for k, v in rules if k == "allow" and v and p.startswith(v)), default=-1)
        verdicts.append((p, not (dis >= 0 and dis > alw)))
    return ua, verdicts


def fetch(host: str) -> tuple:
    """(상태코드, 본문). 404 는 (404, '')."""
    req = urllib.request.Request(f"https://{host}/robots.txt", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except (urllib.error.URLError, OSError) as e:
        sys.stderr.write(f"네트워크 오류: {e}\n")
        return 0, ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="robots.txt 판정. 전부 허용일 때만 종료 0.")
    ap.add_argument("host", nargs="?", help="호스트(예: careers.kakao.com). --file 이면 생략")
    ap.add_argument("paths", nargs="*", help="확인할 경로(예: / /jobs)")
    ap.add_argument("--file", help="받아 둔 robots.txt 를 판정")
    ap.add_argument("--save", help="받은 robots.txt 를 이 경로에 둔다")
    a = ap.parse_args(argv)

    paths = list(a.paths)
    if a.file:
        if a.host:
            paths.insert(0, a.host)
        text = open(a.file, encoding="utf-8", errors="replace").read()
    else:
        if not a.host:
            ap.print_usage(sys.stderr)
            return 5
        code, text = fetch(a.host)
        if code == 404:
            text = ""
        elif code != 200:
            sys.stderr.write(f"robots.txt 를 받지 못함: HTTP {code} — 확인 불가, 직접 접근하지 않는다\n")
            return 2
        if a.save:
            open(a.save, "w", encoding="utf-8").write(text)
    if not paths:
        paths = ["/"]

    ua, verdicts = judge(text, paths)
    print(f"블록: {ua if ua else '없음(robots 없음 또는 비어 있음) → 허용'}")
    for p, ok in verdicts:
        print(f"{p} {'허용' if ok else '차단'}")
    for s in sitemaps(text):
        print(f"Sitemap: {s}")
    return 0 if all(ok for _, ok in verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
