"""Fit the model on the training split of the _marteo corpus and score it on the verification split.
Writes model.json only with --write. The corpus evolves: refitting changes the table slightly,
so compare the scores and run check_all.py before keeping a new model.

Usage: python train.py [--repo PATH] [--write] [--resplit]
  --resplit  draw a new 70/30 split (seed 20261108) over the current _marteo pieces with NABC and signs
             and write split.json; otherwise the split of 08/11/2026 is kept, so that scores stay comparable"""
import argparse, collections, glob, json, os, random, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from nrparse import *
from build import rows_for, learn_lengths
from rules import fit_table, score_rows, summary, sumdg
from model import save_model

ap = argparse.ArgumentParser()
ap.add_argument('--repo', default='.')
ap.add_argument('--write', action='store_true')
ap.add_argument('--resplit', action='store_true')
a = ap.parse_args()
os.chdir(a.repo)
SPLIT = os.path.join(HERE, 'split.json')
if a.resplit:
    ids = []
    for f in sorted(glob.glob('gabc/*_marteo.gabc')):
        gs = re.findall(r'\(([^()]*)\)', open(f, encoding='utf-8', errors='replace').read().rpartition('%%')[2])
        if any('|' in g for g in gs) and any(re.search(r'[_.]', g.split('|')[0]) for g in gs):
            ids.append(os.path.basename(f)[:-12])
    s = ids[:]
    random.Random(20261108).shuffle(s)
    k = round(len(s) * .3)
    json.dump({'seed': 20261108, 'test': sorted(s[:k]), 'train': sorted(s[k:])}, open(SPLIT, 'w'), indent=0)
sp = json.load(open(SPLIT))
sp = {k: [i for i in v if os.path.exists(f'gabc/{i}_marteo.gabc')] for k, v in sp.items() if k != 'seed'}
L = learn_lengths(sp['train'])
Rt = []
for i in sp['train']:
    Rt += rows_for(i, f'gabc/{i}_marteo.gabc', L)
T = fit_table(Rt)
ct, dt, Rt = score_rows(Rt, T)
print('apprentissage', len(sp['train']), 'pieces', summary(ct), sumdg(dt))
stat = dict(aligned_notes=0, unaligned_notes=0, unaligned_snip=0, no_nabc_notes=0, ex=[])
Rv = []
for i in sp['test']:
    Rv += rows_for(i, f'gabc/{i}_marteo.gabc', L, stat)
cv, dv, Rv = score_rows(Rv, T)
print('verification', len(sp['test']), 'pieces', summary(cv))
print('  chiffres', sumdg(dv))
print('  notes alignees', stat['aligned_notes'], 'non alignees', stat['unaligned_notes'])
for n, f in (('repons', lambda r: r['part'] == 're'), ('repons authentiques', lambda r: r['part'] == 're' and not r['syn']),
             ('repons synthetiques (ob/cb)', lambda r: r['part'] == 're' and r['syn'])):
    print(' ', n, summary(collections.Counter((r['sign'], r['pred']) for r in Rv if f(r))))
print('--- ecarts principaux (repons de verification) : neume, position, marteo, regles')
for k, v in collections.Counter((r['atom'], r['pos'] if r['role'] == 'base' else r['role'], r['sign'], r['pred'])
                                for r in Rv if r['part'] == 're' and r['sign'] != r['pred']).most_common(16):
    print(' ', k, v)
if a.write:
    save_model(T, L)
    print('model.json ecrit')
