"""Render listening A/B files: OB-Xf reference vs Virus patch, loudness-matched.

usage: .venv/bin/python tools/ab_render.py "Obright Original" patches/obright.syx renders/obright/listen [--hold 2 --tail 1.5]

For each example (single note, fifth, chord) writes <example>_obxf.wav, <example>_virus.wav
and <example>_AB.wav (OB-Xf, short gap, then Virus). Both are scaled to the same RMS so
the comparison is about tone, not volume. OB-Xf renders keep its analog drift ("slop") on.
"""
import argparse
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


def level_match(x, hold):
    rms = np.sqrt(np.mean(x[: int(hold * RATE)] ** 2)) + 1e-12
    return x * (10 ** (TARGET_RMS_DB / 20) / rms)


def write(path, x):
    peak = np.abs(x).max()
    if peak > 0.98:  # never clip
        x = x * (0.98 / peak)
    wavfile.write(path, RATE, x.astype(np.float32))


def ab(ref, syx, out, hold=HOLD, tail=TAIL):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    patch = Patch.from_syx(syx)
    gap = np.zeros(int(0.6 * RATE))
    for name, notes in EXAMPLES.items():
        a = level_match(render_obxf(ref, notes=notes, hold=hold, tail=tail, slop=True), hold)
        b = level_match(render_virus(patch, notes=notes, hold=hold, tail=tail), hold)
        write(out / f"{name}_obxf.wav", a)
        write(out / f"{name}_virus.wav", b)
        write(out / f"{name}_AB.wav", np.concatenate([a, gap, b]))
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("syx")
    ap.add_argument("out")
    ap.add_argument("--hold", type=float, default=HOLD)
    ap.add_argument("--tail", type=float, default=TAIL)
    a = ap.parse_args()
    ab(a.ref, a.syx, a.out, a.hold, a.tail)


if __name__ == "__main__":
    main()
