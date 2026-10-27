"""Final tone fit on the demo phrase itself: match its long-term spectrum to the reference.

    .venv/bin/python tools/phrase_fit.py juno-brass-1 [--suffix v2] [--set "Amp Env Attack=0" ...] [--no-fit]

The translators fit on one note and one chord around middle C. The demo phrase plays in
the patch's own register with its own note lengths, effects on, and that is what the user
hears: a bass played two octaves lower came out 5-20 dB dull above 200 Hz, short brass
stabs 8-16 dB dark above 5 kHz. This stage nudges cutoff, envelope amount, key tracking,
low/high EQ and Osc Mainvolume (less analog-filter drive) to match third-octave levels of
the level-matched phrase. --set applies by-ear edits first; those parameters stay fixed.

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


def free_params(p, fixed):
    out = {"Cutoff": (max(0, p["Cutoff"] - 16), min(127, p["Cutoff"] + 16)),
           "Filter1 Env Amt": (max(0, p["Filter1 Env Amt"] - 16), min(127, p["Filter1 Env Amt"] + 16)),
           "Filter1 Keyfollow": (64, 127), "LowEQ Gain": (40, 88), "HighEQ Gain": (40, 100),
           "Osc Mainvolume": (16, 64)}
    if p["Filter1 Env Amt"] == 0:
        del out["Filter1 Env Amt"]
    if p["Osc Balance"] > 0:  # a sub (or second osc) is mixed in
        out["Osc Balance"] = (max(1, p["Osc Balance"] - 24), min(127, p["Osc Balance"] + 24))
    if p["Filter Balance"] == 64 and p["Filter2 Mode"] == 1:  # HPF in use
        out["Cutoff2"] = (max(0, p["Cutoff2"] - 16), min(127, p["Cutoff2"] + 16))
    return {k: v for k, v in out.items() if k not in fixed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--suffix", default="v2")
    ap.add_argument("--set", action="append", default=[], metavar="PARAM=VALUE")
    ap.add_argument("--no-fit", action="store_true")
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
    target = np.mean([phrase_bands(level_match(ref_seq(ref, seq, tail))) for _ in range(2)], axis=0)

    def loss_fn(ps):
        with ThreadPoolExecutor() as ex:
            xs = list(ex.map(lambda q: render_virus_seq(q, seq, tail=tail, stereo=True), ps))
        return [loss(target, phrase_bands(x)) for x in xs]
    l0 = loss_fn([p])[0]
    before = p.copy()
    if not a.no_fit:
        p, l1 = coordinate_search(p, free_params(p, fixed), loss_fn, start_step=8, max_rounds=30)
    else:
        l1 = l0
    for k, (old, new) in sorted(p.diff(before).items()):
        edits.append(f"{k} {old} -> {new} (phrase fit)")
    out = f"{a.slug}-{a.suffix}"
    p.save(ROOT / "patches" / f"{out}.syx")
    report = json.loads((ROOT / "patches" / f"{a.slug}.json").read_text())
    report.update(variant_edits=edits, phrase_error_db=[round(l0, 2), round(l1, 2)],
                  changes_from_init={k: [x, y] for k, (x, y) in sorted(p.diff(Patch.from_syx()).items())})
    (ROOT / "patches" / f"{out}.json").write_text(json.dumps(report, indent=1))
    print(f"wrote patches/{out}.syx  phrase band error {l0:.2f} -> {l1:.2f} dB")
    for e in edits:
        print("  ", e)


if __name__ == "__main__":
    main()
