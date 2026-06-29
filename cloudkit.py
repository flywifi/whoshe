#!/usr/bin/env python3
"""
iMessage Forensic CloudKit Analyser v1.0
Reads cloudkit_probe.json + export_raw.json from an iMsgForensic_* folder
and classifies every message ROWID by its iCloud sync status.

Classification labels:
  ICLOUD_SYNCED   — present locally AND acknowledged by CloudKit sync log
  LOCAL_ONLY      — in local db, no CloudKit record (MDM-blocked or never uploaded)
  ICLOUD_DELETED  — CloudKit has a deletion record; local row still exists (tombstone)
  LOCAL_DELETED   — deletion record exists but no matching local row (purged locally)

Usage:
    python3 cloudkit.py --input ~/Desktop/iMsgForensic_20240101_120000
    python3 cloudkit.py --input ~/Desktop/merged_timeline
"""
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║          iMessage CloudKit Analyser v1.0                        ║
║          Classify messages by iCloud sync status                ║
╚══════════════════════════════════════════════════════════════════╝
"""

# Status constants
ICLOUD_SYNCED   = "ICLOUD_SYNCED"
LOCAL_ONLY      = "LOCAL_ONLY"
ICLOUD_DELETED  = "ICLOUD_DELETED"
LOCAL_DELETED   = "LOCAL_DELETED"
UNKNOWN         = "UNKNOWN"

# ---------------------------------------------------------------------------
# CloudKit table name heuristics
# These are the real table names observed in macOS 12-15 chat.db databases.
# ---------------------------------------------------------------------------

# Tables that track sync state per message
SYNC_STATE_TABLES = {
    "sync_deleted_messages",
    "chat_recoverable_message_join",
    "deleted_messages",
}

# Tables that contain CloudKit change tokens / record metadata
RECORD_TABLES = {
    "kvs",
    "ck_record_change_tag",
    "ckdatabasechange",
    "cloudkit_info",
    "sync_state",
    "ck_sync_state",
}

# Tables that hold per-message CloudKit record identifiers
MESSAGE_RECORD_TABLES = {
    "chat_message_join",     # has cloudkit fields in newer macOS
    "ck_message",
    "cloudkit_message",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _str(v) -> str:
    return str(v).strip() if v is not None else ""

def _int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def _extract_rowid(row: dict | list, columns: list[str]) -> int | None:
    """Pull ROWID/message_id/record_id from a row dict or list."""
    if isinstance(row, dict):
        for key in ("message_id", "ROWID", "rowid", "record_id", "id"):
            if key in row:
                return _int(row[key])
    elif isinstance(row, list) and columns:
        for key in ("message_id", "ROWID", "rowid", "record_id", "id"):
            if key in columns:
                return _int(row[columns.index(key)])
    return None

def _extract_guid(row: dict | list, columns: list[str]) -> str | None:
    """Pull a message GUID string from a row."""
    if isinstance(row, dict):
        for key in ("guid", "message_guid", "record_name", "ck_record_id"):
            if key in row:
                return _str(row[key]) or None
    elif isinstance(row, list) and columns:
        for key in ("guid", "message_guid", "record_name", "ck_record_id"):
            if key in columns:
                val = row[columns.index(key)]
                return _str(val) or None
    return None

# ---------------------------------------------------------------------------
# Core classification logic
# ---------------------------------------------------------------------------

def analyse_cloudkit(probe: dict, local_rowids: set[int], local_guids: set[str]) -> dict:
    """
    Returns:
      {
        "deleted_rowids":  set[int],   # confirmed CloudKit deletion records
        "deleted_guids":   set[str],
        "synced_rowids":   set[int],   # confirmed CloudKit sync records
        "synced_guids":    set[str],
        "table_coverage":  dict,       # which tables contributed what
      }
    """
    deleted_rowids: set[int] = set()
    deleted_guids:  set[str] = set()
    synced_rowids:  set[int] = set()
    synced_guids:   set[str] = set()
    table_coverage: dict[str, dict] = {}

    for table_name, table_data in probe.items():
        if "error" in table_data:
            continue

        cols    = table_data.get("columns", [])
        rows    = table_data.get("rows", [])
        tname   = table_name.lower()

        is_deletion_table = any(kw in tname for kw in (
            "delet", "recover", "tombstone", "purge"
        ))
        is_sync_table = any(kw in tname for kw in (
            "sync", "cloud", "ck_", "_ck", "kvs", "change"
        ))

        contrib = {"rows": len(rows), "deleted_ids": 0, "synced_ids": 0}

        for row in rows:
            rid  = _extract_rowid(row, cols)
            guid = _extract_guid(row, cols)

            if is_deletion_table:
                if rid is not None:
                    deleted_rowids.add(rid)
                    contrib["deleted_ids"] += 1
                if guid:
                    deleted_guids.add(guid)
            elif is_sync_table:
                if rid is not None:
                    synced_rowids.add(rid)
                    contrib["synced_ids"] += 1
                if guid:
                    synced_guids.add(guid)

        table_coverage[table_name] = contrib

    return {
        "deleted_rowids":  deleted_rowids,
        "deleted_guids":   deleted_guids,
        "synced_rowids":   synced_rowids,
        "synced_guids":    synced_guids,
        "table_coverage":  table_coverage,
    }

def classify_record(rowid: int, guid: str | None, ck: dict) -> str:
    deleted = (rowid in ck["deleted_rowids"]) or (guid and guid in ck["deleted_guids"])
    synced  = (rowid in ck["synced_rowids"])  or (guid and guid in ck["synced_guids"])

    if deleted:
        return ICLOUD_DELETED   # CloudKit says deleted, but local row exists
    if synced:
        return ICLOUD_SYNCED
    return LOCAL_ONLY

# ---------------------------------------------------------------------------
# Orphan detection (deletion records without a matching local row)
# ---------------------------------------------------------------------------

def find_orphaned_deletions(ck: dict, local_rowids: set[int], local_guids: set[str]) -> list[dict]:
    orphans = []
    for rid in ck["deleted_rowids"]:
        if rid not in local_rowids:
            orphans.append({"rowid": rid, "guid": None, "status": LOCAL_DELETED})
    for guid in ck["deleted_guids"]:
        if guid not in local_guids:
            orphans.append({"rowid": None, "guid": guid, "status": LOCAL_DELETED})
    return orphans

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(BANNER)

    ap = argparse.ArgumentParser(
        description="Classify iMessage records by CloudKit sync status"
    )
    ap.add_argument("--input", required=True, type=Path,
                    help="iMsgForensic_* folder or merged_timeline folder")
    ap.add_argument("--output", default=None, type=Path,
                    help="Output folder (default: same as --input)")
    args = ap.parse_args()

    folder  = args.input
    out_dir = args.output or folder

    if not folder.exists():
        print(f"[!] Folder not found: {folder}")
        sys.exit(1)

    # Locate cloudkit_probe.json — may be directly in folder or in a subfolder
    probe_path = folder / "cloudkit_probe.json"
    if not probe_path.exists():
        for candidate in folder.rglob("cloudkit_probe.json"):
            probe_path = candidate
            break

    if not probe_path.exists():
        print("[!] cloudkit_probe.json not found.")
        print("    Run core.py first — it probes CloudKit tables automatically.")
        sys.exit(1)

    # Locate message records
    records_path = folder / "export_raw.json"
    if not records_path.exists():
        records_path = folder / "unified_timeline.json"   # merged_timeline output
    if not records_path.exists():
        print("[!] No export_raw.json or unified_timeline.json found.")
        sys.exit(1)

    print(f"[*] CloudKit probe : {probe_path}")
    print(f"[*] Message records: {records_path}")

    with open(probe_path, encoding="utf-8") as f:
        probe: dict = json.load(f)

    with open(records_path, encoding="utf-8") as f:
        records: list[dict] = json.load(f)

    if not probe:
        print("\n[~] cloudkit_probe.json is empty — no CloudKit tables were present")
        print("    This database was never synced via iCloud, or iCloud Messages is disabled.")
        sys.exit(0)

    print(f"\n[*] {len(probe)} CloudKit table(s) in probe")
    print(f"[*] {len(records)} message records to classify")

    # Build local sets
    local_rowids: set[int]  = set()
    local_guids:  set[str]  = set()
    for r in records:
        rid = r.get("ROWID") or r.get("rowid")
        if rid is not None:
            try:
                local_rowids.add(int(rid))
            except (ValueError, TypeError):
                pass
        guid = r.get("reply_to_guid") or r.get("guid")
        if guid:
            local_guids.add(str(guid).strip())

    # Analyse CloudKit tables
    ck = analyse_cloudkit(probe, local_rowids, local_guids)

    print(f"\n[*] CloudKit deletion records : {len(ck['deleted_rowids'])} ROWIDs, "
          f"{len(ck['deleted_guids'])} GUIDs")
    print(f"[*] CloudKit sync records     : {len(ck['synced_rowids'])} ROWIDs, "
          f"{len(ck['synced_guids'])} GUIDs")

    # Classify every local record
    classified: list[dict] = []
    counts: dict[str, int] = {
        ICLOUD_SYNCED: 0, LOCAL_ONLY: 0, ICLOUD_DELETED: 0, UNKNOWN: 0
    }

    for r in records:
        rid  = None
        try:
            rid = int(r.get("ROWID") or r.get("rowid") or 0) or None
        except (ValueError, TypeError):
            pass
        guid  = r.get("reply_to_guid") or r.get("guid") or None
        status = classify_record(rid, guid, ck) if rid or guid else UNKNOWN

        counts[status] = counts.get(status, 0) + 1
        classified.append({
            "ROWID":        rid,
            "guid":         guid,
            "date_local":   r.get("date_local") or r.get("timestamp_normalized"),
            "contact":      r.get("contact"),
            "text_preview": (str(r.get("text") or "")[:80]) or None,
            "sync_status":  status,
        })

    # Find orphaned deletions (LOCAL_DELETED — cloud says gone, row not in local db)
    orphans = find_orphaned_deletions(ck, local_rowids, local_guids)
    counts[LOCAL_DELETED] = len(orphans)

    # Write output
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "analyser_version": "1.0",
        "analysed_at": datetime.now().isoformat(),
        "source_folder": str(folder),
        "counts": counts,
        "table_coverage": ck["table_coverage"],
        "classified_records": classified,
        "local_deleted_orphans": orphans,
    }

    out_path = out_dir / "cloudkit_classification.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"""
[+] Classification complete → {out_path}

    {ICLOUD_SYNCED:<18} {counts.get(ICLOUD_SYNCED, 0):>6}
    {LOCAL_ONLY:<18} {counts.get(LOCAL_ONLY, 0):>6}
    {ICLOUD_DELETED:<18} {counts.get(ICLOUD_DELETED, 0):>6}  ← tombstones (cloud-deleted, locally present)
    {LOCAL_DELETED:<18} {counts.get(LOCAL_DELETED, 0):>6}  ← purged locally, deletion record in cloud
    {UNKNOWN:<18} {counts.get(UNKNOWN, 0):>6}

ICLOUD_DELETED records have the highest forensic value — they were
deleted from the cloud but the local row survives.

Next:
  python3 parser.py  --input "{folder}"
  python3 report.py  --input "{folder}" --cloudkit "{out_path}"
""")

if __name__ == "__main__":
    main()
