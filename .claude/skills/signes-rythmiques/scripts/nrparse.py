"""GABC/NABC parsing for the rhythmic-sign study (Nocturnale Romanum)."""
import re

BAR_LEVEL = {'`': 0.5, '^': 0.5, ',': 1, ';': 2, ':': 3, '::': 4}
BASES = ('vi pu ta gr un cl pe po to ci sc pf sf tr st ds ts tg bv tv pr pi vs or sa pq ql qi pt oc ni').split()
RE_BASE = '|'.join(BASES)


class Note:
    __slots__ = ('pitch', 'cap', 'shape', 'ep', 'dot', 'dbl', 'seg', 'bar', 'epd', 'sep')

    def __init__(self, pitch, cap, seg):
        self.pitch, self.cap, self.seg = pitch, cap, seg
        self.shape = ''
        self.ep = False
        self.dot = False
        self.dbl = False   # part of a ".." group
        self.bar = 0
        self.epd = ''      # digits after the episema
        self.sep = ''      # separators written before the next note


def strip_gabc(s):
    s = re.sub(r'\[[^\]]*\]', '', s)
    s = re.sub(r"(?<![_'.\d])[cf]b?[1-5](?:@[cf]b?[1-5])?", '', s)   # clefs
    s = re.sub(r'[zZ][0+\-]?', '', s)                                 # line breaks
    s = re.sub(r'[a-nA-N]\+', '', s)                                  # custos
    s = re.sub(r'[a-n](?:##|[xy#XY])\??', '', s)                      # alterations
    return s


def parse_notes(s, notes, seg, unknown=None):
    """Append the notes of a GABC snippet; signs apply to the notes they follow."""
    s = strip_gabc(s)
    i, L = 0, len(s)
    while i < L:
        c = s[i]
        if s.startswith('::', i):
            if notes:
                notes[-1].bar = max(notes[-1].bar, 4)
            i += 2
            while i < L and s[i] in "'_": i += 1
            continue
        if c in ',;:`^':
            if notes:
                notes[-1].bar = max(notes[-1].bar, BAR_LEVEL[c])
            i += 1
            while i < L and (s[i].isdigit() or s[i] in "'_?"): i += 1
            continue
        if 'a' <= c <= 'n' or 'A' <= c <= 'N':
            notes.append(Note(c.lower(), c.isupper(), seg))
            i += 1
            continue
        if c in 'vs' and notes and notes[-1].shape.endswith(c) and notes[-1].seg == seg:
            # hvv, hss: another note on the same pitch
            nn = Note(notes[-1].pitch, False, seg)
            nn.shape = c
            notes.append(nn)
            i += 1
            continue
        if c in 'vVsoOw~<>qrR=':
            if notes:
                notes[-1].shape += c
            i += 1
            while i < L and s[i].isdigit() and c in 'oOrs': i += 1
            continue
        if c == '_':
            j = i
            while j < L and s[j] == '_': j += 1
            n = j - i
            for nt in notes[-n:]:
                nt.ep = True
            i = j
            d0 = i
            while i < L and s[i].isdigit(): i += 1
            if notes and i > d0:
                notes[-1].epd += s[d0:i]
            continue
        if c == '.':
            j = i
            while j < L and s[j] == '.': j += 1
            n = j - i
            if notes:
                notes[-1].dot = True
                if n >= 2:
                    notes[-1].dbl = True
                    if len(notes) >= 2:
                        notes[-2].dot = True
                        notes[-2].dbl = True
            i = j
            while i < L and s[i].isdigit(): i += 1
            continue
        if c in "/!@ -'" or c.isdigit():
            if notes and c in '/!@ ':
                notes[-1].sep += c
            i += 1
            continue
        if unknown is not None:
            unknown[c] += 1
        i += 1


RE_PITCH = r'(?:h[a-np])?'
RE_GLYPH = rf'(?:{RE_BASE})\d*(?:[SGM\-><~]\d*)*{RE_PITCH}'
RE_TOK = re.compile(
    r'(?P<space>[/`]+)'
    r'|(?P<br>(?:ob|cb))' + RE_PITCH.replace('(?:', '(?P<brp>', 1) +
    r'|(?P<sp>(?:su|pp)[tuvwxynqz]?\d+)' + r'(?P<spp>h[a-np])?' +
    r'|(?P<ls>l[st][a-z\-]*?\d)' +
    r'|(?P<bang>!)' +
    rf'|(?P<gl>{RE_GLYPH})'
)


class Atom:
    __slots__ = ('role', 'name', 'count', 'ls', 'cx', 'bracket', 'raw')

    def __init__(self, role, name, count, cx, bracket, raw=''):
        self.role, self.name, self.count, self.cx, self.bracket, self.raw = role, name, count, cx, bracket, raw
        self.ls = []


def glyph_name(g):
    return re.sub(r'h[a-np]$', '', g)


def parse_nabc(s, state, residue=None):
    """Return atoms in NOTE order: for each complex neume, pp, then glyphs, then su.
    state['b'] is the ob/cb bracket state, carried over the piece."""
    out, i, cx = [], 0, None
    def flush():
        nonlocal cx
        if cx:
            for a in cx['pp'] + cx['gl'] + cx['su']:
                a.ls = cx['ls']
                a.cx = cx['id']
                out.append(a)
        cx = None
    def new():
        nonlocal cx
        state['cx'] = state.get('cx', 0) + 1
        cx = {'pp': [], 'gl': [], 'su': [], 'ls': [], 'id': state['cx']}
    bang = False
    while i < len(s):
        m = RE_TOK.match(s, i)
        if not m:
            if residue is not None:
                residue[s[i:i+4]] += 1
            i += 1
            continue
        i = m.end()
        if m.group('space'):
            continue
        if m.group('br'):
            flush()
            state['b'] = (m.group('br') == 'ob') or (state['b'] and m.group('br') != 'cb')
            if m.group('br') == 'cb':
                state['closed'] = True
            continue
        if m.group('bang'):
            bang = True
            continue
        if m.group('gl'):
            if not bang:
                flush()
                new()
            bang = False
            g = m.group('gl')
            cx['gl'].append(Atom('base', glyph_name(g), None, 0, state['b'], g))
            continue
        if m.group('sp'):
            if cx is None:
                new()
            t = m.group('sp')
            kind, mod, n = t[:2], t[2:-1] if not t[-2:].isdigit() else re.sub(r'\d+$', '', t[2:]), int(re.search(r'\d+$', t).group())
            for _ in range(n):
                a = Atom(kind, kind + mod, 1, 0, state['b'], t)
                (cx['pp'] if kind == 'pp' else cx['su']).append(a)
            continue
        if m.group('ls'):
            if cx is None:
                new()
            cx['ls'].append(m.group('ls'))
    flush()
    return out


RE_GROUP = re.compile(r'([^()]*)\(([^()]*)\)')


def tokenise(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    head, _, n = t.rpartition('%%')
    def h(k):
        m = re.search(rf'^{k}:\s*([^;]*);', head, re.M)
        return m.group(1).strip() if m else ''
    return {'mode': h('mode'), 'part': h('office-part'), 'name': h('name')}, RE_GROUP.findall(n)
