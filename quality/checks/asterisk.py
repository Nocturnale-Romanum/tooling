import re
from ..gabc import split_header, header_field

NAME = 'asterisk'
DESCRIPTION = ("antiphons, responsories, invitatories and psalms have a <sp>*</sp>; next to a bar, it is "
               "written right under it: <sp>*</sp>(,), not (,) <sp>*</sp> nor <sp>*</sp> (,)")

CATEGORIES = [
  ('missing', 'no <sp>*</sp> in the piece'),
  ('after-bar', '<sp>*</sp> written after a bar instead of under it'),
  ('space', 'space between <sp>*</sp> and the bar under which it is written'),
]

PARTS = ('an', 're', 'in', 'ps')
BAR = re.compile(r"[`,;:]+[0-9'_]*|::|;[0-9]*|:[0-9']*")
STAR = '<sp>*</sp>'


def is_bar(group):
  return bool(BAR.fullmatch(group.split('|')[0].strip()))


def check(text):
  header, body, off = split_header(text)
  if (header_field(header, 'office-part') or '') not in PARTS:
    return
  body = re.sub(r'%[^\n]*', lambda m: ' ' * len(m.group()), body)   # comments, offsets kept
  stars = [m.start() for m in re.finditer(re.escape(STAR), body)]
  if not stars:
    yield off, 'no <sp>*</sp> in the piece', 'missing'
  for s in stars:
    prev = re.search(r'\(([^)]*)\)(\s*)$', body[:s])
    nxt = re.match(r'(\s*)\(([^)]*)\)', body[s + len(STAR):])
    under = nxt and nxt.group(1) == '' and is_bar(nxt.group(2))
    if prev and is_bar(prev.group(1)) and not under:
      yield off + s, f'<sp>*</sp> written after the bar ({prev.group(1)}) instead of under it', 'after-bar'
    elif nxt and nxt.group(1) and is_bar(nxt.group(2)):
      yield off + s, f'space between <sp>*</sp> and the bar ({nxt.group(2)}): write <sp>*</sp>({nxt.group(2)})', 'space'
