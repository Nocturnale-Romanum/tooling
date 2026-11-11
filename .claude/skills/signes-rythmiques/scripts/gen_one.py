"""Write gabc/<ID>_marteo.gabc from gabc/<ID>_dcrochu.gabc in a Nocturnale Romanum working copy (no commit),
and list what to review. Never overwrites an existing _marteo.

Usage: python gen_one.py (<ID> | --next) [--repo PATH] [--samples DIR] [--pdf]
  --repo     root of the nocturnale-romanum working copy (default: current directory)
  --samples  where to put a copy of the file and <ID>.tex for rendering (default: <temp>/signes-rythmiques)
  --pdf      also compile <ID>.pdf (lualatex, gregall font) and <ID>-1.png (pdftoppm, 170 dpi)"""
import argparse, os, re, shutil, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nrparse import *
from writer import notes_of
from generate import generate, targets

TEX = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=18mm]{geometry}
\usepackage{fontspec}
\usepackage[autocompile]{gregoriotex}
\gresetnabcfont{gregall}{12}
\grechangestaffsize{17}
\pagestyle{empty}
\begin{document}
\gregorioscore{%s_marteo}
\end{document}
"""


def incise_ends(G):
    """The sign on the last note before each bar, with flags for the cases to review."""
    rows, P = G['rows'], G['P']
    _, gs = tokenise(G['path'])
    cur, pbar, start, cue = [], 4, True, False
    out = []
    for gi, (txt_, g) in enumerate(gs):
        ns = notes_of(g)
        gg = g.split('|')[0]
        if start and ns:
            cue = '<sp>' in txt_ and not re.search(r'<sp>\s*(V/|\*)', txt_)
            start = False
        t = re.sub(r'<[^>]*>[^<]*</[^>]*>|<[^>]*>', '', txt_).replace('{', '').replace('}', '')
        star = '<sp>*</sp>' in txt_
        if ns:
            cur.append((gi, t, len(ns)))
        bm = re.findall(r'::|[,;:`^]', re.sub(r'\[[^\]]*\]', '', gg)) if not ns else []
        if bm and cur:
            sg = P.get((cur[-1][0], cur[-1][2] - 1), '?')
            text = ' '.join(''.join(a[1] for a in cur).split())
            bar = max(BAR_LEVEL[x] for x in bm)
            fl = []
            if star:
                fl.append('fin incipit')
            if bar == 2 and pbar >= 2 and len(cur) <= 8:
                fl.append(f'; apres pause longue, {len(cur)} syll.')
            if bar == 1 and re.search(r'[,;:.!?]\s*$', text):
                fl.append('virgule')
            if bar == 2 and not re.search(r'[,;:.!?]\s*$', text):
                fl.append('; sans ponct')
            out.append(f"  {bm[-1]:2s} {sg:2s} {'R' if cue else ' '} {text}" + ('   <' + ', '.join(fl) + '>' if fl else ''))
            pbar = bar
            cur = []
        if '::' in gg:
            start = True
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('id', nargs='?')
    ap.add_argument('--next', action='store_true')
    ap.add_argument('--repo', default='.')
    ap.add_argument('--samples', default=os.path.join(tempfile.gettempdir(), 'signes-rythmiques'))
    ap.add_argument('--pdf', action='store_true')
    a = ap.parse_args()
    samples = os.path.abspath(a.samples)
    os.chdir(a.repo)
    if a.next:
        tg = targets()
        print('restants', len(tg))
        i = tg[0]
    else:
        i = a.id
    dest = f'gabc/{i}_marteo.gabc'
    assert not os.path.exists(dest), dest + ' existe deja'
    G = generate(i)
    assert not G['left'], f"raccourcis restants : {G['left']}"
    open(dest, 'w', encoding='utf-8', newline='').write(G['text'])
    raised = G['raised']
    print('NABC eleve sur', len(raised), 'syllabes ; tassees sous hl :', [r[0] for r in raised if r[3]])
    for r in raised:
        print('   ', r[0], '|', r[1].split('|')[0], '|', ' / '.join(r[1].split('|')[1::2]), '->',
              ' / '.join(r[2].split('|')[1::2]), '(tassee)' if r[3] else '')
    st = G['stat']
    print('piece', i, '|', G['first'].split(';')[0], '| notes', len(G['rows']), '| non alignees', st['unaligned_notes'],
          '| sans NABC', st['no_nabc_notes'], '| seuls les signes different de dcrochu :', G['same'])
    vals = list(G['P'].values())
    print('episemes', vals.count('E'), 'points', vals.count('D'), 'chiffres', sorted(set(G['Dg'].values())), len(G['Dg']))
    for e in st['ex']:
        print('  NON ALIGNE', e)
    print('--- fins d incise (barre, signe, R = reprise, incise, <a revoir>)')
    print('\n'.join(incise_ends(G)))
    os.makedirs(samples, exist_ok=True)
    shutil.copy(dest, f'{samples}/{i}_marteo.gabc')
    open(f'{samples}/{i}.tex', 'w', encoding='utf-8').write(TEX % i)
    print('echantillon :', f'{samples}/{i}.tex')
    if a.pdf:
        # gregorio refuses absolute paths (kpse): compile from inside the folder
        subprocess.run(['lualatex', '--interaction=nonstopmode', '--shell-escape', f'{i}.tex'], cwd=samples,
                       stdout=subprocess.DEVNULL)
        subprocess.run(['pdftoppm', '-r', '170', '-png', f'{i}.pdf', i], cwd=samples)
        print('rendu :', f'{samples}/{i}.pdf')


if __name__ == '__main__':
    main()
