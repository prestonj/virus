"""OB-Xf cross-mod -> Virus FM Amount; merges tables into tools/calibration.json.

    .venv/bin/python tools/calibrate_xmod.py      (~15 min)

OB-Xf cross-mod adds osc 1's output (+/-0.5) x OscCrossmod x 48 semitones to osc 2's pitch:
exponential FM, peak deviation 24 x OscCrossmod semitones. Virus FM (Osc FM Mode "Wave") is
linear, ~2.95 % of the carrier frequency per step, clamped near -83 %..+135 % (FINDINGS).

Exponential FM also raises osc 2's average pitch (translate.xmod_carrier_shift); the Virus
test patches get that shift too, as the translator applies it.

Method: osc 2 alone (triangle, 5 cents detuned so the 1:1 phase averages out), osc 1 as the
modulator. Compare the *change* in harmonic levels from each synth's own unmodulated sound,
so the small difference between their triangle waves cancels. Osc 2 at unison and +12.

Tables (OscCrossmod -> Virus Osc2 FM Amount):
  virus_fm_for_obxf_xmod_saw    osc 1 saw or triangle (they match)
  virus_fm_for_obxf_xmod_pulse  osc 1 pulse (needs ~1.5-2x at audio rate)
"""
import json
import pathlib

import numpy as np
from scipy.optimize import brentq

from render_lib import RATE, render_obxf, render_virus_many
from translate import CAL, inverse, logsc, set_osc2_pitch, xmod_carrier_shift
from virus_patch import Patch

OUT = pathlib.Path(__file__).resolve().parent / "calibration.json"
NOTE, F0, WIN = 48, 130.81, (0.3, 2.9)
XMOD = (0.03, 0.06, 0.1, 0.15, 0.25, 0.35, 0.5, 0.65, 0.85)
AMTS = list(range(0, 61, 2))
OB_WAVE = {"saw": dict(Osc1SawWave=1.0), "tri": dict(Osc1SawWave=0.0),
           "pulse": dict(Osc1SawWave=0.0, Osc1PulseWave=1.0, OscPW=0.0)}
V_WAVE = {"saw": dict(Osc1_Shape=64), "tri": dict(Osc1_Shape=0, Osc1_Wave_Select=1),
          "pulse": dict(Osc1_Shape=127, Osc1_Pulsewidth=0)}
MAX_LOSS = 5.0  # dB; worse fits are chaotic extreme-depth renders, dropped


def harmonics_db(x):
    s = x[int(WIN[0] * RATE):int(WIN[1] * RATE)] * np.hanning(int((WIN[1] - WIN[0]) * RATE))
    p = np.abs(np.fft.rfft(s)) ** 2
    f = np.fft.rfftfreq(len(s), 1 / RATE)
    h = np.array([p[(f > F0 * (k - 0.4)) & (f < F0 * (k + 0.4))].sum() for k in range(1, 50)])
    return 10 * np.log10(h / h.sum() + 1e-7)


def best_amounts(mod, semi):
    """{OscCrossmod: (best Virus FM Amount, loss dB)} for one modulator wave and interval."""
    ob_det = brentq(lambda v: 100 * logsc(v, 0.001, 0.6) - 5.0, 0, 1)

    def virus(c, amts):
        ps = []
        for a in amts:
            q = Patch.from_syx().set(Osc_Balance=127, Osc2_Shape=0, Osc2_Wave_Select=1, Osc_FM_Mode=2,
                                     Osc2_FM_Amount=a, **V_WAVE[mod])
            set_osc2_pitch(q, semi, 5.0 + 100 * xmod_carrier_shift(c, "pulse" if mod == "pulse" else "saw"))
            ps.append(q)
        return [harmonics_db(x) for x in render_virus_many(ps, notes=(NOTE,), hold=3.0, tail=0.05)]

    v0 = virus(0.0, [0])[0]  # unmodulated, unshifted: the reference for the Virus's change

    def ob(c):
        o = {"Osc1Mix": 0.0, "Osc2Mix": 1.0, "Osc2SawWave": 0.0, "OscCrossmod": c, "Osc2Detune": ob_det,
             "Osc2Pitch": 0.5 + semi / 48, **OB_WAVE[mod]}
        return np.mean([harmonics_db(render_obxf(None, o, notes=(NOTE,), hold=3.0, tail=0.05)) for _ in range(2)], axis=0)

    o0, out = ob(0.0), {}
    for c in XMOD:
        d = ob(c) - o0
        losses = [float(np.mean(np.abs((x - v0) - d))) for x in virus(c, AMTS)]
        i = int(np.argmin(losses))
        out[c] = (AMTS[i], losses[i])
    return out


def table(mods):
    runs = [best_amounts(m, s) for m in mods for s in (0, 12)]
    tab, last = {"0.0": 0}, 0
    for c in XMOD:
        good = sorted((r[c][1], r[c][0]) for r in runs if r[c][1] < MAX_LOSS)
        if good:
            # median of 3+ runs; with fewer, the best-fitting run (a median of two lets one bad fit win)
            pick = float(np.median([a for _, a in good])) if len(good) >= 3 else float(good[0][1])
            last = max(last, pick)  # keep it monotonic
            tab[str(c)] = last
        print(f"  xmod {c}: {[r[c] for r in runs]} -> {tab.get(str(c))}")
    return tab


def main():
    cal = json.loads(OUT.read_text())
    print("saw / triangle modulator")
    cal["virus_fm_for_obxf_xmod_saw"] = table(("saw", "tri"))
    print("pulse modulator")
    cal["virus_fm_for_obxf_xmod_pulse"] = table(("pulse",))
    OUT.write_text(json.dumps(cal, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
