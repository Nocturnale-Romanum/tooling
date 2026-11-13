"""Run quality checks on Nocturnale Romanum GABC files.

Usage: python3 -m quality [--check NAME ...] [FILE ...]
Without FILE, checks <repo>/gabc/*_marteo.gabc, repo defaulting to ../liber-responsorialis/nocturnale-romanum.
"""
import argparse
import glob
import os
import sys

from .checks import CHECKS
from .gabc import line_col

DEFAULT_REPO = os.path.join(os.path.dirname(__file__), '..', '..', 'liber-responsorialis', 'nocturnale-romanum')


def main():
  p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  p.add_argument('files', nargs='*')
  p.add_argument('--repo', default=DEFAULT_REPO)
  p.add_argument('--check', action='append', choices=[c.NAME for c in CHECKS])
  p.add_argument('--list', action='store_true', help='list available checks')
  a = p.parse_args()
  if a.list:
    for c in CHECKS:
      print(f'{c.NAME}: {c.DESCRIPTION}')
    return 0
  checks = [c for c in CHECKS if not a.check or c.NAME in a.check]
  files = a.files or sorted(glob.glob(os.path.join(a.repo, 'gabc', '*_marteo.gabc')))
  count = 0
  for f in files:
    with open(f, encoding='utf-8') as fh:
      text = fh.read()
    for c in checks:
      for pos, msg in c.check(text):
        line, col = line_col(text, pos)
        excerpt = text[max(0, pos - 15):pos + 25].replace('\n', ' ')
        print(f'{os.path.relpath(f)}:{line}:{col}: [{c.NAME}] {msg}  …{excerpt}…')
        count += 1
  print(f'{count} issue(s) in {len(files)} file(s)', file=sys.stderr)
  return 1 if count else 0


if __name__ == '__main__':
  sys.exit(main())
