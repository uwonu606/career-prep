#!/usr/bin/env python3
"""저장소에서 인출 재료만 뽑는다.

재료층 = 시각 · 개수 · 변경량 · 이름 없는 묶음.
내용층 = 커밋 메시지 · 파일 경로 · 문서 본문. 이 스크립트는 내용층을 출력하지 않는다.

    python3 repo_scan.py <저장소 절대경로> [author 이메일]

표준 라이브러리만 쓴다.
"""
import subprocess, sys, collections

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
    """커밋마다 (epoch, 날짜, 시각, 변경파일집합, 신규수). 메시지는 읽지 않는다.

    author 는 git 의 --author 로 거르지 않는다. 그것은 앵커 없는 정규식이라
    남의 주소를 부분일치로 함께 집어온다 (me@x.com 이 notme@x.com 을 문다).
    %ae 를 받아 파이썬에서 정확히 비교한다.
    """
    out = git(repo, "log", "--no-merges", "--reverse", f"--format={HEAD}%at{SEP}%ad{SEP}%ae",
              "--date=format:%Y-%m-%d%H:%M", "--name-status")
    rows, cur = [], None
    for line in out.splitlines():
        if line.startswith(HEAD):
            if cur:
                rows.append(cur)
            at, ad, ae = line[len(HEAD):].split(SEP, 2)  # 주소가 마지막이라 남는 건 다 주소다
            cur = {"at": int(at), "date": ad[:10], "time": ad[10:], "mail": ae, "files": set(), "new": 0}
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
        else:
            out.append({"date": c["date"], "start": c["time"], "end": c["time"],
                        "at_start": c["at"], "at_end": c["at"],
                        "n": 1, "files": set(c["files"]), "new": c["new"]})
    return out


def number_by_day(gs):
    """같은 날 안에서 몇 번째 묶음인지 각 묶음에 적어 둔다.

    시각 문자열로 자리를 찾으면 같은 분에 시작한 묶음 둘이 같은 번호를 받는다.
    """
    for date in {g["date"] for g in gs}:
        same = sorted([g for g in gs if g["date"] == date], key=lambda g: g["at_start"])
        for i, g in enumerate(same, 1):
            g["idx"], g["of"] = i, len(same)


def main():
    repo = sys.argv[1]
    mail = sys.argv[2] if len(sys.argv) > 2 else None
    if not git(repo, "rev-parse", "--is-inside-work-tree").strip():
        print("저장소가 아니거나 읽을 수 없다"); return

    al = authors(repo)
    print("== author ==")
    for mailx, (n, names) in al:
        print(f"{mailx}  커밋 {n}  (이름 표기 {len(names)}종)")
    if len(al) > 1 and not mail:
        print("\nauthor 가 여럿이다. 어느 것이 사용자인지 물어본 뒤 그 이메일로 다시 돌린다.")
        return

    rows = commits(repo, mail or (al[0][0] if al else None))
    if not rows:
        print("\n해당 author 의 커밋이 없다"); return
    gs = cluster(rows)
    number_by_day(gs)
    dates = [r["date"] for r in rows]

    print(f"\n== 재료 ==  커밋 {len(rows)}  기간 {min(dates)} ~ {max(dates)}  묶음 {len(gs)}")
    print("날짜        시각          커밋  묶음  파일  신규")
    for g in sorted(gs, key=lambda g: -g["n"])[:12]:
        span = g["start"] if g["start"] == g["end"] else f"{g['start']}~{g['end']}"
        idx = f"{g['idx']}/{g['of']}"
        print(f"{g['date']}  {span:<12}  {g['n']:>3}   {idx:>4}  {len(g['files']):>3}  {g['new']:>3}")
    print("\n파일 경로·커밋 메시지는 재료가 아니다. 이 출력에 없는 것은 묻지 않는다.")


main()
