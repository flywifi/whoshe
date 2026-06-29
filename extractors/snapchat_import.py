"""
Snapchat "My Data" export importer.

Users request their data at: https://accounts.snapchat.com → My Data
They receive a ZIP file containing json/chat_history.json.

NOTE: Only SAVED messages are included. Ephemeral snaps that were not saved
by either party are NOT present in the export (by design — they are deleted).

Usage:
    from extractors.snapchat_import import find_zips, extract
    zips = find_zips(drop_folder)
    rows = extract(zip_path, out_dir)
"""
import csv
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from .normalize import normalize_rows

PLATFORM = "Snapchat"

_DATE_FMTS = [
    "%Y-%m-%d %H:%M:%S %Z",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S UTC",
]


def _parse_ts(s: str) -> str:
    s = (s or "").strip().replace("UTC", "").strip()
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(s, fmt.replace(" %Z", "")).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return s


def find_zips(folder: Path) -> list[Path]:
    return [p for p in folder.iterdir()
            if p.suffix.lower() == ".zip" and _is_snapchat_zip(p)]


def _is_snapchat_zip(p: Path) -> bool:
    try:
        with zipfile.ZipFile(p) as zf:
            return any("chat_history" in n.lower() for n in zf.namelist())
    except Exception:
        return False


def extract(zip_path: Path, out_dir: Path) -> list[dict]:
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Not a ZIP: {zip_path}")

    print(f"[+] Snapchat import: reading {zip_path.name}")
    raw: list[dict] = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        chat_files = [n for n in zf.namelist() if "chat_history" in n.lower() and n.endswith(".json")]
        if not chat_files:
            raise RuntimeError(
                "No chat_history.json found in this ZIP.\n"
                "Make sure this is a Snapchat My Data export."
            )
        data = json.loads(zf.read(chat_files[0]).decode("utf-8"))

    # Snapchat export schema varies across versions
    # Common keys: "Received Saved Chat History", "Sent Saved Chat History"
    rowid = 0
    for section_key, is_me_val in [
        ("Sent Saved Chat History", 1),
        ("Received Saved Chat History", 0),
    ]:
        section = data.get(section_key, [])
        if isinstance(section, dict):
            # Some exports nest by username
            items = []
            for v in section.values():
                items.extend(v if isinstance(v, list) else [v])
            section = items

        for msg in section:
            if not isinstance(msg, dict):
                continue
            sender   = msg.get("From", msg.get("Sender", ""))
            text     = msg.get("Text", msg.get("Content", "")) or ""
            media    = msg.get("Media Type", msg.get("Type", ""))
            ts_raw   = msg.get("Created", msg.get("Timestamp", ""))
            raw.append({
                "ROWID":          rowid,
                "date_local":     _parse_ts(str(ts_raw)),
                "contact":        sender,
                "text":           text,
                "is_from_me":     is_me_val,
                "is_delivered":   1,
                "is_read":        1,
                "is_empty":       0 if text else 1,
                "has_attachment": 1 if (media and media.lower() not in ("text", "")) else 0,
                "thread":         sender,
            })
            rowid += 1

    if not raw:
        raise RuntimeError(
            "No saved messages found in Snapchat export.\n"
            "Only messages explicitly saved by either party appear in My Data exports.\n"
            "Ephemeral snaps cannot be recovered."
        )

    raw.sort(key=lambda r: r["date_local"])
    print(f"  [+] {len(raw)} saved Snapchat messages (ephemeral snaps not included)")

    rows = normalize_rows(raw, PLATFORM)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv  = out_dir / "snapchat_messages.csv"
    out_json = out_dir / "snapchat_messages.json"
    if rows:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, default=str)
    print(f"  [+] Saved → {out_csv.name}")
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 snapchat_import.py <mydata.zip> <out_dir>"); sys.exit(1)
    rows = extract(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"[+] Done — {len(rows)} messages")
