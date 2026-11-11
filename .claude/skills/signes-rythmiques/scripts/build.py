"""Rows of features, one per GABC note aligned with a NABC atom; note lengths of the NABC glyphs."""
import collections, math, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nrparse import *
DEF = dict(vi=1, pu=1, ta=1, gr=1, un=1, cl=2, pe=2, po=3, to=3, ci=3, sc=3, pf=4, sf=4, tr=4, st=1, ds=2, ts=3, tg=3,
           bv=2, tv=3, pr=3, pi=2, vs=2, or_=1, sa=3, pq=2, ql=2, qi=2, pt=2, oc=2, ni=0)
DEF['or'] = 1


def lenprob(a, L):
    if a.role != 'base':
        return {1: 1.0}
    if a.name[:2] in ('ql', 'qi'):
        # the quilisma glyph may cover only the wavy note when another neume carries the following note
        d = {int(k): v for k, v in L.get(a.name, {'2': 1.0}).items()}
        d.setdefault(1, .1)
        return d
    if a.name in L:
        return {int(k): v for k, v in L[a.name].items()}
    b = DEF.get(a.name[:2], 1)
    if re.search(r'[>~]', a.name):
        return {b: .5, b + 1: .3, b - 1: .2} if b > 0 else {0: 1.0}
    return {b: 1.0}


def align(atoms, notes, L):
    """Best partition of the notes among the atoms: list of (atom, index, length) per note, or None."""
    n, m = len(notes), len(atoms)
    best = {(0, 0): (0.0, None, 0)}
    for i in range(m):
        pr = lenprob(atoms[i], L)
        for j in range(n + 1):
            if (i, j) not in best:
                continue
            for k, p in pr.items():
                if j + k > n or p <= 0:
                    continue
                sc = best[(i, j)][0] + math.log(p)
                seg = notes[j:j + k]
                if atoms[i].role == 'base' and seg:
                    nm = atoms[i].name
                    liq = re.search(r'[~<>]', seg[-1].shape)
                    if re.search(r'[>~]', nm) and liq:
                        sc += 1.5
                    if not re.search(r'[>~]', nm) and liq:
                        sc -= 1.5
                    if nm[:2] in ('ql', 'qi') and 'w' in seg[0].shape:
                        sc += 1.5
                key = (i + 1, j + k)
                if key not in best or best[key][0] < sc:
                    best[key] = (sc, j, k)
    if (m, n) not in best:
        return None
    out = [None] * n
    i, j = m, n
    while i > 0:
        _, pj, k = best[(i, j)]
        for x in range(k):
            out[pj + x] = (atoms[i - 1], x, k)
        i, j = i - 1, pj
    return out


def sign(n):
    return ('E' if n.ep else '') + ('D' if n.dot else '') or 'N'


def rows_for(pid, path, L, stat=None):
    h, gs = tokenise(path)
    st = {'b': False}
    groups = []
    for txt, g in gs:
        p = g.split('|')
        joint = []
        segs = []
        for k in range(0, len(p), 2):
            a0 = len(joint)
            parse_notes(p[k], joint, k // 2)   # joint parse: signs may reach back over a snippet boundary
            a = parse_nabc(p[k + 1], st) if k + 1 < len(p) else None
            segs.append((a0, len(joint), a))
        groups.append(dict(txt=txt, g=g, notes=joint, segs=[(joint[a:b], x) for a, b, x in segs]))
    for gi, G in enumerate(groups):
        nb = 0
        for H in groups[gi + 1:]:
            if H['notes']:
                break
            m = re.findall(r'::|[,;:`^]', re.sub(r'\[[^\]]*\]', '', H['g'].split('|')[0]))
            if m:
                nb = max(BAR_LEVEL[x] for x in m)
                break
        else:
            nb = 4 if G['notes'] else 0
        G['nb'] = nb
        w = True
        for H in groups[gi + 1:]:
            w = H['txt'].startswith(' ') or H['txt'] == ''
            break
        G['wordend'] = w
    seq = []
    for gi, G in enumerate(groups):
        for nn, a in G['segs']:
            if not a:
                if stat is not None and nn:
                    stat['no_nabc_notes'] += len(nn)
                seq += [(gi, x, None, 0, 0) for x in nn]
                continue
            al = align(a, nn, L)
            if al is None:
                if stat is not None:
                    stat['unaligned_notes'] += len(nn)
                    stat['unaligned_snip'] += 1
                    if stat.get('ex') is not None and len(stat['ex']) < 60:
                        stat['ex'].append((pid, G['txt'], ''.join(n.pitch for n in nn), [x.name for x in a]))
                seq += [(gi, x, None, 0, 0) for x in nn]
                continue
            if stat is not None:
                stat['aligned_notes'] += len(nn)
            seq += [(gi, x, at, i, k) for x, (at, i, k) in zip(nn, al)]
    # repetendum cue: last section, opened by a <sp> mark other than V/, R/ or *
    cue_from = None
    # section by section: a section opened by <sp>+</sp>, ‡ or R/ is a cue up to the next ::
    in_cue, start = False, True
    for G in groups:
        if start and G['notes']:
            in_cue = '<sp>' in G['txt'] and not re.search(r'<sp>\s*(V/|\*)', G['txt'])
            start = False
        G['cue'] = in_cue
        if '::' in G['g'].split('|')[0] and not start:
            start = True
    # words and stress: a marked accent, or the first syllable of a two-syllable word
    words, cur = [], []
    for gi, G in enumerate(groups):
        t = re.sub(r'<[^>]*>[^<]*</[^>]*>|<[^>]*>', '', G['txt'])
        if not re.search(r'[^\W\d_]', t):
            if not G['notes'] and cur:
                words.append(cur)
                cur = []
            continue
        if G['txt'][:1].isspace() and cur:
            words.append(cur)
            cur = []
        cur.append(gi)
    if cur:
        words.append(cur)
    for w in words:
        for gi in w:
            groups[gi]['accent'] = bool(re.search('[áéíóúýǽÁÉÍÓÚÝǼ]|œ́|ǽ', groups[gi]['txt']))
            groups[gi]['wlen'] = len(w)
            groups[gi]['wpos'] = w.index(gi)
        if len(w) == 2:
            groups[w[0]]['accent'] = groups[w[0]]['accent'] or not groups[w[1]]['accent']
    def plain(t):
        t = re.sub(r'<[^>]*>[^<]*</[^>]*>|<[^>]*>', '', t).replace('{', '').replace('}', '')
        t = unicodedata.normalize('NFD', t)
        t = ''.join(c for c in t if unicodedata.category(c) != 'Mn').replace('æ', 'ae').replace('œ', 'oe').replace('ǽ', 'ae')
        return t.lower()
    for G in groups:
        G['n'] = re.sub(r'[^a-z]', '', plain(G['txt']))
    # first word after each group, read over the following syllables of the word
    for gi, G in enumerate(groups):
        w = ''
        for j, H in enumerate(groups[gi + 1:]):
            if not H['notes']:
                continue
            t = plain(H['txt'])
            if not w:
                w = re.sub(r'[^a-z]', '', t)
                k = gi + 1 + j
                for H2 in groups[k + 1:]:
                    if not H2['notes'] or H2['txt'][:1].isspace():
                        break
                    w += re.sub(r'[^a-z]', '', plain(H2['txt']))
                break
        G['nx_word'] = w
    # cue sections: copy of the body
    start = True
    for gi, G in enumerate(groups):
        G['src'] = None
    for gi, G in enumerate(groups):
        if start and G['notes']:
            m = re.search(r'<sp>([^<]*)</sp>', G['txt'])
            start = False
            if m and m.group(1).strip() not in ('V/', '*', 'R/'):
                mk = m.group(1).strip()
                c = []
                for H in groups[gi:]:
                    if H['notes']:
                        c.append(H)
                    if '::' in H['g'].split('|')[0]:
                        break
                body = None
                for bi in range(gi):
                    if groups[bi]['notes'] and '<sp>' + mk in groups[bi]['txt'].replace(' ', '') and groups[bi]['n'] == c[0]['n']:
                        body = bi
                        break
                if body is None:
                    p0 = ''.join(n.pitch for n in c[0]['notes'])
                    for bi in range(gi):
                        if groups[bi]['notes'] and groups[bi]['n'] == c[0]['n'] and ''.join(n.pitch for n in groups[bi]['notes']) == p0:
                            body = bi
                            break
                if body is not None:
                    bd = [H for H in groups[body:gi] if H['notes']][:len(c)]
                    for a, b_ in zip(c, bd):
                        if a['n'] == b_['n'] and [n.pitch for n in a['notes']] == [n.pitch for n in b_['notes']]:
                            a['src'] = groups.index(b_)
        if '::' in G['g'].split('|')[0]:
            start = True
    for gi, G in enumerate(groups):
        nx_g = next((H for H in groups[gi + 1:] if H['notes']), None)
        G['nxfinal'] = bool(nx_g and (nx_g['nb'] >= 2 or nx_g['notes'][-1].bar >= 2))
        G['nxfirst'] = nx_g['notes'][0].pitch if nx_g else None
        G['nxlen'] = len(nx_g['notes']) if nx_g else 0
    rows = []
    for q, (gi, x, at, i, k) in enumerate(seq):
        if at is None:
            continue
        G = groups[gi]
        # the note closing this atom
        endq = q + (k - 1 - i)
        endn = seq[endq] if endq < len(seq) else seq[q]
        endG = groups[endn[0]]
        end_last = endn[1] is endG['notes'][-1]
        abar = endn[1].bar or (endG['nb'] if end_last else 0)
        ns = G['notes']
        last = x is ns[-1]
        nx = seq[q + 1] if q + 1 < len(seq) else None
        pv = seq[q - 1] if q > 0 else None
        nxa = None
        for r in seq[q + 1:q + 9]:
            if r[2] is not None and r[2] is not at:
                nxa = r[2]
                break
        rows.append(dict(
            pid=pid, part=h['part'], mode=h['mode'], syn=at.bracket, role=at.role, atom=at.name, base=at.name[:2],
            mods=at.name[2:], idx=i, alen=k,
            pos='only' if k == 1 else ('first' if i == 0 else ('last' if i == k - 1 else 'mid')),
            ls=tuple(sorted(re.sub(r'\d$', '', l) for l in at.ls)), lsraw=tuple(at.ls),
            syl_n=len(ns), syllabic=len(ns) == 1, lastsyl=last, bar=x.bar or (G['nb'] if last else 0),
            cue_src=G['src'], nx_word=G['nx_word'], cx=at.cx, epd=x.epd, sep=x.sep, next_ep=bool(nx and nx[1].ep), next_atom_same=bool(nx and nx[2] is at),
            next_pitch=nx[1].pitch if nx else '', next_cap=bool(nx and nx[1].cap), prev_ep=bool(pv and pv[1].ep),
            next_cx_same=bool(nx and nx[2] is not None and nx[2].cx == at.cx),
            first_syl=x is ns[0], raw_atom=at.raw, sig=q,
            wordend=last and G['wordend'], abar=abar, cue=G['cue'], gi=gi, ni=next(n for n, y in enumerate(ns) if y is x),
            punct=bool(re.search(r'[,;:.!?]\s*$', re.sub(r'\{|\}', '', G['txt']))),
            accent=G.get('accent', False), wlen=G.get('wlen', 0), wpos=G.get('wpos', 0),
            precad=last and G['nxfinal'], precad_uni=last and G['nxfinal'] and G['nxfirst'] == x.pitch, nxlen=G['nxlen'],
            apeak=ord(x.pitch) == max(ord(s[1].pitch) for s in seq[q - i:q - i + k] if s[2] is at),
            next_atom=nxa.name if nxa else '', next_role=nxa.role if nxa else '',
            next_w=bool(nx and 'w' in nx[1].shape),
            next_int=(ord(nx[1].pitch) - ord(x.pitch)) if nx and nx[0] == gi else None,
            next_int_any=(ord(nx[1].pitch) - ord(x.pitch)) if nx else None,
            prev_int=(ord(x.pitch) - ord(pv[1].pitch)) if pv else None,
            shape=x.shape, cap=x.cap, pitch=x.pitch, sign=sign(x), dbl=x.dbl, raw=G['g'], txt=G['txt'].strip()))
    # position inside the complex neume, for significant letters
    by = collections.defaultdict(list)
    for r in rows:
        by[(r['gi'], r['cx'])].append(r)
    for v in by.values():
        ql = False
        for k, r in enumerate(v):
            r['cx_i'], r['cx_n'] = k, len(v)
            r['after_ql'] = ql
            if r['base'] in ('ql', 'qi'):
                ql = True
    return rows


def learn_lengths(ids):
    H = collections.defaultdict(collections.Counter)
    for i in ids:
        _, gs = tokenise(f'gabc/{i}_marteo.gabc')
        st = {'b': False}
        for txt, g in gs:
            p = g.split('|')
            for k in range(1, len(p), 2):
                ns = []
                parse_notes(p[k - 1], ns, 0)
                at = parse_nabc(p[k], st)
                b = [a for a in at if a.role == 'base']
                if len(b) == 1:
                    H[b[0].name][len(ns) - sum(a.role != 'base' for a in at)] += 1
    L = {}
    for k, v in H.items():
        tot = sum(v.values())
        d = {c: n / tot for c, n in v.items() if c >= 0 and n / tot >= .02}
        de = DEF.get(k[:2], 1)
        d.setdefault(de, .02)
        L[k] = d
    return L
