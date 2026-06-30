# MAINTAINER — signal-desktop extractor

## Extractor identity
- **id**: `signal-desktop`
- **detect_mode**: `auto` (no arguments — probes local filesystem)
- **platform**: macOS
- **label**: Signal Desktop Extractor

## Non-negotiable invariants
1. `detect()` must return `False` (not raise) if the Signal app directory does not exist.
2. `extract(out_dir)` must never write files outside `out_dir`.
3. Every output record must include `platform: "Signal"` and `retrieved_at` (ISO 8601).
4. The decryption key is read from `config.json` — never hardcode or log it.
5. If SQLCipher is unavailable, raise `ImportError` with a clear install message; do not silently return empty results.

## Failure modes
- `sqlcipher3` not installed → `ImportError` (expected; documented in module docstring)
- Signal not installed → `detect()` returns `False`
- DB locked by running Signal → log warning and return partial results; do not crash
- Config key missing from `config.json` → raise `ValueError("Signal config missing 'key'")`

## Regression cases
- Upgrade to new Signal Desktop version changes DB schema → `extract()` must adapt or raise a clear schema error
- WAL mode DB: ensure both `-wal` and `-shm` files are handled

## Approval-gated changes
- Any change to decryption key handling requires a second maintainer review.
- Changes to the output schema (`messages` array structure) must update `extractors_manifest.json` output_schema.

## Minority-report policy
If WAL recovery yields rows that conflict with main DB rows (same message ID, different content),
emit a minority report in the output record: `"minority_report": {"conflicts": [...]}`.
