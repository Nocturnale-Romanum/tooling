"""Regenerate the generated pieces that marteo has not touched (file still matching the manifest) and that the
current rules write differently. Never touches a committed file or a file edited by hand. From the NR root.
Usage: python regen_intact.py <skill scripts> <samples> [--dry]"""
import difflib, hashlib, json, os, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
K, samples = sys.argv[1], os.path.abspath(sys.argv[2])
dry = '--dry' in sys.argv
sys.path.insert(0, K)
from generate import generate
man = json.load(open(samples + '/manifest.json'))
tracked = set(subprocess.run(['git', 'ls-files', 'gabc'], capture_output=True, text=True).stdout.split())
h = lambda b: hashlib.sha256(b).hexdigest()
skipped, changed, same = [], [], 0
for i in sorted(man):
    f = f'gabc/{i}_marteo.gabc'
    if f in tracked or not os.path.exists(f) or h(open(f, 'rb').read()) != man[i]:
        skipped.append(i)
        continue
    G = generate(i)
    assert G['same'] and not G['left'], (i, G['left'])
    new = G['text'].encode('utf-8')
    if new == open(f, 'rb').read():
        same += 1
        continue
    old = open(f, encoding='utf-8', newline='').read()
    d = [l for l in difflib.unified_diff(old.split('\n'), G['text'].split('\n'), lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
    changed.append(i)
    print(i, *[('   ' + l)[:240] for l in d], sep='\n')
    if not dry:
        open(f, 'wb').write(new)
        open(f'{samples}/{i}_marteo.gabc', 'wb').write(new)
        man[i] = h(new)
if not dry:
    json.dump(man, open(samples + '/manifest.json', 'w'), indent=0)
print('regeneres', len(changed), '| inchanges', same, '| laisses (commites ou retouches)', skipped)
