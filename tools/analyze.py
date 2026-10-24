"""Measure and plot renders so patches can be compared without listening.

usage: .venv/bin/python tools/analyze.py renders/a.wav [renders/b.wav ...] [--png out.png]

Prints per-file metrics and, with --png, draws a spectrogram + envelope panel per file.
"""
import argparse
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import stft


def load_mono(path):
    rate, data = wavfile.read(path)
    data = data.astype(np.float64)
    if data.ndim == 2:
        data = data.mean(axis=1)
    return rate, data


def envelope_db(x, rate, win_ms=10):
    n = max(1, int(rate * win_ms / 1000))
    frames = len(x) // n
    rms = np.sqrt(np.mean(x[: frames * n].reshape(frames, n) ** 2, axis=1) + 1e-12)
    return np.arange(frames) * n / rate, 20 * np.log10(rms)


def metrics(path):
    rate, x = load_mono(path)
    t_env, env = envelope_db(x, rate)
    peak_db = env.max()
    # attack: time from -40 dB below peak to within 3 dB of peak
    above = np.where(env > peak_db - 40)[0]
    near = np.where(env > peak_db - 3)[0]
    attack = (t_env[near[0]] - t_env[above[0]]) if len(above) and len(near) else float("nan")

    f, t, z = stft(x, rate, nperseg=4096, noverlap=3072)
    mag = np.abs(z)
    centroid = (f[:, None] * mag).sum(axis=0) / (mag.sum(axis=0) + 1e-12)
    loud = env.max() - 30
    sustain_slice = (t > 0.3) & (t < 1.2)
    return {
        "file": path,
        "seconds": len(x) / rate,
        "peak_db": round(float(peak_db), 1),
        "attack_ms": round(float(attack * 1000), 1),
        "centroid_hz_peak": round(float(centroid.max()), 0),
        "centroid_hz_sustain": round(float(np.median(centroid[sustain_slice])) if sustain_slice.any() else float("nan"), 0),
    }, (rate, x, t_env, env, f, t, mag)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wavs", nargs="+")
    ap.add_argument("--png")
    args = ap.parse_args()

    results = [metrics(w) for w in args.wavs]
    for m, _ in results:
        print("  ".join(f"{k}={v}" for k, v in m.items()))

    if args.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(len(results), 2, figsize=(12, 3.2 * len(results)), squeeze=False,
                                 gridspec_kw={"width_ratios": [3, 1]})
        for row, (m, (rate, x, t_env, env, f, t, mag)) in enumerate(results):
            ax = axes[row][0]
            db = 20 * np.log10(mag + 1e-9)
            ax.pcolormesh(t, f, db, vmin=db.max() - 80, vmax=db.max(), shading="auto", cmap="magma")
            ax.set_yscale("symlog", linthresh=200)
            ax.set_ylim(40, rate / 2)
            ax.set_ylabel("Hz")
            ax.set_title(m["file"], fontsize=9, loc="left")
            ax2 = axes[row][1]
            ax2.plot(t_env, env, lw=1)
            ax2.set_ylim(env.max() - 60, env.max() + 3)
            ax2.set_title("level dB", fontsize=9)
        axes[-1][0].set_xlabel("s")
        fig.tight_layout()
        fig.savefig(args.png, dpi=90)
        print("wrote", args.png)


if __name__ == "__main__":
    sys.exit(main())
