"""Generation of one <ID>_marteo.gabc from <ID>_dcrochu.gabc, in memory. The current directory is the repository root."""
import glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nrparse import *
from build import rows_for
from rules import predict_piece, digits_piece
from writer import rewrite, expand_shorthands, shorthands_left
from raise_nabc import raise_body
from model import load_model

_M = None


def model():
    global _M
    if _M is None:
        _M = load_model()
    return _M


def targets():
    """Responsories with NABC that have a _dcrochu and no _marteo, in order."""
    M = {os.path.basename(f)[:-12] for f in glob.glob('gabc/*_marteo.gabc')}
    out = []
    for f in sorted(glob.glob('gabc/*_dcrochu.gabc')):
        i = os.path.basename(f)[:-13]
        t = open(f, encoding='utf-8', errors='replace').read()
        p = re.search(r'office-part:\s*([^;]*);', t)
        if i not in M and p and p.group(1).strip() == 're' and '|' in t.rpartition('%%')[2]:
            out.append(i)
    return out


def strip_signs(s):
    return re.sub(r'_+\d*|\.+\d*', '', s)


def generate(i):
    """Everything about the generated piece: text of the file, rows, signs, raised syllables, checks."""
    T, L = model()
    path = f'gabc/{i}_dcrochu.gabc'
    stat = dict(aligned_notes=0, unaligned_notes=0, unaligned_snip=0, no_nabc_notes=0, ex=[])
    rows = rows_for(i, path, L, stat)
    P = predict_piece(rows, T)
    Dg = digits_piece(rows, P)
    head, body = rewrite(path, P, Dg)
    first = head.split('%%')[0].rstrip()          # first header block only
    first = re.sub(r'^submitter:.*$', 'submitter:marteo;', first, flags=re.M)
    if 'nabc-lines' not in first:
        first += '\nnabc-lines:1;'
    signed = body
    body, raised = raise_body(body)
    txt = first.replace('\r\n', '\n') + '\n%%' + body.replace('\r\n', '\n')
    if b'\r\n' in open(path, 'rb').read():
        txt = txt.replace('\n', '\r\n')
    d0 = open(path, encoding='utf-8', errors='replace').read().rpartition('%%')[2].replace('\r\n', '\n')
    return dict(id=i, path=path, text=txt, first=first, rows=rows, P=P, Dg=Dg, stat=stat, raised=raised,
                signed=signed, body=body,
                same=strip_signs(expand_shorthands(d0)) == strip_signs(signed.replace('\r\n', '\n')),
                left=shorthands_left(body))
