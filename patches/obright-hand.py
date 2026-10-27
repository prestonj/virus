"""Obright: Virus TI translation of OB-Xf's "Obright Original" (OB-Xa style polybrass).

Run: .venv/bin/python patches/obright-hand.py           # write patches/obright-hand.syx from FINAL
     .venv/bin/python patches/obright-hand.py --fit     # re-run stages 1-2 (amp, brightness)
     .venv/bin/python patches/obright-hand.py --refine  # stage 3 (band shapes) from obright-hand.syx

FINAL is what the user picked by ear ("dark"): the stage 3 band-shape fit, then
cutoff 47 -> 40 because the fits still sounded brighter than OB-Xf. Re-running the
fits will not reproduce it exactly.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ab_render import EXAMPLES, HOLD, TAIL  # noqa: E402
from fit import (coordinate_search, level_fit_loss, obxf_band_target, obxf_target,  # noqa: E402
                 spectral_fit_loss_multi, tone_fit_loss_multi)
from virus_patch import Patch  # noqa: E402

REF = "Obright Original"
CHORD = dict(notes=(48, 55, 60, 64), hold=1.5, tail=1.5, vel=100)


def voice():
    """Fixed structure taken straight from the OB-Xf patch."""
    p = Patch.from_syx()
    p.name = "Obright TI"
    p.set(
        Transpose=64 - 12,                 # the OB-Xf patch sounds an octave below the key played
        Osc1_Shape=64, Osc2_Shape=64,      # both sawtooth
        Osc_Balance=64 - 9,                # osc2 mix 0.72 vs osc1 1.0: lean slightly to osc1
        Osc2_Detune=48,                    # measured: 48 = +5.2 cents, matching OB-Xf's Osc2Detune 0.32
                                           # (the Virus curve is very non-linear: 16 is only +0.4 cents)
        Filter1_Mode=7,                    # Analog 4 Pole (OB-Xa CEM3320-style 24 dB)
        Filter_Routing=0,
        Filter_Balance=0,                  # filter 1 only: the OB-Xa has one filter, and in INIT's
                                           # serial routing filter 2 (no envelope) would stay closed
        Filter1_Resonance=0,
        Filter1_Keyfollow=64 + 32,         # OB-Xf keytrack 1.0 = full tracking
        Flt1_EnvAmt_Velocity=64 - 20,      # velocity reduces filter env, like VelToFilterEnv
    )
    return p


# Chosen by listening on 2026-10-24 (variants tried: resonance 20/24/30 with matching
# cutoff 39/38/36; the user preferred less resonance than 20).
FINAL = dict(
    Cutoff=40, Filter1_Resonance=14, Filter1_Env_Amt=91, Filter1_Keyfollow=90,
    Filter_Env_Attack=16, Filter_Env_Decay=95, Filter_Env_Sustain=11,
    Filter_Env_Sustain_Time=56, Filter_Env_Release=19,
    Amp_Env_Attack=16, Amp_Env_Decay=83, Amp_Env_Sustain=98, Amp_Env_Release=37,
)


def final():
    p = voice().set(**FINAL)
    out = ROOT / "patches" / "obright-hand.syx"
    p.save(out)
    print("wrote", out)
    return p


def main():
    # Stage 1: amp envelope, both filters wide open so only the VCA shapes the level
    _, target_level = obxf_target(REF, {"FilterCutoff": 1.0, "FilterEnvAmount": 0.0}, **CHORD)
    p = voice().set(Cutoff=127, Filter1_Env_Amt=0)
    p.set(Amp_Env_Attack=20, Amp_Env_Decay=80, Amp_Env_Sustain=98, Amp_Env_Release=50)
    p, loss = coordinate_search(p, {"Amp Env Attack": (0, 127), "Amp Env Decay": (0, 127),
                                    "Amp Env Sustain": (0, 127), "Amp Env Release": (0, 127)},
                                level_fit_loss(target_level, **CHORD))
    amp = {k: p[k] for k in ("Amp Env Attack", "Amp Env Decay", "Amp Env Sustain", "Amp Env Release")}
    print("amp envelope:", amp, f"(level shape error {loss:.2f} dB)")

    # Stage 2: filter, with the amp envelope fixed. Fitted over the same single note, fifth and
    # chord used for listening: fitting one low chord left the attack ~5 semitones too bright
    # on the others.
    targets = []
    for notes in EXAMPLES.values():
        kw = dict(notes=notes, hold=HOLD, tail=TAIL, vel=100)
        targets.append((*obxf_target(REF, **kw), kw))
    p = voice().set(**{k.replace(" ", "_"): v for k, v in amp.items()})
    p.set(Cutoff=56, Filter1_Env_Amt=96, Filter_Env_Attack=16, Filter_Env_Decay=88,
          Filter_Env_Sustain=19, Filter_Env_Release=20)
    p, loss = coordinate_search(p, {"Cutoff": (0, 127), "Filter1 Env Amt": (0, 127),
                                    "Filter Env Attack": (0, 127), "Filter Env Decay": (0, 127),
                                    "Filter Env Sustain": (0, 127), "Filter Env Release": (0, 127),
                                    "Filter Env Sustain Time": (0, 127),
                                    "Filter1 Keyfollow": (64, 127)},
                                tone_fit_loss_multi(targets), start_step=8)
    print(f"filter fit: brightness error {loss:.3f} octaves")

    out = ROOT / "patches" / "obright-hand.syx"
    p.save(out)
    print("wrote", out)
    for k, (old, new) in sorted(p.diff(Patch.from_syx()).items()):
        print(f"  {k:28s} {old:3d} -> {new:3d}")


def refine():
    """Stage 3: match third-octave band shapes, not just brightness.

    After v2 the user still heard the Virus as brighter and "less OB filter": its filter
    rolled off less steeply above cutoff and lacked the OB's plateau-then-knee. So the
    filter structure (resonance, poles, serial filter 2) is free here too.
    """
    targets = []
    for notes in EXAMPLES.values():
        kw = dict(notes=notes, hold=HOLD, tail=TAIL, vel=100)
        targets.append((*obxf_band_target(REF, **kw), kw))
    p = Patch.from_syx(ROOT / "patches" / "obright-hand.syx")
    free = {
        "Cutoff": (0, 127), "Filter1 Env Amt": (0, 127), "Filter1 Resonance": (0, 90),
        "Filter1 Mode": (4, 7), "Filter Routing": (0, 1), "Filter Balance": (0, 127),
        "Filter2 Env Amt": (0, 127), "Cutoff2 Offset": (32, 96), "Filter2 Resonance": (0, 60),
        "Filter Env Attack": (0, 127), "Filter Env Decay": (0, 127), "Filter Env Sustain": (0, 127),
        "Filter Env Sustain Time": (0, 127), "Filter1 Keyfollow": (64, 127),
    }
    p, loss = coordinate_search(p, free, spectral_fit_loss_multi(targets), start_step=8, max_rounds=60)
    print(f"band-shape error {loss:.2f} dB")
    p.save(ROOT / "patches" / "obright-hand.syx")
    for k, (old, new) in sorted(p.diff(Patch.from_syx()).items()):
        print(f"  {k:28s} {old:3d} -> {new:3d}")


if __name__ == "__main__":
    if "--refine" in sys.argv:
        refine()
    elif "--fit" in sys.argv:
        main()
    else:
        final()
