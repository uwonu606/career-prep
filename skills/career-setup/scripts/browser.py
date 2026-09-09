#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.58.0"]
# ///
"""로그인 상태를 만들고, 그 상태로 페이지 하나를 읽는다.

  browser.py login <url>               창을 연다. 로그인하고 창을 닫으면 auth/<host>.json 이 남는다
  browser.py list                      auth/ 의 호스트·쿠키 수·가장 이른 만료
  browser.py open <url> [--html] [--out FILE] [--no-auth]
                                       URL 의 호스트에 맞는 auth 가 있으면 그 상태로, 헤드리스로 페이지 하나를 읽는다.
                                       stdout(또는 --out) 에 제목·최종 URL·본문 텍스트(--html 이면 HTML). 어느 auth 를 썼는지는 stderr.

auth/ 는 현재 디렉토리(데이터 디렉토리) 바로 아래다. 상태 파일의 내용은 이 스크립트만 읽는다.
종료 0 정상 / 2 페이지를 못 열음 / 3 크로미움 없음 / 5 인자 오류
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

AUTH_DIR = Path("auth")
NAV_TIMEOUT_MS = 30_000
SETTLE_MS = 1_500


def chromium_path() -> Path:
    env = os.environ.get("CHROMIUM_PATH")
    if env and Path(env).exists():
        return Path(env)
    hits = sorted(glob.glob(str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux64/chrome")))
    if hits:
        return Path(hits[-1])
    sys.stderr.write(
        "크로미움이 없습니다. `uv run --with playwright playwright install chromium` 으로 받거나 "
        "CHROMIUM_PATH 에 실행 파일 경로를 넣으세요.\n"
    )
    sys.exit(3)


def host_of(url: str) -> str:
    h = (urlparse(url).hostname or "").lower()
    if not h:
        sys.stderr.write(f"URL 에 호스트가 없습니다: {url}\n")
        sys.exit(5)
    return h[4:] if h.startswith("www.") else h


def auth_file_for(host: str) -> Path | None:
    """host 와 같거나 host 의 상위 도메인인 파일 중 가장 긴 것. 없으면 None."""
    best = None
    for f in AUTH_DIR.glob("*.json"):
        name = f.stem
        if host == name or host.endswith("." + name):
            if best is None or len(name) > len(best.stem):
                best = f
    return best


def summarize(state: dict) -> tuple[int, str]:
    cookies = state.get("cookies", [])
    exp = [c["expires"] for c in cookies if c.get("expires", -1) > 0]
    earliest = dt.datetime.fromtimestamp(min(exp)).strftime("%Y-%m-%d") if exp else "세션"
    return len(cookies), earliest


def cmd_login(url: str) -> int:
    from playwright.sync_api import sync_playwright

    exe = chromium_path()
    host = host_of(url)
    AUTH_DIR.mkdir(exist_ok=True)
    target = AUTH_DIR / f"{host}.json"
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(exe), headless=False)
        ctx = browser.new_context(storage_state=str(target) if target.exists() else None)
        page = ctx.new_page()
        page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="load")
        sys.stderr.write(f"창에서 로그인한 뒤 창을 닫으세요. 닫히면 {target} 이 남습니다.\n")
        last = None
        while browser.is_connected() and ctx.pages:
            try:
                last = ctx.storage_state()
            except Exception:
                break
            time.sleep(2)
        if last is None:
            sys.stderr.write("저장할 상태가 없습니다.\n")
            return 2
        target.write_text(json.dumps(last))
        try:
            browser.close()
        except Exception:
            pass
    n, earliest = summarize(last)
    print(f"{target} 저장 — 쿠키 {n}개, 가장 이른 만료 {earliest}")
    return 0


def cmd_list() -> int:
    chromium_path()
    files = sorted(AUTH_DIR.glob("*.json"))
    if not files:
        print("auth/ 비어 있음")
        return 0
    for f in files:
        n, earliest = summarize(json.loads(f.read_text()))
        print(f"{f.stem}\t쿠키 {n}개\t가장 이른 만료 {earliest}")
    return 0


def cmd_open(url: str, html: bool, out: str | None, no_auth: bool) -> int:
    from playwright.sync_api import Error as PwError, sync_playwright

    exe = chromium_path()
    host = host_of(url)
    auth = None if no_auth else auth_file_for(host)
    sys.stderr.write(f"auth: {auth} (규칙 예외 — 출처에 적을 것)\n" if auth else "auth: 없음\n")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(exe), headless=True)
        ctx = browser.new_context(storage_state=str(auth) if auth else None)
        page = ctx.new_page()
        try:
            resp = page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="load")
        except PwError as e:
            sys.stderr.write(f"못 열음: {e.message.splitlines()[0]}\n")
            browser.close()
            return 2
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except PwError:
            pass
        page.wait_for_timeout(SETTLE_MS)
        status = resp.status if resp else "~"
        body = page.content() if html else page.inner_text("body")
        head = f"# {page.title()}\nURL: {page.url}\nHTTP: {status}\n\n"
        browser.close()
    text = head + body
    if out:
        Path(out).write_text(text)
        sys.stderr.write(f"{out} 에 {len(text)}자\n")
    else:
        sys.stdout.write(text)
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="browser.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("login"); s.add_argument("url")
    sub.add_parser("list")
    s = sub.add_parser("open"); s.add_argument("url")
    s.add_argument("--html", action="store_true"); s.add_argument("--out"); s.add_argument("--no-auth", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "login":
        return cmd_login(a.url)
    if a.cmd == "list":
        return cmd_list()
    return cmd_open(a.url, a.html, a.out, a.no_auth)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
