"""Review list of the generated pieces, from the logs of gen_one.py: a Markdown file, and a short table on stdout."""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
samples, out_md = sys.argv[1], sys.argv[2]
man = json.load(open(samples + '/manifest.json'))
L = lambda i: f'[{i}](https://nocturnale.marteo.fr/chant/{i})'
F = lambda i: f'[fichier](gabc/{i}_marteo.gabc)'
md = ['# Répons générés : points à revoir', '',
      'Pour chaque pièce : notes non alignées (restées sans signe), syllabes dont le NABC est élevé, '
      'et fins d\'incise à regarder.', '']
short = []
tot = dict(n=0, u=0, e=0, d=0, r=0)
for i in sorted(man):
    out = open(f'{samples}/logs/{i}.txt', encoding='utf-8').read()
    head = re.search(r'^piece .*\| name:([^|]*)\| notes (\d+) \| non alignees (\d+) .*: (\w+)$', out, re.M)
    sg = re.search(r'^episemes (\d+) points (\d+)', out, re.M)
    rz = re.search(r'^NABC eleve sur (\d+) syllabes ; tassees sous hl : (.*)$', out, re.M)
    una = re.findall(r"NON ALIGNE \('[^']*', '([^']*)', '([^']*)', \[([^\]]*)\]", out)
    fl = re.findall(r'^  (\S+)\s+(\S+)\s+(R?)\s*(.*?)\s+<([^>]*)>\s*$', out, re.M)
    raised = re.findall(r'^    (\S+) \| (.*?) \| (.*?) -> (.*?) (\(tassee\))?$', out, re.M)
    name, n, u, same = head.group(1).strip(), int(head.group(2)), int(head.group(3)), head.group(4)
    e, d = int(sg.group(1)), int(sg.group(2))
    tot['n'] += n; tot['u'] += u; tot['e'] += e; tot['d'] += d; tot['r'] += int(rz.group(1))
    md += [f'## {L(i)} — {name}', '',
           f'{F(i)} · {n} notes, {e} épisèmes, {d} points'
           + (f' · **{u} notes non alignées**' if u else '') + ('' if same == 'True' else ' · **notes modifiées !**'), '']
    if una:
        md += ['**Non alignées :** ' + ' ; '.join(f'*{t}* `({nn}|{a.replace(chr(39), "").replace(", ", " ")})`' for t, nn, a in una), '']
    if raised:
        md += ['**NABC élevé :** ' + ', '.join(f'*{t}*' + (' (tassée)' if tz else '') for t, g, a, b, tz in raised), '']
    if fl:
        md += ['**Fins d\'incise :**', '']
        md += [f'- `{b}` {s} *{t}* — {f}' + (' (reprise)' if r else '') for b, s, r, t, f in fl]
        md += ['']
    short.append((i, name, u, len(fl)))
open(out_md, 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print(len(man), 'pieces', tot)
for i, name, u, nf in short:
    print(f'| {L(i)} | {name} | {u or ""} | {nf or ""} |')
