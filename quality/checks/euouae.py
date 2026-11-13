import re
from ..gabc import split_header, header_field, last_clef, to_c4, NOTE_GROUP

NAME = 'euouae'
DESCRIPTION = ("antiphons have one <eu>...</eu> holding 'E U O U A E.' or 'Et sic finiátur.', "
               "whose melody is the one of the differentia given by the mode: header")

TEXTS = ('E U O U A E.', 'Et sic finiátur.')

# Melody of each differentia, one group per syllable, pitches transposed to a c4 clef.
# Built from the antiphons _marteo of 2026-11-14 (one melody per label, after PR #533).
DIFFERENTIAE = {
  '1a': 'h h g f g h',
  '1a2': 'h h g f g gh',
  '1a3': 'h h g f gh gh',
  '1d': 'h h g f gh gfed',
  '1d-': 'h h g f g gfed',
  '1d2': 'h h g f gf d',
  '1f': 'h h g f gh gf',
  '1g': 'h h g f gh g',
  '1g2': 'h h g f g ghg',
  '2d': 'm m m l j k',
  '3a': 'i i j h j ih',
  '3a2': 'i i j hi h gh',
  '3a3': 'i i ji hi h gh',
  '3b': 'i i j h j i',
  '3g': 'i i ji hi h g',
  '4a': 'k j k l j h',
  '4a2': 'h g h i g h',
  '4d': 'k j k l j k',
  '4e': 'h g h ih gf e',
  '4g': 'h h h h h g',
  '5a': 'j j k i j h',
  '6c': 'l l j kl k j',
  '6f': 'h h f gh g f',
  '7a': 'k k l k j ih',
  '7c': 'k k l k j ij',
  '7c2': 'k k l k j kj',
  '7d': 'k k l k j ik',
  '8c': 'j j h j k j',
  '8g': 'j j i j h g',
  '8g2': 'j j i j h ghg',
  'E': 'h h i g i h',
  'irreg.': 'h h i g i h',
  'P': 'g g g d f ed',
}


def melody(eu, after, clef):
  groups = re.findall(r'\(([^)]*)\)', eu)
  if not eu.rstrip().endswith(')') and after:   # E.</eu>(g): last note right after the tag
    groups.append(after)
  out = []
  for g in groups:
    g = re.sub(r'[a-m][xy#]', '', g.split('|')[0])
    out.append(to_c4(''.join(c for c in g if c.lower() in 'abcdefghijklm'), clef))
  return ' '.join(out)


def check(text):
  header, body, off = split_header(text)
  part = header_field(header, 'office-part')
  if not part or not part.lower().startswith('an'):
    return
  tags = [m.start() for m in re.finditer(r'<eu>', body)]
  if len(tags) != 1:
    yield off + (tags[1] if tags else 0), f'{len(tags)} <eu> tags instead of 1'
    return
  m = re.compile(r'<eu>(.*?)</eu>(?:\s*\(([^)]*)\))?', re.S).search(body)
  if not m:
    yield off + tags[0], '<eu> not closed by </eu>'
    return
  pos = off + m.start()
  words = re.sub(r'\s+', ' ', NOTE_GROUP.sub('', m.group(1))).strip()
  if words not in TEXTS:
    yield pos, f"text '{words}' instead of " + ' or '.join(f"'{t}'" for t in TEXTS)
  mode = header_field(header, 'mode')
  clef = last_clef(body[:m.start()])
  if clef is None:
    yield pos, 'no clef before <eu>'
    return
  got = melody(m.group(1), m.group(2), clef)
  if mode not in DIFFERENTIAE:
    yield pos, f"mode '{mode}' not in the differentia table (EUOUAE in c4: {got})"
  elif got != DIFFERENTIAE[mode]:
    other = [k for k, v in DIFFERENTIAE.items() if v == got]
    yield pos, (f"EUOUAE in c4 '{got}' is not the one of mode {mode} ('{DIFFERENTIAE[mode]}')"
                + (f", it is the one of {'/'.join(other)}" if other else ''))
