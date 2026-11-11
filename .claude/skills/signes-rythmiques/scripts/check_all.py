"""Generate every remaining target in memory (nothing is written) and check the invariants:
notes unchanged, no shorthand left, NABC raise consistent. Run after any change to the rules or the model.

Usage: python check_all.py [--repo PATH] [ID ...]"""
import argparse, collections, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nrparse import *
from generate import generate, targets
from raise_nabc import LET, CEILING, pitches, need_of, notes_of_group

ap = argparse.ArgumentParser()
ap.add_argument('ids', nargs='*')
ap.add_argument('--repo', default='.')
a = ap.parse_args()
os.chdir(a.repo)
ids = a.ids or targets()
bad = collections.Counter()
ex = collections.defaultdict(list)
signs = collections.Counter()
notes = unal = moved = spread = 0
nh = lambda s: re.sub(r'(?<=[a-z\->~SGM\d])h[a-np]', '', s)
for i in ids:
    G = generate(i)
    notes += len(G['rows'])
    unal += G['stat']['unaligned_notes']
    signs.update(G['P'].values())
    if not G['same']:
        bad['notes changees'] += 1
        ex['notes changees'].append(i)
    if G['left']:
        bad['raccourcis restants'] += 1
        ex['raccourcis restants'].append((i, G['left']))
    for txt, old, new, sp in G['raised']:
        moved += 1
        spread += sp
        po = [LET.index(c) for x in old.split('|')[1::2] for c in pitches(x)]
        pn = [LET.index(c) for x in new.split('|')[1::2] for c in pitches(x)]
        need = LET.index(need_of(notes_of_group(old)))
        k = (i, txt)
        if old.split('|')[0::2] != new.split('|')[0::2]:
            bad['notes modifiees par l elevation'] += 1
        if nh('|'.join(old.split('|')[1::2])) != nh('|'.join(new.split('|')[1::2])):
            bad['neumes modifies'] += 1
            ex['neumes modifies'].append(k)
        if min(pn) < need:
            bad['hauteur minimale non atteinte'] += 1
            ex['hauteur minimale non atteinte'].append(k)
        for x, y in zip(po, pn):
            if y < x:
                bad['neume abaisse'] += 1
            if x > CEILING and y != x:
                bad['neume > hl deplace'] += 1
            if x <= CEILING and y > CEILING:
                bad['neume porte au-dessus de hl'] += 1
        if any(x1 < x2 and y1 > y2 for x1, y1 in zip(po, pn) for x2, y2 in zip(po, pn)):
            bad['ordre inverse'] += 1
            ex['ordre inverse'].append(k)
        if not sp and len({y - x for x, y in zip(po, pn) if x <= CEILING}) != 1:
            bad['facteur non uniforme hors tassement'] += 1
            ex['facteur non uniforme hors tassement'].append(k)
print('pieces', len(ids), '| notes', notes, '| non alignees', unal, '| signes', dict(signs))
print('syllabes elevees', moved, '| dont tassees', spread)
print('INVARIANTS VIOLES', dict(bad))
for k, v in ex.items():
    print(' ', k, v[:5])
