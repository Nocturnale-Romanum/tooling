import re
from ..gabc import nabc_snippets

NAME = 'ob-cb'
DESCRIPTION = "every NABC 'ob' (opening bracket) is closed by a 'cb' before the next 'ob' or the end of the piece"


def check(text):
  opened = None
  for pos, snip in nabc_snippets(text):
    for m in re.finditer(r'ob|cb', snip):
      if m.group() == 'ob':
        if opened is not None:
          yield opened, "'ob' not closed by 'cb' before next 'ob'"
        opened = pos + m.start()
      elif opened is None:
        yield pos + m.start(), "'cb' without preceding 'ob'"
      else:
        opened = None
  if opened is not None:
    yield opened, "'ob' not closed by 'cb' before end of piece"
