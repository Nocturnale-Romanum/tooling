"""Report on the melodies of the responsory verses: standard melody of each half-verse by mode,
deviations of 1 to 3 notes from it, proper and semi-proper verses.

Usage: python3 -m quality.versets [--repo REPO] [--set marteo|base|all] [-o OUT.html]

Each verse (from <sp>V/</sp> to the (::) bar) is split at its first ';' bar (else ':').
Each half is reduced to a skeleton: pitches transposed to c4, repeated notes merged,
repeated recitation motifs merged (hghg -> hg). A skeleton shared by at least MIN_FAMILY
verses of the same mode is a standard form; a half at edit distance 1..MAX_NEAR from one
(without transposition) is a deviation to check.
"""
import argparse
import collections
import html
import os
import re

from .__main__ import SETS, DEFAULT_REPO

MIN_FAMILY = 4
MAX_NEAR = 3
CLEF = re.compile(r'(?<![a-z])([cf])(b?)([1-4])(?![0-9])')
BAR = re.compile(r"[`,;:]+[0-9'_]*|::|;[0-9]*|:[0-9']*")


# ---- parsing

def shift(clef):
  return 2 * (4 - clef[1]) + (3 if clef[0] == 'f' else 0)


def pieces(repo, sel):
  gabc = os.path.join(repo, 'gabc')
  for n in sorted(os.listdir(gabc)):
    if not SETS[sel](n):
      continue
    with open(os.path.join(gabc, n), encoding='utf-8') as fh:
      h, _, b = fh.read().partition('%%')
    part = re.search(r'^office-part:\s*([^;]*)', h, re.M)
    if not part or part.group(1).strip() != 're':
      continue
    mode = re.search(r'^mode:\s*([^;]*)', h, re.M)
    yield re.sub(r'(_[^_.]+)?\.gabc$', '', n), (mode.group(1).strip() if mode else '')[:1], b


def tokens(body):
  """Yield ('sp', text), ('bar', bar) and ('syl', text, c4 notes, original GABC) tokens."""
  clef = None
  for m in re.finditer(r'([^()]*)\(([^)]*)\)', body):
    txt, g = m.group(1), m.group(2).split('|')[0]
    for sp in re.findall(r'<sp>(.*?)</sp>', txt):
      yield ('sp', sp)
    txt = re.sub(r'<[^>]*>', '', re.sub(r'<sp>.*?</sp>', '', txt)).strip()
    g = re.sub(r'\[[^\]]*\]', '', g)
    for c in CLEF.finditer(g):
      clef = (c.group(1), int(c.group(3)))
    g2 = re.sub(r'[a-mA-M]\+|[zZ][0-9+-]?', '', CLEF.sub('', g)).strip()
    if g2 and BAR.fullmatch(g2):
      yield ('bar', g2)
      continue
    g2 = re.sub(r'[a-mA-M][xy#]', '', g2)
    notes = ''.join(chr(ord(c.lower()) + shift(clef)) for c in g2 if c.lower() in 'abcdefghijklm') if clef else ''
    if notes:
      yield ('syl', txt, notes, m.group(2).split('|')[0])


def verses(body):
  out, cur = [], None
  for k in tokens(body):
    if k[0] == 'sp' and k[1] == 'V/':
      cur = []
      out.append(cur)
    elif cur is None or k[0] == 'sp':
      continue
    elif k[0] == 'bar' and k[1] == '::':
      cur = None
    else:
      cur.append(k)
  return out


def halves(v):
  for mark in (';', ':'):
    i = next((j for j, k in enumerate(v) if k[0] == 'bar' and k[1].startswith(mark)), None)
    if i is not None:
      return v[:i], v[i + 1:]
  return None


# ---- melodies

def syls(h):
  return [k for k in h if k[0] == 'syl']


def collapse(s):
  return re.sub(r'(.)\1+', r'\1', s)


def flat(h):
  return collapse(''.join(k[2] for k in syls(h)))


def skeleton(h):
  s, prev = flat(h), None
  while prev != s:
    prev = s
    s = collapse(re.sub(r'(.{2,4}?)\1+', r'\1', s))
  return s


def lev(a, b):
  p = list(range(len(b) + 1))
  for i, x in enumerate(a, 1):
    c = [i]
    for j, y in enumerate(b, 1):
      c.append(min(p[j] + 1, c[j - 1] + 1, p[j - 1] + (x != y)))
    p = c
  return p[-1]


def transpose(s, k):
  return ''.join(chr(ord(c) + k) for c in s)


def collapsed_map(h):
  """Collapsed note string of h and, for each note, the index of its syllable."""
  s, idx = '', []
  for i, k in enumerate(syls(h)):
    for c in k[2]:
      if not (s and s[-1] == c):
        s += c
        idx.append(i)
  return s, idx


def align(a, b):
  """Edit operations (i in a, j in b) turning a into b."""
  n, m = len(a), len(b)
  D = [[0] * (m + 1) for _ in range(n + 1)]
  for i in range(n + 1):
    D[i][0] = i
  for j in range(m + 1):
    D[0][j] = j
  for i in range(1, n + 1):
    for j in range(1, m + 1):
      D[i][j] = min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
  ops, i, j = [], n, m
  while i or j:
    if i and j and D[i][j] == D[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
      if a[i - 1] != b[j - 1]:
        ops.append((i - 1, j - 1))
      i, j = i - 1, j - 1
    elif i and D[i][j] == D[i - 1][j] + 1:
      ops.append((i - 1, j))
      i -= 1
    else:
      ops.append((i, j - 1))
      j -= 1
  return ops


# ---- analysis

class Half:
  def __init__(self, id, mode, verse, part, toks):
    self.id, self.mode, self.verse, self.part, self.toks = id, mode, verse, part, toks
    self.skel = skeleton(toks)
    s = syls(toks)
    self.gloria = bool(s) and s[0][1].startswith('Gl')


def analyse(repo, sel):
  H = []
  for id, mode, b in pieces(repo, sel):
    for vi, v in enumerate(verses(b)):
      hs = halves(v)
      if hs:
        H += [Half(id, mode, vi, 1, hs[0]), Half(id, mode, vi, 2, hs[1])]
      else:
        H.append(Half(id, mode, vi, 0, v))
  fam = {}
  for m in sorted({h.mode for h in H}):
    for p in (1, 2):
      c = collections.Counter(h.skel for h in H if h.mode == m and h.part == p)
      fam[(m, p)] = [(s, n) for s, n in c.most_common() if n >= MIN_FAMILY]
  for h in H:
    best = None
    for p in ((h.part,) if h.part else (1, 2)):
      for f, _ in fam.get((h.mode, p), []):
        for k in range(-5, 6):
          d = lev(transpose(h.skel, k), f)
          if best is None or (d, abs(k)) < (best[0], abs(best[2])):
            best = (d, f, k, p)
    h.dist, h.family, h.shift, h.fpart = best or (99, None, 0, h.part or 1)
    h.kind = ('std' if h.dist == 0 else 'near' if h.shift == 0 and h.dist <= MAX_NEAR else 'proper')
  std = collections.defaultdict(list)
  for h in H:
    if h.kind == 'std' and h.shift == 0:
      std[(h.mode, h.fpart)].append(h)
  for h in H:
    if h.kind != 'near':
      continue
    a, ia = collapsed_map(h.toks)
    best = None
    for e in std[(h.mode, h.fpart)]:
      b, ib = collapsed_map(e.toks)
      d = lev(a, b)
      if best is None or d < best[0]:
        best = (d, e, ib)
    _, h.example, ib = best
    ops = align(a, collapsed_map(h.example.toks)[0])
    h.marks = {ia[min(i, len(ia) - 1)] for i, j in ops}
    h.exmarks = {ib[min(j, len(ib) - 1)] for i, j in ops}
  # a deviation shared by several verses is more likely a variant
  sig = lambda h: (h.mode, h.fpart, tuple(k[2] for i, k in enumerate(syls(h.toks)) if i in h.marks))
  near = [h for h in H if h.kind == 'near']
  c1 = collections.Counter((h.mode, h.fpart, h.skel) for h in near)
  c2 = collections.Counter(sig(h) for h in near)
  for h in near:
    h.recurrent = max(c1[(h.mode, h.fpart, h.skel)], c2[sig(h)]) > 1
  return H, fam


# ---- rendering

E = html.escape


def link(id):
  return f'<a href="https://nocturnale.marteo.fr/chant/{E(id)}">{E(id)}</a>'


def vlabel(v, gloria):
  return 'Gloria Patri' if gloria else ('V/' if v == 0 else f'V/ {v + 1}')


def half_label(p):
  return {0: 'verset court', 1: '1<sup>re</sup> moitié', 2: '2<sup>de</sup> moitié'}[p]


def melody(h, marks=()):
  return '<span class="mel">' + ' '.join(
    f'<span class="s{" hit" if i in marks else ""}" title="{E(k[3])}">{E(k[1])}<i>{E(k[2])}</i></span>'
    for i, k in enumerate(syls(h.toks))) + '</span>'


def render(H, fam):
  modes = sorted(fam and {m for m, _ in fam})
  byv = collections.defaultdict(list)
  for h in H:
    byv[(h.id, h.verse)].append(h)
  summ = collections.defaultdict(collections.Counter)
  status = {}
  for key, hs in byv.items():
    kinds = [h.kind for h in hs]
    if 'near' in kinds:
      k = 'near'
    elif hs[0].part == 0:
      k = 'short' if kinds[0] == 'std' else 'proper'
    else:
      k = {('std', 'std'): 'std', ('proper', 'proper'): 'proper'}.get(tuple(kinds), 'semi')
    status[key] = k
    summ[hs[0].mode][k] += 1
    summ[hs[0].mode]['tot'] += 1
  tot = collections.Counter()
  rows = ''
  for m in modes + ['Total']:
    s = summ[m] if m != 'Total' else tot
    if m != 'Total':
      tot.update(s)
    rows += (f"<tr{' class=tot' if m == 'Total' else ''}><th>{m}</th><td>{s['tot']}</td><td>{s['std']}</td><td>{s['short']}</td>"
             f"<td>{s['semi']}</td><td>{s['proper']}</td><td class='warn'>{s['near'] or ''}</td></tr>")

  def nearrow(h):
    e = h.example
    return (f"<tr><td>{link(h.id)}<div class='sub'>mode {h.mode} · {vlabel(h.verse, h.gloria)} · {half_label(h.part)}</div></td>"
            f"<td class='num'>{h.dist}</td><td>{melody(h, h.marks)}</td>"
            f"<td>{melody(e, h.exmarks)}<div class='sub'>{link(e.id)} {vlabel(e.verse, e.gloria)}</div></td></tr>")
  head = ("<thead><tr><th>Pièce</th><th>Écart</th><th>Verset (notes en c4, syllabes en écart surlignées)</th>"
          "<th>Verset standard le plus proche</th></tr></thead>")
  near = [h for h in H if h.kind == 'near']
  iso = sorted((h for h in near if not h.recurrent), key=lambda h: (h.dist, h.mode, h.id))
  rec = sorted((h for h in near if h.recurrent), key=lambda h: (h.mode, h.part, h.skel, h.id))

  fams = ''
  for m in modes:
    fams += f'<h3>Mode {m}</h3>'
    if m == '6':
      fams += ("<p class='note'>Pas de vraie mélodie standard : une fois les répétitions de la récitation réduites, "
               "il ne reste que l'intonation et les cadences typiques. Les familles ci-dessous ne contrôlent donc que ces deux éléments.</p>")
    for p in (1, 2):
      fams += (f"<div class='fam'><h4>{half_label(p).capitalize()}</h4><table><thead><tr><th>Versets</th>"
               "<th>Squelette</th><th>Exemple</th></tr></thead><tbody>")
      for s, n in fam[(m, p)]:
        ex = next(h for h in H if h.kind == 'std' and h.shift == 0 and h.mode == m and h.fpart == p
                  and h.skel == s and not h.gloria)
        fams += f"<tr><td class='num'>{n}</td><td><code>{E(s)}</code></td><td>{melody(ex)}<div class='sub'>{link(ex.id)}</div></td></tr>"
      fams += '</tbody></table></div>'

  pill = {'std': '<span class="pill std">standard</span>', 'proper': '<span class="pill pr">propre</span>',
          'near': '<span class="pill nr">écart</span>'}
  proper = ''
  for m in modes:
    keys = sorted(k for k, hs in byv.items() if hs[0].mode == m and status[k] not in ('std', 'short'))
    proper += (f"<h3>Mode {m} <span class='count'>{len(keys)}</span></h3><div class='tw'><table class='pl'><thead><tr>"
               "<th>Pièce</th><th>Verset</th><th>1<sup>re</sup> moitié</th><th>2<sup>de</sup> moitié</th></tr></thead><tbody>")
    for k in keys:
      hs = byv[k]
      cells = (f"<td colspan=2>verset court : {pill[hs[0].kind]}</td>" if hs[0].part == 0
               else ''.join(f'<td>{pill[h.kind]}</td>' for h in hs))
      proper += f"<tr><td>{link(k[0])}</td><td>{vlabel(k[1], hs[0].gloria)}</td>{cells}</tr>"
    proper += '</tbody></table></div>'

  with open(os.path.join(os.path.dirname(__file__), 'versets_template.html'), encoding='utf-8') as fh:
    tpl = fh.read()
  for key, val in {'@@SUMMARY@@': rows, '@@NISO@@': str(len(iso)), '@@NREC@@': str(len(rec)),
                   '@@ISO@@': head + '<tbody>' + ''.join(map(nearrow, iso)) + '</tbody>',
                   '@@REC@@': head + '<tbody>' + ''.join(map(nearrow, rec)) + '</tbody>',
                   '@@FAMS@@': fams, '@@PROPER@@': proper, '@@NV@@': str(len(byv))}.items():
    tpl = tpl.replace(key, val)
  return tpl


def main():
  p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  p.add_argument('--repo', default=DEFAULT_REPO)
  p.add_argument('--set', choices=SETS, default='marteo')
  p.add_argument('-o', '--output', default='versets-repons.html')
  a = p.parse_args()
  H, fam = analyse(a.repo, a.set)
  with open(a.output, 'w', encoding='utf-8') as fh:
    fh.write(render(H, fam))
  print(f'{a.output}: {len({(h.id, h.verse) for h in H})} verses, '
        f'{sum(h.kind == "near" for h in H)} half-verses with a deviation')


if __name__ == '__main__':
  main()
