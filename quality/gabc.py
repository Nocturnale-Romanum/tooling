"""Minimal GABC/NABC parsing helpers shared by the quality checks."""
import re

NOTE_GROUP = re.compile(r'\(([^)]*)\)')


def split_header(text):
  """Return (header, body, body_offset)."""
  i = text.find('%%')
  if i < 0:
    return '', text, 0
  return text[:i], text[i + 2:], i + 2


def nabc_lines(header):
  m = re.search(r'^nabc-lines:\s*(\d+)', header, re.M)
  return int(m.group(1)) if m else 0


def line_col(text, pos):
  line = text.count('\n', 0, pos) + 1
  return line, pos - text.rfind('\n', 0, pos)


def nabc_snippets(text):
  """Yield (pos, snippet) for each NABC snippet of the body, pos being its offset in text.
  Inside a note group, snippets separated by '|' alternate GABC, NABC 1..n, GABC, ..."""
  header, body, off = split_header(text)
  n = nabc_lines(header)
  if not n:
    return
  for m in NOTE_GROUP.finditer(body):
    pos = off + m.start(1)
    for i, snip in enumerate(m.group(1).split('|')):
      if i % (n + 1):
        yield pos, snip
      pos += len(snip) + 1


def header_field(header, name):
  m = re.search(r'^' + name + r':\s*([^;]*);', header, re.M)
  return m.group(1).strip() if m else None


CLEF = re.compile(r'(?<![a-z])([cf])b?([1-4])(?![0-9])')


def last_clef(body):
  """(type, line) of the last clef in body, e.g. ('c', 4)."""
  clef = None
  for m in NOTE_GROUP.finditer(body):
    for c in CLEF.finditer(m.group(1).split('|')[0]):
      clef = c.group(1), int(c.group(2))
  return clef


def to_c4(notes, clef):
  """Transpose GABC pitch letters written under clef to the same pitches under a c4 clef."""
  shift = 2 * (4 - clef[1]) + (3 if clef[0] == 'f' else 0)
  return ''.join(chr(ord(n) + shift) for n in notes.lower())
