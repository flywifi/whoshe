"""
Meta Data Export importer — Instagram DMs and Facebook Messenger.

Users request their data at:
  Instagram: https://accountscenter.instagram.com/info_and_permissions/dyi/
  Facebook:  https://www.facebook.com/dyi

The downloaded ZIP contains:
  messages/inbox/<thread_name>/message_1.json  (and message_2.json, etc.)

Meta encodes text in Latin-1 with escaped Unicode — this module fixes that.

Usage:
    from extractors.meta_import import find_zips, extract
    zips = find_zips(drop_folder)
    rows = extract(zip_path, out_dir)
"""
import csv
import json
import sys
import zipfile
from pathlib import Path

from .normalize import normalize_rows, ms_to_local

PLATFORM_IG = "Instagram"
PLATFORM_FB = "Facebook"


def _fix_encoding(s: str) -> str:
    """Fix Meta's Latin-1-encoded Unicode escape bug."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def _detect_platform(zf: zipfile.ZipFile) -> str:
    names = zf.namelist()
    # Instagram exports include 'personal_information/' or 'account_information/'
    for n in names:
        if "personal_information" in n or "account_information" in n:
            return PLATFORM_IG
    return PLATFORM_FB


def find_zips(folder: Path) -> list[Path]:
    """Find any Meta data export ZIPs in the given folder."""
    return [p for p in folder.iterdir()
            if p.suffix.lower() == ".zip" and _is_meta_zip(p)]


def _is_meta_zip(p: Path) -> bool:
    try:
        with zipfile.ZipFile(p) as zf:
            return any("messages/inbox" in n or "messages/archived_threads" in n
                       for n in zf.namelist())
    except Exception:
        return False


def detect(zip_path: Path) -> bool:
    """Return True if zip_path is a Meta (Facebook/Instagram) data export."""
    return _is_meta_zip(zip_path)


def extract(zip_path: Path, out_dir: Path) -> list[dict]:
    """
    Parse a Meta data export ZIP and return normalized message rows.
    Handles both Instagram and Facebook Messenger formats.
    """
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Not a ZIP file: {zip_path}")

    raw: list[dict] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        platform = _detect_platform(zf)
        print(f"[+] Meta import ({platform}): reading {zip_path.name}")

        msg_files = sorted(
            n for n in zf.namelist()
            if n.endswith(".json") and "/messages/" in n
            and ("inbox/" in n or "archived_threads/" in n or "message_requests/" in n)
        )
        print(f"  [~] {len(msg_files)} message JSON file(s) found")

        rowid = 0
        for fname in msg_files:
            try:
                data = json.loads(zf.read(fname).decode("utf-8"))
            except Exception:
                continue

            participants = data.get("participants", [])
            # Determine the "other" participant (not the account owner — first participant)
            others = [p.get("name", "") for p in participants[1:]]
            thread_name = data.get("title") or (", ".join(others) if others else "Unknown")

            my_name = participants[0].get("name", "") if participants else ""

            for msg in data.get("messages", []):
                sender = _fix_encoding(msg.get("sender_name", ""))
                content = _fix_encoding(msg.get("content", "") or "")
                ts_ms = msg.get("timestamp_ms", 0)
                mtype = msg.get("type", "Generic")

                if mtype not in ("Generic", "Share"):
                    continue

                is_me = 1 if sender == my_name else 0
                raw.append({
                    "ROWID":          rowid,
                    "date_local":     ms_to_local(ts_ms),
                    "contact":        sender,
                    "text":           content,
                    "is_from_me":     is_me,
                    "is_delivered":   1,
                    "is_read":        1,
                    "is_empty":       0 if content else 1,
                    "has_attachment": 1 if (msg.get("photos") or msg.get("videos") or msg.get("files")) else 0,
                    "thread":         _fix_encoding(thread_name),
                })
                rowid += 1

    if not raw:
        raise RuntimeError(f"No messages found in {zip_path.name}. "
                           "Ensure this is a complete Meta data export.")

    # Messages in Meta export are newest-first; reverse to chronological
    raw.reverse()
    print(f"  [+] {len(raw)} messages from {platform}")

    rows = normalize_rows(raw, platform)
    out_dir.mkdir(parents=True, exist_ok=True)
    platform_slug = platform.lower().replace(" ", "_")
    out_csv = out_dir / f"{platform_slug}_messages.csv"
    out_json = out_dir / f"{platform_slug}_messages.json"
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
        print("Usage: python3 meta_import.py <export.zip> <out_dir>"); sys.exit(1)
    rows = extract(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"[+] Done — {len(rows)} messages")
