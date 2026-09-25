#!/usr/bin/env python3
"""
Drift guard for the iMessage forensic toolkit.

The security-relevant code exists twice:
  - in the standalone CLI scripts (core.py, parser.py, merge.py, report.py,
    extractors/*.py)
  - in the six Python heredocs embedded in imessage_ultimate_launcher.command
    (CORE, CK, PARSER, REPORT, REORG, PLATFORM)

The copies are separate programs with different features and CLI surfaces, so
a plain textual diff is not meaningful. Instead this script asserts that each
listed SECURITY-CRITICAL invariant is present in every copy that needs it, so a
fix can't land in one place but not the other (the bug that produced v9.3).

It checks ONLY the invariants listed below. Other logic drift between a
standalone script and its heredoc is not detected. It also fails if the launcher
gains a *_PY_EOF heredoc that isn't registered here, so a new embedded module
can't go unguarded.

Output is ASCII-only, so it also works on Windows consoles (cp1252).

Run:   python3 sync_check.py
Exit:  0 if every invariant holds, 1 (with a report) otherwise.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAUNCHER = HERE / "imessage_ultimate_launcher.command"

# Heredoc end-markers embedded in the launcher.
HEREDOC_MARKERS = [
    "CORE_PY_EOF", "CK_PY_EOF", "PARSER_PY_EOF", "REPORT_PY_EOF", "REORG_PY_EOF",
    "PLATFORM_PY_EOF",
]

# Matches every `cat << 'SOMETHING_PY_EOF'` heredoc opener in the launcher.
HEREDOC_OPENER = re.compile(r"cat\s*<<\s*'(\w+_PY_EOF)'")


def extract_heredocs(text: str) -> dict[str, str]:
    """Return {marker: body} for each `cat <<'MARKER' ... MARKER` block."""
    out: dict[str, str] = {}
    for marker in HEREDOC_MARKERS:
        m = re.search(
            rf"cat\s*<<\s*'{marker}'.*?\n(.*?)\n{marker}\n",
            text, re.DOTALL,
        )
        out[marker] = m.group(1) if m else ""
    return out


def at_least_two(token: str):
    """Predicate: token appears >= 2 times (i.e. defined AND applied)."""
    return lambda s: s.count(token) >= 2


def has(*patterns: str):
    """Predicate: every regex pattern is found."""
    compiled = [re.compile(p) for p in patterns]
    return lambda s: all(c.search(s) for c in compiled)


# Each invariant lists the sources that MUST satisfy the given predicate.
# Source keys: a standalone filename, or "launcher:MARKER" for a heredoc.
INVARIANTS = [
    ("formula-injection guard defined", has(r"_FORMULA_PFX", r"def _safe"), [
        "core.py", "parser.py", "merge.py", "extractors/normalize.py",
        "launcher:CORE_PY_EOF", "launcher:PARSER_PY_EOF", "launcher:REORG_PY_EOF",
        "launcher:PLATFORM_PY_EOF",
    ]),
    ("formula-injection guard applied (not just defined)", at_least_two("_safe("), [
        "core.py", "parser.py", "merge.py", "extractors/normalize.py",
        "launcher:CORE_PY_EOF", "launcher:PARSER_PY_EOF", "launcher:REORG_PY_EOF",
        "launcher:PLATFORM_PY_EOF",
    ]),
    ("SQLite table name SQL-quoted in CloudKit probe", has(r"'\"\"'", r'FROM "'), [
        "core.py", "launcher:CORE_PY_EOF",
    ]),
    ("WAL carving has count + length caps", has(r"50_?000", r"2_?000"), [
        "core.py", "launcher:CORE_PY_EOF",
    ]),
    ("symlink artifacts are logged", has(r"is_symlink"), [
        "core.py", "launcher:CORE_PY_EOF",
    ]),
    ("report ships CSP + AI boundary + banner + risk flags", has(
        r"Content-Security-Policy", r"FORENSIC BOUNDARY", r"sec-banner", r"risk_flags",
    ), [
        "report.py", "launcher:REPORT_PY_EOF",
    ]),
    ("WAL attribution engine present (threshold + scorer)", has(
        r"ATTRIBUTED_THRESHOLD|_ATTR_THRESH", r"top_platform",
    ), [
        "extractors/attribution.py", "launcher:PARSER_PY_EOF",
    ]),
    ("platform-organized report sections present", has(
        r"platform_section",
    ), [
        "report.py", "launcher:REPORT_PY_EOF",
    ]),
    ("misc/unattributed tab present for unclaimed fragments", has(
        r"misc_section|unattributed",
    ), [
        "report.py", "launcher:REPORT_PY_EOF",
    ]),
    ("attribution confidence badge present in report", has(
        r"conf-badge",
    ), [
        "report.py", "launcher:REPORT_PY_EOF",
    ]),
]


def main() -> int:
    if not LAUNCHER.exists():
        print(f"[!] Launcher not found: {LAUNCHER}")
        return 1

    launcher_text = LAUNCHER.read_text(encoding="utf-8")
    unregistered = sorted(set(HEREDOC_OPENER.findall(launcher_text)) - set(HEREDOC_MARKERS))
    if unregistered:
        print(f"[!] Unregistered heredoc(s) in the launcher: {', '.join(unregistered)}")
        print("    Add them to HEREDOC_MARKERS and to the invariants that apply.")
        return 1

    heredocs = extract_heredocs(launcher_text)
    missing_heredocs = [m for m, body in heredocs.items() if not body]
    if missing_heredocs:
        print(f"[!] Could not extract heredoc(s): {', '.join(missing_heredocs)}")
        return 1

    sources: dict[str, str] = {}

    def load(key: str) -> str:
        if key in sources:
            return sources[key]
        if key.startswith("launcher:"):
            sources[key] = heredocs[key.split(":", 1)[1]]
        else:
            sources[key] = (HERE / key).read_text(encoding="utf-8")
        return sources[key]

    failures: list[str] = []
    for desc, predicate, keys in INVARIANTS:
        for key in keys:
            if not predicate(load(key)):
                failures.append(f"  FAIL {desc}\n       missing in: {key}")

    print("iMessage forensic toolkit - embedded/standalone drift check\n")
    if failures:
        print("DRIFT DETECTED - security invariants out of sync:\n")
        print("\n".join(failures))
        print(f"\n{len(failures)} invariant(s) failed. "
              "Port the fix to BOTH the standalone module and the launcher heredoc.")
        return 1

    print(f"OK - all {len(INVARIANTS)} security invariants present in every listed copy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
