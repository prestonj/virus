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
from ab_render import EXAMPLES  # noqa: E402
from demo import demo  # noqa: E402
from fit import coordinate_search, level_fit_loss, obxf_band_target, obxf_target, spectral_fit_loss_multi  # noqa: E402
from render_lib import RATE, ROOT, centroid, level_db, render_obxf, render_virus_many  # noqa: E402
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


def xmod_carrier_shift(xmod, wave, pw=0.5):
    """Semitones OB-Xf's cross-mod raises osc 2's average pitch (exponential FM; linear Virus FM doesn't).

    osc 2 pitch += osc1out x 48 x xmod semitones. Saw/triangle osc1out is uniform over +/-0.5;
    the pulse sits at pw-1 for a fraction pw of the cycle and at pw for the rest (PulseOsc.h).
    """
    k = 48 * xmod
    if wave == "pulse":
        m = pw * 2 ** (k * (pw - 1) / 12) + (1 - pw) * 2 ** (k * pw / 12)
    else:
        m = float(np.mean(2 ** (k * np.linspace(-0.5, 0.5, 1001) / 12)))
    return 12 * math.log2(m)


def table_db(tab, v):
    """OB-Xf mix-style table (value -> dB), interpolated in log(value)."""
    xs, ys = zip(*sorted((float(k), u) for k, u in tab.items()))
    return float(np.interp(math.log(max(v, xs[0])), np.log(xs), ys))


RING_HIGH_EQ = 100  # +9 dB (0.25 dB/step): brought pure ring's 6-20 kHz balance within 0.6 dB of OB-Xf


def map_pernote_tuning(p, d, notes):
    """OB-Xf re-detunes each oscillator at every note on (x UnisonDetune), so the osc 2 - osc 1 interval
    and the beat rate change note to note. The Virus detunes both oscillators together; LFO 3
    sample-and-hold on osc 2 adds the missing independent part (calibrate.py pernote)."""
    if not ((d["Osc1Mix"] > 0.01 and d["Osc2Mix"] > 0.01) or d["RingModMix"] > 0.01):
        return  # the interval isn't heard
    if d["Unison"] > 0.5:
        return  # in unison this randomness is the unison spread, already mapped to Unison Detune
    target = float(np.interp(d["UnisonDetune"], *zip(*sorted((float(k), v) for k, v in CAL["obxf_pernote_interval_cents"].items()))))
    if target <= CAL["virus_lfo3_sh_interval_cents"]["0"]:
        return
    p.set(Lfo3_Shape=4, Lfo3_Rate=32, Lfo3_Destination=2,
          Osc_Lfo3_Amount=inverse(CAL["virus_lfo3_sh_interval_cents"], target))
    notes.append(f"per-note osc 2 random tuning: interval std {target:.1f} c -> LFO 3 S&H amount {p['Osc Lfo3 Amount']}")


def map_mixer(p, d, notes):
    m1, m2, r = d["Osc1Mix"], d["Osc2Mix"], d["RingModMix"]
    l1 = table_db(CAL["obxf_mix_db"], m1) if m1 > 0.01 else None
    l2 = table_db(CAL["obxf_mix_db"], m2) if m2 > 0.01 else None
    bal = {int(k): v for k, v in CAL["virus_balance_db"].items()}
    if l1 is None and l2 is None:
        p["Osc Balance"] = 64
    elif l2 is None:
        p["Osc Balance"] = 0
    elif l1 is None:
        p["Osc Balance"] = 127
    else:  # osc 2 re osc 1 in dB rises with balance
        diffs = {k: v[1] - v[0] for k, v in bal.items() if 0 < k < 127}
        p["Osc Balance"] = inverse(diffs, l2 - l1)
    if r <= 0.01:
        return
    lr = table_db(CAL["obxf_ring_db"], r)
    ring = {int(k): v for k, v in CAL["virus_ring_db"].items()}
    if l1 is None and l2 is None:  # ring mod alone: Mainvolume 0 mutes the oscillators, not the ring
        # ring 64, not 127: less drive into the analog filter; the user preferred it (FINDINGS)
        p["Osc Mainvolume"], p["Ringmodulator Volume"] = 0, 64
        p["HighEQ Gain"] = RING_HIGH_EQ
        notes.append(f"ring mod only (oscillators muted with Mainvolume 0), high EQ +{(RING_HIGH_EQ - 64) / 4:.0f} dB")
        return
    nearest = min(bal, key=lambda k: abs(k - p["Osc Balance"]))
    vmax = max(bal[nearest])  # Virus level of the louder osc at this balance
    want = vmax + lr - max(x for x in (l1, l2) if x is not None)
    if want <= ring[127]:
        p["Ringmodulator Volume"] = inverse(CAL["virus_ring_db"], want)
    else:  # ring louder than the Virus allows: turn the oscillators down instead
        p["Ringmodulator Volume"] = 127
        p["Osc Mainvolume"] = inverse(CAL["virus_mainvol_db"], CAL["virus_mainvol_db"]["64"] - (want - ring[127]))
    rel = lr - max(x for x in (l1, l2) if x is not None)
    if rel >= -20:  # audible ring: the analog filter dulls its top end even fully open
        p["HighEQ Gain"] = RING_HIGH_EQ
    notes.append(f"ring mod {rel:+.1f} dB re louder osc -> Ringmodulator Volume {p['Ringmodulator Volume']}, "
                 f"Osc Mainvolume {p['Osc Mainvolume']}" + (f", high EQ +{(RING_HIGH_EQ - 64) / 4:.0f} dB" if rel >= -20 else ""))


def set_osc2_pitch(p, semis, cents):
    """Osc 2 at a fractional offset: whole semitones plus Osc2 Detune (only sharpens, up to ~39 c)."""
    total = semis + cents / 100
    k = math.floor(total)
    rem = (total - k) * 100
    top = max(CAL["virus_osc2_detune_cents"].values())
    if rem > top and 100 - rem < rem - top:
        k, rem = k + 1, 0.0
    p["Osc2 Semitone"] = 64 + k
    p["Osc2 Detune"] = inverse(CAL["virus_osc2_detune_cents"], min(rem, top))


def attack_value(v):
    """OB-Xf envelope attack (0-1) -> Virus attack with the same 10-90 % rise time (calibration tables).

    Fitting attack on the level envelope went badly wrong: Tubular Bells (OB-Xf 0 = 2.7 ms) got 66 (~80 ms).
    """
    ms = float(np.interp(v, *zip(*sorted((float(k), t) for k, t in CAL["obxf_attack_ms"].items()))))
    return inverse(CAL["virus_attack_ms"], ms)


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
        elif saw:
            p[f"Osc{i} Shape"] = 64
        else:  # neither: OB-Xf plays a triangle; Virus Shape 0 = wave, Wave Select 1 = triangle
            p[f"Osc{i} Shape"] = 0
            p[f"Osc{i} Wave Select"] = 1
            notes.append(f"osc{i}: triangle")

    # Mixer: osc 1/2 and ring-mod levels from measured tables (calibrate.py mixer). Osc Balance is
    # close to equal-power; the ring has its own level control, unaffected by balance and Mainvolume.
    map_mixer(p, d, notes)
    map_pernote_tuning(p, d, notes)

    detune_c = 100 * logsc(d["Osc2Detune"], 0.001, 0.6)
    p["Osc2 Detune"] = inverse(CAL["virus_osc2_detune_cents"], detune_c)
    notes.append(f"osc2 detune {detune_c:.1f} cents")
    if d["OscSync"] > 0.5:
        p["Osc2 Sync"] = 1
    # Cross-mod: OB-Xf osc 1 -> osc 2 exponential FM, peak 24 x OscCrossmod semitones. Virus FM
    # (mode Wave: osc 1's own wave -> osc 2) is linear and clamps; amounts from tools/calibrate_xmod.py
    if d["OscCrossmod"] > 0.01:
        pulse_mod = d["Osc1PulseWave"] > 0.5 and d["Osc1SawWave"] <= 0.5
        tab = CAL["virus_fm_for_obxf_xmod_pulse" if pulse_mod else "virus_fm_for_obxf_xmod_saw"]
        xs, ys = zip(*sorted((float(k), v) for k, v in tab.items()))
        p["Osc FM Mode"] = 2
        p["Osc2 FM Amount"] = int(round(np.interp(d["OscCrossmod"], xs, ys)))
        depth = 24 * d["OscCrossmod"]
        # exponential FM raises osc 2's average pitch; move the Virus osc 2 there (FINDINGS: Cross-mod)
        shift = xmod_carrier_shift(d["OscCrossmod"], "pulse" if pulse_mod else "saw",
                                   min(1.0, max(0.1, 0.5 * d["OscPW"] + 0.5)))
        set_osc2_pitch(p, round((d["Osc2Pitch"] - 0.5) * 48), detune_c + 100 * shift)
        notes.append(f"cross-mod +/-{depth:.1f} st -> Virus FM {p['Osc2 FM Amount']}, osc 2 raised {shift:+.2f} st"
                     + (" (beyond ~17 st the Virus FM clamps)" if depth > 17 else "")
                     + ("" if not pulse_mod else
                        " -- pulse cross-mod not translated: the Virus FMs with osc 1's saw, never a square"))
    if abs(d["Tune"] - 0.5) > 0.005:
        notes.append(f"Tune {200 * (d['Tune'] - 0.5):+.0f} c not translated (no patch fine tune on the Virus)")

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

    # LFO -> oscillator pitch (vibrato / opposed-pitch shimmer). OB-Xf's LFO 1 first; its per-voice
    # LFO 2 goes onto the Virus LFO 1 when LFO 1 doesn't touch pitch (same rate/amount scales).
    lfo = "LFO1"
    o1, o2 = remap_lfo_dest(d["LFO1ToOsc1Pitch"]), remap_lfo_dest(d["LFO1ToOsc2Pitch"])
    if not (o1 or o2):
        lfo = "LFO2"
        o1, o2 = remap_lfo_dest(d["LFO2ToOsc1Pitch"]), remap_lfo_dest(d["LFO2ToOsc2Pitch"])
    if o1 or o2:
        hz = logsc(d[f"{lfo}Rate"], 0.0, 250.0, 3775.0)
        cents = 100 * logsc(logsc(d[f"{lfo}ModAmount1"], 0.0, 1.0, 60.0), 0.0, 60.0, 10.0)
        p["Lfo1 Rate"] = inverse({k: v for k, v in CAL["virus_lfo1_rate_hz"].items() if int(k) >= 40}, hz)
        p["Lfo1 Shape"] = 0  # sine
        amt = inverse(CAL["virus_lfo1_osc_depth_cents"], cents) - 64
        if o1:
            p["Osc1 Lfo1 Amount"] = 64 + o1 * amt
        if o2:
            p["Osc2 Lfo1 Amount"] = 64 + o2 * amt
        notes.append(f"OB-Xf {lfo} {hz:.2f} Hz, +/-{cents:.1f} c on osc1 {o1:+d} / osc2 {o2:+d} -> Virus LFO1")
    for k in ("LFO1ToFilterCutoff", "LFO1ToOsc1PW", "LFO1ToOsc2PW", "LFO2ToFilterCutoff", "LFO2ToOsc1Pitch",
              "LFO2ToOsc2Pitch", "LFO2ToOsc1PW", "LFO2ToOsc2PW", "EnvToPitchAmount", "EnvToPWAmount", "Portamento"):
        if lfo == "LFO2" and k in ("LFO2ToOsc1Pitch", "LFO2ToOsc2Pitch"):
            continue
        if lfo == "LFO1" and k in ("LFO2ToOsc1Pitch", "LFO2ToOsc2Pitch") and d.get(k, 0) > 0.01:
            notes.append(f"{k} not translated (Virus LFO1 already used for OB-Xf LFO1)")
            continue
        if d.get(k, 0) > 0.01:
            notes.append(f"{k}={d[k]:.3f} not translated")
    # Sound-changing OB-Xf features with no mapping yet (counts in FINDINGS: unsupported features)
    for k in ("NoiseMix", "LFO1ToVolume", "LFO2ToVolume"):
        if d[k] > 0.01:
            notes.append(f"{k}={d[k]:.3f} not translated")
    if d["OscBrightness"] < 0.99:
        notes.append(f"OscBrightness={d['OscBrightness']:.3f} not translated")
    if d["Filter4PoleMode"] < 0.5:
        for k in ("Filter2PolePush", "Filter2PoleBPBlend"):
            if d[k] > 0.01:
                notes.append(f"{k}={d[k]:.3f} not translated")
    if d["FilterEnvInvert"] > 0.5:
        notes.append("FilterEnvInvert not translated")
    if o1 or o2:
        waves = [round(d[f"{lfo}Wave{i}"], 2) for i in (1, 2, 3)]
        if waves != [0.0, 0.5, 0.5]:  # OB-Xf's usual LFO waveform setting; translated as sine
            notes.append(f"{lfo} waveform {waves} not translated (sine used)")
    if p["Key Mode"] and d["EnvLegatoMode"] > 0.01:
        notes.append(f"EnvLegatoMode={d['EnvLegatoMode']:.2f} not translated")
    return p, notes


def timing(d):
    """Hold/tail long enough to hear the envelopes, within limits."""
    a = logsc(d["AmpEnvAttack"], 4, 60000, 900) / 1000
    r = logsc(d["AmpEnvRelease"], 8, 60000, 900) / 1000
    hold = float(np.clip(a + 1.5, 2.0, 4.0))
    tail = float(np.clip(r * 1.2, 1.5, 4.0))
    return round(hold, 1), round(tail, 1)


def held_brightness(x, hold):
    """Brightness (octaves) of the held note: mean of the attack (0-0.3 s) and sustain medians.

    Matching the attack alone left a slow pad (Warmth) ~3.5 semitones dark in the sustain.
    Only frames within 30 dB of the peak count: a plucked/bass note that has decayed
    to silence otherwise measures the noise floor (OBX Bass 2 read a 22-semitone gap).
    """
    c = centroid(x)
    lev = level_db(x, win_ms=512 * 1000 / RATE)
    loud = lev[: len(c)] > lev.max() - 30
    a, h = int(0.3 * RATE / 512), int(hold * RATE / 512)
    att, sus = c[:a][loud[:a]], c[a:h][loud[a:h]]
    return np.median(att) if len(sus) < 4 else (np.median(att) + np.median(sus)) / 2


def attack_brightness(patches_or_ref, examples, hold, tail, ref_name=None):
    """Held-note brightness (see held_brightness), averaged across examples."""
    if ref_name:
        vals = []
        for notes in examples:
            xs = [render_obxf(ref_name, notes=notes, hold=hold, tail=tail) for _ in range(3)]
            vals.append(np.mean([held_brightness(x, hold) for x in xs]))
        return float(np.mean(vals))
    tot = np.zeros(len(patches_or_ref))
    for notes in examples:
        for i, x in enumerate(render_virus_many(patches_or_ref, notes=notes, hold=hold, tail=tail)):
            tot[i] += held_brightness(x, hold)
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
    p.set(Amp_Env_Attack=attack_value(d["AmpEnvAttack"]), Amp_Env_Decay=80,
          Amp_Env_Sustain=int(127 * d["AmpEnvSustain"]), Amp_Env_Release=50)
    amp_free = {k: (0, 127) for k in ("Amp Env Decay", "Amp Env Sustain", "Amp Env Release")}
    p, l1 = coordinate_search(p, amp_free, level_fit_loss(lvl, **chord), log=log)
    report["amp_level_error_db"] = round(l1, 2)
    amp = {k: p[k] for k in (*amp_free, "Amp Env Attack")}

    # Stage 2: filter on third-octave band shapes over single, fifth, chord
    targets = [(*obxf_band_target(name, **kw(n)), kw(n)) for n in examples]
    p = base.copy()
    for k, v in amp.items():
        p[k] = v
    p.set(Cutoff=int(20 + 90 * d["FilterCutoff"]), Filter1_Env_Amt=int(127 * min(1, d["FilterEnvAmount"] * 1.2)),
          Filter1_Resonance=int(60 * d["FilterResonance"]), Filter_Env_Attack=attack_value(d["FilterEnvAttack"]), Filter_Env_Decay=80,
          Filter_Env_Sustain=int(127 * d["FilterEnvSustain"]), Filter_Env_Release=30)
    # Resonance stays near OB-Xf's own: the fit buys brightness with resonance the OB doesn't have
    # (OBX Bass 2: 44 vs OB-Xf ~7, user chose 8). The fit runs to whatever ceiling it gets
    # (cap +16 -> res 23 with cutoff 7), so keep the cap tight.
    res_cap = min(90, round(60 * d["FilterResonance"]) + 8)
    report["resonance_cap"] = res_cap
    free = {"Cutoff": (0, 127), "Filter1 Env Amt": (0, 127), "Filter1 Resonance": (0, res_cap),
            "Filter1 Keyfollow": (64, 127), "Filter Env Decay": (0, 127),
            "Filter Env Sustain": (0, 127), "Filter Env Sustain Time": (0, 127), "Filter Env Release": (0, 127)}
    p, l2 = coordinate_search(p, free, spectral_fit_loss_multi(targets), start_step=16, max_rounds=40, log=log)
    report["band_shape_error_db"] = round(l2, 2)

    # Stage 3: trim cutoff so the held note is as bright as OB-Xf, attack and sustain weighted
    # equally (Obright: attack-matched won by ear; Warmth/OBX Bass 1: user then asked for brighter)
    ref_b = attack_brightness(None, examples, hold, tail, ref_name=name)
    cuts = list(range(max(0, p["Cutoff"] - 12), min(127, p["Cutoff"] + 12) + 1))
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
    demo(slug, ref=name)  # one melodic phrase, OB-Xf then Virus (tools/demo.py)
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
