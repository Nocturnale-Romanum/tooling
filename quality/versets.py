"""Report on the melodies of the responsory verses: standard melody of each half-verse by mode,
deviations of 1 to 3 notes from it, proper and semi-proper verses.

Usage: python3 -m quality.versets [--repo REPO] [--set marteo|base|all] [-o OUT.html]

Each verse (from <sp>V/</sp> to the (::) bar) is split at its ';' and ':' bars: two halves,
or, for a long verse, a first incise, middle incises and a last one. Each part is reduced to a skeleton: pitches transposed to c4, repeated notes merged,
repeated recitation motifs merged (hghg -> hg). A skeleton shared by at least MIN_FAMILY
verses of the same mode is a standard form; a half at edit distance 1..MAX_NEAR from one
(without transposition) is a deviation to check. Incises of long verses may end on a
provisional cadence (and middle ones start without intonation); halves shorter than 90% of the
standard ones may drop the beginning of the formula.
"""
import argparse
import collections
import html
import os
import re

from .__main__ import SETS, DEFAULT_REPO

MIN_FAMILY = 4
# Deviations accepted by marteo: (piece, part) -> reason; part 1 first half, 2 last half, 0 short verse.
# They apply to every verse of the piece (verse and Gloria Patri).
EXCEPTIONS = {
  ('0106N3R2', 2): 'la dernière syllabe du verset est propre à ce verset',
}
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


def segments(v):
  """Split a verse at its ';' and ':' bars: two halves, or more incises for a long verse."""
  out = [[]]
  for k in v:
    if k[0] == 'bar' and k[1][0] in ';:':
      out.append([])
    else:
      out[-1].append(k)
  return [s for s in out if syls(s)]


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
  """A part of a verse: 0 whole short verse, 1 first half (or first incise), 2 last half, 3 middle incise."""
  def __init__(self, id, mode, verse, part, toks, long):
    self.id, self.mode, self.verse, self.part, self.toks, self.long = id, mode, verse, part, toks, long
    self.skel = skeleton(toks)
    s = syls(toks)
    self.gloria = bool(s) and s[0][1].startswith('Gl')
    self.note = ''


def free_dist(s, f, head_s=0, head_f=False, tail_s=0, tail_f=False):
  """Edit distance between s and f, ignoring up to head_s/tail_s notes at the ends of s,
  and, when head_f/tail_f, any number of notes at the ends of f."""
  best = lev(s, f)
  for h in range(head_s + 1):
    for t in range(tail_s + 1):
      ss = s[h:len(s) - t]
      if not ss:
        continue
      for a in (range(len(f)) if head_f else (0,)):
        for b in (range(a + 1, len(f) + 1) if tail_f else (len(f),)):
          best = min(best, lev(ss, f[a:b]))
  return best


def analyse(repo, sel):
  H = []
  for id, mode, b in pieces(repo, sel):
    for vi, v in enumerate(verses(b)):
      S = segments(v)
      if len(S) == 1:
        H.append(Half(id, mode, vi, 0, S[0], False))
      elif S:
        long = len(S) > 2
        H += [Half(id, mode, vi, 1 if i == 0 else 2 if i == len(S) - 1 else 3, s, long) for i, s in enumerate(S)]
  fam = {}
  for m in sorted({h.mode for h in H}):
    for p in (1, 2):
      c = collections.Counter(h.skel for h in H if h.mode == m and h.part == p and not h.long)
      fam[(m, p)] = [(s, n) for s, n in c.most_common() if n >= MIN_FAMILY]
    # middle incises of long verses: a skeleton found in two of them is a formula
    c = collections.Counter(h.skel for h in H if h.mode == m and h.part == 3)
    fam[(m, 3)] = [(s, n) for s, n in c.most_common() if n >= 2]
  forms = lambda m, p: [f for q in ((p,) if p in (1, 2) else (1, 2, 3)) for f, _ in fam.get((m, q), [])]
  # a half shorter than 90% of the standard ones may drop the beginning of the formula
  short = {}
  for (m, p) in fam:
    n = sorted(len(syls(h.toks)) for h in H if h.mode == m and h.part == p and not h.long and h.skel in dict(fam[(m, p)]))
    short[(m, p)] = n[len(n) // 10] if n else 0
  for h in H:
    best = None
    for f in forms(h.mode, h.part or 3):
      for k in range(-5, 6):
        d = lev(transpose(h.skel, k), f)
        if best is None or (d, abs(k)) < (best[0], abs(best[1])):
          best = (d, k)
    h.dist, h.shift = best or (99, 0)
    if h.dist and h.long and h.part in (1, 3):
      # incise of a long verse: provisional cadence, and no intonation for a middle incise
      d = min(free_dist(h.skel, f, tail_s=4, tail_f=True, head_f=h.part == 3) for f in forms(h.mode, h.part))
      if d < h.dist or h.shift:
        h.dist, h.shift = d, 0
        if d == 0:
          h.note = 'incise'
    if h.dist and h.part in (1, 2) and not h.long and len(syls(h.toks)) < short[(h.mode, h.part)]:
      d = min(free_dist(h.skel, f, head_s=3, head_f=True) for f in forms(h.mode, h.part))
      if d < h.dist or h.shift:
        h.dist, h.shift = d, 0
        if d == 0:
          h.note = 'début omis'
    # middle incises are adapted too freely for their deviations to be meaningful
    h.kind = 'std' if h.dist == 0 else 'near' if h.shift == 0 and h.dist <= MAX_NEAR and h.part != 3 else 'proper'
    if h.kind == 'near' and (h.id, h.part) in EXCEPTIONS:
      h.exception = EXCEPTIONS[(h.id, h.part)]
  std = collections.defaultdict(list)
  for h in H:
    if h.kind == 'std' and h.shift == 0 and not h.note:
      std[(h.mode, h.part if h.part in (1, 2) else 1)].append(h)
  for h in H:
    if h.kind != 'near':
      continue
    a, ia = collapsed_map(h.toks)
    best = None
    for e in std[(h.mode, h.part if h.part in (1, 2) else 1)] + (std[(h.mode, 2)] if h.part in (0, 3) else []):
      b, ib = collapsed_map(e.toks)
      d = lev(a, b)
      if best is None or d < best[0]:
        best = (d, e, ib)
    _, h.example, ib = best
    ops = align(a, collapsed_map(h.example.toks)[0])
    h.marks = {ia[min(i, len(ia) - 1)] for i, j in ops}
    h.exmarks = {ib[min(j, len(ib) - 1)] for i, j in ops}
  for h in H:
    if getattr(h, 'exception', None):
      h.kind, h.note = 'std', 'exception'
  # a deviation shared by several verses is more likely a variant
  sig = lambda h: (h.mode, h.part, tuple(k[2] for i, k in enumerate(syls(h.toks)) if i in h.marks))
  near = [h for h in H if h.kind == 'near']
  c1 = collections.Counter((h.mode, h.part, h.skel) for h in near)
  c2 = collections.Counter(sig(h) for h in near)
  for h in near:
    h.recurrent = max(c1[(h.mode, h.part, h.skel)], c2[sig(h)]) > 1
  # verses with no standard part in their mode, but some in another mode
  byv = collections.defaultdict(list)
  for h in H:
    byv[(h.id, h.verse)].append(h)
  suspects = []
  for hs in byv.values():
    if any(h.kind == 'std' for h in hs):
      continue
    fits = {m: sum(any(lev(h.skel, f) == 0 for f in forms(m, h.part or 3)) for h in hs)
            for m in sorted({m for m, _ in fam}) if m != hs[0].mode}
    m = max(fits, key=fits.get)
    if fits[m]:
      suspects.append((hs, m, fits[m]))
  return H, fam, suspects


# ---- rendering

E = html.escape


def link(id):
  return f'<a href="https://nocturnale.marteo.fr/chant/{E(id)}">{E(id)}</a>'


def vlabel(v, gloria):
  return 'Gloria Patri' if gloria else ('V/' if v == 0 else f'V/ {v + 1}')


def half_label(p, long=False):
  if long:
    return {1: 'incise initiale', 2: 'incise finale', 3: 'incise centrale'}[p]
  return {0: 'verset court', 1: '1<sup>re</sup> moitié', 2: '2<sup>de</sup> moitié'}[p]


def melody(h, marks=()):
  return '<span class="mel">' + ' '.join(
    f'<span class="s{" hit" if i in marks else ""}" title="{E(k[3])}">{E(k[1])}<i>{E(k[2])}</i></span>'
    for i, k in enumerate(syls(h.toks))) + '</span>'


def render(H, fam, suspects):
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
      k = 'std' if set(kinds) == {'std'} else 'proper' if set(kinds) == {'proper'} else 'semi'
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
    return (f"<tr><td>{link(h.id)}<div class='sub'>mode {h.mode} · {vlabel(h.verse, h.gloria)} · {half_label(h.part, h.long)}</div></td>"
            f"<td class='num'>{h.dist}</td><td>{melody(h, h.marks)}</td>"
            f"<td>{melody(e, h.exmarks)}<div class='sub'>{link(e.id)} {vlabel(e.verse, e.gloria)}</div></td></tr>")
  head = ("<thead><tr><th>Pièce</th><th>Écart</th><th>Verset (notes en c4, syllabes en écart surlignées)</th>"
          "<th>Verset standard le plus proche</th></tr></thead>")
  near = [h for h in H if h.kind == 'near']
  iso = sorted((h for h in near if not h.recurrent), key=lambda h: (h.dist, h.mode, h.id))
  rec = sorted((h for h in near if h.recurrent), key=lambda h: (h.mode, h.part, h.skel, h.id))
  exc = sorted((h for h in H if h.note == 'exception'), key=lambda h: (h.id, h.verse))
  exc_rows = ''.join(nearrow(h).replace('</td><td class=\'num\'>', f"<div class='sub'>{E(h.exception)}</div></td><td class='num'>", 1)
                     for h in exc)
  susp = ''.join(
    f"<tr><td>{link(hs[0].id)}</td><td>{vlabel(hs[0].verse, hs[0].gloria)}</td><td class='num'>{hs[0].mode}</td>"
    f"<td class='num'>{m}</td><td class='num'>{n} / {len(hs)}</td></tr>"
    for hs, m, n in sorted(suspects, key=lambda x: (x[0][0].id, x[0][0].verse)))

  fams = ''
  for m in modes:
    fams += f'<h3>Mode {m}</h3>'
    if m == '6':
      fams += ("<p class='note'>Pas de vraie mélodie standard : une fois les répétitions de la récitation réduites, "
               "il ne reste que l'intonation et les cadences typiques. Les familles ci-dessous ne contrôlent donc que ces deux éléments.</p>")
    for p in (1, 2, 3):
      if not fam.get((m, p)):
        continue
      title = half_label(p).capitalize() if p < 3 else 'Incises centrales des versets longs (formule présente dans au moins 2 versets)'
      fams += (f"<div class='fam'><h4>{title}</h4><table><thead><tr><th>Versets</th>"
               "<th>Squelette</th><th>Exemple</th></tr></thead><tbody>")
      for s, n in fam[(m, p)]:
        cand = [h for h in H if h.mode == m and h.part == p and h.skel == s and h.long == (p == 3)]
        ex = next((h for h in cand if not h.gloria), cand[0])
        fams += f"<tr><td class='num'>{n}</td><td><code>{E(s)}</code></td><td>{melody(ex)}<div class='sub'>{link(ex.id)}</div></td></tr>"
      fams += '</tbody></table></div>'

  pill = {'std': '<span class="pill std">standard</span>', 'proper': '<span class="pill pr">propre</span>',
          'near': '<span class="pill nr">écart</span>'}

  def status_pill(h):
    p = pill[h.kind] if not h.note else f'<span class="pill std">standard, {h.note}</span>'
    return p if not h.long else f'<span class="seg">{half_label(h.part, True)}</span> {p}'
  proper = ''
  for m in modes:
    keys = sorted(k for k, hs in byv.items() if hs[0].mode == m and (status[k] not in ('std', 'short') or hs[0].long
                                                                    or any(h.note == 'début omis' for h in hs)))
    proper += (f"<h3>Mode {m} <span class='count'>{len(keys)}</span></h3><div class='tw'><table class='pl'><thead><tr>"
               "<th>Pièce</th><th>Verset</th><th>1<sup>re</sup> moitié</th><th>2<sup>de</sup> moitié</th></tr></thead><tbody>")
    for k in keys:
      hs = byv[k]
      if hs[0].part == 0:
        cells = f"<td colspan=2>verset court : {status_pill(hs[0])}</td>"
      elif hs[0].long:
        cells = f"<td colspan=2><div class='segs'>{''.join(f'<div>{status_pill(h)}</div>' for h in hs)}</div></td>"
      else:
        cells = ''.join(f'<td>{status_pill(h)}</td>' for h in hs)
      proper += f"<tr><td>{link(k[0])}</td><td>{vlabel(k[1], hs[0].gloria)}</td>{cells}</tr>"
    proper += '</tbody></table></div>'

  with open(os.path.join(os.path.dirname(__file__), 'versets_template.html'), encoding='utf-8') as fh:
    tpl = fh.read()
  for key, val in {'@@SUMMARY@@': rows, '@@NISO@@': str(len(iso)), '@@NREC@@': str(len(rec)),
                   '@@ISO@@': head + '<tbody>' + ''.join(map(nearrow, iso)) + '</tbody>',
                   '@@REC@@': head + '<tbody>' + ''.join(map(nearrow, rec)) + '</tbody>',
                   '@@FAMS@@': fams, '@@NSUSP@@': str(len(suspects)), '@@NEXC@@': str(len(exc)),
                   '@@EXC@@': head + '<tbody>' + exc_rows + '</tbody>', '@@SUSP@@': susp, '@@PROPER@@': proper, '@@NV@@': str(len(byv))}.items():
    tpl = tpl.replace(key, val)
  return tpl


def main():
  p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  p.add_argument('--repo', default=DEFAULT_REPO)
  p.add_argument('--set', choices=SETS, default='marteo')
  p.add_argument('-o', '--output', default='versets-repons.html')
  a = p.parse_args()
  H, fam, suspects = analyse(a.repo, a.set)
  with open(a.output, 'w', encoding='utf-8') as fh:
    fh.write(render(H, fam, suspects))
  print(f'{a.output}: {len({(h.id, h.verse) for h in H})} verses, '
        f'{sum(h.kind == "near" for h in H)} half-verses with a deviation')


if __name__ == '__main__':
  main()
