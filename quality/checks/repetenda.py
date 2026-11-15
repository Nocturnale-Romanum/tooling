import re
from ..gabc import split_header, header_field, CLEF

NAME = 'repetenda'
DESCRIPTION = ("in responsories, the repetendum after each verse starts with the <sp> marking where it starts "
               "in the respond (R/ for the beginning), quotes the respond (text, GABC, NABC without lse<n> "
               "and pitch descriptors) and ends with a period")

# Categories of the reports, in the order of the batches to process them in.
CATEGORIES = [
  ('period', 'final period missing'),
  ('cb-in-gabc', "'cb' written in the GABC instead of the NABC"),
  ('nabc-missing', 'NABC missing from the repetendum'),
  ('syllables', 'syllabification differs from the respond'),
  ('engraving', 'GABC differs from the respond, same pitches (spacing, episema, liquescence, accidental...)'),
  ('nabc', 'NABC differs from the respond'),
  ('melody', 'GABC differs from the respond, different pitches'),
  ('structure', 'missing or misplaced marker, repetendum missing or not found in the respond'),
]

GROUP = re.compile(r'([^()]*)\(([^)]*)\)')
BAR = re.compile(r"[`,;:]+[0-9'_?]*|::|;[0-9]*|:[0-9']*")
PUNCT = re.compile(r'[^\w]', re.U)


def nabc_norm(s):
  """NABC without lse<n> significant letters, pitch descriptors (h + pitch), ob/cb brackets and spacing."""
  out = []
  for tok in re.split(r'((?<![cq])l[st][a-z]{1,3}\d)', s):
    if re.fullmatch(r'l[st][a-z]{1,3}\d', tok):
      if not re.fullmatch(r'lse\d', tok):
        out.append(tok)
    else:
      # pitch descriptors, ob/cb brackets of the repeated passage, spacing
      tok = re.sub(r'h[a-np]|[`/]', '', tok)
      out.append(re.sub(r'(?:^|(?<=[-!]))ob|cb(?!v)', '', tok))
  return ''.join(out)


LIGATURES = {"'oe": 'œ', "'ae": 'æ', "'æ": 'æ', "'œ": 'œ'}


def pitches(g):
  """Pitch letters of a GABC group, without accidentals, line breaks and custos."""
  g = re.sub(r'\[[^\]]*\]|<[^>]*>|[a-m][xy#]|[zZ][0-9+-]?|[a-m]\+', '', g)
  return ''.join(c.lower() for c in g if c.lower() in 'abcdefghijklm')


def gabc_norm(g):
  """GABC without line breaks and custos."""
  return re.sub(r'[zZ][0-9+-]?|[a-m]\+', '', g).strip()


def units(body, off):
  """Yield ('sp', label, pos), ('bar', bar, pos) and ('syl', text, gabc, nabc, pos, starts a word).
  When a group's text holds a marker after some text (t{o}. <sp>+</sp> Pasce.(ed.. ::)), the notes and bars
  belong to the text before the marker, and the text after it is a repetendum written as pure text."""
  for m in GROUP.finditer(body):
    txt = re.sub(r"<sp>('[^<]*)</sp>", lambda x: LIGATURES.get(x.group(1), x.group(1)), m.group(1))
    pos = off + m.start(1)
    parts = m.group(2).split('|')
    g, n = parts[0].strip(), '|'.join(parts[1:]).strip()
    core = re.sub(r'[a-mA-M]\+|[zZ][0-9+-]?|[a-m][xy#]', '', CLEF.sub('', g)).strip()
    pieces = re.split(r'<sp>(.*?)</sp>', txt)
    clean = [re.sub(r'<[^>]*>|[{}]', '', t) for t in pieces[::2]]
    if len(pieces) > 1 and clean[0].strip():
      notes = ' '.join(t for t in g.split() if not BAR.fullmatch(t))
      yield ('syl', clean[0].strip(), notes, n, pos, clean[0][:1].isspace() or not pieces[0])
      for t in g.split():
        if BAR.fullmatch(t):
          yield ('bar', t, off + m.start(2))
      for k in range(1, len(pieces), 2):
        yield ('sp', pieces[k], pos)
        if clean[(k + 1) // 2].strip():
          yield ('syl', clean[(k + 1) // 2].strip(), '', '', pos, True)
      continue
    for k in range(1, len(pieces), 2):
      yield ('sp', pieces[k], pos)
    txt = clean[-1]
    new_word = txt[:1].isspace() or not txt or len(pieces) > 1
    txt = txt.strip()
    junk = re.fullmatch(r'(.*?)([oc]b)', core or '-')
    if not txt and junk and BAR.fullmatch(junk.group(1)):
      yield ('bar', junk.group(1), off + m.start(2))
      yield ('err', f"'{junk.group(2)}' written in the GABC of the bar ({core})", off + m.start(2))
    elif not txt and BAR.fullmatch(core or '-'):
      yield ('bar', core, off + m.start(2))
    elif txt or core:
      yield ('syl', txt, g, n, pos, new_word)


def norm_text(t):
  return ' '.join(PUNCT.sub('', w).lower() for w in t.split())


def joined(syls):
  return norm_text(''.join((' ' if u[5] else '') + u[1] for u in syls))


def check(text):
  header, body, off = split_header(text)
  if (header_field(header, 'office-part') or '') != 're' or '(' not in body:
    return
  U = list(units(body, off))
  for u in U:
    if u[0] == 'err':
      yield u[2], u[1], 'cb-in-gabc'
  U = [u for u in U if u[0] != 'err']
  # respond: everything before the first verse, with the position of each marker
  first_v = next((i for i, u in enumerate(U) if u[0] == 'sp' and u[1] == 'V/'), len(U))
  respond, marks = [], {'R/': 0}
  for u in U[:first_v]:
    if u[0] == 'sp':
      marks.setdefault(u[1], len(respond))
    elif u[0] == 'syl':
      respond.append(u)
  end = lambda u: (u[0] == 'bar' and u[1] == '::') or (u[0] == 'sp' and u[1] == 'V/')
  i = first_v
  while i < len(U):
    if not (U[i][0] == 'sp' and U[i][1] == 'V/'):
      i += 1
      continue
    vpos = U[i][2]
    # the verse ends at its (::) bar, or at a marker if the repetendum follows without a bar
    j, seen = i + 1, False
    while j < len(U) and not end(U[j]) and not (seen and U[j][0] == 'sp'):
      seen = seen or U[j][0] == 'syl'
      j += 1
    k = j + 1 if j < len(U) and U[j][0] == 'bar' else j
    rep = []
    while k < len(U) and not end(U[k]):
      rep.append(U[k])
      k += 1
    i = k
    syls = [u for u in rep if u[0] == 'syl']
    sps = [u for u in rep if u[0] == 'sp']
    if not syls:
      if not sps:   # a bare <sp>+</sp> after the verse is an accepted way to mark the repetendum
        yield vpos, 'verse not followed by a repetendum', 'structure'
      continue
    if rep[0][0] != 'sp':
      yield syls[0][4], 'repetendum does not start with a <sp> marker', 'structure'
      continue
    label, rtext = sps[0][1], joined(syls)
    # syllables of the respond from which the repetendum text is quoted
    starts = []
    for st in range(len(respond)):
      if not (respond[st][5] or st == 0):
        continue
      e = st
      while e < len(respond) and len(joined(respond[st:e])) < len(rtext):
        e += 1
      if joined(respond[st:e]) == rtext or (joined(respond[st:e]) + ' ').startswith(rtext + ' '):
        starts.append((st, e))
    if not starts:
      yield syls[0][4], f"repetendum text '{' '.join(u[1] for u in syls)}' not found in the respond", 'structure'
      continue
    start = marks.get(label)
    if start not in [st for st, _ in starts]:
      right = [l for l, p in marks.items() if p in [st for st, _ in starts]]
      yield sps[0][2], (f"repetendum starts with <sp>{label}</sp>"
                        + (f" but quotes the respond from <sp>{right[0]}</sp>" if right else
                           " but quotes the respond from a point with no <sp> marker")), 'structure'
      start = starts[0][0]
    e = dict(starts)[start]
    quoted = respond[start:e]
    if not any(u[2] for u in syls):
      pass   # repetendum written as pure text: only its marker, text and period are checked
    elif [norm_text(u[1]) for u in syls] != [norm_text(u[1]) for u in quoted]:
      yield syls[0][4], (f"syllables '{'-'.join(u[1] for u in syls)}' differ from the respond "
                         f"('{'-'.join(u[1] for u in quoted)}')"), 'syllables'
    else:
      for u, r in zip(syls, quoted):
        if re.fullmatch(r'(.*)[oc]b', gabc_norm(u[2])) and gabc_norm(u[2])[:-2] == gabc_norm(r[2]):
          yield u[4], f"'{u[2][-2:]}' written in the GABC of '{u[1]}' ({u[2]})", 'cb-in-gabc'
        elif gabc_norm(u[2]) != gabc_norm(r[2]):
          yield (u[4], f"GABC of '{u[1]}' ({u[2]}) differs from the respond ({r[2]})",
                 'engraving' if pitches(u[2]) == pitches(r[2]) else 'melody')
        if nabc_norm(u[3]) != nabc_norm(r[3]):
          yield u[4], f"NABC of '{u[1]}' ({u[3]}) differs from the respond ({r[3]})", 'nabc-missing' if not u[3] else 'nabc'
    if not syls[-1][1].endswith('.'):
      yield syls[-1][4], f"repetendum text does not end with a period ('{syls[-1][1]}')", 'period'
