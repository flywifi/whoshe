"""
Google Messages (RCS/SMS) export importer via Google Takeout.

Users request at: https://takeout.google.com → select "Messages" → download ZIP.

The export contains:
  Takeout/Messages/           ← per-thread HTML files (most common)
  Takeout/Messages/*.json     ← some exports include JSON (less common)

This importer handles both HTML and JSON formats.

Usage:
    from extractors.google_messages_import import find_zips, extract
    zips = find_zips(drop_folder)
    rows = extract(zip_path, out_dir)
"""
import csv
import html
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .normalize import normalize_rows

PLATFORM = "Google Messages"

_TS_PATTERN = re.compile(r'(\w{3} \d{1,2}, \d{4}, \d{1,2}:\d{2}:\d{2}\s*[AP]M)')
_SENDER_PATTERN = re.compile(r'<span class="sender">([^<]+)</span>')
_TEXT_PATTERN   = re.compile(r'<q>([^<]+)</q>')


def find_zips(folder: Path) -> list[Path]:
    return [p for p in folder.iterdir()
            if p.suffix.lower() == ".zip" and _is_google_zip(p)]


def _is_google_zip(p: Path) -> bool:
    try:
        with zipfile.ZipFile(p) as zf:
            return any("Takeout/Messages" in n for n in zf.namelist())
    except Exception:
        return False


def _parse_google_ts(s: str) -> str:
    """Parse 'Jan 5, 2023, 3:45:00 PM' style timestamps."""
    s = s.strip()
    for fmt in ("%b %d, %Y, %I:%M:%S %p", "%b %d, %Y, %I:%M %p"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return s


def _parse_html_file(content: str, thread_name: str) -> list[dict]:
    """Parse a Google Takeout Messages HTML file."""
    rows = []
    # Each message is a <div class="message"> block
    msg_blocks = re.findall(
        r'<div class="message[^"]*">(.*?)</div>\s*</div>',
        content, re.DOTALL
    )
    for i, block in enumerate(msg_blocks):
        sender_m = _SENDER_PATTERN.search(block)
        text_m   = _TEXT_PATTERN.search(block)
        ts_m     = _TS_PATTERN.search(block)

        sender = html.unescape(sender_m.group(1)) if sender_m else ""
        text   = html.unescape(text_m.group(1))   if text_m   else ""
        ts     = _parse_google_ts(ts_m.group(1))  if ts_m     else ""

        rows.append({
            "ROWID":          i,
            "date_local":     ts,
            "contact":        sender,
            "text":           text,
            "is_from_me":     0,
            "is_delivered":   1,
            "is_read":        1,
            "is_empty":       0 if text else 1,
            "thread":         thread_name,
        })
    return rows


def _parse_json_file(data: dict | list, thread_name: str) -> list[dict]:
    """Parse JSON variant of Google Messages Takeout."""
    rows = []
    msgs = data if isinstance(data, list) else data.get("messages", [])
    for i, msg in enumerate(msgs):
        rows.append({
            "ROWID":          i,
            "date_local":     str(msg.get("date", "")),
            "contact":        msg.get("from", {}).get("name", "") if isinstance(msg.get("from"), dict) else str(msg.get("from", "")),
            "text":           msg.get("text", msg.get("body", "")) or "",
            "is_from_me":     int(msg.get("selfSent", False)),
            "is_delivered":   1,
            "is_read":        1,
            "is_empty":       0 if msg.get("text") else 1,
            "thread":         thread_name,
        })
    return rows


def extract(zip_path: Path, out_dir: Path) -> list[dict]:
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Not a ZIP: {zip_path}")

    print(f"[+] Google Messages import: reading {zip_path.name}")
    raw: list[dict] = []
    rowid_offset = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        msg_files = [n for n in zf.namelist()
                     if "Takeout/Messages" in n and (n.endswith(".html") or n.endswith(".json"))]
        print(f"  [~] {len(msg_files)} message file(s) found")

        for fname in msg_files:
            thread_name = Path(fname).stem
            content = zf.read(fname).decode("utf-8", errors="replace")

            if fname.endswith(".html"):
                file_rows = _parse_html_file(content, thread_name)
            else:
                try:
                    data = json.loads(content)
                    file_rows = _parse_json_file(data, thread_name)
                except Exception:
                    continue

            for r in file_rows:
                r["ROWID"] = rowid_offset
                rowid_offset += 1
            raw.extend(file_rows)

    if not raw:
        raise RuntimeError(
            "No messages found in Google Takeout export.\n"
            "Ensure you selected 'Messages' when creating the Takeout export."
        )

    raw.sort(key=lambda r: r.get("date_local", ""))
    print(f"  [+] {len(raw)} Google Messages extracted")

    rows = normalize_rows(raw, PLATFORM)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv  = out_dir / "google_messages.csv"
    out_json = out_dir / "google_messages.json"
    if rows:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, default=str, ensure_ascii=False)
    print(f"  [+] Saved → {out_csv.name}")
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 google_messages_import.py <takeout.zip> <out_dir>"); sys.exit(1)
    rows = extract(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"[+] Done — {len(rows)} messages")
