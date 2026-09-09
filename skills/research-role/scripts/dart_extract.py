#!/usr/bin/env python3
"""DART 사업보고서 원문 XML에서 두 절을 마크다운으로 뽑는다.

- 「II. 사업의 내용」 전체 → business.md
- 「VIII. 임원 및 직원 등에 관한 사항」의 하위 1(임원 및 직원(등)의 현황)만 → people.md

    python3 dart_extract.py <xml> [--out business.md] [--people people.md]

--out 이 없으면 business 를 stdout 에 쓰고, --people 이 없으면 people 은 만들지 않는다.
네트워크를 쓰지 않는 순수 변환이다. 표준 라이브러리만 쓴다.

종료 코드: 0 성공 / 2 절을 못 찾음(어느 절인지 stderr) / 3 XML 파싱 실패(전처리 후에도).
둘 중 하나만 찾아도 찾은 것은 쓰고 2 로 끝난다. 실패는 조용히 빈 결과를 내지 않는다.

원문은 그대로 XML 파서에 들어가지 않는다(미정의 엔티티 &cr; &nbsp;, 본문의 <당기> 같은
한글 의사 태그, dart4 의 홑 & "F&B"). 전처리 네 줄 뒤 strict 파싱만 한다 — recover 모드는
SECTION-2 를 TABLE 아래로 잘못 붙이는 것이 실측돼 쓰지 않는다.
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROMAN = str.maketrans({
    "Ⅰ": "I", "Ⅱ": "II", "Ⅲ": "III", "Ⅳ": "IV", "Ⅴ": "V", "Ⅵ": "VI",
    "Ⅶ": "VII", "Ⅷ": "VIII", "Ⅸ": "IX", "Ⅹ": "X", "Ⅺ": "XI", "Ⅻ": "XII",
})
XML_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}

# 절 식별은 SECTION-1 의 직속 TITLE 을 정규화(공백 제거, 로마숫자→ASCII)한 뒤 정규식으로.
# 텍스트 첫 매치는 목차 셀·참조 문장에 걸리는 일이 잦아 쓰지 않는다.
BUSINESS_TITLE = re.compile(r"^II\.?사업의내용$")
PEOPLE_TITLE = re.compile(r"^VIII\.?임원및직원(등)?(에)?관한사항$")
PEOPLE_SUB_TITLE = re.compile(r"^(1\.?)?임원및직원(등)?의현황$")
RND = "연구개발"

# 출력 H1 은 이 문자열로 고정한다 — role.md 가 앵커(#ii-사업의-내용 …)로 참조하므로 원문 제목의
# 표기 차이("임원 및 직원에 관한 사항" 등)가 새면 안 된다. H2 이하는 원문 TITLE 그대로다.
BUSINESS_HEADING = "II. 사업의 내용"
PEOPLE_HEADING = "VIII. 임원 및 직원 등에 관한 사항"

CELL_TAGS = ("TH", "TD", "TU", "TE")
# 본문에 남길 텍스트가 없는 태그: 그림(파일명·캡션), 쪽 나눔, 편집기 메타.
SKIP_TAGS = frozenset({"IMAGE", "IMG", "IMG-CAPTION", "PGBRK",
                       "COMMENT", "LIBRARYLIST", "FILENAME"})
# 자식을 그대로 이어서 읽는 감싸개. 하위 절이 LIBRARY(> INSERTION) 안에 있을 수 있다.
WRAPPER_TAGS = frozenset({"LIBRARY", "INSERTION", "TABLE-GROUP"})


# ---------------------------------------------------------------- 읽기·전처리

def read_text(path):
    """XML 선언의 encoding 으로 읽고, 안 되면 cp949 로 읽는다."""
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    m = re.match(rb"<\?xml[^>]*encoding=[\"']([^\"']+)[\"']", raw)
    declared = m.group(1).decode("ascii", "replace") if m else "utf-8"
    try:
        return raw.decode(declared)
    except (UnicodeDecodeError, LookupError):
        return raw.decode("cp949")


def preprocess(text):
    """strict 파싱이 되게 네 가지만 고친다. 그 밖의 원문은 건드리지 않는다."""
    text = text.replace("&cr;", "&#13;").replace("&nbsp;", "&#160;")
    text = re.sub(
        r"&(?!#)([A-Za-z][A-Za-z0-9]*);",
        lambda m: m.group(0) if m.group(1) in XML_ENTITIES else "&amp;" + m.group(1) + ";",
        text,
    )
    # 참조(&amp; &#13; &#xA0;)를 시작하지 않는 홑 & 는 본문 글자다 — dart4 원문은 "F&B"·"M&A" 를
    # 이스케이프 없이 쓴다(속성값 안에서도). 위 줄이 만든 &amp;foo; 는 참조 꼴이라 다시 건드리지 않는다.
    text = re.sub(r"&(?!(?:[A-Za-z][A-Za-z0-9]*|#[0-9]+|#x[0-9A-Fa-f]+);)", "&amp;", text)
    # '<' 또는 '</' 바로 뒤가 비ASCII 면 태그가 아니라 본문의 <당기> 같은 글자다.
    return re.sub(r"<(/?)(?=[^\x00-\x7f])", r"&lt;\1", text)


def load(path):
    """파일을 읽어 전처리한 뒤 strict 파싱한 루트를 돌려준다. 실패는 ET.ParseError."""
    return ET.fromstring(preprocess(read_text(path)))


# ---------------------------------------------------------------- 절 찾기

def normalize_title(text):
    return re.sub(r"\s+", "", text or "").translate(ROMAN)


def find_section1(root, pattern):
    """직속 TITLE 이 pattern 에 맞는 SECTION-1 하나. 없으면 None."""
    for sec in root.iter("SECTION-1"):
        title = sec.find("TITLE")
        if title is not None and pattern.match(normalize_title(inline_text(title))):
            return sec
    return None


def section_business(root):
    return find_section1(root, BUSINESS_TITLE)


def section_people(root):
    return find_section1(root, PEOPLE_TITLE)


def subsections(section):
    """절 아래 SECTION-2 전부(후손 탐색). 직계만 보면 LIBRARY 안의 것을 놓친다."""
    return list(section.iter("SECTION-2"))


def subsection_titles(section):
    return [heading_text(s) for s in subsections(section)]


def people_subsection(section_viii):
    """VIII 아래 '임원 및 직원(등)의 현황' SECTION-2. 없으면 None."""
    for sub in subsections(section_viii):
        if PEOPLE_SUB_TITLE.match(normalize_title(heading_text(sub))):
            return sub
    return None


def has_rnd(section_ii):
    return any(RND in t for t in subsection_titles(section_ii))


# ---------------------------------------------------------------- 텍스트 정리

def iter_inline(el):
    """요소 안의 글자를 순서대로. SKIP_TAGS 아래 글자는 버리되 그 뒤 tail 은 살린다."""
    if el.tag in SKIP_TAGS:
        return
    if el.text:
        yield el.text
    for child in el:
        yield from iter_inline(child)
        if child.tail:
            yield child.tail


def inline_text(el):
    return "".join(iter_inline(el))


def clean_lines(text):
    """&#13;(\\r)은 줄바꿈, 연속 공백은 하나로, 빈 줄은 버린다."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = (re.sub(r"[^\S\n]+", " ", line).strip() for line in text.split("\n"))
    return [line for line in lines if line]


def heading_text(section):
    """절의 직속 TITLE 을 한 줄로. 로마숫자는 ASCII 로 맞춘다."""
    title = section.find("TITLE")
    if title is None:
        return ""
    return " ".join(clean_lines(inline_text(title))).translate(ROMAN)


def paragraph(el):
    # 줄 앞의 # 은 마크다운 헤딩으로 읽혀 절 구조를 흐리므로 escape 한다
    lines = [re.sub(r"^#", r"\\#", line) for line in clean_lines(inline_text(el))]
    return "\n".join(lines) if lines else None


def cell_text(cell):
    # 표 안에서는 줄바꿈을 <br> 로, 파이프는 escape 해 표가 깨지지 않게 한다.
    return "<br>".join(clean_lines(inline_text(cell))).replace("|", "\\|")


# ---------------------------------------------------------------- 표

def span(cell, name):
    value = cell.get(name, "1")
    return max(int(value), 1) if value.isdigit() else 1


def flatten_rows(trs, repeat):
    """colspan/rowspan 을 펴서 문자열 격자로. repeat 면 걸친 칸에 글자를 반복하고 아니면 비운다.

    셀 수가 줄마다 달라도 예외 없이 격자를 만든다(부족한 칸은 비움).
    """
    grid, carry = [], {}  # carry: 열 → (글자, 남은 줄 수)
    for tr in trs:
        cells = [c for c in tr if c.tag in CELL_TAGS]
        row, col, idx = [], 0, 0
        while True:
            if col in carry:
                text, remaining = carry.pop(col)
                row.append(text if repeat else "")
                if remaining > 1:
                    carry[col] = (text, remaining - 1)
                col += 1
                continue
            if idx >= len(cells):
                if any(c > col for c in carry):  # 이 줄에 셀은 없는데 위에서 걸친 칸이 더 있다
                    row.append("")
                    col += 1
                    continue
                break
            cell = cells[idx]
            idx += 1
            text = cell_text(cell)
            rows_down = span(cell, "ROWSPAN")
            for k in range(span(cell, "COLSPAN")):
                row.append(text if (k == 0 or repeat) else "")
                if rows_down > 1:
                    carry[col] = (text, rows_down - 1)
                col += 1
        grid.append(row)
    return grid


def merge_header_rows(rows, width):
    """머리글이 여러 줄이면 열마다 겹치지 않는 글자를 이어 한 줄로 만든다."""
    merged = []
    for j in range(width):
        parts = []
        for row in rows:
            text = row[j] if j < len(row) else ""
            if text and text not in parts:
                parts.append(text)
        merged.append(" ".join(parts))
    return merged


def table_rows(table):
    head, body = [], []
    for child in table:
        if child.tag == "THEAD":
            head.extend(tr for tr in child if tr.tag == "TR")
        elif child.tag in ("TBODY", "TFOOT"):
            body.extend(tr for tr in child if tr.tag == "TR")
        elif child.tag == "TR":
            body.append(child)
    return head, body


def markdown_table(table):
    """TABLE → 마크다운 표 줄들. 한 줄짜리 표(기준일·단위 캡션)는 문단 한 줄로."""
    head_trs, body_trs = table_rows(table)
    if not head_trs and body_trs:
        # THEAD 가 없으면 첫 줄이 머리글. 첫 줄 셀에 ROWSPAN=n 이 있으면 머리글이 n 줄이다.
        depth = max((span(c, "ROWSPAN") for c in body_trs[0] if c.tag in CELL_TAGS), default=1)
        head_trs, body_trs = body_trs[:depth], body_trs[depth:]
    head = flatten_rows(head_trs, repeat=True)
    body = flatten_rows(body_trs, repeat=False)
    if not head:
        return []
    width = max(len(r) for r in head + body)
    header = merge_header_rows(head, width)
    if not body:
        line = " ".join(c for c in header if c)
        return [line] if line else []
    rows = [r + [""] * (width - len(r)) for r in body]
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    out.extend("| " + " | ".join(r) + " |" for r in rows)
    return out


# ---------------------------------------------------------------- 마크다운 조립

def render_children(el, depth, blocks):
    """el 의 자식을 문서 순서대로 블록으로. 절 자신의 TITLE 은 제목으로 이미 썼으니 건너뛴다."""
    own_title = el.find("TITLE") if el.tag.startswith("SECTION") else None
    for child in el:
        tag = child.tag
        if tag == "TITLE":
            if child is own_title:
                continue
            caption = " ".join(clean_lines(inline_text(child)))
            if caption:
                blocks.append(f"**{caption}**")  # 표 그룹 캡션 등 절 제목이 아닌 TITLE
        elif tag.startswith("SECTION-"):
            render_section(child, depth + 1, blocks)
        elif tag in WRAPPER_TAGS:
            render_children(child, depth, blocks)
        elif tag == "P":
            text = paragraph(child)
            if text:
                blocks.append(text)
        elif tag == "TABLE":
            lines = markdown_table(child)
            if lines:
                blocks.append("\n".join(lines))
        elif tag in SKIP_TAGS:
            continue
        else:
            text = paragraph(child)  # 모르는 태그도 글자는 잃지 않는다
            if text:
                blocks.append(text)


def render_section(section, depth, blocks):
    title = heading_text(section)
    if title:
        blocks.append("#" * min(depth, 6) + " " + title)
    render_children(section, depth, blocks)


def business_markdown(section_ii):
    """`# II. 사업의 내용` 아래 절 전체. 하위 SECTION-2 는 각각 `## <원문 TITLE>`, 없으면 본문만."""
    blocks = ["# " + BUSINESS_HEADING]
    render_children(section_ii, 1, blocks)
    return "\n\n".join(blocks) + "\n"


def people_markdown(section_viii, sub):
    """`# VIII. …` 아래 하위 1(임원 및 직원 현황)만 `## <원문 TITLE>`로. 하위 2(임원의 보수 등)는 넣지 않는다."""
    blocks = ["# " + PEOPLE_HEADING]
    render_section(sub, 2, blocks)
    return "\n\n".join(blocks) + "\n"


# ---------------------------------------------------------------- CLI

def write(text, path):
    if path is None:
        sys.stdout.write(text)
    else:
        Path(path).write_text(text, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("xml", help="사업보고서 본문 XML({rcept_no}.xml)")
    ap.add_argument("--out", metavar="PATH", help="「사업의 내용」 마크다운을 쓸 경로(없으면 stdout)")
    ap.add_argument("--people", metavar="PATH", help="「임원 및 직원 현황」 마크다운을 쓸 경로(없으면 만들지 않음)")
    args = ap.parse_args(argv)

    try:
        root = load(args.xml)
    except OSError as e:
        print(f"읽기 실패: {e}", file=sys.stderr)
        return 1
    except ET.ParseError as e:
        print(f"XML 파싱 실패(전처리 후에도): {args.xml}: {e}", file=sys.stderr)
        return 3

    missing = []
    try:
        ii = section_business(root)
        if ii is None:
            missing.append("II. 사업의 내용")
        else:
            if not has_rnd(ii):
                print("연구개발 절 없음", file=sys.stderr)
            write(business_markdown(ii), args.out)

        if args.people:
            viii = section_people(root)
            sub = people_subsection(viii) if viii is not None else None
            if viii is None:
                missing.append("VIII. 임원 및 직원 등에 관한 사항")
            elif sub is None:
                found = ", ".join(subsection_titles(viii)) or "(하위 절 없음)"
                missing.append(f"VIII 하위 '임원 및 직원 등의 현황' — 있는 하위 절: {found}")
            else:
                write(people_markdown(viii, sub), args.people)
    except OSError as e:
        print(f"쓰기 실패: {e}", file=sys.stderr)
        return 1

    for name in missing:
        print(f"절을 찾지 못함: {name}", file=sys.stderr)
    return 2 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
