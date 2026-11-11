"""Raise the NABC of a syllable when a high note carries an episema (marteo's rules, 09/11/2026).

- Minimal height of the syllable: i_ -> hh, j_ -> hj, k_ -> hl (l_ and above: hl).
- _0 (below the note) and the first note of a pes (below the note) do not count.
- Normally the whole syllable moves by one factor.
- If that factor would take a neume past hl, the heights are spread evenly between the minimal
  height and hl: the lowest neumes rise more, the highest less.
- A neume dcrochu already put above hl stays where it is.
Usage: python raise_nabc.py <file.gabc> [--write]"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nrparse import *

LET = 'abcdefghijklmnp'
NEED = {'i': 'h', 'j': 'j', 'k': 'l', 'l': 'l', 'm': 'l', 'n': 'l'}
CEILING = LET.index('l')


def pitches(s):
    out = []
    i = 0
    while i < len(s):
        m = RE_TOK.match(s, i)
        if not m:
            i += 1
            continue
        i = m.end()
        if m.group('gl'):
            g = re.search(r'h([a-np])$', m.group('gl'))
            out.append(g.group(1) if g else 'f')
    return out


def lift(s, fn):
    """Same NABC with each height passed through fn; a neume without height stands at the default hf."""
    out, i = [], 0
    while i < len(s):
        m = RE_TOK.match(s, i)
        if not m:
            out.append(s[i])
            i += 1
            continue
        i = m.end()
        t = m.group()
        if m.group('gl') or m.group('br'):
            g = re.search(r'h([a-np])$', t)
            if g:
                t = t[:-2] + 'h' + LET[fn(LET.index(g.group(1)))]
            else:
                t = t + 'h' + LET[fn(LET.index('f'))]
        elif m.group('sp') and m.group('spp'):
            t = t[:-1] + LET[fn(LET.index(t[-1]))]
        out.append(t)
    return ''.join(out)


def notes_of_group(g):
    ns = []
    p = g.split('|')
    for k in range(0, len(p), 2):
        parse_notes(p[k], ns, k // 2)
    return ns


def need_of(ns):
    """Lowest height the syllable's NABC must reach, or None."""
    best = None
    for q, n in enumerate(ns):
        nx = ns[q + 1] if q + 1 < len(ns) else None
        pes = (nx is not None and nx.seg == n.seg and not n.sep and not n.cap and 'v' not in n.shape.lower()
               and nx.pitch > n.pitch and '1' not in n.epd)
        if n.ep and '0' not in n.epd and not pes and n.pitch in NEED:
            r = NEED[n.pitch]
            if best is None or LET.index(r) > LET.index(best):
                best = r
    return best


def mapping(ps, need):
    """Height map for a syllable (indices in LET), or None if nothing moves. Returns (fn, spread?)."""
    R = LET.index(need)
    low = min(ps)
    if low >= R:
        return None
    k = R - low
    under = [p for p in ps if p <= CEILING]
    top = max(under)
    if top + k <= CEILING:
        spread = False
        T = top + k
    else:
        spread = True
        T = CEILING

    def fn(h):
        if h > CEILING:
            return h                     # above hl in dcrochu: untouched
        if h <= low:
            return R
        if h >= top:
            return T
        return int(R + (h - low) * (T - R) / (top - low) + 0.5)
    return fn, spread


def raise_group(g):
    """Returns (new group, moved?, spread?)."""
    p = g.split('|')
    if len(p) < 2:
        return g, False, False
    need = need_of(notes_of_group(g))
    if need is None:
        return g, False, False
    ps = [LET.index(c) for k in range(1, len(p), 2) for c in pitches(p[k])]
    if not ps:
        return g, False, False
    mp = mapping(ps, need)
    if mp is None:
        return g, False, False
    fn, spread = mp
    for x in range(1, len(p), 2):
        p[x] = lift(p[x], fn)
    return '|'.join(p), True, spread


def raise_body(body):
    """Whole notation; returns (new notation, list of changes: text, old, new, spread?)."""
    changes = []

    def rep(mo):
        ng, moved, spread = raise_group(mo.group(2))
        if moved:
            changes.append((mo.group(1).strip(), mo.group(2), ng, spread))
        return mo.group(1) + '(' + ng + ')'
    return RE_GROUP.sub(rep, body), changes


if __name__ == '__main__':
    path = sys.argv[1]
    t = open(path, encoding='utf-8', newline='').read()
    h, sep, b = t.rpartition('%%')
    nb, ch = raise_body(b)
    for c in ch:
        print(f"{c[0]!r}\n   {c[1]}\n   {c[2]}{'   TASSE' if c[3] else ''}")
    print(len(ch), 'syllabes elevees')
    if '--write' in sys.argv:
        open(path, 'w', encoding='utf-8', newline='').write(h + sep + nb)
