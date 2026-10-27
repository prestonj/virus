"""Translate an Arturia Jun-6 V (Juno-6/60) preset into a Virus TI patch: map, then fit by rendering.

    .venv/bin/python tools/translate_juno.py "Vintage Factory/17 Brass 1" --slug juno-brass-1

Same method as translate.py (OB-Xf): map every control through the calibration tables
(tools/calibrate_juno.py), then fit the envelopes and filter against Jun-6 V renders.
Writes patches/<slug>.syx, patches/<slug>.json and renders/<slug>/listen/demo_AB.wav.

Juno voice -> Virus:
  DCO saw / square / saw+square   osc 1: Shape 64 / 127 / between (an in-phase crossfade)
  sub (square, -1 oct)            osc 2: pulse 50 %, -12 semitones, level by Osc Balance
  noise                           Noise Volume
  HPF                             filter 2 high-pass, serial after filter 1
  VCF (IR3109, 24 dB)             filter 1 analog 4 pole
  one ADSR (VCF and VCA)          amp and filter envelopes, seeded alike, then fitted
  LFO (triangle, delay)           LFO 3 (the only one with a fade-in): vibrato on its own
                                  destination, VCF and PWM through matrix slots
  PWM from the envelope           matrix: filter envelope -> osc 1 pulse width
  chorus I / II                   Vintage chorus (BBD-like: leaves the top steady), fitted per mode
"""
import argparse
import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import jun6  # noqa: E402
from ab_render import EXAMPLES  # noqa: E402
from demo import demo  # noqa: E402
from fit import coordinate_search, level_fit_loss, spectral_fit_loss_multi  # noqa: E402
from render_lib import ROOT, band_shape, level_db, render_virus_many  # noqa: E402
from translate import CAL, held_brightness, timing  # noqa: E402
from virus_patch import Patch  # noqa: E402

FX_OFF = dict(fx_section_on_off=False)  # fit stages compare dry voices; chorus is added at the end


def table(name):
    """Calibration table as sorted (control, unit) arrays."""
    pts = sorted((float(k), v) for k, v in CAL[name].items() if v == v)  # v != v: NaN (not measurable)
    return np.array([p[0] for p in pts]), np.array([p[1] for p in pts], dtype=float)


def at(name, x, logx=False):
    """Unit at control x (interpolated; log control axis for Hz/seconds knobs)."""
    xs, ys = table(name)
    if logx:
        return float(np.interp(math.log(max(x, xs[0])), np.log(xs), ys))
    return float(np.interp(x, xs, ys))


def inv(name, target, logy=False, lo=0, hi=127):
    """Control value whose measured unit is nearest target; tables may rise or fall."""
    xs, ys = table(name)
    if logy:
        ys = np.log(np.maximum(ys, 1e-6))
        target = math.log(max(target, 1e-6))
    if ys[-1] < ys[0]:
        ys, target = -ys, -target
    ys = np.maximum.accumulate(ys)  # tolerate small wobble
    return int(np.clip(round(float(np.interp(target, ys, xs))), lo, hi))


def juno_params(name):
    jun6.load(name)
    return jun6.params()


def bal_level(b, osc):
    """Virus osc level (dB) at Osc Balance b, re osc 1 at Balance 0 (virus_balance_db)."""
    xs, ys = table("virus_balance_db")
    v = np.array([CAL["virus_balance_db"][str(int(x))][osc] for x in xs])
    return float(np.interp(b, xs, v)) - CAL["virus_balance_db"]["0"][0]


def map_structure(d):
    p = Patch.from_syx()
    notes = []
    saw, sq = bool(d["dco_saw"]), bool(d["dco_square"])
    pw = float(d["dco_pulse_width_modulation"])
    pwm_mode = d["dco_pulse_width_mode"]
    static_pw = pw if pwm_mode == "Manual" else 0.0  # LFO/Envelope modes: the knob is the mod depth

    # --- osc 1: saw, square or both (one oscillator; Shape crossfades saw -> pulse in phase)
    if saw and sq:
        # the fitted Shape wanders (80-99, flat loss); the Juno's saw:pulse balance doesn't depend
        # on PW, so use the median Shape and interpolate only the width
        knobs, sw = zip(*sorted((float(k), v) for k, v in CAL["virus_sawsq_shape_pw"].items()))
        p.set(Osc1_Shape=int(np.median([s for s, _ in sw])),
              Osc1_Pulsewidth=int(round(np.interp(static_pw, knobs, [w for _, w in sw]))))
        osc_db = at("juno_sawsq_db", static_pw)
    elif sq:
        p.set(Osc1_Shape=127, Osc1_Pulsewidth=inv("virus_pulse_duty", at("juno_square_duty", static_pw)))
        osc_db = at("juno_square_db", static_pw)
    else:
        p["Osc1 Shape"] = 64
        osc_db = 0.0 if saw else None
    if sq and pwm_mode == "LFO" and pw > 0.01:
        knobs, duties = zip(*sorted((float(k), v) for k, v in CAL["juno_pwm_lfo_duty"].items()))
        lo, hi = (float(np.interp(pw, knobs, [v[i] for v in duties])) for i in (0, 1))
        p["Osc1 Pulsewidth"] = inv("virus_pulse_duty", (lo + hi) / 2)
        notes.append(f"PWM from LFO: duty {lo:.2f}-{hi:.2f}")
    if sq and pwm_mode == "Envelope" and pw > 0.01:
        p["Osc1 Pulsewidth"] = 0
        target = at("juno_pwm_env_duty", pw)
        p.set(Assign3_Source=20, Assign3_Destination1=7, Assign3_Amount1=64 + inv("virus_fenv_pw_duty", target, lo=0, hi=63))
        notes.append(f"PWM from envelope: duty 0.50 -> {target:.2f} at full envelope (filter env -> PW)")

    # --- sub on osc 2 (square one octave down); the Virus sub oscillator can't get loud enough
    sub_on = bool(d["dco_sub"]) and d["dco_sub_volume"] > 0.01
    sub_db = at("juno_sub_db", d["dco_sub_volume"]) if sub_on else None
    if sub_on:
        p.set(Osc2_Shape=127, Osc2_Pulsewidth=0, Osc2_Semitone=52, Osc2_Detune=0)
    sq_db = CAL["virus_shape_db"]["127"]
    sh_db = float(np.interp(p["Osc1 Shape"], *table("virus_shape_db")))
    if osc_db is not None and sub_db is not None:
        diffs = {b: (bal_level(b, 1) + sq_db) - (bal_level(b, 0) + sh_db) for b in range(1, 127)}
        want = sub_db - osc_db
        p["Osc Balance"] = min(diffs, key=lambda b: abs(diffs[b] - want))
        gain = bal_level(p["Osc Balance"], 0) + sh_db - osc_db  # Virus dB re its saw = Juno dB + gain
    elif sub_db is not None:
        p["Osc Balance"] = 127
        gain = bal_level(127, 1) + sq_db - sub_db
    elif osc_db is not None:
        p["Osc Balance"] = 0
        gain = sh_db - osc_db
    else:
        p["Osc Mainvolume"] = 0  # noise only: mutes the oscillators, not the noise
        gain = 0.0
    if d["dco_noise_volume"] > 0.01:
        p["Noise Volume"] = inv("virus_noise_db", at("juno_noise_db", d["dco_noise_volume"]) + gain, lo=1)
        notes.append(f"noise {at('juno_noise_db', d['dco_noise_volume']):+.1f} dB re saw -> Noise Volume {p['Noise Volume']}")

    # --- filters
    p.set(Filter1_Mode=7, Filter_Balance=0)
    # Juno corner; below the measurable range (< ~25 Hz, knob < 124) extend its knob/corner ratio
    knob = d["vcf_cutoff_hz"]
    corner = at("juno_cutoff_hz", knob, logx=True) if knob >= 124 else max(1.0, knob * CAL["juno_cutoff_hz"]["124.1"] / 124.1)
    p["Cutoff"] = inv("virus_cutoff_hz", corner, logy=True)
    v_corner = float(np.exp(np.interp(p["Cutoff"], *[np.array(a) for a in (table("virus_cutoff_hz")[0], np.log(table("virus_cutoff_hz")[1]))])))
    p["Filter1 Resonance"] = inv("virus_res_peak_db", at("juno_res_peak_db", d["vcf_resonance"]))
    p["Filter1 Keyfollow"] = inv("virus_keytrack", at("juno_keytrack", d["vcf_keyboard_modulation"]), lo=64)
    env_oct = at("juno_env_octaves", d["vcf_envelope_modulation"])
    if d["vcf_envelope_modulation"] > 0.6:  # past the measured range: extend linearly
        xs, ys = table("juno_env_octaves")
        env_oct = ys[-1] + (d["vcf_envelope_modulation"] - xs[-1]) * (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
    if d["vcf_envelope_polarity"] == "Negative":
        p["Filter1 Env Polarity"] = 0
    else:
        # match where the sweep peaks, not its size: the Virus can't rest below 33 Hz, so a Juno that
        # rests at ~5 Hz and sweeps 9 octaves (Brass 1) would overshoot by ~3 octaves (fit loss 17)
        env_oct = max(0.0, math.log2(corner * 2 ** env_oct / v_corner))
    p["Filter1 Env Amt"] = inv("virus_env_octaves", env_oct) if d["vcf_envelope_modulation"] > 0.005 else 0
    if d["hpf_cutoff_hz"] > 20:
        p.set(Filter_Balance=64, Filter_Routing=0, Filter2_Mode=1, Filter2_Cutoff_Link=0, Filter2_Env_Amt=0)
        p["Cutoff2"] = inv("virus_hpf_hz", at("juno_hpf_hz", d["hpf_cutoff_hz"], logx=True), logy=True)
        notes.append(f"HPF {d['hpf_cutoff_hz']:.0f} -> filter 2 high-pass, Cutoff2 {p['Cutoff2']}")

    # --- envelope (one ADSR on the Juno; both Virus envelopes start from it)
    a = inv("virus_attack_ms", at("juno_attack_ms", d["envelope_1_attack_s"], logx=True))
    dec = inv("virus_decay_ms", at("juno_decay_ms", d["envelope_1_decay_s"], logx=True), logy=True)
    rel = inv("virus_release_ms", at("juno_release_ms", d["envelope_1_release_s"], logx=True), logy=True)
    s = float(d["envelope_1_sustain"])
    sus = 0 if s < 0.01 else (127 if s > 0.99 else inv("virus_sustain_db", at("juno_sustain_db", s)))
    # the Virus filter envelope runs far slower than its amp envelope at the same setting: own tables
    fa = inv("virus_fenv_attack_ms", at("juno_fenv_attack_ms", d["envelope_1_attack_s"], logx=True))
    fd = inv("virus_fenv_decay_ms", at("juno_fenv_decay_ms", d["envelope_1_decay_s"], logx=True), logy=True)
    p.set(Filter_Env_Attack=fa, Filter_Env_Decay=fd, Filter_Env_Sustain=sus, Filter_Env_Release=rel)
    if d["vca_modulation_source"] == "Gate":
        p.set(Amp_Env_Attack=0, Amp_Env_Decay=127, Amp_Env_Sustain=127, Amp_Env_Release=inv("virus_release_ms", 5.0, logy=True))
        notes.append("VCA gate")
    else:
        p.set(Amp_Env_Attack=a, Amp_Env_Decay=dec, Amp_Env_Sustain=sus, Amp_Env_Release=rel)

    # --- LFO -> LFO 3
    vib = at("juno_vib_cents", d["dco_lfo_modulation"]) >= 1.0  # many presets leave 0.004 (0.7 c): inaudible
    vcf = d["vcf_lfo_modulation"] > 0.002
    pwl = sq and pwm_mode == "LFO" and pw > 0.01
    if vib or vcf or pwl:
        hz = at("juno_lfo_hz", d["lfo_1_rate_unsync_hz"], logx=True)
        p.set(Lfo3_Shape=1, Lfo3_Mode=0, Lfo3_Rate=inv("virus_lfo3_hz", hz, logy=True))
        if d["lfo_1_delay_time_s"] > 0.02:
            p["Lfo3 Fade-In Time"] = inv("virus_lfo3_fade_s", at("juno_lfo_delay_s", d["lfo_1_delay_time_s"], logx=True))
        if d["lfo_1_delay_mode"] != "Delay + Rise":
            notes.append(f"LFO delay mode {d['lfo_1_delay_mode']} treated as delay + rise")
        p["Lfo3 Destination"] = 1
        if vib:
            c = at("juno_vib_cents", d["dco_lfo_modulation"])
            p["Osc Lfo3 Amount"] = inv("virus_lfo3_vib_cents", c, lo=1)
            notes.append(f"vibrato {c:.1f} c at {hz:.2f} Hz -> LFO 3 amount {p['Osc Lfo3 Amount']}")
        if vcf:
            o = at("juno_lfo_vcf_oct", d["vcf_lfo_modulation"])
            p.set(Assign1_Source=23, Assign1_Destination=24, Assign1_Amount=64 + inv("virus_lfo3_cut_oct", o, lo=1, hi=63))
            notes.append(f"VCF LFO +/-{o:.2f} oct -> matrix LFO 3 -> cutoff {p['Assign1 Amount'] - 64:+d}")
        else:
            p.set(Assign1_Source=0, Assign1_Amount=64)
        if pwl:
            xs = sorted((float(k), v) for k, v in CAL["virus_lfo3_pw_duty"].items())
            swing = [(v[1] - v[0]) / 2 for _, v in xs]
            want = (hi - lo) / 2
            amt = int(round(np.interp(want, np.maximum.accumulate(swing), [k for k, _ in xs])))
            p.set(Assign2_Source=23, Assign2_Destination1=7, Assign2_Amount1=64 + max(1, min(63, amt)))
    else:
        p.set(Assign1_Source=0, Assign1_Amount=64)

    # --- chorus
    if d["chorus_modes"] in ("Mode 1", "Mode 2"):
        p["Chorus/Type"] = 2
        for k, v in CAL["juno_chorus"][d["chorus_modes"]].items():
            p[k] = v
    elif d["chorus_modes"] != "Off":
        notes.append(f"chorus {d['chorus_modes']} not translated")

    # --- what isn't translated
    if d["unison"]:
        notes.append("unison not translated")
    if d["portamento_ms"] > 0.5:
        notes.append(f"portamento {d['portamento_ms']:.0f} ms not translated")
    for k in ("delay_on_off", "reverb_on_off"):
        wet = d[k.replace("on_off", "dry_wet")]
        if d[k] and wet > 0.01:
            notes.append(f"{k.split('_')[0]} (wet {wet:.2f}) not translated")
    if d["arpeggiator_on_off"]:
        notes.append("arpeggiator not translated")
    return p, notes


# ---------------------------------------------------------------- references


def juno_render(name, overrides=None):
    def r(notes, hold, tail):
        jun6.load(name, {**FX_OFF, **(overrides or {})})
        return jun6.render(notes, hold, tail)
    return r


def juno_target(name, overrides=None, runs=2, notes=(60,), hold=1.5, tail=1.5):
    """Averaged band shapes and level (Jun-6 V varies a little run to run)."""
    jun6.load(name, {**FX_OFF, **(overrides or {})})
    xs = [jun6.render(notes, hold, tail) for _ in range(runs)]
    n = min(len(x) for x in xs)
    return np.mean([band_shape(x[:n]) for x in xs], axis=0), np.mean([level_db(x[:n]) for x in xs], axis=0)


def juno_brightness(name, examples, hold, tail):
    jun6.load(name, FX_OFF)
    return float(np.mean([held_brightness(jun6.render(n, hold, tail), hold) for n in examples]))


def virus_brightness(patches, examples, hold, tail):
    tot = np.zeros(len(patches))
    for n in examples:
        for i, x in enumerate(render_virus_many(patches, notes=n, hold=hold, tail=tail)):
            tot[i] += held_brightness(x, hold)
    return tot / len(examples)


def translate(name, slug, log=print):
    d = juno_params(name)
    base, notes = map_structure(d)
    chorus = {"Chorus/Type": base["Chorus/Type"]}
    dry = base.copy()
    dry["Chorus/Type"] = 0
    hold, tail = timing(None, render=juno_render(name))
    examples = [EXAMPLES["1_single"], EXAMPLES["3_chord"]]
    kw = lambda n: dict(notes=n, hold=hold, tail=tail)  # noqa: E731
    report = {"reference": f"Jun-6 V: {name}", "hold": hold, "tail": tail, "mapping_notes": notes,
              "mapped": {k: v for k, v in sorted(base.diff(Patch.from_syx()).items())}}
    for n in notes:
        log("  map:", n)

    # Stage 1: amp envelope, filter wide open (chord). Gate VCA is fixed.
    if d["vca_modulation_source"] != "Gate":
        _, lvl = juno_target(name, {"vcf_cutoff_hz": 102600.0, "vcf_envelope_modulation": 0.0, "vcf_resonance": 0.0},
                             **kw(examples[-1]))
        p = dry.copy().set(Cutoff=127, Filter1_Env_Amt=0, Filter1_Resonance=0)
        free = {k: (0, 127) for k in ("Amp Env Decay", "Amp Env Sustain", "Amp Env Release")}
        p, l1 = coordinate_search(p, free, level_fit_loss(lvl, **kw(examples[-1])), start_step=8, log=log)
        report["amp_level_error_db"] = round(l1, 2)
        for k in free:
            dry[k] = p[k]

    # Stage 2: filter on band shapes (single + chord); resonance kept near the mapped value
    targets = [(*juno_target(name, **kw(n)), kw(n)) for n in examples]
    r0, a0 = dry["Filter1 Resonance"], dry["Filter Env Attack"]
    free = {"Cutoff": (0, 127), "Filter Env Attack": (max(0, a0 - 12), min(127, a0 + 12)), "Filter1 Env Amt": (0, 127), "Filter1 Resonance": (max(0, r0 - 8), min(127, r0 + 8)),
            "Filter1 Keyfollow": (64, 127), "Filter Env Decay": (0, 127), "Filter Env Sustain": (0, 127),
            "Filter Env Release": (0, 127)}
    p, l2 = coordinate_search(dry, free, spectral_fit_loss_multi(targets), start_step=8, max_rounds=40, log=log)
    report["band_shape_error_db"] = round(l2, 2)

    # Stage 3: cutoff trim so the held note is as bright as the Juno
    ref_b = juno_brightness(name, examples, hold, tail)
    cuts = list(range(max(0, p["Cutoff"] - 8), min(127, p["Cutoff"] + 8) + 1))
    bs = virus_brightness([p.copy().set(Cutoff=c) for c in cuts], examples, hold, tail)
    i = int(np.argmin(np.abs(bs - ref_b)))
    report["cutoff_fit"], report["cutoff_trimmed"] = p["Cutoff"], cuts[i]
    report["brightness_gap_semitones"] = round(12 * float(bs[i] - ref_b), 2)
    p["Cutoff"] = cuts[i]
    for k, v in chorus.items():
        p[k] = v

    out = ROOT / "patches" / f"{slug}.syx"
    p.save(out)
    report["changes_from_init"] = {k: [a, b] for k, (a, b) in sorted(p.diff(Patch.from_syx()).items())}
    (ROOT / "patches" / f"{slug}.json").write_text(json.dumps(report, indent=1))
    log(f"wrote {out}  bands {l2:.2f} dB, cutoff {report['cutoff_fit']} -> {cuts[i]}")
    demo(slug, ref=f"jun6:{name}")
    return p, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--map-only", action="store_true", help="write the mapped patch without fitting")
    a = ap.parse_args()
    if a.map_only:
        p, notes = map_structure(juno_params(a.name))
        p.save(ROOT / "patches" / f"{a.slug}.syx")
        print("\n".join(notes))
        return
    translate(a.name, a.slug)


if __name__ == "__main__":
    main()
