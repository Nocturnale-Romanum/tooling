"""The fitted model: T (neume table: key -> episema?) and L (note lengths of the NABC glyphs), stored as JSON."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, 'model.json')


def load_model(path=MODEL):
    m = json.load(open(path, encoding='utf-8'))
    return {tuple(k): v for k, v in m['T']}, m['L']


def save_model(T, L, path=MODEL):
    json.dump({'T': [[list(k), v] for k, v in sorted(T.items(), key=lambda a: str(a[0]))],
               'L': {k: {str(a): b for a, b in v.items()} for k, v in sorted(L.items())}},
              open(path, 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
