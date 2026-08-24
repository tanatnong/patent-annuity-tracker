import json, re, sys
from pathlib import Path
from datetime import datetime, date

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FEE_DATA = DATA / "fee_data.json"
META = DATA / "patents_meta.json"
TEMPLATE = ROOT / "report_template.html"
OUT = ROOT / "report.html"

THAI_MONTHS = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
               "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def thai_date(d: date) -> str:
    return f"{d.day} {THAI_MONTHS[d.month]} {d.year + 543}"


def parse_thai_date(s):
    if not s or s.strip() in ("", "-", "null"):
        return None
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s.strip())
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return datetime(y - 543, mo, d)
    except ValueError:
        return None


def status_of(p, today):
    if p["fp"]:
        return "paid"
    if p["fd"]:
        fd = datetime.fromisoformat(p["fd"])
        days = (fd - today).days
        if days < 0:
            return "critical"
        if p["lp"]:
            return "critical"
        if days <= 90:
            return "warning"
        return "ok"
    if p["lp"]:
        return "critical"
    return "ok"


def main():
    fee_data = json.loads(FEE_DATA.read_text(encoding="utf-8"))
    meta = {m["a"]: m for m in json.loads(META.read_text(encoding="utf-8"))}

    patents = []
    dropped = []
    for d in fee_data:
        appno = d["appno"]
        if not d.get("ok") or not d.get("rows") or appno not in meta:
            dropped.append(appno)
            continue
        rows = d["rows"]
        next_action = None
        unpaid_count = 0
        for row in rows:
            if "ยังไม่ชำระ" in row["status"]:
                unpaid_count += 1
                if next_action is None:
                    next_action = row
        is_fully_paid = next_action is None
        lapsed = bool(next_action and "หมดอายุ" in next_action.get("note", ""))
        final_dt = parse_thai_date(next_action["final_date"]) if next_action else None

        m = meta[appno]
        row_tuples = [
            [r["year"], r["due"], r["payable_from"], r["amount"], r["penalty_free_until"],
             r["penalty"], r["final_date"], r["status"], r["note"]]
            for r in rows
        ]
        patents.append({
            "a": appno, "t": m["t"], "p": m["p"], "g": m["g"], "s": m["s"], "n": m["n"],
            "r": row_tuples, "u": unpaid_count, "fp": is_fully_paid, "lp": lapsed,
            "fd": final_dt.isoformat() if final_dt else None, "o": m["o"],
        })

    if dropped:
        print("dropped (no fee data or no meta):", dropped)

    today = datetime.combine(date.today(), datetime.min.time())
    fee_date_str = thai_date(date.today())

    counts = {"critical": 0, "warning": 0, "ok": 0, "paid": 0}
    warning_items = []
    for p in patents:
        s = status_of(p, today)
        counts[s] += 1
        if s == "warning":
            days = (datetime.fromisoformat(p["fd"]) - today).days
            warning_items.append((days, p["a"], p["n"], p["o"]))
    warning_items.sort()

    template = TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("__PATENT_DATA__", json.dumps(patents, ensure_ascii=False))
    html = html.replace("__FEE_DATE__", fee_date_str)
    html = html.replace("__TOTAL_COUNT__", str(len(patents)))
    OUT.write_text(html, encoding="utf-8")

    print(f"wrote {OUT} ({len(html)} chars)")
    print(f"total={len(patents)} critical={counts['critical']} warning={counts['warning']} ok={counts['ok']} paid={counts['paid']}")
    print("WARNING_ITEMS_JSON:" + json.dumps(warning_items, ensure_ascii=False))


if __name__ == "__main__":
    main()
