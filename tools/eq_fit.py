"""Fit the Virus EQ (low shelf, mid peak, high shelf) so harmonic levels match OB-Xf.

    .venv/bin/python tools/eq_fit.py <slug> "<OB-Xf name>" [--hold 3] [--out patches/<slug>-eq.syx]

Compares loudness-normalised harmonic amplitudes (h1..h12) of single notes in three
registers, OB-Xf averaged over 3 renders. Use it when the filter fit matches overall
brightness but the body differs (Warmth: OB-Xf had 2nd-4th harmonics 8-14 dB stronger).
"""
import argparse
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fit import coordinate_search  # noqa: E402
from render_lib import RATE, ROOT, render_obxf, render_virus_many  # noqa: E402
from virus_patch import Patch  # noqa: E402

NOTES = (48, 60, 67)
HARMONICS = 12


def harmonic_db(x, note, hold, transpose):
    f0 = 440 * 2 ** ((note + transpose - 69) / 12)
    seg = x[int(0.4 * RATE):int(hold * RATE)]
    seg = seg / (np.sqrt(np.mean(seg ** 2)) + 1e-12)
    n = 1 << 18
    s = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n))
    f = np.fft.rfftfreq(n, 1 / RATE)
    return np.array([20 * np.log10(s[(f > k * f0 * 0.985) & (f < k * f0 * 1.015)].max() + 1e-9)
                     for k in range(1, HARMONICS + 1)])


def eq_loss(ref, hold, transpose, target):
    def fn(patches):
        out = np.zeros(len(patches))
        for note, tgt in zip(NOTES, target):
            for i, x in enumerate(render_virus_many(patches, notes=(note,), hold=hold, tail=0.2)):
                out[i] += np.mean(np.abs(harmonic_db(x, note, hold, transpose) - tgt)) / len(NOTES)
        return list(out)
    return fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("ref")
    ap.add_argument("--hold", type=float, default=3.0)
    ap.add_argument("--out")
    a = ap.parse_args()
    patch = Patch.from_syx(ROOT / "patches" / f"{a.slug}.syx")
    transpose = patch["Transpose"] - 64 + patch["Osc1 Semitone"] - 64  # sounding offset of the fundamental
    target = [np.mean([harmonic_db(render_obxf(a.ref, notes=(n,), hold=a.hold, tail=0.2), n, a.hold, transpose)
                       for _ in range(3)], axis=0) for n in NOTES]
    loss = eq_loss(a.ref, a.hold, transpose, target)
    before = loss([patch])[0]
    free = {"LowEQ Frequency": (0, 127), "LowEQ Gain": (16, 112), "MidEQ Frequency": (0, 127),
            "MidEQ Gain": (16, 112), "MidEQ Q-Factor": (0, 60), "HighEQ Gain": (16, 112)}  # Q <= ~1.4: musical, not one harmonic
    p = patch.copy()
    for k, v in {"MidEQ Frequency": 50, "MidEQ Gain": 64, "MidEQ Q-Factor": 51, "LowEQ Gain": 64, "HighEQ Gain": 64}.items():
        p[k] = v
    p, after = coordinate_search(p, free, loss, start_step=16, max_rounds=40)
    out = a.out or ROOT / "patches" / f"{a.slug}-eq.syx"
    p.save(out)
    print(f"harmonic error {before:.2f} dB -> {after:.2f} dB; wrote {out}")
    for k, (o, n) in sorted(p.diff(patch).items()):
        print(f"  {k:18s} {o:3d} -> {n:3d}")


if __name__ == "__main__":
    main()
