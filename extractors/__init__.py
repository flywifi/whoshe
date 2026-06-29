"""
Multi-platform message extractors for the iMessage Forensic Toolkit.

Each module exports a single function:
    extract(out_dir: Path) -> list[dict]  — returns normalized message rows

Normalized row keys match parsed_messages.csv columns:
    ROWID, date_local, contact, text, is_from_me, is_delivered, is_read,
    is_empty, error, has_attachment, summary_info, reply_to_guid, thread,
    attachment_path, attachment_mime, platform

The 'platform' key is added by these extractors (not present in iMessage output).
"""
