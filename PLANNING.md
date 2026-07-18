# Annuity Renewal — Patent Fee Tracker

## Status
Weekly patent annual-fee tracking report for Patent To You (บริษัท พาเท้นท์ ทู ยู จำกัด). Publishes to a Claude Artifact.

## What this does
- `data/app_numbers.json` — 173 patent/petty-patent/design-patent application numbers (from Granted folder on Google Drive, `H:\My Drive\PTY\Granted`).
- `data/patents_meta.json` — static per-patent fields: type, patent no., grant/submit dates, invention name, owner/applicant name. Owner name was verified against search.ipthailand.go.th on 2026-07-18 (that site requires an hCaptcha check, so it is NOT re-verified automatically — only refresh manually if ownership changes).
- `scripts/fetch_fees.py` — re-fetches annual fee schedule + payment status per application number from patentpub.ipthailand.go.th (no auth/captcha needed, safe to automate). Writes `data/fee_data.json`.
- `scripts/build_report.py` — merges fee data + static meta into `report_template.html`, computes status (paid / critical-overdue / warning-due-soon / ok), writes `report.html`. Also prints a `WARNING_ITEMS_JSON` line listing items due within 90 days (used for the weekly push notification).
- `report_template.html` — the report's HTML/CSS/JS shell with `__PATENT_DATA__` / `__FEE_DATE__` / `__TOTAL_COUNT__` placeholders.
- `report.html` — generated output (gitignored is NOT set — kept so cloud agent runs have a fallback to diff against, but always regenerated fresh each run).

## Weekly automation
A scheduled cloud agent (see https://claude.ai/code/routines) runs weekly:
1. `python scripts/fetch_fees.py`
2. `python scripts/build_report.py`
3. Publish `report.html` as a Claude Artifact to the existing URL: https://claude.ai/code/artifact/b320a8b9-3501-4c0c-b59a-41d3edb0d478
4. Push-notify the user with items from `WARNING_ITEMS_JSON` (due within 90 days).

## Known bug fixed (2026-07-18)
Original status logic trusted the department's "หมดอายุ" (expired) note as the only signal for "overdue" — but that note sometimes lags reality. Fixed to compare the final payable date against today's date directly (`status()` in the report JS, and `status_of()` in `build_report.py`) — both must stay in sync.

## Data caveats
- Application number `2203002391` exists as a filename in the Granted folder but has no record in the department system (likely a typo for `2303002391`, which is correct and present). Excluded from the report; footer note explains this.
