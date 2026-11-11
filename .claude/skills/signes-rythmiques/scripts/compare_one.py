"""Compare a generated piece with the version marteo committed, syllable by syllable:
signs, NABC heights, notes or neumes, text.

Usage: python compare_one.py <ID> [--repo PATH] [--samples DIR]
  compares <samples>/<ID>_marteo.gabc (copy kept by gen_one.py) with <repo>/gabc/<ID>_marteo.gabc"""
import argparse, os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nrparse import *

ap = argparse.ArgumentParser()
ap.add_argument('id')
ap.add_argument('--repo', default='.')
ap.add_argument('--samples', default=os.path.join(tempfile.gettempdir(), 'signes-rythmiques'))
a = ap.parse_args()
i = a.id
mine = open(os.path.join(a.samples, f'{i}_marteo.gabc'), encoding='utf-8').read()
his = open(os.path.join(a.repo, 'gabc', f'{i}_marteo.gabc'), encoding='utf-8').read()
same_head = mine.partition('%%')[0].split() == his.partition('%%')[0].split()
print('en-tete identique', same_head)
if not same_head:
    print(his.partition('%%')[0])
A = RE_GROUP.findall(mine.rpartition('%%')[2])
B = RE_GROUP.findall(his.rpartition('%%')[2])
print('groupes', len(A), len(B))
strip = lambda s: re.sub(r'_+\d*|\.+\d*', '', s)
nh = lambda s: re.sub(r'(?<=[a-z\->~SGM\d])h[a-np]', '', s)
sig = rise = other = txt = 0
for (ta, ga), (tb, gb) in zip(A, B):
    if ta.strip() != tb.strip():
        txt += 1
        print('TEXTE', repr(ta.strip()), repr(tb.strip()))
    if ga == gb:
        continue
    pa, pb = ga.split('|'), gb.split('|')
    ga_, gb_ = pa[0::2], pb[0::2]
    na, nb = pa[1::2], pb[1::2]
    kinds = []
    if ga_ != gb_:
        kinds.append('signes' if [strip(x) for x in ga_] == [strip(x) for x in gb_] else 'notes')
    if na != nb:
        kinds.append('hauteurs' if [nh(x) for x in na] == [nh(x) for x in nb] else 'neumes')
    print(f"{ta.strip():10s} {'+'.join(kinds):16s} moi {ga}\n{'':27s}toi {gb}")
    sig += 'signes' in kinds
    rise += 'hauteurs' in kinds
    other += ('notes' in kinds) + ('neumes' in kinds)
print('syllabes differentes : signes', sig, 'hauteurs', rise, 'notes ou neumes', other, 'texte', txt)
