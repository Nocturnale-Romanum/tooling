# Quality checks for Nocturnale Romanum

    cd tooling && python3 -m quality            # all checks on gabc/*_marteo.gabc
    python3 -m quality --set base             # base pieces <ID>.gabc (also: marteo, all)
    python3 -m quality --list
    python3 -m quality --by-category          # issues grouped by check and category, i.e. by batch to process
    python3 -m quality --check ob-cb FILE...

Exit status is 1 when an issue is found. To add a check, create `checks/<name>.py`
with `NAME`, `DESCRIPTION` and `check(text)` yielding `(offset, message)` or `(offset, message, category)`
(categories listed, in batch order, in an optional `CATEGORIES` list of `(key, label)`), and register it in `checks/__init__.py`.

| Check | What it verifies |
|---|---|
| `ob-cb` | every NABC `ob` is closed by a `cb` before the next `ob` or the end of the piece |
| `repetenda` | in responsories, the repetendum after each verse starts with the `<sp>` marking where it starts in the respond (`R/` for the beginning), quotes the respond syllable by syllable (text, GABC, NABC ignoring `lse<n>`, pitch descriptors, `ob`/`cb` and spacing) and ends with a period; a bare `<sp>+</sp>` after the verse is accepted, and a repetendum written as pure text (`Sanct{o}. <sp>+</sp> Pasce.(ed.. ::)`) is only checked for its marker, text and period |
| `asterisk` | antiphons, responsories and invitatories (not psalms, hymns, orations) have a `<sp>*</sp>`; next to a bar it is written right under it: `<sp>*</sp>(,)`, not `(,) <sp>*</sp>` nor `<sp>*</sp> (,)`; in invitatories it follows the bar instead: `(;) <sp>*</sp> Ve(…)` |
| `euouae` | antiphons (`office-part:an`) have exactly one `<eu>…</eu>`, holding `E U O U A E.` or `Et sic finiátur.`, whose melody (transposed to c4) is the one of the differentia of the `mode:` header; the table is `DIFFERENTIAE` in `checks/euouae.py` |

## Reports

    python3 -m quality.versets -o versets-repons.html   # responsory verses: standard melodies by mode, deviations, proper verses

`versets.py` is deterministic; the fixed text of the page is in `versets_template.html`.
