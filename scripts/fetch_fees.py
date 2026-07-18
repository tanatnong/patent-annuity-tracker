import json, re, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
NUMS_FILE = ROOT / "data" / "app_numbers.json"
OUT_FILE = ROOT / "data" / "fee_data.json"

BASE = "https://patentpub.ipthailand.go.th/_AppPublic/PatentAnnualCheck.aspx?appNo={}"

nums = json.loads(NUMS_FILE.read_text(encoding="utf-8"))


def fetch_one(appno, retries=3):
    url = BASE.format(appno)
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=25)
            if r.status_code != 200:
                time.sleep(1)
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find(id="contentMain_gvMain")
            rows = []
            if table:
                for tr in table.find_all("tr")[1:]:
                    tds = tr.find_all("td")
                    if len(tds) < 9:
                        continue
                    rows.append(
                        {
                            "year": " ".join(tds[0].get_text(" ", strip=True).split()),
                            "due": tds[1].get_text(strip=True),
                            "payable_from": tds[2].get_text(strip=True),
                            "amount": tds[3].get_text(strip=True),
                            "penalty_free_until": tds[4].get_text(strip=True),
                            "penalty": tds[5].get_text(strip=True),
                            "final_date": tds[6].get_text(strip=True),
                            "status": " ".join(tds[7].get_text(" ", strip=True).split()),
                            "note": tds[8].get_text(strip=True),
                        }
                    )
            return {"appno": appno, "ok": True, "rows": rows}
        except Exception as e:
            if attempt == retries - 1:
                return {"appno": appno, "ok": False, "error": str(e)}
            time.sleep(2)
    return {"appno": appno, "ok": False, "error": "max retries"}


def main():
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(fetch_one, n): n for n in nums}
        for fut in as_completed(futures):
            results.append(fut.result())
    results.sort(key=lambda r: r["appno"])
    OUT_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"TOTAL: {len(results)}  OK: {sum(1 for r in results if r.get('ok'))}  FAILED: {sum(1 for r in results if not r.get('ok'))}")


if __name__ == "__main__":
    main()
