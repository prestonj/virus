"""Render listening A/B files: OB-Xf reference vs Virus patch, loudness-matched.

usage: .venv/bin/python tools/ab_render.py "Obright Original" patches/obright.syx renders/obright/listen

For each example (single note, fifth, chord) writes <example>_obxf.wav, <example>_virus.wav
and <example>_AB.wav (OB-Xf, short gap, then Virus). Both are scaled to the same RMS so
the comparison is about tone, not volume. OB-Xf renders keep its analog drift ("slop") on.
"""
import pathlib
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from render_lib import RATE, render_obxf, render_virus  # noqa: E402
from virus_patch import Patch  # noqa: E402

EXAMPLES = {
    "1_single": (60,),
    "2_fifth": (60, 67),
    "3_chord": (55, 60, 64, 67),
}
HOLD, TAIL, TARGET_RMS_DB = 2.0, 1.5, -20.0


def level_match(x):
    rms = np.sqrt(np.mean(x[: int(HOLD * RATE)] ** 2)) + 1e-12
    return x * (10 ** (TARGET_RMS_DB / 20) / rms)


def write(path, x):
    peak = np.abs(x).max()
    if peak > 0.98:  # never clip; both files of a pair get the same treatment via shared target
        x = x * (0.98 / peak)
    wavfile.write(path, RATE, x.astype(np.float32))


def main():
    ref, syx, out = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    patch = Patch.from_syx(syx)
    gap = np.zeros(int(0.6 * RATE))
    for name, notes in EXAMPLES.items():
        a = level_match(render_obxf(ref, notes=notes, hold=HOLD, tail=TAIL, slop=True))
        b = level_match(render_virus(patch, notes=notes, hold=HOLD, tail=TAIL))
        write(out / f"{name}_obxf.wav", a)
        write(out / f"{name}_virus.wav", b)
        write(out / f"{name}_AB.wav", np.concatenate([a, gap, b]))
        print(f"{name}: notes {notes}")
    print("wrote", out)


if __name__ == "__main__":
    main()
