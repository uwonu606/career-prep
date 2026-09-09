#!/usr/bin/env python3
"""git 저장소에서 사실을 구조화해 JSON 으로 낸다. 표준 라이브러리와 git 만 쓴다.

    python3 repo_facts.py <repo_dir> --out <dir> [--since <sha>] [--author <email>]...

<dir> 에 두 파일을 쓴다.
  summary.json  저장소 한 장 — 기간·저자·태그·파일 분포·흔적 표지(CI·테스트·에이전트 설정·evals·배포)
  commits.json  커밋 목록 — 한 건마다 저자·본문·트레일러·바뀐 파일·되돌림 여부·본인 여부·건드린 영역

--since <sha> 를 주면 그 커밋 뒤(sha..HEAD)만 낸다. --author 는 여러 번 줄 수 있고,
하나라도 주면 커밋마다 mine 이 true/false 로 채워지고 안 주면 null 이다.

종료 코드: 0 성공 · 2 인자·저장소 오류.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from typing import Dict, List, Optional

RS, US = "\x1e", "\x1f"

TEST_PAT = re.compile(r"(^|/)(tests?|__tests__|spec)/|(^|/)test_[^/]*\.py$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$")
CI_PAT = re.compile(r"^\.github/workflows/|^\.gitlab-ci\.yml$|^Jenkinsfile$|^\.circleci/|^\.travis\.yml$|^azure-pipelines\.yml$|^bitbucket-pipelines\.yml$")
DOC_PAT = re.compile(r"\.(md|rst|adoc)$|^docs?/", re.I)
AGENT_PAT = re.compile(r"(^|/)(CLAUDE|AGENTS|GEMINI)\.md$|^\.claude/|^\.cursor/|^\.cursorrules$|^\.windsurfrules$|^\.mcp\.json$|^\.github/copilot-instructions\.md$|^\.aider|^\.codex/", re.I)
EVAL_PAT = re.compile(r"(^|/)(evals?|evaluations?|benchmarks?)/", re.I)
ADR_PAT = re.compile(r"(^|/)(adrs?|decisions)/|(^|/)adr-\d+|(^|/)\d{3,4}-[a-z0-9-]+\.md$", re.I)
DEPLOY_NAMES = {"Dockerfile", "Procfile", "fly.toml", "vercel.json", "netlify.toml", "serverless.yml", "app.yaml", "render.yaml"}
DEPLOY_PAT = re.compile(r"^docker-compose[^/]*\.ya?ml$|^compose\.ya?ml$|(^|/)(k8s|kubernetes|helm|terraform|deploy|deployment)/|\.tf$|(^|/)Dockerfile(\.|$)")
MANIFESTS = {"package.json", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "Gemfile", "composer.json", "mix.exs", "pubspec.yaml", "CMakeLists.txt", "Makefile"}
TRAILER_PAT = re.compile(r"^([A-Za-z][A-Za-z-]*): (.+)$")


def die(msg: str, code: int = 2) -> None:
    print(f"repo_facts: {msg}", file=sys.stderr)
    sys.exit(code)


def git(repo: str, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and proc.returncode != 0:
        die(f"git {' '.join(args)} 실패: {proc.stderr.strip()}")
    return proc.stdout


def parse_trailers(body: str) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for line in body.splitlines():
        m = TRAILER_PAT.match(line.strip())
        if m:
            out.setdefault(m.group(1), []).append(m.group(2).strip())
    return out


def classify(path: str) -> Dict[str, bool]:
    return {
        "tests": bool(TEST_PAT.search(path)),
        "ci": bool(CI_PAT.search(path)),
        "docs": bool(DOC_PAT.search(path)),
        "agent_config": bool(AGENT_PAT.search(path)),
        "evals": bool(EVAL_PAT.search(path)),
        "deploy": os.path.basename(path) in DEPLOY_NAMES or bool(DEPLOY_PAT.search(path)),
    }


def read_commits(repo: str, rng: str, authors: List[str]) -> List[dict]:
    fmt = RS + US.join(["%H", "%h", "%aI", "%an", "%ae", "%P", "%s", "%B"]) + US
    raw = git(repo, "log", rng, "--numstat", "--date=iso-strict", f"--format={fmt}")
    mine_set = {a.lower() for a in authors}
    commits: List[dict] = []
    for rec in raw.split(RS):
        if not rec.strip():
            continue
        parts = rec.split(US)
        if len(parts) < 9:
            continue
        sha, short, date, an, ae, parents, subject, body, rest = parts[:9]
        files = []
        added = deleted = 0
        for line in rest.splitlines():
            m = re.match(r"^(\d+|-)\t(\d+|-)\t(.+)$", line)
            if not m:
                continue
            a = 0 if m.group(1) == "-" else int(m.group(1))
            d = 0 if m.group(2) == "-" else int(m.group(2))
            path = m.group(3)
            if " => " in path:  # rename: "old => new" 또는 "dir/{old => new}/x"
                path = re.sub(r"\{[^{}]* => ([^{}]*)\}", r"\1", path)
                if " => " in path:
                    path = path.split(" => ", 1)[1]
                path = path.replace("//", "/")
            files.append({"path": path, "added": a, "deleted": d})
            added += a
            deleted += d
        body = body.strip("\n")
        trailers = parse_trailers(body)
        touches = {k: 0 for k in ("tests", "ci", "docs", "agent_config", "evals", "deploy")}
        for f in files:
            for k, v in classify(f["path"]).items():
                touches[k] += int(v)
        commits.append({
            "sha": sha,
            "short": short,
            "date": date,
            "author_name": an,
            "author_email": ae,
            "parents": parents.split() if parents else [],
            "is_merge": len(parents.split()) > 1,
            "is_revert": subject.startswith("Revert") or "This reverts commit" in body,
            "subject": subject,
            "body": body,
            "trailers": trailers,
            "mine": (ae.lower() in mine_set) if mine_set else None,
            "stats": {"files": len(files), "added": added, "deleted": deleted},
            "touches": touches,
            "files": files,
        })
    return commits


def read_summary(repo: str, commits: List[dict], rng: str, since: Optional[str], authors: List[str]) -> dict:
    tracked = [p for p in git(repo, "ls-files").splitlines() if p]
    by_ext: Counter = Counter()
    markers = {"agent_config": [], "ci": [], "evals": [], "adr": [], "deploy": [], "manifests": [], "readme": None, "docs_dirs": []}
    test_files = 0
    for p in tracked:
        ext = os.path.splitext(p)[1].lower() or "(없음)"
        by_ext[ext] += 1
        c = classify(p)
        if c["tests"]:
            test_files += 1
        if c["agent_config"]:
            markers["agent_config"].append(p)
        if c["ci"]:
            markers["ci"].append(p)
        if c["evals"]:
            markers["evals"].append(p)
        if ADR_PAT.search(p):
            markers["adr"].append(p)
        if c["deploy"]:
            markers["deploy"].append(p)
        base = os.path.basename(p)
        if base in MANIFESTS:
            markers["manifests"].append(p)
        if markers["readme"] is None and re.match(r"^readme(\.[a-z]+)?$", base, re.I) and "/" not in p:
            markers["readme"] = p
        top = p.split("/", 1)[0]
        if top.lower() in ("docs", "doc") and top not in markers["docs_dirs"]:
            markers["docs_dirs"].append(top)
    markers["tests"] = test_files
    for k in ("agent_config", "ci", "evals", "adr", "deploy", "manifests"):
        markers[k] = sorted(set(markers[k]))[:50]

    readme_head = None
    if markers["readme"]:
        try:
            with open(os.path.join(repo, markers["readme"]), encoding="utf-8", errors="replace") as fh:
                readme_head = "".join(fh.readlines()[:80])
        except OSError:
            readme_head = None

    author_stats: Dict[str, dict] = {}
    for c in commits:
        key = c["author_email"].lower()
        a = author_stats.setdefault(key, {"name": c["author_name"], "email": c["author_email"], "commits": 0, "first": c["date"], "last": c["date"]})
        a["commits"] += 1
        a["first"] = min(a["first"], c["date"])
        a["last"] = max(a["last"], c["date"])
    authors_out = sorted(author_stats.values(), key=lambda a: -a["commits"])

    tags = []
    for line in git(repo, "for-each-ref", "refs/tags", "--sort=-creatordate", "--format=%(refname:short)\t%(creatordate:iso-strict)").splitlines():
        if "\t" in line:
            name, date = line.split("\t", 1)
            tags.append({"name": name, "date": date})

    remote = git(repo, "remote", "get-url", "origin", check=False).strip() or None
    head = git(repo, "rev-parse", "HEAD").strip()
    dates = [c["date"] for c in commits]
    return {
        "repo": os.path.abspath(repo),
        "remote": remote,
        "head": head,
        "since": since,
        "range": rng,
        "commit_count": len(commits),
        "merge_count": sum(1 for c in commits if c["is_merge"]),
        "revert_count": sum(1 for c in commits if c["is_revert"]),
        "mine_count": sum(1 for c in commits if c["mine"]) if authors else None,
        "first_commit_date": min(dates) if dates else None,
        "last_commit_date": max(dates) if dates else None,
        "identities": authors,
        "authors": authors_out,
        "tags": tags[:100],
        "files": {"count": len(tracked), "by_ext": dict(by_ext.most_common(15))},
        "markers": markers,
        "readme_head": readme_head,
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--out", required=True, help="summary.json·commits.json 을 쓸 디렉토리")
    ap.add_argument("--since", help="이 커밋 뒤만 (sha..HEAD)")
    ap.add_argument("--author", action="append", default=[], help="본인 이메일. 여러 번 가능")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.repo):
        die(f"디렉토리가 없다: {args.repo}")
    if subprocess.run(["git", "-C", args.repo, "rev-parse", "--git-dir"], capture_output=True).returncode != 0:
        die(f"git 저장소가 아니다: {args.repo}")
    if subprocess.run(["git", "-C", args.repo, "rev-parse", "--verify", "-q", "HEAD"], capture_output=True).returncode != 0:
        die("커밋이 하나도 없다")
    rng = "HEAD"
    if args.since:
        if subprocess.run(["git", "-C", args.repo, "cat-file", "-e", f"{args.since}^{{commit}}"], capture_output=True).returncode != 0:
            die(f"--since 커밋을 찾을 수 없다: {args.since}")
        rng = f"{args.since}..HEAD"

    commits = read_commits(args.repo, rng, args.author)
    summary = read_summary(args.repo, commits, rng, args.since, args.author)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(args.out, "commits.json"), "w", encoding="utf-8") as fh:
        json.dump(commits, fh, ensure_ascii=False, indent=1)

    mine = f", 본인 {summary['mine_count']}" if summary["mine_count"] is not None else ""
    print(f"커밋 {summary['commit_count']}{mine}, 되돌림 {summary['revert_count']}, 저자 {len(summary['authors'])}, "
          f"파일 {summary['files']['count']}, 테스트 파일 {summary['markers']['tests']}, "
          f"에이전트 설정 {len(summary['markers']['agent_config'])}, CI {len(summary['markers']['ci'])} → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
