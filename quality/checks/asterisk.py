import re
from ..gabc import split_header, header_field

NAME = 'asterisk'
DESCRIPTION = ("antiphons, responsories and invitatories (not psalms, hymns, orations) have a <sp>*</sp>; next to a bar, it is "
               "written right under it: <sp>*</sp>(,), not (,) <sp>*</sp> nor <sp>*</sp> (,) (no placement rule for invitatories)")

CATEGORIES = [
  ('missing', 'no asterisk at all in the piece'),
  ('bare', "'*' written in the text without <sp></sp>"),
  ('after-bar', '<sp>*</sp> written after a bar instead of under it'),
  ('space', 'space between <sp>*</sp> and the bar under which it is written'),
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
  # '*' in the text (outside note groups and <sp></sp>)
  text_only = re.sub(r'\([^)]*\)|<sp>[^<]*</sp>', lambda m: ' ' * len(m.group()), body)
  bare = [m.start() for m in re.finditer(r'\*', text_only)]
  for b in bare:
    yield off + b, "'*' written without <sp></sp>: write <sp>*</sp>", 'bare'
  if not stars and not bare:
    yield off, 'no asterisk in the piece', 'missing'
  invitatory = header_field(header, 'office-part') == 'in'
  for s in stars:
    prev = re.search(r'\(([^)]*)\)(\s*)$', body[:s])
    nxt = re.match(r'(\s*)\(([^)]*)\)', body[s + len(STAR):])
    under = nxt and nxt.group(1) == '' and is_bar(nxt.group(2))
    if invitatory:
      continue   # no placement rule for invitatories
    if prev and is_bar(prev.group(1)) and not under:
      yield off + s, f'<sp>*</sp> written after the bar ({prev.group(1)}) instead of under it', 'after-bar'
    elif nxt and nxt.group(1) and is_bar(nxt.group(2)):
      yield off + s, f'space between <sp>*</sp> and the bar ({nxt.group(2)}): write <sp>*</sp>({nxt.group(2)})', 'space'
