"""
Platform attribution engine for the iMessage Forensic Toolkit.

Scores WAL fragments and recovered text against per-platform heuristic
patterns. Assigns confidence 0.0–1.0 per platform. Uses contact
cross-reference to boost scores when known identifiers appear in the text.

Usage:
    from extractors.attribution import attribute_fragment, build_contact_index

    idx = build_contact_index(records)
    result = attribute_fragment(fragment_text, idx)

Result shape:
    {
        "scores": [{"platform": str, "confidence": float}, ...],  # sorted desc
        "top_platform": str | None,   # None when max confidence < THRESHOLD
        "top_confidence": float,
        "is_attributed": bool,
    }
"""
import re
from typing import Any

ATTRIBUTED_THRESHOLD = 0.40    # minimum confidence to claim a platform
CONTACT_MATCH_BOOST  = 0.20    # additive boost per matching contact identifier

# ---------------------------------------------------------------------------
# Per-platform heuristic pattern sets.
# Each entry: (compiled_regex, weight).
# Weights are summed and normalised by max-possible weight for the platform.
# ---------------------------------------------------------------------------
_ATTR_PATTERNS: dict[str, list[tuple]] = {
    "iMessage": [
        (re.compile(r'imessage|icloud|apple\.com|@icloud\.com',   re.I), 0.7),
        (re.compile(r'chat\.db|Messages/chat',                    re.I), 0.9),
        (re.compile(r'\+?1\s?\(?\d{3}\)?\s?\d{3}[-.\s]\d{4}'),         0.2),
        (re.compile(r'bluebubble|sms|mms|is_from_me',             re.I), 0.5),
    ],
    "WhatsApp": [
        (re.compile(r'whatsapp|whasapp|wa\.me|whatsup',           re.I), 0.9),
        (re.compile(r'ChatStorage\.sqlite|msgstore',               re.I), 0.9),
        (re.compile(r'Missed\s+voice\s+call|Missed\s+video\s+call', re.I), 0.5),
        (re.compile(r'Messages\s+and\s+calls\s+are\s+end',        re.I), 0.8),
        (re.compile(r'end.to.end\s+encrypted',                    re.I), 0.4),
    ],
    "Signal": [
        (re.compile(r'signal\.org|signal\s+messenger',            re.I), 0.9),
        (re.compile(r'db\.sqlite.*signal|signal.*db\.sqlite',     re.I), 0.9),
        (re.compile(r'sealed\s+sender|safety\s+number|note\s+to\s+self', re.I), 0.7),
        (re.compile(r'This\s+message\s+will\s+disappear|disappearing\s+messages', re.I), 0.6),
    ],
    "Instagram": [
        (re.compile(r'instagram',                                  re.I), 0.8),
        (re.compile(r'IGDatabaseCore|instagram\.com',             re.I), 0.9),
        (re.compile(r'Direct\s+Message|story\s+reply|reel',       re.I), 0.4),
        (re.compile(r'sent\s+you\s+a\s+(photo|video|reel|message)', re.I), 0.5),
        (re.compile(r'meta\.com',                                  re.I), 0.2),
    ],
    "Facebook": [
        (re.compile(r'facebook(?!\.sqlite)|m\.me',                re.I), 0.8),
        (re.compile(r'messenger\.db|thread_key',                  re.I), 0.9),
        (re.compile(r'You\s+missed\s+a\s+call|Wave\s+to\s+friends', re.I), 0.5),
        (re.compile(r'meta\.com',                                  re.I), 0.2),
    ],
    "Snapchat": [
        (re.compile(r'snapchat|snap\.com',                        re.I), 0.9),
        (re.compile(r'main\.db.*snap|snap.*main\.db',             re.I), 0.9),
        (re.compile(r'streaks|snap\s+sent|👻',                    re.I), 0.5),
        (re.compile(r'Best\s+Friends|Snap\s+Score',               re.I), 0.6),
    ],
    "Telegram": [
        (re.compile(r'telegram|t\.me|tg://',                      re.I), 0.9),
        (re.compile(r'postboxes\.db|TelegramCore',                re.I), 0.9),
        (re.compile(r'supergroup|channel|bot\s+command|/start',   re.I), 0.4),
        (re.compile(r'This\s+message\s+was\s+deleted',            re.I), 0.4),
    ],
    "Google Messages": [
        (re.compile(r'google\s*messages|messages\.google\.com',   re.I), 0.8),
        (re.compile(r'bugle|bugle\.db|chimaera',                  re.I), 0.8),
        (re.compile(r'Delivered\s+to\s+Google|Sent\s+via\s+Google', re.I), 0.6),
        (re.compile(r'\brcs\b',                                    re.I), 0.5),
    ],
}


def score_fragment(text: str) -> dict[str, float]:
    """Return {platform: normalised_score 0.0–1.0} for every platform."""
    scores: dict[str, float] = {}
    for platform, patterns in _ATTR_PATTERNS.items():
        raw = sum(w for pat, w in patterns if pat.search(text))
        max_possible = sum(w for _, w in patterns)
        scores[platform] = min(1.0, raw / max_possible) if max_possible else 0.0
    return scores


def build_contact_index(records: list[dict]) -> dict[str, set[str]]:
    """
    Build a mapping of known contact identifiers from structured records.
    Returns {normalised_id: set_of_platforms}.
    """
    _phone  = re.compile(r'\+?1?\s*[\(\-]?\d{3}[\)\-\s]?\s*\d{3}[\-\s]?\d{4}')
    _email  = re.compile(r'[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}', re.I)
    _handle = re.compile(r'@\w{3,}')

    idx: dict[str, set[str]] = {}
    for r in records:
        platform = str(r.get("platform") or "iMessage")
        for field in ("contact", "thread"):
            raw = str(r.get(field) or "")
            for pat in (_phone, _email, _handle):
                for m in pat.findall(raw):
                    key = (re.sub(r'\D', '', m) if pat is _phone
                           else m.lower().strip())
                    if len(key) >= 7:
                        idx.setdefault(key, set()).add(platform)
    return idx


def infer_platform_from_contacts(
    text: str, contact_idx: dict[str, set[str]]
) -> dict[str, float]:
    """
    Scan `text` for phone/email/handle identifiers.
    For each match found in contact_idx, add CONTACT_MATCH_BOOST.
    Returns {platform: total_boost}.
    """
    _phone  = re.compile(r'\+?1?\s*[\(\-]?\d{3}[\)\-\s]?\s*\d{3}[\-\s]?\d{4}')
    _email  = re.compile(r'[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}', re.I)
    _handle = re.compile(r'@\w{3,}')

    boosts: dict[str, float] = {}
    for pat in (_phone, _email, _handle):
        for m in pat.findall(text):
            key = (re.sub(r'\D', '', m) if pat is _phone else m.lower().strip())
            for platform in contact_idx.get(key, set()):
                boosts[platform] = min(
                    1.0, boosts.get(platform, 0.0) + CONTACT_MATCH_BOOST
                )
    return boosts


def attribute_fragment(
    text: str, contact_idx: dict[str, set[str]] | None = None
) -> dict[str, Any]:
    """
    Score a text fragment against all platforms.
    Returns an attribution result dict.
    """
    scores = score_fragment(text)

    if contact_idx:
        for platform, boost in infer_platform_from_contacts(text, contact_idx).items():
            scores[platform] = min(1.0, scores.get(platform, 0.0) + boost)

    sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
    top_platform = sorted_scores[0][0] if sorted_scores else None
    top_conf     = sorted_scores[0][1] if sorted_scores else 0.0

    return {
        "scores": [
            {"platform": p, "confidence": round(c, 3)}
            for p, c in sorted_scores
            if c > 0.0
        ],
        "top_platform":    top_platform if top_conf >= ATTRIBUTED_THRESHOLD else None,
        "top_confidence":  round(top_conf, 3),
        "is_attributed":   top_conf >= ATTRIBUTED_THRESHOLD,
    }
