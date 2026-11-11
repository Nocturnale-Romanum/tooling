"""Write predicted signs into the GABC snippets; write out stropha and virga shorthands."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nrparse import *

TOK = re.compile(r"\[[^\]]*\]|(?<![_'.\d])[cf]b?[1-5](?:@[cf]b?[1-5])?|[zZ][0+\-]?|[a-nA-N]\+|[a-n](?:##|[xy#XY])\??"
                 r"|::|[,;:`^]\d?'?_?|_+\d*|\.+\d*|[a-nA-N](?:[vVsoOw~<>qrR=]\d*|\d)*")
NOTE = re.compile(r'[a-nA-N](?:[vVsoOw~<>qrR=]\d*|\d)*$')


def split_token(t):
    """One string per note: fss -> fs, fs."""
    out, cur, i, last = [], t[0], 1, ''
    while i < len(t):
        c = t[i]
        if c in 'vs' and last == c:
            # fss, fvv: always written out (fsfs, fvfv), since tools disagree on fss_ (marteo, 09/11/2026)
            out.append(cur)
            cur = t[0].lower() + c
        else:
            cur += c
        if not c.isdigit():
            last = c
        i += 1
    out.append(cur)
    return out


def annotate(s, sg, dg, n0):
    """GABC snippet s with signs; sg(i) gives 'E', 'D' or 'N' for note i, dg(i) the episema digit."""
    parts, i, pos = [], n0, 0
    for mo in TOK.finditer(s):
        if mo.start() > pos:
            parts.append(('x', s[pos:mo.start()]))
        t = mo.group()
        pos = mo.end()
        if t[0] in '_.':
            continue
        if NOTE.match(t):
            for u in split_token(t):
                parts.append(('n', u, i))
                i += 1
        else:
            parts.append(('x', t))
    if pos < len(s):
        parts.append(('x', s[pos:]))
    plainE = lambda p: p[0] == 'n' and 'E' in sg(p[2]) and not dg(p[2])
    out = []
    for k, p in enumerate(parts):
        if p[0] == 'x':
            out.append(p[1])
            continue
        out.append(p[1])
        cur = sg(p[2])
        nxt = parts[k + 1] if k + 1 < len(parts) else None
        if 'E' in cur:
            if dg(p[2]):
                out.append('_' + dg(p[2]))
            elif not (nxt is not None and plainE(nxt)):
                n, b = 1, k
                while b - 1 >= 0 and plainE(parts[b - 1]):
                    n += 1
                    b -= 1
                out.append('_' * n)
        if 'D' in cur and not (nxt is not None and nxt[0] == 'n' and 'D' in sg(nxt[2])):
            prev = parts[k - 1] if k else None
            out.append('..' if prev is not None and prev[0] == 'n' and 'D' in sg(prev[2]) else '.')
    return ''.join(out), i


def rewrite(path, sm, dm):
    """(header, notation) of the file with the signs sm[(group, note)] and digits dm[(group, note)]."""
    t = open(path, encoding='utf-8', errors='replace').read()
    head, sep, n = t.rpartition('%%')
    gi = [0]

    def rep(mo):
        g = gi[0]
        gi[0] += 1
        p = mo.group(2).split('|')
        i = 0
        for k in range(0, len(p), 2):
            p[k], i = annotate(p[k], lambda x: sm.get((g, x), 'N'), lambda x: dm.get((g, x), ''), i)
        return mo.group(1) + '(' + '|'.join(p) + ')'
    return head, RE_GROUP.sub(rep, n)


def notes_of(g):
    ns = []
    p = g.split('|')
    for k in range(0, len(p), 2):
        parse_notes(p[k], ns, k // 2)
    return ns


RE_SH = re.compile(r'(\[[^\]]*\])|([a-nA-N])(s{2,}|v{2,})')


def on_gabc(body, fn):
    """Apply fn to the GABC snippets only: the NABC has its own ss (lss2)."""
    def rep(mo):
        p = mo.group(2).split('|')
        p[0::2] = [fn(x) for x in p[0::2]]
        return mo.group(1) + '(' + '|'.join(p) + ')'
    return RE_GROUP.sub(rep, body)


def expand_shorthands(body):
    """fss -> fsfs, fvvv -> fvfvfv, in the GABC snippets."""
    def one(m):
        return m.group(1) or m.group(2) + m.group(3)[0] + ''.join(m.group(2).lower() + c for c in m.group(3)[1:])
    return on_gabc(body, lambda x: RE_SH.sub(one, x))


def shorthands_left(body):
    """Shorthands still present: fss, fvv, and fs_s or fs.s."""
    left = []
    pat = re.compile(r"[a-nA-N](?:s{2,}|v{2,})|[a-nA-N]([sv])[_.\d'<>~]+\1")

    def look(x):
        left.extend(m.group() for m in pat.finditer(re.sub(r'\[[^\]]*\]', '', x)))
        return x
    on_gabc(body, look)
    return left
