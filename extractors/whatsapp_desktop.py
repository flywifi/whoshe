"""
WhatsApp Desktop extractor for macOS.

WhatsApp Desktop on macOS may store messages in a local SQLite database.
Encryption status varies by version:
  - Older web-wrapper versions: unencrypted SQLite (readable directly)
  - Newer native app (2023+): may be encrypted or use a different format

This extractor attempts a direct read. If the database is encrypted or
uses an unsupported format, it falls back to a per-chat text export guide.

Usage:
    from extractors.whatsapp_desktop import detect, extract
    if detect():
        rows = extract(out_dir)
"""
import csv
import glob
import json
import sqlite3
import sys
from pathlib import Path

from .normalize import normalize_rows, ms_to_local, sec_to_local

PLATFORM = "WhatsApp"

# Known possible database locations across WhatsApp Desktop versions
_CANDIDATE_PATHS = [
    Path.home() / "Library" / "Application Support" / "WhatsApp" / "databases" / "msgstore.db",
    Path.home() / "Library" / "Containers" / "net.whatsapp.WhatsApp" / "Data" / "Library" / "Application Support" / "ChatStorage.sqlite",
]

# Glob patterns for less predictable paths
_GLOB_PATTERNS = [
    str(Path.home() / "Library" / "Group Containers" / "*.net.whatsapp*" / "**" / "*.sqlite"),
    str(Path.home() / "Library" / "Group Containers" / "*.net.whatsapp*" / "**" / "*.db"),
    str(Path.home() / "Library" / "Application Support" / "WhatsApp" / "**" / "*.sqlite"),
    str(Path.home() / "Library" / "Application Support" / "WhatsApp" / "**" / "*.db"),
]


def _find_db() -> Path | None:
    for p in _CANDIDATE_PATHS:
        if p.exists():
            return p
    for pattern in _GLOB_PATTERNS:
        matches = sorted(glob.glob(pattern, recursive=True))
        for m in matches:
            p = Path(m)
            if p.stat().st_size > 4096:
                return p
    return None


def detect() -> bool:
    wa_dir = Path.home() / "Library" / "Application Support" / "WhatsApp"
    wa_container = Path.home() / "Library" / "Containers" / "net.whatsapp.WhatsApp"
    wa_group = list((Path.home() / "Library" / "Group Containers").glob("*.net.whatsapp*"))
    return wa_dir.exists() or wa_container.exists() or bool(wa_group)


def _try_open(db_path: Path) -> sqlite3.Connection | None:
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return conn
    except Exception:
        return None


def _tables(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]


def _extract_zwamessage(conn: sqlite3.Connection) -> list[dict]:
    """iOS backup / older macOS WhatsApp schema (ZWAMESSAGE table)."""
    rows = []
    try:
        contacts = {}
        for r in conn.execute("SELECT ZCONTACTJID, ZPUSHNAME FROM ZWAPROFILEPUSHNAME").fetchall():
            contacts[r[0]] = r[1]
    except Exception:
        contacts = {}

    try:
        cursor = conn.execute(
            """
            SELECT m.Z_PK, m.ZMESSAGEDATE, m.ZISFROMME,
                   m.ZTEXT, m.ZSTANZAID,
                   s.ZCONTACTJID, s.ZPARTNERNAME
            FROM ZWAMESSAGE m
            LEFT JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
            ORDER BY m.ZMESSAGEDATE ASC
            """
        )
        for row in cursor.fetchall():
            pk, ts, is_me, text, stanza, jid, partner = row
            # WhatsApp Desktop uses CoreData timestamps (seconds since 2001-01-01)
            date_str = sec_to_local((ts or 0) + 978307200) if ts else ""
            contact = contacts.get(jid, partner or jid or "")
            rows.append({
                "ROWID":      pk,
                "date_local": date_str,
                "contact":    contact,
                "text":       text or "",
                "is_from_me": int(is_me or 0),
                "is_delivered": 1,
                "is_read":    1,
                "is_empty":   0 if text else 1,
                "thread":     partner or jid or "",
            })
    except Exception as e:
        print(f"  [!] WhatsApp ZWAMESSAGE read error: {e}")
    return rows


def _extract_generic(conn: sqlite3.Connection, tables: list[str]) -> list[dict]:
    """Attempt generic extraction from any message-like table."""
    msg_tables = [t for t in tables if "message" in t.lower() or "msg" in t.lower()]
    if not msg_tables:
        return []
    rows = []
    for tname in msg_tables[:3]:
        try:
            cols = [d[0] for d in conn.execute(f'SELECT * FROM "{tname}" LIMIT 1').description or []]
            text_col = next((c for c in cols if "text" in c.lower() or "body" in c.lower() or "content" in c.lower()), None)
            ts_col   = next((c for c in cols if "date" in c.lower() or "time" in c.lower() or "ts" in c.lower()), None)
            if not text_col:
                continue
            for i, r in enumerate(conn.execute(f'SELECT * FROM "{tname}" ORDER BY rowid ASC LIMIT 50000').fetchall()):
                rd = dict(zip(cols, r))
                rows.append({
                    "ROWID":      rd.get("rowid", i),
                    "date_local": sec_to_local(rd.get(ts_col)) if ts_col else "",
                    "contact":    "",
                    "text":       str(rd.get(text_col) or ""),
                    "is_from_me": 0,
                    "thread":     tname,
                })
        except Exception:
            continue
    return rows


def extract(out_dir: Path) -> list[dict]:
    if not detect():
        raise RuntimeError("WhatsApp Desktop not found on this Mac.")

    db_path = _find_db()
    if db_path is None:
        raise RuntimeError(
            "WhatsApp Desktop is installed but no readable database was found.\n"
            "Your version may use an encrypted format. Use WhatsApp's built-in\n"
            "per-chat export (Chat → More → Export Chat) as an alternative."
        )

    print(f"[+] WhatsApp Desktop: found {db_path.name} ({db_path.stat().st_size // 1024} KB)")
    conn = _try_open(db_path)
    if conn is None:
        raise RuntimeError(
            f"Could not open {db_path.name} — likely encrypted.\n"
            "Use WhatsApp's built-in per-chat export as an alternative."
        )

    tables = _tables(conn)
    print(f"  [~] Tables: {', '.join(tables[:10])}")

    if "ZWAMESSAGE" in tables:
        raw = _extract_zwamessage(conn)
    else:
        raw = _extract_generic(conn, tables)
    conn.close()

    if not raw:
        raise RuntimeError("No messages found in WhatsApp database (may be encrypted or empty).")

    print(f"  [+] {len(raw)} WhatsApp messages extracted")
    rows = normalize_rows(raw, PLATFORM)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "whatsapp_messages.csv"
    out_json = out_dir / "whatsapp_messages.json"
    if rows:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    with open(out_json, "w") as f:
        json.dump(raw, f, indent=2, default=str)
    print(f"  [+] Saved → {out_csv.name}")
    return rows


if __name__ == "__main__":
    rows = extract(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Desktop" / "whatsapp_export")
    print(f"[+] Done — {len(rows)} messages")
