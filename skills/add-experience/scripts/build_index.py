#!/usr/bin/env python3
"""career/index.md 를 다시 만든다.

각 파일의 frontmatter 가 진실이고 index.md 는 파생 캐시다.
사용자가 파일을 직접 고치는 것이 정상 동작이므로, index 를 읽기 전에 매번 이걸 돌린다.

    python3 build_index.py <career 절대경로> [vocabulary.md 경로]

Python 3.9+ · 표준 라이브러리만 쓴다.
"""

import sys
from pathlib import Path

BAR = " · "


def indent_of(line):
    return len(line) - len(line.lstrip())


def strip_comment(v):
    """따옴표 밖에서 공백 뒤에 오는 # 부터 줄 끝까지를 주석으로 본다 (YAML 규칙).

    따옴표는 값이 따옴표로 시작할 때만 따옴표다. 아무 데서나 세면 `don't stop  # 주석`
    의 아포스트로피가 닫히지 않는 여는 따옴표가 되어 주석이 값에 남는다.
    URL 앵커(.../42#c1)는 앞에 공백이 없어 걸리지 않는다.
    """
    start = 0
    if v[:1] in ('"', "'"):
        close = v.find(v[0], 1)
        if close == -1:
            return v  # 닫히지 않은 따옴표는 통째로 값으로 둔다
        start = close + 1
    for i in range(start, len(v)):
        if v[i] == "#" and (i == 0 or v[i - 1] in " \t"):
            return v[:i].rstrip()
    return v


BLOCK_MARKS = ("|", ">", "|-", ">-", "|+", ">+")


def read_block(lines, i, indent, mark):
    """블록 스칼라 본문을 읽고 (값, 다음 줄 번호) 를 돌려준다.

    | 는 개행을 지키고 > 는 공백으로 잇는다. chomping 표시(-, +)는 받되 무시한다 —
    표 한 칸에 들어갈 값이라 끝의 개행을 남기는 것과 자르는 것이 구분되지 않는다.
    안 받으면 `>-` 가 그대로 값이 되어, 이 함수가 막으려는 것과 같은 쓰레기가 남는다.

    본문은 문면 그대로가 값이라 clean() 을 걸지 않는다 — ~ 도 따옴표도 사용자가 적은
    글자다.
    """
    body = []
    while i < len(lines):
        nxt = lines[i]
        if nxt.strip() and indent_of(nxt) <= indent:
            break
        body.append(nxt)
        i += 1
    # 들여쓰기는 본문 전체의 최소값으로 벗긴다. 첫 줄 기준으로 자르면 뒤에 오는 덜
    # 들여쓴 줄이 통째로 사라진다 — 조용한 손실이다.
    base = min([indent_of(b) for b in body if b.strip()] or [0])
    body = [b[base:].rstrip() if b.strip() else "" for b in body]
    joined = "\n".join(body) if mark[0] == "|" else " ".join(x for x in body if x)
    return joined.strip(), i


def parse_frontmatter(text):
    """--- 로 감싼 앞부분을 아주 작은 YAML 부분집합으로 읽는다.

    지원: key: value / key: [a, b] / key: 다음 줄부터 "- item" (여러 줄 이어짐 포함)
    / 한 단계 중첩 맵 / 블록 스칼라(| >) / 값 뒤의 인라인 주석.

    `block_key` 는 "key:" 만 나와 목록인지 맵인지 아직 모르는 키이고, `map_key` 는
    들여쓴 "k: v" 가 와서 맵으로 확정된 키다. 둘은 같은 줄에서 시작해 다음 줄이
    갈라 준다.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data, block_key, map_key = {}, None, None
    lines = text[3:end].splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = indent_of(raw)
        line = raw.strip()

        if line.startswith("- ") and block_key:
            if not isinstance(data.get(block_key), list):
                data[block_key] = []  # "key:" 다음 줄부터 목록이 오면 맵이 아니라 목록이다
            # 목록 항목에는 clean() 을 걸지 않는다. open_questions 가 산문이라
            # 따옴표를 벗기면 `"두 시간쯤" 까지만 나옴` 같은 항목이 한쪽만 잘려 깨진다.
            data[block_key].append(line[2:].strip())
            map_key = None
            continue

        # 목록 항목이 여러 줄로 이어진다. schema.md 가 park한 칸에 요구하는 형태다 —
        # 여기서 안 받으면 콜론이 든 이어짐 줄이 가짜 최상위 키가 된다.
        if indent and map_key is None and isinstance(data.get(block_key), list) and data[block_key]:
            data[block_key][-1] += " " + line
            continue

        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), strip_comment(v.strip())

        if indent and map_key is not None:
            # 블록 스칼라는 값이 오는 자리 어디서든 같게 읽는다. 여기서 안 읽으면
            # 표시가 값이 되고 본문이 조용히 사라진다 — 위와 같은 종류의 손실이다.
            if v in BLOCK_MARKS:
                data[map_key][k], i = read_block(lines, i, indent, v)
            else:
                data[map_key][k] = clean(v)
            continue

        map_key = None
        if v in BLOCK_MARKS:
            data[k], i = read_block(lines, i, indent, v)
            block_key = None
            continue
        if v == "":
            data[k] = {}
            map_key = k
            block_key = k
        elif v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            # 인라인 목록의 항목은 태그·스택처럼 짧은 값이라 clean() 을 건다.
            # schema.md 의 "모르는 필드는 ~ 로 두고" 가 여기서도 통해야 한다.
            data[k] = [clean(x) for x in inner.split(",") if x.strip()] if inner else []
            block_key = None
        else:
            data[k] = clean(v)
            block_key = None
    return data


def clean(v):
    v = v.strip().strip('"').strip("'")
    return "" if v == "~" else v


def read(path):
    """읽지 못한 파일을 건너뛰지 않는다. 에피소드 하나가 조용히 빠지면 역량 커버리지가
    그만큼 틀리고, 그 줄이 다음에 캘 자리를 고르는 근거다.

    낡은 index.md 는 지우지 않고 그대로 둔다 — 파생 캐시라 지우는 쪽이 손실이 크고,
    종료 코드 1 이 다시 만들지 못했다는 것을 말한다.
    """
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"읽을 수 없다: {path} ({e.__class__.__name__})")
        return None


def load_vocabulary(path):
    """vocabulary.md 의 표 첫 열을, 소제목별로 나눠 순서대로 읽는다."""
    groups, current = {}, None
    for line in (read(path) or "").splitlines():
        line = line.strip()
        if line.startswith("## "):
            current = line[3:].strip()
            continue
        if not line.startswith("|") or current is None:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        tag = cells[0] if cells else ""
        if not tag or tag == "태그" or set(tag) <= set("- :"):
            continue
        tags = groups.setdefault(current, [])
        if tag not in tags:  # 같은 태그를 두 번 적어도 커버리지 줄에는 한 번만 나온다
            tags.append(tag)
    return groups  # 그룹 키는 append 직전에만 생기므로 빈 그룹은 만들어지지 않는다


def row(cells):
    # 값에 들어간 | 와 개행이 표를 깨지 않게 막는다. None 은 "None" 이 아니라 빈 칸이다.
    out = []
    for c in cells:
        s = "" if c is None else str(c)
        s = " ".join(s.split("\n")).strip()
        out.append(s.replace("|", "\\|") if s else "—")
    return "| " + " | ".join(out) + " |"


def table(headers, rows):
    out = [row(headers), "| " + " | ".join("---" for _ in headers) + " |"]
    out.extend(row(r) for r in rows)
    return out


def main():
    if len(sys.argv) < 2:
        print("쓰임: python3 build_index.py <career 절대경로> [vocabulary.md 경로]")
        return 1
    career = Path(sys.argv[1])
    if not career.is_dir():
        # career/ 를 만드는 것은 SKILL.md 1단계의 일이다. 여기서 만들면 오타 경로에
        # 조용히 두 번째 저장소가 생기고, 역량 커버리지가 그만큼 갈라진다.
        print(f"career 디렉토리가 아니거나 읽을 수 없다: {career}")
        return 1
    default_vocab = Path(__file__).resolve().parent.parent / "references" / "vocabulary.md"
    vocab_path = Path(sys.argv[2]) if len(sys.argv) > 2 else default_vocab
    if not vocab_path.exists():
        # 어휘가 없으면 역량 커버리지의 0인 축이 통째로 사라진다. 앵커 선택이 그 줄에
        # 의존하므로 조용히 넘어가지 않는다.
        print(f"vocabulary.md 를 찾을 수 없다: {vocab_path}")
        return 1

    episodes = []
    for f in sorted((career / "episodes").glob("*.md")):
        text = read(f)
        if text is None:
            return 1
        fm = parse_frontmatter(text)
        fm.setdefault("id", f.stem)
        episodes.append(fm)

    projects = []
    for f in sorted((career / "projects").glob("*/project.md")):
        text = read(f)
        if text is None:
            return 1
        fm = parse_frontmatter(text)
        fm.setdefault("id", f.parent.name)
        projects.append(fm)

    lines = [
        "<!-- 자동 생성 파일입니다. 원본은 각 파일의 frontmatter입니다. -->",
        "<!-- scripts/build_index.py 가 다시 만듭니다. 직접 고친 내용은 사라집니다. -->",
        "",
        "## 프로젝트",
        "",
    ]
    counts = {}
    for ep in episodes:
        for pid in ep.get("projects") or []:
            counts[pid] = counts.get(pid, 0) + 1
    lines += table(
        ["id", "제목", "기간", "역할", "에피소드 수"],
        [
            [p.get("id"), p.get("title"), p.get("period"), p.get("role"), counts.get(p.get("id"), 0)]
            for p in projects
        ],
    )

    lines += ["", "## 에피소드", ""]
    lines += table(
        ["id", "제목", "프로젝트", "역량", "증거", "미해결"],
        [
            [
                ep.get("id"),
                ep.get("title"),
                ", ".join(ep.get("projects") or []),
                ", ".join(ep.get("skills") or []),
                ep.get("evidence"),
                len(ep.get("open_questions") or []),
            ]
            for ep in episodes
        ],
    )

    known = {ep.get("id") for ep in episodes}
    forward = {
        ep.get("id"): [t if t in known else f"{t}(?)" for t in (ep.get("related") or [])]
        for ep in episodes
    }
    backward = {}
    for src, targets in forward.items():
        for t in targets:
            backward.setdefault(t, []).append(src)
    linked = sorted(set(forward) & (set(backward) | {k for k, v in forward.items() if v}))
    if linked:
        lines += ["", "## 이어지는 사건", ""]
        lines += table(
            ["에피소드", "선행", "후속"],
            [[e, ", ".join(forward.get(e) or []), ", ".join(backward.get(e) or [])] for e in linked],
        )

    used = {}
    for ep in episodes:
        for tag in ep.get("skills") or []:
            used[tag] = used.get(tag, 0) + 1
    groups = load_vocabulary(vocab_path)
    listed = {t for tags in groups.values() for t in tags}
    extra = [t for t in used if t not in listed]
    if extra:
        groups.setdefault("어휘 밖", []).extend(extra)
    lines += ["", "## 역량 커버리지", ""]
    for name, tags in groups.items():
        label = "주제" if "주제" in name else name  # "기술 주제" 는 줄머리에서 "주제" 로 줄인다
        lines += [f"**{label}:** " + BAR.join(f"{t} {used.get(t, 0)}" for t in tags), ""]

    (career / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"episodes={len(episodes)} projects={len(projects)} -> {career / 'index.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
