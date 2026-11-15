import re
from ..gabc import split_header, header_field

NAME = 'asterisk'
DESCRIPTION = ("antiphons, responsories and invitatories (not psalms, hymns, orations) have a <sp>*</sp>; next to a bar, it is "
               "written right under it: <sp>*</sp>(,), not (,) <sp>*</sp> nor <sp>*</sp> (,); in invitatories it follows "
               "the bar instead: (;) <sp>*</sp> Ve(...)")

CATEGORIES = [
  ('missing', 'no <sp>*</sp> in the piece'),
  ('after-bar', '<sp>*</sp> written after a bar instead of under it'),
  ('space', 'space between <sp>*</sp> and the bar under which it is written'),
  ('invitatory', 'invitatory: <sp>*</sp> written under or before a bar instead of after it'),
]

PARTS = ('an', 're', 'in')   # not psalms, hymns, orations
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
  invitatory = header_field(header, 'office-part') == 'in'
  for s in stars:
    prev = re.search(r'\(([^)]*)\)(\s*)$', body[:s])
    nxt = re.match(r'(\s*)\(([^)]*)\)', body[s + len(STAR):])
    under = nxt and nxt.group(1) == '' and is_bar(nxt.group(2))
    if invitatory:
      if nxt and is_bar(nxt.group(2)) and not (prev and is_bar(prev.group(1))):
        yield (off + s, f'invitatory: <sp>*</sp> written {"under" if under else "before"} the bar ({nxt.group(2)}) '
               f'instead of after it: ({nxt.group(2)}) <sp>*</sp>', 'invitatory')
    elif prev and is_bar(prev.group(1)) and not under:
      yield off + s, f'<sp>*</sp> written after the bar ({prev.group(1)}) instead of under it', 'after-bar'
    elif nxt and nxt.group(1) and is_bar(nxt.group(2)):
      yield off + s, f'space between <sp>*</sp> and the bar ({nxt.group(2)}): write <sp>*</sp>({nxt.group(2)})', 'space'
