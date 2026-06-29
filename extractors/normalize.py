"""
Normalize message rows from any platform into the common CSV schema.

All extractors call normalize_rows() before returning their results so the
report, merge, and parser modules can consume any platform without special-casing.
"""
import datetime as _dt
from typing import Any

COMMON_HEADERS = [
    "ROWID", "date_local", "contact", "text", "is_from_me", "is_delivered",
    "is_read", "is_empty", "error", "has_attachment", "summary_info",
    "reply_to_guid", "thread", "attachment_path", "attachment_mime", "platform",
]

_FORMULA_PFX = ('=', '+', '-', '@', '\t', '\r')


def _safe(v: Any) -> Any:
    s = "" if v is None else str(v)
    return ("'" + s) if (s and s[0] in _FORMULA_PFX) else v


def ms_to_local(ts_ms: int | float | None) -> str:
    """Convert Unix millisecond timestamp → 'YYYY-MM-DD HH:MM:SS' local time."""
    if not ts_ms:
        return ""
    try:
        return _dt.datetime.fromtimestamp(float(ts_ms) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts_ms)


def sec_to_local(ts_s: int | float | None) -> str:
    """Convert Unix second timestamp → 'YYYY-MM-DD HH:MM:SS' local time."""
    if not ts_s:
        return ""
    try:
        return _dt.datetime.fromtimestamp(float(ts_s)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts_s)


def normalize_row(row: dict, platform: str) -> dict:
    """Ensure a row has all COMMON_HEADERS keys, applying _safe() to text fields."""
    out = {h: None for h in COMMON_HEADERS}
    out.update(row)
    out["platform"] = platform
    for field in ("text", "contact", "thread"):
        out[field] = _safe(out.get(field))
    return out


def normalize_rows(rows: list[dict], platform: str) -> list[dict]:
    return [normalize_row(r, platform) for r in rows]
