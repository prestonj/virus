"""Final tone fit on the demo phrase itself: match its long-term spectrum to the reference.

    .venv/bin/python tools/phrase_fit.py juno-brass-1 [--suffix v2] [--set "Amp Env Attack=0" ...] [--no-fit] [--time]

The translators fit on one note and one chord around middle C. The demo phrase plays in
the patch's own register with its own note lengths, effects on, and that is what the user
hears: a bass played two octaves lower came out 5-20 dB dull above 200 Hz, short brass
stabs 8-16 dB dark above 5 kHz. This stage nudges cutoff, envelope amount, key tracking,
low/high EQ and Osc Mainvolume (less analog-filter drive) to match third-octave levels of
the level-matched phrase. --set applies by-ear edits first; those parameters stay fixed.
--time also matches loudness over time (0.1 s frames) and frees the filter envelope's attack and
decay, amp release, delay feedback and Envelope 3 release: for pads, where the swell and the tail
are the sound.

Reads patches/<slug>.syx, writes patches/<slug>-<suffix>.syx/.json (report notes what changed).
"""
import argparse
import json
import pathlib
import sys

import numpy as np
from scipy.signal import welch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from demo import PHRASES, ROLES, level_match, ref_seq  # noqa: E402
from fit import coordinate_search  # noqa: E402
from render_lib import RATE, ROOT, render_virus_seq  # noqa: E402
from virus_patch import Patch  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402

CENT = [63 * 2 ** (i / 3) for i in range(25)]  # 63 Hz - 16 kHz
FLOOR = 50.0  # dB under the loudest band: quieter bands don't count


def phrase_bands(x):
    m = x.mean(axis=1) if x.ndim == 2 else x
    f, p = welch(m, RATE, nperseg=8192)
    b = np.array([10 * np.log10(p[(f >= c / 2 ** (1 / 6)) & (f < c * 2 ** (1 / 6))].sum() + 1e-20) for c in CENT])
    return b - b.max()


def loss(target, b):
    w = target > -FLOOR
    return float(np.mean(np.abs(np.maximum(b, -FLOOR - 10) - target)[w]))


def phrase_level(x, frame=0.1):
    m = x.mean(axis=1) if x.ndim == 2 else x
    n = int(frame * RATE)
    lv = np.array([10 * np.log10(np.mean(m[i:i + n] ** 2) + 1e-20) for i in range(0, len(m) - n, n)])
    return np.maximum(lv - lv.max(), -40.0)


def free_params(p, fixed, time=False):
    out = {"Cutoff": (max(0, p["Cutoff"] - 16), min(127, p["Cutoff"] + 16)),
           "Filter1 Env Amt": (max(0, p["Filter1 Env Amt"] - 16), min(127, p["Filter1 Env Amt"] + 16)),
           "Filter1 Keyfollow": (64, 127), "LowEQ Gain": (40, 88), "HighEQ Gain": (40, 100),
           "Osc Mainvolume": (16, 64)}
    if p["Filter1 Env Amt"] == 0:
        del out["Filter1 Env Amt"]
    if p["Osc Balance"] > 0:  # a sub (or second osc) is mixed in
        out["Osc Balance"] = (max(1, p["Osc Balance"] - 24), min(127, p["Osc Balance"] + 24))
    if p["Noise Volume"] > 0:  # the Virus noise at Color 64 carries more low end than the Juno's (Afterglow Pad +14 dB at 63 Hz)
        out["Noise Color"] = (32, 127)
    if p["Filter Balance"] == 64 and p["Filter2 Mode"] == 1:  # HPF in use
        out["Cutoff2"] = (max(0, p["Cutoff2"] - 16), min(127, p["Cutoff2"] + 16))
    if time:
        # the filter envelope's timing shapes a pad's swell (Afterglow Pad's negative envelope dips the level
        # 17 dB at 0.75 s); left out, the fit slowed the amp attack to fake the dip
        for k in ("Filter Env Attack", "Filter Env Decay", "Amp Env Release", "Delay Feedback", "Envelope 3/Release"):
            out[k] = (max(0, p[k] - 16), min(127, p[k] + 16))
        if not p["Delay Send"]:
            del out["Delay Feedback"]
        if p["Assign 4 Source"] != 38:
            del out["Envelope 3/Release"]
    return {k: v for k, v in out.items() if k not in fixed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--suffix", default="v2")
    ap.add_argument("--set", action="append", default=[], metavar="PARAM=VALUE")
    ap.add_argument("--no-fit", action="store_true")
    ap.add_argument("--time", action="store_true", help="also match loudness over time (pads)")
    a = ap.parse_args()
    ref, role, _ = ROLES[a.slug]
    seq, tail = PHRASES[role][0](), PHRASES[role][1]
    p = Patch.from_syx(ROOT / "patches" / f"{a.slug}.syx")
    edits, fixed = [], set()
    for s in a.set:
        k, v = s.rsplit("=", 1)
        edits.append(f"{k} {p[k]} -> {int(v)} (by ear)")
        p[k] = int(v)
        fixed.add(k)
    refs = [level_match(ref_seq(ref, seq, tail)) for _ in range(2)]
    target = np.mean([phrase_bands(x) for x in refs], axis=0)
    t_level = np.mean([phrase_level(x) for x in refs], axis=0)

    def one(x):
        out = loss(target, phrase_bands(x))
        if a.time:
            lv = phrase_level(x)
            n = min(len(lv), len(t_level))
            out += float(np.mean(np.abs(lv[:n] - t_level[:n])))
        return out

    def loss_fn(ps):
        with ThreadPoolExecutor() as ex:
            xs = list(ex.map(lambda q: render_virus_seq(q, seq, tail=tail, stereo=True), ps))
        return [one(x) for x in xs]
    l0 = loss_fn([p])[0]
    before = p.copy()
    if not a.no_fit:
        p, l1 = coordinate_search(p, free_params(p, fixed, a.time), loss_fn, start_step=8, max_rounds=30)
    else:
        l1 = l0
    for k, (old, new) in sorted(p.diff(before).items()):
        edits.append(f"{k} {old} -> {new} (phrase fit)")
    out = f"{a.slug}-{a.suffix}"
    p.save(ROOT / "patches" / f"{out}.syx")
    report = json.loads((ROOT / "patches" / f"{a.slug}.json").read_text())
    report.update(variant_edits=edits, phrase_error_db=[round(l0, 2), round(l1, 2)], phrase_fit_time=a.time,
                  changes_from_init={k: [x, y] for k, (x, y) in sorted(p.diff(Patch.from_syx()).items())})
    (ROOT / "patches" / f"{out}.json").write_text(json.dumps(report, indent=1))
    print(f"wrote patches/{out}.syx  phrase band error {l0:.2f} -> {l1:.2f} dB")
    for e in edits:
        print("  ", e)


if __name__ == "__main__":
    main()
