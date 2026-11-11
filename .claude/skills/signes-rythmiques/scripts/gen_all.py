"""Generate every remaining target with the skill's gen_one.py, one after the other, from the NR root.
Keeps each log in <samples>/logs/<ID>.txt and a manifest (ID -> sha256 of the written file) in <samples>/manifest.json,
so that later a file can be removed or regenerated only if marteo has not touched it.
Prints one summary line per piece as it goes."""
import hashlib, json, os, re, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
K, samples = sys.argv[1], os.path.abspath(sys.argv[2])
sys.path.insert(0, K)
from generate import targets
os.makedirs(samples + '/logs', exist_ok=True)
man_path = samples + '/manifest.json'
man = json.load(open(man_path)) if os.path.exists(man_path) else {}
env = dict(os.environ, PYTHONIOENCODING='utf-8')
for i in targets():
    r = subprocess.run([sys.executable, '-I', K + '/gen_one.py', i, '--samples', samples],
                       capture_output=True, text=True, encoding='utf-8', env=env)
    out = r.stdout + r.stderr
    open(f'{samples}/logs/{i}.txt', 'w', encoding='utf-8').write(out)
    if r.returncode:
        print(f'{i}\tERREUR\t{out.strip().splitlines()[-1]}', flush=True)
        continue
    man[i] = hashlib.sha256(open(f'gabc/{i}_marteo.gabc', 'rb').read()).hexdigest()
    json.dump(man, open(man_path, 'w'), indent=0)
    head = re.search(r'^piece .*\| notes (\d+) \| non alignees (\d+) .*: (\w+)$', out, re.M)
    sg = re.search(r'^episemes (\d+) points (\d+)', out, re.M)
    rz = re.search(r'^NABC eleve sur (\d+) syllabes ; tassees sous hl : (.*)$', out, re.M)
    name = re.search(r'\| name:([^|]*)\|', out)
    flags = [f'{b} {s} {t.strip()} <{f}>' for b, s, t, f in
             re.findall(r'^  (\S+)\s+(\S+)\s+R?\s*(.*?)\s+<([^>]*)>\s*$', out, re.M)]
    una = re.findall(r"NON ALIGNE \('[^']*', '([^']*)', '([^']*)', \[([^\]]*)\]", out)
    print('\t'.join([i, name.group(1).strip() if name else '?', head.group(1), head.group(2), head.group(3),
                     sg.group(1), sg.group(2), rz.group(1), str(len(eval(rz.group(2)))),
                     ' ; '.join(f"{t}({n}|{a.replace(chr(39), '')})" for t, n, a in una),
                     ' ; '.join(flags)]), flush=True)
