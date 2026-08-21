#!/usr/bin/env python3
"""저장소에서 인출 재료만 뽑는다.

재료층 = 시각 · 개수 · 변경량 · 이름 없는 묶음.
내용층 = 커밋 메시지 · 파일 경로 · 문서 본문. stdout 에는 내용층이 한 글자도 나가지 않는다.
내용층은 career/ 안의 **정리 파일**로 간다 — 그 파일을 읽는 사람은 사용자다.

    python3 repo_scan.py <저장소 절대경로> <career 절대경로> [author 이메일]

Python 3.9+ · 표준 라이브러리만 쓴다.
"""
import collections
import datetime
import hashlib
import os
import re
import subprocess
import sys

SEP = "|@|"          # \x1e 는 str.splitlines() 가 줄바꿈으로 취급해서 못 쓴다
HEAD = "@@CMT@@"
GAP_MIN = 45  # 이 간격 이상 벌어지면 다른 묶음으로 본다


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if r.returncode != 0:
        return ""
    return r.stdout


def authors(repo):
    out = git(repo, "log", "--no-merges", f"--format=%ae{SEP}%an")
    by_mail = collections.defaultdict(lambda: [0, set()])
    for line in out.splitlines():
        if SEP not in line:
            continue
        mail, name = line.split(SEP, 1)
        by_mail[mail][0] += 1
        by_mail[mail][1].add(name)
    return sorted(by_mail.items(), key=lambda kv: -kv[1][0])


def commits(repo, mail):
    """커밋마다 (sha, epoch, 날짜, 시각, 변경파일집합, 신규수). 메시지는 여기서 읽지 않는다.

    author 는 git 의 --author 로 거르지 않는다. 그것은 앵커 없는 정규식이라
    남의 주소를 부분일치로 함께 집어온다 (me@x.com 이 notme@x.com 을 문다).
    %ae 를 받아 파이썬에서 정확히 비교한다.
    """
    out = git(repo, "log", "--no-merges", "--reverse",
              f"--format={HEAD}%H{SEP}%at{SEP}%ad{SEP}%ae",
              "--date=format:%Y-%m-%d%H:%M", "--name-status")
    rows, cur = [], None
    for line in out.splitlines():
        if line.startswith(HEAD):
            if cur:
                rows.append(cur)
            sha, at, ad, ae = line[len(HEAD):].split(SEP, 3)  # 주소가 마지막이라 남는 건 다 주소다
            cur = {"sha": sha, "at": int(at), "date": ad[:10], "time": ad[10:], "mail": ae,
                   "files": set(), "new": 0}
        elif line.strip() and cur is not None:
            parts = line.split("\t")
            if len(parts) >= 2:
                cur["files"].add(parts[-1])
                if parts[0].startswith("A"):
                    cur["new"] += 1
    if cur:
        rows.append(cur)
    if mail:
        rows = [r for r in rows if r["mail"] == mail]
    # author 시각은 커밋 순서와 어긋날 수 있다 (리베이스·cherry-pick·--amend --date).
    # 묶기도 기간도 시간순을 전제하므로 여기서 한 번 세운다.
    # 안정 정렬이라 같은 시각끼리는 --reverse 가 준 순서를 그대로 지킨다.
    rows.sort(key=lambda r: r["at"])
    return rows


def messages(repo):
    """{sha: 커밋 메시지 전문}. 정리 파일 전용이다 — stdout 으로는 나가지 않는다.

    구분자가 NUL(-z) 이라 본문에 어떤 문자가 들어 있어도 레코드가 깨지지 않는다.
    """
    out = git(repo, "log", "--no-merges", "-z", "--format=%H%x1f%B")
    msgs = {}
    for rec in out.split("\0"):
        if not rec:
            continue
        sha, _, msg = rec.partition("\x1f")
        msgs[sha] = msg
    return msgs


def cluster(rows):
    """같은 날 안에서, 파일이 겹치거나 시간이 붙어 있으면 한 묶음."""
    out = []
    for c in rows:
        if out and out[-1]["date"] == c["date"] and (
                (c["at"] - out[-1]["at_end"]) <= GAP_MIN * 60 or (out[-1]["files"] & c["files"])):
            g = out[-1]
            g["n"] += 1
            g["at_end"] = c["at"]
            g["end"] = c["time"]
            g["files"] |= c["files"]
            g["new"] += c["new"]
            g["commits"].append(c)
        else:
            out.append({"date": c["date"], "start": c["time"], "end": c["time"],
                        "at_start": c["at"], "at_end": c["at"],
                        "n": 1, "files": set(c["files"]), "new": c["new"], "commits": [c]})
    return out


def number_by_day(gs):
    """같은 날 안에서 몇 번째 묶음인지 각 묶음에 적어 둔다.

    시각 문자열로 자리를 찾으면 같은 분에 시작한 묶음 둘이 같은 번호를 받는다.
    """
    for date in {g["date"] for g in gs}:
        same = sorted([g for g in gs if g["date"] == date], key=lambda g: g["at_start"])
        for i, g in enumerate(same, 1):
            g["idx"], g["of"] = i, len(same)


# 접두 하이픈으로 합쳐도 되는 구분자. 이 밖의 글자가 지워지면 정보가 소실된 것이다.
구분자 = re.compile(r"[a-z0-9\-_. ]")


def span(g):
    """묶음의 시간 표기. 재료표와 정리 파일이 같은 문자열을 쓴다."""
    return g["start"] if g["start"] == g["end"] else f"{g['start']}~{g['end']}"


def slugify(name):
    """저장소 디렉토리 이름을 프로젝트 slug 로 바꾼다. 형식은 references/schema.md.

    영문 밖 글자(한글·악센트)는 [^a-z0-9] 에 걸려 통째로 사라진다. 그대로 두면
    이름이 다른 두 저장소가 같은 slug 를 받아 정리가 한 디렉토리에 섞인다
    ('늑대인간'·'프로젝트' → 둘 다 'repo', '게임잼-2026' → '2026').
    소실이 있었으면 원본 이름의 짧은 해시를 붙여 구분을 되살린다.
    """
    low = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", low).strip("-")
    if any(not 구분자.match(ch) for ch in low):
        h = hashlib.sha1(name.encode("utf-8")).hexdigest()[:6]
        return f"{s}-{h}" if s else f"repo-{h}"
    return s or "repo"


def write_summary(career, repo, rows, gs, msgs):
    """정리 파일을 쓰고 그 경로를 돌려준다. 내용층이 나가는 유일한 자리다.

    읽는 사람은 사용자다. 메인은 이 파일을 열지 않는다 (SKILL.md 2단계).
    파일명이 HEAD 라서 같은 HEAD 를 다시 스캔하면 덮어쓴다.
    """
    slug = slugify(os.path.basename(os.path.realpath(repo)))
    head = git(repo, "rev-parse", "HEAD").strip()
    short = git(repo, "rev-parse", "--short", "HEAD").strip()
    d = os.path.join(career, "projects", slug, "artifacts")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"repo-scan-{short}.md")

    dates = [r["date"] for r in rows]
    out = ["---",
           f"scanned_at: {datetime.datetime.now().isoformat(timespec='seconds')}",
           f"head: {head}",
           "---",
           "",
           f"# 저장소 정리 — {slug} ({short})",
           "",
           f"커밋 {len(rows)} · 기간 {min(dates)} ~ {max(dates)} · 묶음 {len(gs)}",
           ""]
    # 재료표와 달리 여기는 전량이고 시간순이다. 사용자가 자기 하루를 되짚는 순서다.
    for g in sorted(gs, key=lambda g: g["at_start"]):
        out.append(f"## {g['date']}  {span(g)}  커밋 {g['n']}  ({g['idx']}/{g['of']})")
        out.append("")
        for c in g["commits"]:
            lines = msgs.get(c["sha"], "").splitlines()
            out.append(f"- {c['time']} `{lines[0] if lines else ''}`")
            body = "\n".join(lines[1:]).strip("\n").rstrip()
            if body:
                bl = body.splitlines()
                out.append(f"  본문: {bl[0]}")
                out.extend(f"  {x}" if x else "" for x in bl[1:])
            out.extend(f"  - {p}" for p in sorted(c["files"]))
        out.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out).rstrip() + "\n")
    return path


def main():
    if len(sys.argv) < 3:
        print("쓰임: python3 repo_scan.py <저장소 절대경로> <career 절대경로> [author 이메일]")
        return 1
    repo = sys.argv[1]
    career = sys.argv[2]
    mail = sys.argv[3] if len(sys.argv) > 3 else None
    if not os.path.isdir(career):
        # 1단계가 이미 만들었어야 한다. 오타 경로에 트리를 통째로 만드는 것을 막는다.
        print(f"career 디렉토리가 없다: {career}")
        return 1
    if not git(repo, "rev-parse", "--is-inside-work-tree").strip():
        print("저장소가 아니거나 읽을 수 없다")
        return 1

    al = authors(repo)
    print("== author ==")
    for mailx, (n, names) in al:
        print(f"{mailx}  커밋 {n}  (이름 표기 {len(names)}종)")
    if len(al) > 1 and not mail:
        print("\nauthor 가 여럿이다. 어느 것이 사용자인지 물어본 뒤 그 이메일로 다시 돌린다.")
        return 0

    rows = commits(repo, mail or (al[0][0] if al else None))
    if not rows:
        print("\n해당 author 의 커밋이 없다")
        return 0
    gs = cluster(rows)
    number_by_day(gs)
    dates = [r["date"] for r in rows]

    print(f"\n== 재료 ==  커밋 {len(rows)}  기간 {min(dates)} ~ {max(dates)}  묶음 {len(gs)}")
    print("날짜        시각          커밋  묶음  파일  신규")
    shown = sorted(gs, key=lambda g: -g["n"])[:12]
    for g in shown:
        idx = f"{g['idx']}/{g['of']}"
        print(f"{g['date']}  {span(g):<12}  {g['n']:>3}   {idx:>4}  {len(g['files']):>3}  {g['new']:>3}")
    print("\n파일 경로·커밋 메시지는 재료가 아니다. 이 출력에 없는 것은 묻지 않는다.")
    path = write_summary(career, repo, rows, gs, messages(repo))
    if len(gs) > len(shown):
        # 표에서 잘린 묶음이 있다는 사실 자체를 알려야 한다. 없으면 잘린 표에서 센
        # 숫자가 사용자에게 사실처럼 나간다.
        print(f"묶음 {len(gs)}개 중 {len(shown)}개만 위에 표시했다. "
              f"나머지 {len(gs) - len(shown)}개는 정리 파일에 있다.")
    print(f"정리를 저장했다: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
