#!/usr/bin/env python3
"""OpenDART empSttus·exctvSttus JSON 을 마크다운 표로 바꾼다. 순수 함수, 네트워크 없음.

    python3 dart_tables.py --emp empSttus-2024.json [empSttus-2023.json ...] [--exec exctvSttus-2024.json] [--out people-tables.md]

- 헤딩은 고정이다(role.md 가 앵커로 참조): `## 직원 현황` 아래 연도별 `### YYYY`, `## 임원 현황`.
- 직원 현황: 연도 오름차순, 연도마다 표 하나. 원 데이터는 부문(fo_bbm)×성별(sexdstn) 행이라
  부문 단위로 합친다 — 인원(정규직·계약직·합계)은 성별 행을 더하고, 평균근속·1인평균급여는
  더할 수 없으니 "남 x / 여 y" 로 나란히 둔다.
- 연도별 합계 행: 원 데이터에 합계 행이 있으면 그걸 쓰고, 없으면 인원만 더해 넣고 "(계산)" 이라 적는다.
  정규직+계약직이 원 데이터 합계(sm)와 다르면 둘 다 보여 준다.
- 콤마 제거 후 정수/실수. "-"·빈값·"해당사항없음" 은 빈 셀. 숫자로 못 읽는 값은 원문 그대로.
  값을 새로 만들어내지 않는다.
- 임원 현황: 이름 | 직위 | 등기여부 | 상근여부 | 담당업무 | 주요경력.
- 표 아래 출처 줄: 출처: OpenDART empSttus, 사업연도 YYYY, rcept_no ….

종료 코드: 0 성공 / 2 표로 만들 데이터 없음 / 3 JSON 읽기 실패. 표준 라이브러리만 쓴다.
"""

import argparse
import json
import re
import sys
from pathlib import Path

EMPTY = {"", "-", "해당사항없음", "해당없음"}
TOTAL_WORDS = {"합계", "총계", "계", "전체", "총합계"}
# 급여 단위: 가이드는 자릿수(9,999,999,999)만 적고 단위를 말하지 않는다. 원 데이터 값을 그대로 쓰고
# 헤더에 원(₩) 으로 적는다. # 가이드 재확인 필요 — 첫 라이브 데이터에서 단위를 대조할 것
EMP_HEADERS = ["부문", "정규직", "계약직", "합계", "평균근속(년)", "1인평균급여(원)"]
EXEC_HEADERS = ["이름", "직위", "등기여부", "상근여부", "담당업무", "주요경력"]


class TablesError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def parse_num(s):
    """'2,345' → 2345, '5.3' → 5.3, 빈값류·숫자 아님 → None."""
    t = (s or "").strip().replace(",", "")
    if t in EMPTY:
        return None
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return None


def fmt(n):
    return "" if n is None else f"{n:,}"


def text(v):
    """표 셀용 문자열. 줄바꿈은 ' / ' 로, 빈값류는 빈 셀."""
    v = re.sub(r"\s*\n\s*", " / ", (v or "").strip())
    v = re.sub(r"[ \t]+", " ", v)
    return "" if v in EMPTY else v


def is_total(label):
    return re.sub(r"\s+", "", label or "") in TOTAL_WORDS


def row(cells):
    # 값에 들어간 | 가 표를 깨지 않게 막는다. 빈 셀은 빈 채로 둔다
    return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"


def table(headers, rows):
    out = [row(headers), "| " + " | ".join("---" for _ in headers) + " |"]
    out.extend(row(r) for r in rows)
    return out


def nums(rows, key):
    """열 값들의 (숫자 합 또는 None, 숫자로 못 읽은 원문 목록)."""
    total, seen, texts = 0, False, []
    for r in rows:
        v = (r.get(key) or "").strip()
        n = parse_num(v)
        if n is not None:
            total, seen = total + n, True
        elif v.replace(",", "") not in EMPTY:
            texts.append(v)
    return (total if seen else None), texts


def count_cell(rows, key):
    """더할 수 있는 열(인원). 숫자로 못 읽는 값이 섞이면 더하지 않고 원문을 나란히 둔다."""
    total, texts = nums(rows, key)
    if texts:
        return " / ".join(texts + ([fmt(total)] if total is not None else []))
    return fmt(total)


def sum_cell(rows):
    """합계(sm) 열. 정규직+계약직과 다르면 둘 다 표시."""
    cell = count_cell(rows, "sm")
    sm, sm_texts = nums(rows, "sm")
    reg, _ = nums(rows, "rgllbr_co")
    con, _ = nums(rows, "cnttk_co")
    if sm is not None and not sm_texts and reg is not None and con is not None and reg + con != sm:
        cell += f" (정규직+계약직={fmt(reg + con)})"
    return cell


def per_sex_cell(rows, key):
    """더할 수 없는 열(평균근속·1인평균급여). 행이 하나면 그 값, 여럿이면 '남 x / 여 y'."""
    parts = []
    for r in rows:
        v = (r.get(key) or "").strip()
        n = parse_num(v)
        t = fmt(n) if n is not None else ("" if v.replace(",", "") in EMPTY else v)
        if not t:
            continue
        label = (r.get("sexdstn") or "").strip()
        parts.append(f"{label} {t}" if len(rows) > 1 and label else t)
    return " / ".join(parts)


def merge_group(label, rows):
    """부문 하나의 성별 행들 → 표 행 하나. 성별 자리에 합계 행이 있으면 더하지 않고 그걸 쓴다."""
    totals = [r for r in rows if is_total(r.get("sexdstn"))]
    if totals:
        rows = totals
    return [label or "—", count_cell(rows, "rgllbr_co"), count_cell(rows, "cnttk_co"), sum_cell(rows),
            per_sex_cell(rows, "avrg_cnwk_sdytrn"), per_sex_cell(rows, "jan_salary_am")]


def emp_table(rows):
    """한 사업연도의 empSttus 행들 → (표 줄 목록, 주석 줄 목록)."""
    groups = {}  # fo_bbm → 행들, 입력 순서 유지
    for r in rows:
        groups.setdefault((r.get("fo_bbm") or "").strip(), []).append(r)
    total_label = next((k for k in groups if is_total(k)), None)
    body = [merge_group(k, rs) for k, rs in groups.items() if k != total_label]
    notes = []
    merged = any(len(rs) > 1 and not any(is_total(r.get("sexdstn")) for r in rs) for k, rs in groups.items() if k != total_label)
    if merged:
        notes.append("부문 행의 인원은 성별 행을 더한 값. 평균근속·1인평균급여는 더할 수 없어 성별 값을 나란히 적음.")
    if total_label is not None:
        body.append(merge_group(total_label, groups[total_label]))
    else:
        every = [r for k, rs in groups.items() for r in rs]
        body.append(["합계 (계산)", count_cell(every, "rgllbr_co"), count_cell(every, "cnttk_co"), sum_cell(every), "", ""])
        notes.append("합계 행은 원 데이터에 없어 인원만 더해 넣음(계산). 평균근속·급여는 계산하지 않음.")
    return table(EMP_HEADERS, body), notes


def exec_table(rows):
    return table(EXEC_HEADERS, [
        [text(r.get("nm")), text(r.get("ofcps")), text(r.get("rgist_exctv_at")),
         text(r.get("fte_at")), text(r.get("chrg_job")), text(r.get("main_career"))]
        for r in rows
    ])


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise TablesError(3, f"JSON 읽기 실패 {path}: {e}") from None


def year_of(path, rows):
    """파일명의 empSttus-YYYY / exctvSttus-YYYY → 없으면 결산기준일(stlm_dt) 연도 → 없으면 '연도 미상'."""
    m = re.search(r"Sttus-(\d{4})", Path(path).name)
    if m:
        return m.group(1)
    for r in rows:
        m = re.match(r"\d{4}", r.get("stlm_dt") or "")
        if m:
            return m.group(0)
    return "연도 미상"


def source_line(api, year, rows):
    rcept = sorted({(r.get("rcept_no") or "").strip() for r in rows} - {""}) or ["?"]
    stlm = sorted({(r.get("stlm_dt") or "").strip() for r in rows} - {""})
    line = f"출처: OpenDART {api}, 사업연도 {year}, rcept_no {', '.join(rcept)}"
    if stlm:
        line += f" (결산기준일 {', '.join(stlm)})"
    return line


def render(emp_paths, exec_path):
    lines = []
    if emp_paths:
        years = []
        for p in emp_paths:
            data = load(p)
            rows = data.get("list") or []
            if not rows:
                print(f"{p}: 직원 현황 데이터 없음(status {data.get('status')}) — 건너뜀", file=sys.stderr)
                continue
            years.append((year_of(p, rows), rows))
        if not years:
            raise TablesError(2, "표로 만들 직원 현황이 없음(모든 파일이 빈 응답)")
        years.sort(key=lambda t: t[0])
        lines += ["## 직원 현황", ""]
        for year, rows in years:
            tbl, notes = emp_table(rows)
            lines += [f"### {year}", ""] + tbl + [""]
            lines += [f"- {n}" for n in notes] + ([""] if notes else [])  # 목록 뒤 빈 줄, 출처가 목록에 붙지 않게
            lines += [source_line("empSttus", year, rows), ""]
    if exec_path:
        data = load(exec_path)
        rows = data.get("list") or []
        if not rows:
            raise TablesError(2, f"{exec_path}: 임원 현황 데이터 없음(status {data.get('status')})")
        year = year_of(exec_path, rows)
        lines += ["## 임원 현황", ""] + exec_table(rows) + ["", source_line("exctvSttus", year, rows), ""]
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--emp", nargs="+", default=[], metavar="JSON", help="empSttus-YYYY.json (여러 개)")
    ap.add_argument("--exec", dest="exec_path", metavar="JSON", help="exctvSttus-YYYY.json")
    ap.add_argument("--out", type=Path, help="쓸 파일(예: people-tables.md). 없으면 stdout")
    args = ap.parse_args(argv)
    if not args.emp and not args.exec_path:
        ap.error("--emp 또는 --exec 중 하나는 있어야 한다")
    try:
        md = render(args.emp, args.exec_path)
    except TablesError as e:
        print(str(e), file=sys.stderr)
        return e.code
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
        print(f"-> {args.out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
