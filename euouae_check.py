# Accepts as arguments file or directory paths,
# checks all gabc files containing antiphons
# for standard EUOUAE lyrics and tones.

import os
import os.path
import sys

import arpeggio
from music21 import converter, volpiano
from music21.text import assembleLyrics
import chant21
from chant21.gabc.converter import AlterationWarning

euouae_tones = {}


class Skip(RuntimeError):
    pass


def _check(filename, verbose):
    if not filename.endswith('.gabc'):
        raise Skip('not a gabc')
    if '_' in filename:
        raise Skip('submitter (not selected) version')

    if verbose:
        print('checking {}'.format(filename))

    try:
        chant = converter.parse(filename)
    except (arpeggio.NoMatch, AlterationWarning) as e:
        print('ERROR {}: chant21 cannot parse ({})'.format(filename, e))
        return

    metadata = chant.editorial.metadata
    office_part = metadata.get('office-part')
    if office_part != 'an':
        raise Skip('not an antiphon ({})'.format(office_part))

    errors = []

    last_section = chant.sections[-1]
    lyrics = assembleLyrics(last_section)
    has_euouae = 'E U O U A E.' in lyrics
    # TODO: is there a rule which ones have EUOUAE and which Et sic finiatur?
    if not has_euouae and 'Et sic finiátur.' not in lyrics:
        errors.append('unexpected euouae lyrics "{}"'.format(lyrics))

    mode = metadata.get('mode')
    if mode is None:
        errors.append('mode missing')
    elif mode not in euouae_tones:
        if verbose:
            print('differentia {}: setting euouae from {} as standard'
                  .format(mode, filename))
            if not has_euouae:
                print('warning: the tone accepted as standard has'
                      ' less-standard EUOUAE lyrics')
        euouae_tones[mode] = volpiano.fromStream(last_section)
    elif volpiano.fromStream(last_section) != euouae_tones[mode]:
        # TODO: further normalization is required to correctly compare
        # EUOUAEs with Et sic finiatur's
        errors.append('mode {}, expected {}, got {}'
                      .format(mode, euouae_tones[mode],
                              volpiano.fromStream(last_section)))

    if len(errors) > 0:
        print('ERROR {}: {}'.format(filename, '; '.join(errors)))
    elif verbose:
        print('OK {}'.format(filename))


def check(filename, verbose=False):
    try:
        return _check(filename, verbose)
    except Skip as e:
        if verbose:
            print('skip {}: {}'.format(filename, e))


for path in sys.argv[1:]:
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for f in files:
                check(os.path.join(root, f))
    else:
        check(path)
