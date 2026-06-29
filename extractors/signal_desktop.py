"""
Signal Desktop extractor for macOS.

Signal Desktop stores messages in an AES-256 encrypted SQLite (SQLCipher) database.
The decryption key is stored in plaintext in config.json — no password required,
since Signal Desktop's security model relies on the phone link, not a PIN.

Requires: pip install sqlcipher3
  (Homebrew must install sqlcipher first: brew install sqlcipher)

Usage:
    from extractors.signal_desktop import detect, extract
    if detect():
        rows = extract(out_dir)
"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from .normalize import normalize_rows, ms_to_local

SIGNAL_DIR = Path.home() / "Library" / "Application Support" / "Signal"
DB_PATH    = SIGNAL_DIR / "sql" / "db.sqlite"
CONFIG     = SIGNAL_DIR / "config.json"
PLATFORM   = "Signal"


def detect() -> bool:
    """Return True if Signal Desktop appears to be installed and has a database."""
    return DB_PATH.exists() and CONFIG.exists()


def _read_key() -> str | None:
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        return cfg.get("key")
    except Exception:
        return None


def _try_sqlcipher3(key_hex: str) -> list[dict] | None:
    """Attempt decryption using the sqlcipher3 Python package."""
    try:
        import sqlcipher3  # noqa: F401 — availability check
        conn = sqlcipher3.connect(str(DB_PATH))
        conn.execute(f"PRAGMA key = \"x'{key_hex}'\"")
        conn.execute("PRAGMA cipher_page_size = 4096")
        conn.execute("PRAGMA kdf_iter = 64000")
        conn.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512")
        conn.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512")
        return _fetch_messages(conn)
    except ImportError:
        return None
    except Exception as e:
        print(f"  [!] Signal sqlcipher3 error: {e}")
        return None


def _try_sqlcipher_cli(key_hex: str) -> list[dict] | None:
    """Fallback: use the sqlcipher CLI if sqlcipher3 package is unavailable."""
    try:
        result = subprocess.run(
            ["sqlcipher", str(DB_PATH)],
            input=f"PRAGMA key = \"x'{key_hex}'\";\nSELECT json_object('id',m.id,'body',m.body,'sent_at',m.sent_at,'received_at',m.received_at,'type',m.type,'conversationId',m.conversationId,'hasAttachments',m.hasAttachments) FROM messages m;\n.quit\n",
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0 or "Error" in result.stderr:
            return None
        rows = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return rows if rows else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _fetch_messages(conn) -> list[dict]:
    """Read messages and conversations from an open Signal DB connection."""
    try:
        convos = {}
        for row in conn.execute(
            "SELECT id, COALESCE(name, profileName, e164, serviceId) AS display FROM conversations"
        ).fetchall():
            convos[row[0]] = row[1] or row[0]
    except Exception:
        convos = {}

    msgs = []
    try:
        cursor = conn.execute(
            """
            SELECT id, body, sent_at, received_at, type,
                   conversationId, hasAttachments
            FROM messages
            WHERE type IN ('incoming', 'outgoing', 'story-reply')
            ORDER BY sent_at ASC
            """
        )
        for i, row in enumerate(cursor.fetchall()):
            mid, body, sent_ms, recv_ms, mtype, conv_id, has_att = row
            is_me = 1 if mtype == "outgoing" else 0
            ts_ms = sent_ms if is_me else (recv_ms or sent_ms)
            msgs.append({
                "ROWID":          i,
                "date_local":     ms_to_local(ts_ms),
                "contact":        convos.get(conv_id, conv_id or ""),
                "text":           body or "",
                "is_from_me":     is_me,
                "is_delivered":   1,
                "is_read":        1,
                "is_empty":       0 if body else 1,
                "has_attachment": has_att or 0,
                "thread":         convos.get(conv_id, conv_id or ""),
            })
    except Exception as e:
        print(f"  [!] Signal message fetch error: {e}")

    return msgs


def extract(out_dir: Path) -> list[dict]:
    """
    Decrypt and extract Signal Desktop messages.
    Returns normalized rows or raises RuntimeError if decryption fails.
    """
    if not detect():
        raise RuntimeError("Signal Desktop not found on this Mac.")

    key_hex = _read_key()
    if not key_hex:
        raise RuntimeError(f"Could not read Signal key from {CONFIG}.")

    print(f"[+] Signal Desktop: found database ({DB_PATH.stat().st_size // 1024} KB)")

    raw = _try_sqlcipher3(key_hex)
    if raw is None:
        print("  [~] sqlcipher3 not installed — trying sqlcipher CLI...")
        raw = _try_sqlcipher_cli(key_hex)
    if raw is None:
        raise RuntimeError(
            "Could not decrypt Signal database.\n"
            "Install sqlcipher3: brew install sqlcipher && pip install sqlcipher3"
        )

    print(f"  [+] {len(raw)} Signal messages extracted")
    rows = normalize_rows(raw, PLATFORM)

    out_dir.mkdir(parents=True, exist_ok=True)
    import csv, json as _json
    out_csv = out_dir / "signal_messages.csv"
    out_json = out_dir / "signal_messages.json"
    if rows:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    _json.dump(raw, open(out_json, "w"), indent=2, default=str)
    print(f"  [+] Saved → {out_csv.name}, {out_json.name}")
    return rows


if __name__ == "__main__":
    if not detect():
        print("[!] Signal Desktop not found."); sys.exit(1)
    rows = extract(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Desktop" / "signal_export")
    print(f"[+] Done — {len(rows)} messages")
