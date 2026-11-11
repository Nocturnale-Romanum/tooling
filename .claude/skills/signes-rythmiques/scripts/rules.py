"""Rules, version 2 (after marteo's review). Tables are fitted on the training rows only."""
import collections, re
PAIR = {'cl', 'cl-', 'pe', 'sf-'}      # the two last notes take ".." before a bar
SINGLE0 = {'vi-', 'ta-', 'ta', 'vi', 'ppt', 'ppu', 'sut', 'suu'}


def lst(r):
    return [l for l in r['lsraw'] if re.match(r'lst[bmw]?\d$', l)]


def has_lsc(r):
    return any(re.match(r'lsc\d$', l) for l in r['lsraw'])


def key(r):
    k = (r['atom'], r['alen'], r['idx'])
    if r['base'] == 'vs':
        k += (r['after_ql'],)
    return k


def fit_table(R):
    T = collections.defaultdict(collections.Counter)
    for r in R:
        if r['next_w'] or lst(r) or r['abar'] >= 2:
            continue
        if not r['lastsyl'] and r['alen'] == 1 and r['atom'] in ('ta', 'vi'):
            continue
        T[key(r)]['E' if 'E' in r['sign'] else 'N'] += 1
    B = collections.defaultdict(collections.Counter)
    for k, v in T.items():
        p = 'only' if k[1] == 1 else ('first' if k[2] == 0 else ('last' if k[2] == k[1] - 1 else 'mid'))
        B[('*', k[0], p)].update(v)
    out = {k: v['E'] >= v['N'] for k, v in T.items()}
    out.update({k: v['E'] >= v['N'] for k, v in B.items()})
    return out


def episema(r, T):
    k = key(r)
    e = T[k] if k in T else T.get(('*', r['atom'], r['pos']), False)
    if r['atom'] == 'ppt':
        # a lone tractulus, or a non-final tractulus of a rising chain
        e = r['next_role'] == 'pp' or r['cx_i'] == 0
    L = lst(r)
    if L and r['role'] == 'base':
        d = {x[-1] for x in L}
        if r['base'] == 'pf':
            e = True
        elif r['atom'] == 'cl':
            e = '2' in d and not has_lsc(r)     # cllst3 has no sign in the corpus
        else:
            e = e or r['apeak']
    if r['atom'] in ('clS', 'clS-') and has_lsc(r) and r['pos'] == 'last':
        e = False
    if r['atom'] in ('ta', 'vi') and not r['lastsyl']:
        e = (r['next_int_any'] or 0) > 0        # single note in a melisma, before a rising step
    if r['atom'] in ('clS', 'clS-', 'toS2') and r['pos'] == 'last' and r['next_int_any'] == 0:
        e = False                               # before a repercussion
    if r['next_w']:
        e = False                               # note before a quilisma
    return e


def dot(r):
    if r['cue']:
        return False
    if r['lastsyl'] and r['bar'] >= 2:
        return True
    if r['abar'] >= 2 and r['atom'] in PAIR and r['alen'] - r['idx'] == 2:
        return True
    if r['precad_uni'] and r['accent'] and r['role'] == 'base' and r['alen'] == 1 and r['nxlen'] == 1:
        return True
    return False


def predict_one(r, T):
    if dot(r):
        return 'D'
    return 'E' if episema(r, T) else 'N'


def predict_piece(rows, T):
    """Signs for one piece, keyed (gi, ni); cue notes copy the note of the body."""
    P = {(r['gi'], r['ni']): predict_one(r, T) for r in rows}
    for r in rows:
        if r['cue_src'] is not None:
            b = P.get((r['cue_src'], r['ni']))
            if b is not None:
                P[(r['gi'], r['ni'])] = b
    return P


def digits_piece(rows, P):
    """Episema digits for one piece, keyed (gi, ni)."""
    out = {}
    pos = {(r['gi'], r['ni']): i for i, r in enumerate(rows)}
    for i, r in enumerate(rows):
        k = (r['gi'], r['ni'])
        if P[k] != 'E':
            continue
        nx = rows[i + 1] if i + 1 < len(rows) else None
        nE = bool(nx and P[(nx['gi'], nx['ni'])] == 'E')
        up = (r['next_int_any'] or 0) > 0
        d = ''
        if up and r['sep'] and not nE:
            if r['atom'] in SINGLE0 and r['alen'] == 1:
                d = '0'
            elif r['alen'] > 1 and r['next_atom_same']:
                d = '0'
        if r['atom'] == 'pr-' and r['idx'] == 0 and r['pitch'] <= 'f':
            d = '1'
        if r['atom'] == 'tr-3' and r['pos'] == 'last' and r['next_atom'] == 'vi-' and nE:
            d = '2'
        if d:
            out[k] = d
    return out


def split_pieces(R):
    by = collections.defaultdict(list)
    for r in R:
        by[r['pid']].append(r)
    return by


def score_rows(R, T):
    """(sign score, digit score, predictions attached)"""
    c = collections.Counter()
    dg = collections.Counter()
    out = []
    for pid, rows in split_pieces(R).items():
        P = predict_piece(rows, T)
        Dg = digits_piece(rows, P)
        for r in rows:
            k = (r['gi'], r['ni'])
            r['pred'] = P[k]
            r['pdg'] = Dg.get(k, '')
            c[(r['sign'], r['pred'])] += 1
            if 'E' in r['sign'] and 'E' in r['pred']:
                t = next((x for x in ('0', '1', '2') if x in r['epd']), '')
                dg[(t, r['pdg'])] += 1
            out.append(r)
    return c, dg, out


def summary(c):
    tot = sum(c.values())
    ok = sum(v for (a, b), v in c.items() if a == b)
    s = {'exact': round(ok / tot, 4), 'n': tot}
    for x in 'ED':
        tp = sum(v for (a, b), v in c.items() if x in a and x in b)
        fp = sum(v for (a, b), v in c.items() if x not in a and x in b)
        fn = sum(v for (a, b), v in c.items() if x in a and x not in b)
        s[x] = (round(tp / (tp + fp or 1), 3), round(tp / (tp + fn or 1), 3), tp + fn)
    return s


def sumdg(dg):
    tot = sum(dg.values())
    ok = sum(v for (a, b), v in dg.items() if a == b)
    base = sum(v for (a, b), v in dg.items() if a == '')
    s = {'exact': round(ok / max(tot, 1), 4), 'sans chiffre': round(base / max(tot, 1), 4), 'n': tot}
    for x in '012':
        tp = dg.get((x, x), 0)
        fp = sum(v for (a, b), v in dg.items() if b == x and a != x)
        fn = sum(v for (a, b), v in dg.items() if a == x and b != x)
        s['_' + x] = (round(tp / (tp + fp or 1), 3), round(tp / (tp + fn or 1), 3), tp + fn)
    return s
