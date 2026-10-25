"""Translate an OB-Xf patch into a Virus TI patch: map the structure, then fit by rendering.

    .venv/bin/python tools/translate.py "OBX Bass 1" --slug obx-bass-1 [--hold 2 --tail 1.5]

Writes patches/<slug>.syx, patches/<slug>.json (mapping notes, fitted values, scores)
and A/B listening files in renders/<slug>/listen/. See docs/PROCESS.md for the method
and docs/FINDINGS.md for the measurements behind each mapping.
"""
import argparse
import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ab_render import EXAMPLES, ab  # noqa: E402
from fit import coordinate_search, level_fit_loss, obxf_band_target, obxf_target, spectral_fit_loss_multi  # noqa: E402
from render_lib import RATE, ROOT, centroid, render_obxf, render_virus_many  # noqa: E402
from virus_patch import Patch  # noqa: E402

CAL = json.loads((ROOT / "tools" / "calibration.json").read_text())


def logsc(p, lo, hi, r=19.0):
    return ((math.exp(p * math.log(r + 1)) - 1) / r) * (hi - lo) + lo


def inverse(table, target):
    """Control value whose measured unit is closest to target (linear interpolation, monotonic part)."""
    pts = sorted((float(v), float(u)) for v, u in table.items())
    xs, ys = zip(*pts)
    ys = np.maximum.accumulate(ys)  # tolerate small measurement wobble
    return int(round(float(np.interp(target, ys, xs))))


def obxf_params(name):
    from render_lib import obxfpy, find_patch
    e = obxfpy.ObxfEngine(float(RATE))
    e.load_patch(str(find_patch(name)))
    return {k: e.get_param(k) for k in e.get_param_ids()}


def remap_lfo_dest(v):
    """OB-Xf LFO destination switch: 0 -> off, 0.5 -> +1, 1 -> -1."""
    r = round(v * 2) / 2
    return {0.0: 0, 0.5: 1, 1.0: -1}[r]


def map_structure(d, name):
    """Fixed voice structure from OB-Xf parameter values. Returns (patch, notes)."""
    notes = []
    p = Patch.from_syx()
    p.name = name[:10]

    # Pitch. OB-Xf: Transpose = round((2v-1)*24), osc pitch = (v-0.5)*48 semitones
    p["Transpose"] = 64 + round((2 * d["Transpose"] - 1) * 24)
    p["Osc1 Semitone"] = 64 + round((d["Osc1Pitch"] - 0.5) * 48)
    p["Osc2 Semitone"] = 64 + round((d["Osc2Pitch"] - 0.5) * 48)

    # Waveforms. OB-Xf can sum saw+pulse per osc; the Virus can't, so saw wins.
    for i in (1, 2):
        saw, pulse = d[f"Osc{i}SawWave"] > 0.5, d[f"Osc{i}PulseWave"] > 0.5
        if saw and pulse:
            notes.append(f"osc{i}: saw+pulse in OB-Xf, saw only on the Virus")
        if pulse and not saw:
            pw = d["OscPW"] + (d["Osc2PWOffset"] if i == 2 else 0.0)
            duty = float(np.interp(min(pw, 1.0), *zip(*sorted((float(k), v) for k, v in CAL["obxf_pulse_duty"].items()))))
            # virus duty table falls with value; invert on (-duty)
            vtab = {k: -v for k, v in CAL["virus_pulse_duty"].items()}
            p[f"Osc{i} Shape"] = 127
            p[f"Osc{i} Pulsewidth"] = inverse(vtab, -duty)
            notes.append(f"osc{i}: pulse, duty {duty:.3f}")
        else:
            p[f"Osc{i} Shape"] = 64

    # Mix -> balance (0 = osc1 only, 127 = osc2 only)
    m1, m2 = d["Osc1Mix"], d["Osc2Mix"]
    if m1 <= 0.01:
        p["Osc Balance"] = 127
    elif m2 <= 0.01:
        p["Osc Balance"] = 0
    else:
        p["Osc Balance"] = int(round(64 + 63 * (m2 - m1) / max(m1, m2)))

    detune_c = 100 * logsc(d["Osc2Detune"], 0.001, 0.6)
    p["Osc2 Detune"] = inverse(CAL["virus_osc2_detune_cents"], detune_c)
    notes.append(f"osc2 detune {detune_c:.1f} cents")
    if d["OscSync"] > 0.5:
        p["Osc2 Sync"] = 1
    if d["OscCrossmod"] > 0.01:
        notes.append("cross-mod not translated")

    # Filter: one analog filter, filter 2 out of the path (FINDINGS: Filter Balance)
    p["Filter1 Mode"] = 7 if d["Filter4PoleMode"] > 0.5 else 5  # Analog 4 / 2 pole
    p["Filter Balance"] = 0
    p["Filter1 Keyfollow"] = int(round(64 + 26 * d["FilterKeyFollow"]))
    p["Flt1 EnvAmt Velocity"] = int(round(64 - 30 * d["VelToFilterEnv"]))
    p["Amp Velocity"] = int(round(64 + 40 * d["VelToAmpEnv"]))
    if d["Filter4PoleXpander"] > 0.5 or (d["FilterMode"] > 0.01 and d["Filter4PoleMode"] < 0.5):
        notes.append("non-LP filter mode in OB-Xf: translated as low-pass")

    # Unison: OB-Xf scatters voices randomly within +/- UnisonDetune semitones; the Virus spreads
    # evenly. Match the standard deviation: uniform(-s, s) has sd s/sqrt(3); evenly spread N voices
    # across total width w has sd ~ w * sqrt((N+1)/(12(N-1))). Virus twin table gives width per value.
    if d["Unison"] > 0.5:
        n = 1 + int(d["UnisonVoices"] * 32)
        n_v = min(n, 16)
        p["Unison Mode"] = min(n_v - 1, 7)
        n_v = p["Unison Mode"] + 1
        s = 100 * logsc(d["UnisonDetune"], 0.001, 1.0)
        width = (s / math.sqrt(3)) / math.sqrt((n_v + 1) / (12 * max(1, n_v - 1)))
        # Evenly spaced Virus voices beat more regularly than OB-Xf's random ones: the user heard
        # the sd-matched value as wobblier (OBX Bass 1: 121 -> 80 matched OB-Xf's typical wobble)
        p["Unison Detune"] = int(round(inverse(CAL["virus_unison2_cents"], width) * 2 / 3))
        p["Key Mode"] = 1  # OB-Xf unison stacks every voice on one note: mono
        notes.append(f"unison {n} voices (Virus {n_v}), OB-Xf spread +/-{s:.0f} c random -> even width {width:.0f} c")

    # LFO 1 -> oscillator pitch (vibrato / opposed-pitch shimmer)
    o1, o2 = remap_lfo_dest(d["LFO1ToOsc1Pitch"]), remap_lfo_dest(d["LFO1ToOsc2Pitch"])
    if o1 or o2:
        hz = logsc(d["LFO1Rate"], 0.0, 250.0, 3775.0)
        cents = 100 * logsc(logsc(d["LFO1ModAmount1"], 0.0, 1.0, 60.0), 0.0, 60.0, 10.0)
        p["Lfo1 Rate"] = inverse({k: v for k, v in CAL["virus_lfo1_rate_hz"].items() if int(k) >= 40}, hz)
        p["Lfo1 Shape"] = 0  # sine
        amt = inverse(CAL["virus_lfo1_osc_depth_cents"], cents) - 64
        if o1:
            p["Osc1 Lfo1 Amount"] = 64 + o1 * amt
        if o2:
            p["Osc2 Lfo1 Amount"] = 64 + o2 * amt
        notes.append(f"LFO1 {hz:.2f} Hz, +/-{cents:.1f} c on osc1 {o1:+d} / osc2 {o2:+d}")
    for k in ("LFO1ToFilterCutoff", "LFO1ToOsc1PW", "LFO1ToOsc2PW", "LFO2ToFilterCutoff", "LFO2ToOsc1Pitch",
              "LFO2ToOsc2Pitch", "LFO2ToOsc1PW", "LFO2ToOsc2PW", "EnvToPitchAmount", "EnvToPWAmount", "Portamento"):
        if d.get(k, 0) > 0.01:
            notes.append(f"{k}={d[k]:.3f} not translated")
    return p, notes


def timing(d):
    """Hold/tail long enough to hear the envelopes, within limits."""
    a = logsc(d["AmpEnvAttack"], 4, 60000, 900) / 1000
    r = logsc(d["AmpEnvRelease"], 8, 60000, 900) / 1000
    hold = float(np.clip(a + 1.5, 2.0, 4.0))
    tail = float(np.clip(r * 1.2, 1.5, 4.0))
    return round(hold, 1), round(tail, 1)


def attack_brightness(patches_or_ref, examples, hold, tail, ref_name=None):
    """Median brightness (octaves) over the first 0.3 s, averaged across examples."""
    n = int(0.3 * RATE / 512)
    if ref_name:
        vals = []
        for notes in examples:
            xs = [render_obxf(ref_name, notes=notes, hold=hold, tail=tail) for _ in range(3)]
            vals.append(np.mean([np.median(centroid(x)[:n]) for x in xs]))
        return float(np.mean(vals))
    tot = np.zeros(len(patches_or_ref))
    for notes in examples:
        for i, x in enumerate(render_virus_many(patches_or_ref, notes=notes, hold=hold, tail=tail)):
            tot[i] += np.median(centroid(x)[:n])
    return tot / len(examples)


def translate(name, slug, hold=None, tail=None, log=print):
    d = obxf_params(name)
    base, notes = map_structure(d, name)
    if hold is None:
        hold, tail = timing(d)
    examples = list(EXAMPLES.values())
    kw = lambda notes: dict(notes=notes, hold=hold, tail=tail, vel=100)  # noqa: E731
    report = {"reference": name, "hold": hold, "tail": tail, "mapping_notes": notes}
    for n in notes:
        log("  map:", n)

    # Stage 1: amp envelope against OB-Xf with both filters wide open (chord)
    chord = kw(examples[-1])
    _, lvl = obxf_target(name, {"FilterCutoff": 1.0, "FilterEnvAmount": 0.0, "FilterResonance": 0.0}, **chord)
    p = base.copy().set(Cutoff=127, Filter1_Env_Amt=0, Filter1_Resonance=0)
    a_ms = logsc(d["AmpEnvAttack"], 4, 60000, 900)
    p.set(Amp_Env_Attack=min(127, int(20 + 30 * math.log10(max(a_ms, 4) / 4))), Amp_Env_Decay=80,
          Amp_Env_Sustain=int(127 * d["AmpEnvSustain"]), Amp_Env_Release=50)
    amp_free = {k: (0, 127) for k in ("Amp Env Attack", "Amp Env Decay", "Amp Env Sustain", "Amp Env Release")}
    p, l1 = coordinate_search(p, amp_free, level_fit_loss(lvl, **chord), log=log)
    report["amp_level_error_db"] = round(l1, 2)
    amp = {k: p[k] for k in amp_free}

    # Stage 2: filter on third-octave band shapes over single, fifth, chord
    targets = [(*obxf_band_target(name, **kw(n)), kw(n)) for n in examples]
    p = base.copy()
    for k, v in amp.items():
        p[k] = v
    p.set(Cutoff=int(20 + 90 * d["FilterCutoff"]), Filter1_Env_Amt=int(127 * min(1, d["FilterEnvAmount"] * 1.2)),
          Filter1_Resonance=int(60 * d["FilterResonance"]), Filter_Env_Attack=10, Filter_Env_Decay=80,
          Filter_Env_Sustain=int(127 * d["FilterEnvSustain"]), Filter_Env_Release=30)
    free = {"Cutoff": (0, 127), "Filter1 Env Amt": (0, 127), "Filter1 Resonance": (0, 90),
            "Filter1 Keyfollow": (64, 127), "Filter Env Attack": (0, 127), "Filter Env Decay": (0, 127),
            "Filter Env Sustain": (0, 127), "Filter Env Sustain Time": (0, 127), "Filter Env Release": (0, 127)}
    p, l2 = coordinate_search(p, free, spectral_fit_loss_multi(targets), start_step=16, max_rounds=40, log=log)
    report["band_shape_error_db"] = round(l2, 2)

    # Stage 3: trim cutoff so the first 0.3 s is as bright as OB-Xf (fits tend to end up brighter;
    # the user picked the attack-matched "dark" Obright by ear)
    ref_b = attack_brightness(None, examples, hold, tail, ref_name=name)
    cuts = list(range(max(0, p["Cutoff"] - 12), min(127, p["Cutoff"] + 6) + 1))
    bs = attack_brightness([p.copy().set(Cutoff=c) for c in cuts], examples, hold, tail)
    i = int(np.argmin(np.abs(bs - ref_b)))
    report["cutoff_fit"], report["cutoff_trimmed"] = p["Cutoff"], cuts[i]
    report["attack_brightness_gap_semitones"] = round(12 * float(bs[i] - ref_b), 2)
    p["Cutoff"] = cuts[i]

    out = ROOT / "patches" / f"{slug}.syx"
    p.save(out)
    report["changes_from_init"] = {k: [a, b] for k, (a, b) in sorted(p.diff(Patch.from_syx()).items())}
    (ROOT / "patches" / f"{slug}.json").write_text(json.dumps(report, indent=1))
    log(f"wrote {out}  amp {l1:.2f} dB, bands {l2:.2f} dB, cutoff {report['cutoff_fit']} -> {cuts[i]}")
    ab(name, out, ROOT / "renders" / slug / "listen", hold=hold, tail=tail)
    return p, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--hold", type=float)
    ap.add_argument("--tail", type=float)
    a = ap.parse_args()
    translate(a.name, a.slug, a.hold, a.tail)


if __name__ == "__main__":
    main()
