"""
Recursive backup scanner for the iMessage Forensic Toolkit.

Reads iOS MobileSync Manifest.db to discover third-party app databases
inside iPhone/iPad backups, then attempts best-effort message extraction.

iOS backup layout:
  ~/Library/Application Support/MobileSync/Backup/<device_id>/
    Manifest.db      SQLite: Files table maps SHA1 hash filenames to app domain + path
    AB/ABCDEF...     actual file data stored by first 2 hex chars of SHA1

Usage:
    from extractors.recursive_search import run_recursive_search
    discoveries = run_recursive_search(wal_candidates, records, out_dir)
"""
import json
import shutil
import sqlite3
from pathlib import Path

BACKUP_ROOT = (
    Path.home() / "Library" / "Application Support" / "MobileSync" / "Backup"
)

# iOS app bundle domain → (platform name, [typical relative paths])
APP_DOMAINS: dict[str, tuple[str, list[str]]] = {
    "AppDomainGroup-group.net.whatsapp.WhatsApp.shared": ("WhatsApp", [
        "ChatStorage.sqlite",
    ]),
    "AppDomain-com.burbn.instagram": ("Instagram", [
        "Documents/IGDatabaseCore.db",
        "Library/databases/instagram.db",
    ]),
    "AppDomain-com.toyopagroup.picaboo": ("Snapchat", [
        "Documents/main.db",
    ]),
    "AppDomain-com.facebook.Messenger": ("Facebook", [
        "Documents/messenger.db",
    ]),
    "AppDomain-ph.telegra.Telegraph": ("Telegram", [
        "Documents/postboxes.db",
    ]),
    "AppDomain-org.whispersystems.signal": ("Signal", [
        "Documents/db.sqlite",
    ]),
    "AppDomain-com.google.BigTopMessaging": ("Google Messages", [
        "Documents/bugle.db",
    ]),
}


def _find_manifest(backup_dir: Path) -> Path | None:
    c = backup_dir / "Manifest.db"
    return c if c.exists() else None


def _enum_app_dbs(manifest_path: Path) -> list[dict]:
    """Query Manifest.db for files matching known app domains."""
    found = []
    try:
        conn = sqlite3.connect(
            f"file:{manifest_path}?mode=ro&immutable=1", uri=True
        )
        for domain, (platform, _) in APP_DOMAINS.items():
            rows = conn.execute(
                "SELECT fileID, domain, relativePath FROM Files "
                "WHERE domain = ? AND (relativePath LIKE '%.sqlite' "
                "OR relativePath LIKE '%.db' OR relativePath LIKE '%database%')",
                (domain,),
            ).fetchall()
            for file_id, dom, rel_path in rows:
                found.append({
                    "platform": platform,
                    "domain": dom,
                    "file_id": file_id,
                    "relative_path": rel_path,
                })
        conn.close()
    except Exception as exc:
        print(f"  [!] Manifest.db scan error: {exc}")
    return found


def _copy_hashed_file(backup_dir: Path, file_id: str, dest: Path) -> bool:
    """Copy a SHA1-hashed backup file to dest. Returns True on success."""
    src = backup_dir / file_id[:2] / file_id
    if not src.exists():
        return False
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return True
    except Exception:
        return False


def scan_backups_for_platforms(out_dir: Path) -> dict[str, list[Path]]:
    """
    Walk all iOS backups, query each Manifest.db, copy found app databases.
    Returns {platform: [copied_db_path, ...]}.
    """
    discoveries: dict[str, list[Path]] = {}

    if not BACKUP_ROOT.exists():
        print("[~] No MobileSync backups found — skipping app DB scan.")
        return discoveries

    plat_dir = out_dir / "platform_backups"

    for backup_dir in BACKUP_ROOT.iterdir():
        if not backup_dir.is_dir():
            continue
        manifest = _find_manifest(backup_dir)
        if not manifest:
            continue

        print(f"[*] Scanning iOS backup: {backup_dir.name[:8]}...")
        for rec in _enum_app_dbs(manifest):
            platform = rec["platform"]
            file_id  = rec["file_id"]
            rel_safe = rec["relative_path"].replace("/", "_").replace(" ", "_")
            dest = plat_dir / platform / f"{backup_dir.name[:8]}_{rel_safe}"
            if _copy_hashed_file(backup_dir, file_id, dest):
                print(f"  [+] {platform}: {rec['relative_path']}")
                discoveries.setdefault(platform, []).append(dest)

    if discoveries:
        total = sum(len(v) for v in discoveries.values())
        print(
            f"[+] App backup scan: {total} database(s) across "
            f"{len(discoveries)} platform(s)"
        )
        index_path = plat_dir / "manifest_scan.json"
        plat_dir.mkdir(parents=True, exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(
                {p: [str(x) for x in paths] for p, paths in discoveries.items()},
                f, indent=2,
            )
    else:
        print("[~] App backup scan: no third-party databases recovered.")

    return discoveries


# ---------------------------------------------------------------------------
# Best-effort message extractors for found databases
# ---------------------------------------------------------------------------

def _extract_whatsapp(db_path: Path) -> list[dict]:
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if "ZWAMESSAGE" not in tables:
            conn.close()
            return []
        rows = conn.execute(
            "SELECT ZTEXT, ZMESSAGEDATE, ZFROMJID, ZTOJID FROM ZWAMESSAGE "
            "WHERE ZTEXT IS NOT NULL LIMIT 5000"
        ).fetchall()
        conn.close()
        return [{"text": r[0], "date_local": str(r[1] or ""),
                 "contact": r[2] or r[3] or "", "is_from_me": 0,
                 "platform": "WhatsApp"} for r in rows]
    except Exception:
        return []


def _extract_generic(db_path: Path, platform: str) -> list[dict]:
    """Scan any SQLite for a text-bearing table and return up to 1000 rows."""
    _TEXT_COLS = {"text", "body", "message", "content", "msg", "message_body"}
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )]
        for table in tables:
            cur = conn.execute(f'SELECT * FROM "{table}" LIMIT 1')
            if cur.description is None:
                continue
            col_names = [d[0].lower() for d in cur.description]
            text_col = next((c for c in _TEXT_COLS if c in col_names), None)
            if not text_col:
                continue
            raw_rows = conn.execute(f'SELECT * FROM "{table}" LIMIT 1000').fetchall()
            result = []
            for row in raw_rows:
                d = dict(zip(col_names, row))
                if d.get(text_col):
                    result.append({
                        "text": str(d[text_col]),
                        "date_local": "",
                        "contact": "",
                        "is_from_me": 0,
                        "platform": platform,
                    })
            conn.close()
            if result:
                return result
        conn.close()
    except Exception:
        pass
    return []


def _try_extract(db_path: Path, platform: str) -> list[dict]:
    if platform == "WhatsApp":
        rows = _extract_whatsapp(db_path)
        if rows:
            return rows
    return _extract_generic(db_path, platform)


def run_recursive_search(
    wal_candidates: list[dict],
    records: list[dict],
    out_dir: Path,
) -> dict[str, list[dict]]:
    """
    1. Scan iOS backups via Manifest.db for third-party app databases.
    2. Best-effort extract messages from found databases.
    Returns {platform: [normalized_record_dicts]}.
    """
    result: dict[str, list[dict]] = {}

    platform_dbs = scan_backups_for_platforms(out_dir)
    for platform, db_paths in platform_dbs.items():
        for db_path in db_paths:
            rows = _try_extract(db_path, platform)
            if rows:
                result.setdefault(platform, []).extend(rows)
                print(f"  [+] Extracted {len(rows)} rows from {db_path.name}")

    return result
