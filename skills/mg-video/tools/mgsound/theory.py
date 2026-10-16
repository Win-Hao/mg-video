"""Notes and chords: 'A4' → MIDI → Hz, and roman-numeral progressions in a key."""
import numbers
import re

_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'pentatonic': [0, 2, 4, 7, 9],
}
_ROMAN = {'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4, 'VI': 5, 'VII': 6}


def midi(note):
    """'A4' → 69, 'C#3' → 49, 'Eb5' → 75; numbers (numpy's too) pass through."""
    if isinstance(note, numbers.Real):
        return int(note)
    m = re.fullmatch(r'([A-Ga-g])([#b]?)(-?\d)', note.strip())
    if not m:
        raise ValueError(f'not a note name: {note!r}')
    pc = _PC[m.group(1).upper()] + {'#': 1, 'b': -1, '': 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + pc


def hz(note):
    return 440.0 * 2 ** ((midi(note) - 69) / 12)


def chord(symbol, key='C', mode='major', octave=3):
    """Roman numeral in a key → MIDI notes, root in `octave`.
    Upper case = major triad, lower case = minor, '°' or 'dim' = diminished; prefix b/# shifts the root;
    suffix '7', 'maj7', '9', 'maj9', 'add9', 'sus4', '6' extends it. Example: chord('ii7', 'F')."""
    m = re.fullmatch(r'([b#]?)([ivIV]+)(°|dim)?(maj9|maj7|add9|sus4|7|9|6)?', symbol)
    if not m:
        raise ValueError(f'not a roman-numeral chord: {symbol!r}')
    acc, rn, dim, ext = m.groups()
    scale = SCALES[mode]
    root = midi(f'{key}{octave}') + scale[_ROMAN[rn.upper()]] + {'b': -1, '#': 1, '': 0}[acc]
    third = 4 if rn.isupper() else 3
    fifth = 6 if dim else 7
    tones = [0, third, fifth]
    if ext == 'sus4':
        tones = [0, 5, 7]
    elif ext in ('7', '9'):
        tones.append(9 if dim else 10)
    elif ext in ('maj7', 'maj9'):
        tones.append(11)
    elif ext == '6':
        tones.append(9)
    if ext in ('9', 'maj9', 'add9'):
        tones.append(14)
    return [root + t for t in tones]


def progression(prog, key='C', mode='major', octave=3):
    """'I V vi IV' → list of voiced chords, kept inside one octave window so changes move smoothly."""
    out = []
    lo = midi(f'{key}{octave}') - 2
    for sym in prog.split():
        notes = chord(sym, key, mode, octave)
        notes = sorted(n - 12 if n > lo + 14 else n for n in notes)
        out.append(notes)
    return out
