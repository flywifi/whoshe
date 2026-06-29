"""
Telegram Desktop export importer.

Users export in-app: Settings → Advanced → Export Telegram Data → JSON format.
The export produces a folder containing result.json.

Schema:
  {
    "chats": {
      "list": [
        {
          "name": "Contact Name",
          "type": "personal_chat" | "private_group" | "...",
          "messages": [
            { "id", "date", "from", "from_id", "text", "type", "file" }
          ]
        }
      ]
    }
  }

Text may be a string or a list of objects (rich text with entities).

Usage:
    from extractors.telegram_import import find_export, extract
    folder = find_export(drop_folder)
    rows = extract(folder_or_json, out_dir)
"""
import csv
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from .normalize import normalize_rows

PLATFORM = "Telegram"


def _flatten_text(text) -> str:
    """Telegram rich text: may be a string or list of {type, text} objects."""
    if isinstance(text, str):
        return text
    if isinstance(text, list):
        parts = []
        for item in text:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
        return "".join(parts)
    return str(text or "")


def _parse_ts(s: str) -> str:
    try:
        return datetime.fromisoformat(s).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return s or ""


def find_export(folder: Path) -> Path | None:
    """Find result.json in a Telegram export folder or ZIP."""
    result_json = folder / "result.json"
    if result_json.exists():
        return result_json
    # Also accept a ZIP containing result.json
    for p in folder.iterdir():
        if p.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(p) as zf:
                    if "result.json" in zf.namelist():
                        return p
            except Exception:
                pass
    return None


def _load_data(source: Path) -> dict:
    if source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as zf:
            return json.loads(zf.read("result.json").decode("utf-8"))
    return json.loads(source.read_text(encoding="utf-8"))


def extract(source: Path, out_dir: Path) -> list[dict]:
    """
    Parse a Telegram export and return normalized rows.
    source: Path to result.json OR to a ZIP containing result.json.
    """
    print(f"[+] Telegram import: reading {source.name}")
    data = _load_data(source)

    chats = data.get("chats", {}).get("list", [])
    if not chats:
        # Some older exports use "messages" at the root (single chat export)
        if "messages" in data:
            chats = [data]
        else:
            raise RuntimeError("No chats found in Telegram export.")

    raw: list[dict] = []
    rowid = 0
    my_ids: set = set()

    for chat in chats:
        chat_name = chat.get("name", "") or ""
        msgs = chat.get("messages", [])
        for msg in msgs:
            if msg.get("type") not in ("message", "service", None):
                continue
            if msg.get("type") == "service":
                continue

            sender    = msg.get("from", "") or ""
            sender_id = msg.get("from_id", "")
            text      = _flatten_text(msg.get("text", ""))
            ts        = _parse_ts(msg.get("date", ""))
            has_file  = bool(msg.get("file") or msg.get("photo") or msg.get("sticker"))

            # Heuristic: collect from_ids seen as "self"; Telegram marks own messages
            if msg.get("from_id", "").startswith("user") and not sender:
                is_me = 1  # sender field blank often = self in older exports
            else:
                is_me = 0

            raw.append({
                "ROWID":          rowid,
                "date_local":     ts,
                "contact":        sender or chat_name,
                "text":           text,
                "is_from_me":     is_me,
                "is_delivered":   1,
                "is_read":        1,
                "is_empty":       0 if (text or has_file) else 1,
                "has_attachment": 1 if has_file else 0,
                "thread":         chat_name,
            })
            rowid += 1

    if not raw:
        raise RuntimeError("No messages found in Telegram export.")

    print(f"  [+] {len(raw)} Telegram messages from {len(chats)} chat(s)")
    rows = normalize_rows(raw, PLATFORM)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv  = out_dir / "telegram_messages.csv"
    out_json = out_dir / "telegram_messages.json"
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
        print("Usage: python3 telegram_import.py <result.json|export.zip> <out_dir>"); sys.exit(1)
    rows = extract(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"[+] Done — {len(rows)} messages")
