"""mgsound — music beds and sound effects for mg-video, synthesized in numpy/scipy (no samples).

    import sys; sys.path.insert(0, '<skill>/tools')
    from mgsound import Mix, music, sfx
    m = Mix(6.0)
    music.bed(m, 'explainer', drop=3.5, outro=5.0)
    m.sfx(sfx.pop(), at=0.5)
    m.export('out/audio.wav', stems_dir='out/stems')

Reference: <skill>/references/audio.md
"""
from . import analyze, inst, music, sfx, theory
from .core import SR, Sound
from .mix import Mix, lufs, true_peak_db

__all__ = ['Mix', 'Sound', 'SR', 'music', 'sfx', 'inst', 'theory', 'analyze', 'lufs', 'true_peak_db']
