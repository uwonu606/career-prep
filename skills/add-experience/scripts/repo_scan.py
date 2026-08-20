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
    """커밋마다 (epoch, 날짜, 시각, 변경파일집합, 추가, 삭제, 신규수). 메시지는 읽지 않는다."""
    args = ["log", "--no-merges", "--reverse", f"--format={HEAD}%at{SEP}%ad", "--date=format:%Y-%m-%d%H:%M",
            "--name-status"]
    if mail:
        args += [f"--author={mail}"]
    out = git(repo, *args)
    rows, cur = [], None
    for line in out.splitlines():
        if line.startswith(HEAD):
            if cur:
                rows.append(cur)
            at, ad = line[len(HEAD):].split(SEP)
            cur = {"at": int(at), "date": ad[:10], "time": ad[10:], "files": set(), "new": 0}
        elif line.strip() and cur is not None:
            parts = line.split("\t")
            if len(parts) >= 2:
                cur["files"].add(parts[-1])
                if parts[0].startswith("A"):
                    cur["new"] += 1
    if cur:
        rows.append(cur)
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
            out.append({"date": c["date"], "start": c["time"], "end": c["time"], "at_end": c["at"],
                        "n": 1, "files": set(c["files"]), "new": c["new"]})
    return out


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
    gs_by_day = collections.Counter(g["date"] for g in gs)

    print(f"\n== 재료 ==  커밋 {len(rows)}  기간 {rows[0]['date']} ~ {rows[-1]['date']}  묶음 {len(gs)}")
    print("날짜        시각          커밋  묶음  파일  신규")
    for g in sorted(gs, key=lambda g: -g["n"])[:12]:
        span = g["start"] if g["start"] == g["end"] else f"{g['start']}~{g['end']}"
        idx = f"{sorted([x['start'] for x in gs if x['date']==g['date']]).index(g['start'])+1}/{gs_by_day[g['date']]}"
        print(f"{g['date']}  {span:<12}  {g['n']:>3}   {idx:>4}  {len(g['files']):>3}  {g['new']:>3}")
    print("\n파일 경로·커밋 메시지는 재료가 아니다. 이 출력에 없는 것은 묻지 않는다.")


main()
