#!/usr/bin/env python3
"""career/index.md 를 다시 만든다.

각 파일의 frontmatter 가 진실이고 index.md 는 파생 캐시다.
사용자가 파일을 직접 고치는 것이 정상 동작이므로, index 를 읽기 전에 매번 이걸 돌린다.

    python3 build_index.py <career_dir> [vocabulary.md 경로]

표준 라이브러리만 쓴다.
"""

import sys
from pathlib import Path

BAR = " · "


def parse_frontmatter(text):
    """--- 로 감싼 앞부분을 아주 작은 YAML 부분집합으로 읽는다.

    지원: key: value / key: [a, b] / key: 다음 줄부터 "- item" / 한 단계 중첩 맵.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data, key, nested = {}, None, None
    for raw in text[3:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if line.startswith("- ") and key:
            if not isinstance(data.get(key), list):
                data[key] = []  # "key:" 다음 줄부터 목록이 오면 맵이 아니라 목록이다
            data[key].append(line[2:].strip())
            nested = None
            continue

        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()

        if indent and nested is not None:
            data[nested][k] = clean(v)
            continue

        nested = None
        if v == "":
            data[k] = {}
            nested = k
            key = k
        elif v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            data[k] = [x.strip() for x in inner.split(",") if x.strip()] if inner else []
            key = None
        else:
            data[k] = clean(v)
            key = None
    return data


def clean(v):
    v = v.strip().strip('"').strip("'")
    return "" if v == "~" else v


def load_vocabulary(path):
    """vocabulary.md 의 표 첫 열을, 소제목별로 나눠 순서대로 읽는다."""
    groups, current = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
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
        groups.setdefault(current, [])
        if tag not in groups[current]:
            groups[current].append(tag)
    return {k: v for k, v in groups.items() if v}


def row(cells):
    # 값에 들어간 | 가 표를 깨지 않게 막는다
    return "| " + " | ".join(str(c).replace("|", "\\|") if str(c) else "—" for c in cells) + " |"


def table(headers, rows):
    out = [row(headers), "| " + " | ".join("---" for _ in headers) + " |"]
    out.extend(row(r) for r in rows)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    career = Path(sys.argv[1])
    default_vocab = Path(__file__).resolve().parent.parent / "references" / "vocabulary.md"
    vocab_path = Path(sys.argv[2]) if len(sys.argv) > 2 else default_vocab
    if not vocab_path.exists():
        # 어휘가 없으면 역량 커버리지의 0인 축이 통째로 사라진다. 앵커 선택이 그 줄에
        # 의존하므로 조용히 넘어가지 않는다.
        print(f"vocabulary.md 를 찾을 수 없습니다: {vocab_path}", file=sys.stderr)
        return 1

    episodes = []
    for f in sorted((career / "episodes").glob("*.md")):
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        fm.setdefault("id", f.stem)
        episodes.append(fm)

    projects = []
    for f in sorted((career / "projects").glob("*/project.md")):
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
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
        label = "역량" if name == "역량" else ("주제" if "주제" in name else name)
        lines += [f"**{label}:** " + BAR.join(f"{t} {used.get(t, 0)}" for t in tags), ""]

    (career / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"episodes={len(episodes)} projects={len(projects)} -> {career / 'index.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
