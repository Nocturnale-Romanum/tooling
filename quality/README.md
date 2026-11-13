# Quality checks for Nocturnale Romanum

    cd tooling && python3 -m quality            # all checks on gabc/*_marteo.gabc
    python3 -m quality --list
    python3 -m quality --check ob-cb FILE...

Exit status is 1 when an issue is found. To add a check, create `checks/<name>.py`
with `NAME`, `DESCRIPTION` and `check(text)` yielding `(offset, message)`, and register it in `checks/__init__.py`.

| Check | What it verifies |
|---|---|
| `ob-cb` | every NABC `ob` is closed by a `cb` before the next `ob` or the end of the piece |
