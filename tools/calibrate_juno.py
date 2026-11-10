"""Juno (Arturia Jun-6 V) -> Virus calibration tables; merges them into tools/calibration.json.

    .venv/bin/python tools/calibrate_juno.py            # all
    .venv/bin/python tools/calibrate_juno.py waves      # one: waves levels filter env lfo hpf chorus

Every measurement uses a bare test voice on each synth (JUNO_BASE, virus_base): filter open,
no resonance, no envelope or LFO modulation, gate VCA, effects off. See FINDINGS
("Juno -> Virus calibration") for what the tables mean.
"""
import argparse
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import jun6  # noqa: E402
from render_lib import RATE, level_db, render_virus_many  # noqa: E402
from virus_patch import Patch  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "calibration.json"
JUNO_BASE = dict(fx_section_on_off=False, chorus_modes="Off", vca_modulation_source="Gate", vcf_cutoff_hz=102600.0,
                 vcf_resonance=0.0, vcf_envelope_modulation=0.0, vcf_envelope_polarity="Positive",
                 vcf_keyboard_modulation=0.0, hpf_cutoff_hz=17.6, dco_lfo_modulation=0.0, vcf_lfo_modulation=0.0,
                 dco_saw=True, dco_square=False, dco_sub=False, dco_sub_volume=0.0, dco_noise_volume=0.0,
                 dco_pulse_width_mode="Manual", dco_pulse_width_modulation=0.0, envelope_1_attack_s=0.001,
                 envelope_1_decay_s=1.0, envelope_1_sustain=1.0, envelope_1_release_s=0.002,
                 lfo_1_delay_time_s=0.005, unison=False, portamento_ms=0.0)
NOTE, F0 = 60, 261.63


def virus_base():
    """Osc 1 saw alone through filter 1 wide open (analog 4 pole, as translations use)."""
    return Patch.from_syx().set(Osc_Balance=0, Filter_Balance=0, Filter1_Mode=7, Cutoff=127, Filter1_Resonance=0)


def juno(notes=(NOTE,), hold=1.5, tail=0.1, **o):
    jun6.load("Default", {**JUNO_BASE, **o})
    return jun6.render(notes, hold, tail)


def virus(patches, notes=(NOTE,), hold=1.5, tail=0.1):
    return render_virus_many(patches, notes=notes, hold=hold, tail=tail)


def harmonics_db(x, f0=F0, n=30, win=(0.3, 1.3)):
    s = x[int(win[0] * RATE):int(win[1] * RATE)]
    s = s * np.hanning(len(s))
    p = np.abs(np.fft.rfft(s)) ** 2
    f = np.fft.rfftfreq(len(s), 1 / RATE)
    h = np.array([p[(f > f0 * (k - 0.3)) & (f < f0 * (k + 0.3))].sum() for k in range(1, n + 1)])
    return 10 * np.log10(h + 1e-12)


def rms_db(x, win=(0.3, 1.3)):
    s = x[int(win[0] * RATE):int(win[1] * RATE)]
    return 10 * np.log10(np.mean(s ** 2) + 1e-20)


def mono(x):
    return np.asarray(x, dtype=np.float64)


# ---------------------------------------------------------------- waves


def juno_duty(pw):
    """Duty cycle of the Juno square at a manual PW setting, fitted to its harmonics vs its saw.

    Pulse/saw harmonic ratio is 2 g |sin(pi k d)| for duty d (g = level ratio).
    """
    saw, sq = harmonics_db(juno()), harmonics_db(juno(dco_saw=False, dco_square=True, dco_pulse_width_modulation=pw))
    k = np.arange(1, 21)
    r = 10 ** ((sq - saw)[:20] / 20)
    best = None
    for d in np.linspace(0.02, 0.5, 481):
        m = 2 * np.abs(np.sin(np.pi * k * d))
        g = np.sum(r * m) / np.sum(m * m)
        err = np.mean(np.abs(20 * np.log10((g * m + 1e-3) / (r + 1e-3))))
        if best is None or err < best[0]:
            best = (err, d, g)
    return round(float(best[1]), 3), round(float(20 * np.log10(best[2])), 2)


def wave_match(target_rel, cands):
    """Index of the Virus candidate whose harmonics (relative to its own saw) best match target_rel."""
    xs = virus([virus_base()] + cands)
    vsaw = harmonics_db(xs[0])
    def loss(x):  # tone only: the best level offset is removed (levels have their own tables)
        d = np.maximum(harmonics_db(x) - vsaw, -40) - np.maximum(target_rel, -40)
        return float(np.mean(np.abs(d - np.median(d))))
    losses = [loss(x) for x in xs[1:]]
    i = int(np.argmin(losses))
    return i, losses[i]


def cal_waves(cal):
    """juno_square_duty: PW knob -> duty. virus_sawsq_shape_pw: PW knob -> [Osc1 Shape, Pulsewidth] for saw+square.

    Square alone maps through the duty tables (Shape 127). Saw+square is one Virus oscillator:
    Shape between saw (64) and pulse (127) crossfades the two in phase (FINDINGS).
    """
    pws = (0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0)
    duty, sawsq = {}, {}
    jsaw = harmonics_db(juno())
    for pw in pws:
        duty[str(pw)], _ = juno_duty(pw)
        target = harmonics_db(juno(dco_square=True, dco_pulse_width_modulation=pw)) - jsaw
        grid = [(s, w) for s in range(66, 128, 4) for w in range(0, 128, 8)]
        i, loss = wave_match(target, [virus_base().set(Osc1_Shape=s, Osc1_Pulsewidth=w) for s, w in grid])
        s0, w0 = grid[i]
        fine = [(s, w) for s in range(max(64, s0 - 2), min(127, s0 + 2) + 1) for w in range(max(0, w0 - 8), min(127, w0 + 8) + 1, 2)]
        i, loss = wave_match(target, [virus_base().set(Osc1_Shape=s, Osc1_Pulsewidth=w) for s, w in fine])
        sawsq[str(pw)] = list(fine[i])
        print(f"  pw {pw}: duty {duty[str(pw)]}, saw+square -> shape/pw {fine[i]} (loss {loss:.2f} dB)")
    cal["juno_square_duty"], cal["virus_sawsq_shape_pw"] = duty, sawsq


# ---------------------------------------------------------------- levels


def cal_levels(cal):
    """Levels in dB relative to each synth's saw alone (filter open).

    juno_square_db / juno_sawsq_db: PW knob -> level. juno_sub_db, juno_noise_db: volume -> level.
    virus_shape_db: Osc1 Shape -> level. virus_noise_db: Noise Volume -> level (Balance 0).
    The Virus sub oscillator can't play a Juno sub: Osc Mainvolume mutes it with the oscillators,
    and at full volume it sits below the osc while the Juno's sub reaches +5.7 dB over its saw.
    The translator plays the sub on osc 2 (square, -12) instead, mixed with Osc Balance.
    """
    jsaw = rms_db(juno())
    vols = (0.1, 0.25, 0.5, 0.75, 1.0)
    cal["juno_sub_db"] = {str(v): round(rms_db(juno(dco_saw=False, dco_sub=True, dco_sub_volume=v)) - jsaw, 2) for v in vols}
    cal["juno_noise_db"] = {str(v): round(rms_db(juno(dco_saw=False, dco_noise_volume=v)) - jsaw, 2) for v in vols}
    pws = (0.0, 0.4, 0.8, 1.0)
    cal["juno_square_db"] = {str(pw): round(rms_db(juno(dco_saw=False, dco_square=True, dco_pulse_width_modulation=pw)) - jsaw, 2) for pw in pws}
    cal["juno_sawsq_db"] = {str(pw): round(rms_db(juno(dco_square=True, dco_pulse_width_modulation=pw)) - jsaw, 2) for pw in pws}
    # noise alone: Osc Mainvolume 0 silences the oscillators (and the sub oscillator) but not the noise
    shapes = list(range(64, 128, 8)) + [127]
    vvols = (8, 16, 32, 48, 64, 80, 96, 112, 127)
    ps = [virus_base()] + [virus_base().set(Osc1_Shape=s) for s in shapes] \
        + [virus_base().set(Osc_Mainvolume=0, Noise_Volume=v) for v in vvols] + [virus_base().set(Osc_Mainvolume=0)]
    xs = virus(ps)
    vsaw = rms_db(xs[0])
    cal["virus_shape_db"] = {str(s): round(rms_db(x) - vsaw, 2) for s, x in zip(shapes, xs[1:])}
    o = 1 + len(shapes)
    cal["virus_noise_db"] = {str(v): round(rms_db(x) - vsaw, 2) for v, x in zip(vvols, xs[o:o + len(vvols)])}
    print("  Mainvolume 0 alone:", round(rms_db(xs[-1]) - vsaw, 1), "dB re saw")
    for k in ("juno_sub_db", "juno_noise_db", "juno_square_db", "juno_sawsq_db", "virus_shape_db", "virus_noise_db"):
        print(f"  {k}: {cal[k]}")


# ---------------------------------------------------------------- filters
# Noise through each filter, divided by the same noise through the open filter: the
# response in dB. "Cutoff" here = where that response first falls 6 dB (log interpolated).

FREQS = np.geomspace(25, 16000, 120)


def response_db(x, ref):
    from scipy.signal import welch
    f, p = welch(x[int(0.3 * RATE):], RATE, nperseg=4096)
    _, p0 = welch(ref[int(0.3 * RATE):], RATE, nperseg=4096)
    k = np.ones(7) / 7
    r = 10 * np.log10(np.convolve(p, k, "same") / np.convolve(p0, k, "same"))
    return np.interp(FREQS, f, r)


def corner_hz(r, drop=6.0, highpass=False):
    """First frequency (from the passband side) where the response is `drop` dB down."""
    rr, ff = (r[::-1], FREQS[::-1]) if highpass else (r, FREQS)
    below = np.where(rr < -drop)[0]
    if not len(below):
        return float(ff[-1])
    i = below[0]
    if i == 0:
        return float(ff[0])
    t = (-drop - rr[i - 1]) / (rr[i] - rr[i - 1])
    return float(np.exp(np.log(ff[i - 1]) + t * (np.log(ff[i]) - np.log(ff[i - 1]))))


def juno_noise(**o):
    return juno(hold=2.5, dco_saw=False, dco_noise_volume=1.0, **o)


def virus_noise_base():
    return virus_base().set(Osc_Mainvolume=0, Noise_Volume=127)


def virus_noise(patches, notes=(NOTE,)):
    return virus(patches, notes=notes, hold=2.5)


def cal_filter(cal):
    """juno_cutoff_hz: Jun-6 'vcf_cutoff_hz' -> measured -6 dB corner (Hz), key tracking off.
    virus_cutoff_hz: Virus Cutoff -> corner (analog 4 pole, Keyfollow 64 = off).
    juno_keytrack / virus_keytrack: setting -> corner shift per octave played (1 = full tracking).
    juno_res_peak_db / virus_res_peak_db: resonance -> response peak (dB re open) at a mid cutoff.
    """
    jref = juno_noise()
    knobs = [float(v) for v in np.geomspace(20, 100000, 15).round(1)]
    cal["juno_cutoff_hz"] = {str(k): round(corner_hz(response_db(juno_noise(vcf_cutoff_hz=k), jref)), 1) for k in knobs}
    print("  juno cutoff:", cal["juno_cutoff_hz"])
    vals = list(range(0, 128, 4)) + [127]
    xs = virus_noise([virus_noise_base()] + [virus_noise_base().set(Cutoff=c) for c in vals])
    cal["virus_cutoff_hz"] = {str(c): round(corner_hz(response_db(x, xs[0])), 1) for c, x in zip(vals, xs[1:])}
    print("  virus cutoff:", cal["virus_cutoff_hz"])

    # key tracking: corner at notes 36 and 84, with the cutoff set mid-range
    mid_j = float(np.interp(np.log(800), np.log(list(cal["juno_cutoff_hz"].values())), np.log(knobs)))
    mid_j = round(float(np.exp(mid_j)), 1)
    kt = {}
    for amt in (0.0, 0.25, 0.5, 0.75, 1.0):
        c = [corner_hz(response_db(juno(notes=(n,), hold=2.5, dco_saw=False, dco_noise_volume=1.0, vcf_cutoff_hz=mid_j,
                                        vcf_keyboard_modulation=amt), jref)) for n in (36, 84)]
        kt[str(amt)] = round(float(np.log2(c[1] / c[0]) / 4), 3)
    cal["juno_keytrack"] = kt
    vmid = int(round(np.interp(np.log(800), np.log(list(cal["virus_cutoff_hz"].values())), vals)))
    kvals = (64, 72, 80, 88, 96, 104, 112, 120, 127)
    lo = virus_noise([virus_noise_base().set(Cutoff=vmid, Filter1_Keyfollow=k) for k in kvals], notes=(36,))
    hi = virus_noise([virus_noise_base().set(Cutoff=vmid, Filter1_Keyfollow=k) for k in kvals], notes=(84,))
    vref = virus_noise([virus_noise_base()])[0]
    cal["virus_keytrack"] = {str(k): round(float(np.log2(corner_hz(response_db(h, vref)) / corner_hz(response_db(lw, vref))) / 4), 3)
                             for k, lw, h in zip(kvals, lo, hi)}
    print("  keytrack juno:", cal["juno_keytrack"], " virus:", cal["virus_keytrack"])

    # resonance peak height around 800 Hz
    cal["juno_res_peak_db"] = {str(r): round(float(response_db(juno_noise(vcf_cutoff_hz=mid_j, vcf_resonance=r), jref).max()), 2)
                               for r in (0.0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0)}
    rvals = (0, 16, 32, 48, 64, 80, 96, 104, 112, 120, 127)
    xs = virus_noise([virus_noise_base().set(Cutoff=vmid, Filter1_Resonance=r) for r in rvals])
    cal["virus_res_peak_db"] = {str(r): round(float(response_db(x, vref).max()), 2) for r, x in zip(rvals, xs)}
    print("  res peak juno:", cal["juno_res_peak_db"], " virus:", cal["virus_res_peak_db"])


def cal_env_amount(cal):
    """juno_env_octaves / virus_env_octaves: env amount -> corner shift (octaves) at full sustain.

    Base cutoff low (~100 Hz) so the shift stays in band; key tracking off.
    """
    jref = juno_noise()
    knobs = [float(k) for k in cal["juno_cutoff_hz"]]
    lo_j = round(float(np.exp(np.interp(np.log(100), np.log(list(cal["juno_cutoff_hz"].values())), np.log(knobs)))), 1)
    base = corner_hz(response_db(juno_noise(vcf_cutoff_hz=lo_j), jref))
    out = {}
    for amt in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
        out[str(amt)] = round(float(np.log2(corner_hz(response_db(juno_noise(vcf_cutoff_hz=lo_j, vcf_envelope_modulation=amt), jref)) / base)), 2)
    cal["juno_env_octaves"] = out
    vals = list(cal["virus_cutoff_hz"])
    vlo = int(round(np.interp(np.log(100), np.log(list(cal["virus_cutoff_hz"].values())), [int(v) for v in vals])))
    amts = (0, 8, 16, 24, 32, 48, 64, 80, 96)
    vref = virus_noise([virus_noise_base()])[0]
    xs = virus_noise([virus_noise_base().set(Cutoff=vlo, Filter1_Env_Amt=a, Filter_Env_Attack=0, Filter_Env_Sustain=127)
                      for a in amts])
    cs = [corner_hz(response_db(x, vref)) for x in xs]
    tab = {a: float(np.log2(c / cs[0])) for a, c in zip(amts, cs)}
    # Juno env 1.0 is ~9 octaves: the top amounts from Cutoff 0, joined at the overlap (64-96)
    hi_amts = (0, 64, 80, 96, 112, 127)
    xs = virus_noise([virus_noise_base().set(Cutoff=0, Filter1_Env_Amt=a, Filter_Env_Attack=0, Filter_Env_Sustain=127)
                      for a in hi_amts])
    hs = [corner_hz(response_db(x, vref)) for x in xs]
    hi = {a: float(np.log2(c / hs[0])) for a, c in zip(hi_amts, hs)}
    shift = float(np.mean([tab[a] - hi[a] for a in (64, 80, 96)]))
    tab.update({a: hi[a] + shift for a in (112, 127)})
    cal["virus_env_octaves"] = {str(a): round(v, 2) for a, v in sorted(tab.items())}
    print("  env octaves juno:", cal["juno_env_octaves"], " virus:", cal["virus_env_octaves"])


def cal_hpf(cal):
    """juno_hpf_hz: Jun-6 'hpf_cutoff_hz' -> -6 dB corner. virus_hpf_hz: Cutoff2 (filter 2 high-pass,
    serial after filter 1, Filter Balance 64, cutoff link off) -> corner."""
    jref = juno_noise()
    knobs = (17.6, 50.0, 100.0, 200.0, 287.0, 400.0, 588.0, 800.0, 1200.0, 2000.0, 2708.0)
    cal["juno_hpf_hz"] = {str(k): round(corner_hz(response_db(juno_noise(hpf_cutoff_hz=k), jref), highpass=True), 1) for k in knobs}
    vals = list(range(0, 112, 8))
    vref = virus_noise([virus_noise_base()])[0]
    xs = virus_noise([virus_noise_base().set(Filter_Balance=64, Filter2_Mode=1, Filter2_Cutoff_Link=0, Cutoff2=c) for c in vals])
    cal["virus_hpf_hz"] = {str(c): round(corner_hz(response_db(x, vref), highpass=True), 1) for c, x in zip(vals, xs)}
    print("  hpf juno:", cal["juno_hpf_hz"], " virus:", cal["virus_hpf_hz"])


# ---------------------------------------------------------------- envelope times


def env_curve(x):
    """Level (dB) in 2 ms frames."""
    return level_db(x, 2)


def rise_ms(x):
    """10 % -> 90 % of peak amplitude, 1 ms RMS envelope (as calibrate.py)."""
    k = int(0.001 * RATE)
    e = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, "same"))
    return float((np.argmax(e > 0.9 * e.max()) - np.argmax(e > 0.1 * e.max())) / RATE * 1000)


def fall_ms(lv, start_s, drop=20.0, ref=None):
    """Time from start_s until the 2 ms level is `drop` dB under ref (default: its level just before)."""
    i0 = int(start_s * 500)
    ref = np.median(lv[max(0, i0 - 10):i0]) if ref is None else ref
    below = np.where(lv[i0:] < ref - drop)[0]
    return float(below[0] * 2) if len(below) else float("nan")


def cal_env_times(cal):
    """juno_attack_ms (10-90 % rise), juno_decay_ms / virus_decay_ms (sustain 0: peak -> -20 dB),
    juno_release_ms / virus_release_ms (note off -> -20 dB), juno_sustain_db / virus_sustain_db
    (sustain level re full). Virus attack is virus_attack_ms (calibrate.py)."""
    env = dict(vca_modulation_source="Env")
    cal["juno_attack_ms"] = {str(a): round(rise_ms(juno(hold=max(1.0, 3 * a + 0.3), envelope_1_attack_s=a, **env)), 2)
                             for a in (0.001, 0.005, 0.01, 0.03, 0.1, 0.3, 1.0, 2.97)}
    decays = (0.002, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0)
    dec = {}
    for d in decays:
        if d > float(jun6.plugin().parameters["envelope_1_decay_s"].range[1]):
            continue
        x = juno(hold=min(12.0, 3 * d + 0.5), envelope_1_decay_s=d, envelope_1_sustain=0.0, **env)
        lv = env_curve(x)
        dec[str(d)] = round(fall_ms(lv, np.argmax(lv) / 500, ref=lv.max()), 1)
    cal["juno_decay_ms"] = dec
    rel = {}
    for r in decays:
        if r > float(jun6.plugin().parameters["envelope_1_release_s"].range[1]):
            continue
        x = juno(hold=0.5, tail=min(12.0, 3 * r + 0.3), envelope_1_release_s=r, **env)
        rel[str(r)] = round(fall_ms(env_curve(x), 0.5), 1)
    cal["juno_release_ms"] = rel
    sus, full = {}, rms_db(juno(hold=1.5, **env), (1.0, 1.4))
    for s in (0.1, 0.25, 0.5, 0.75):
        x = juno(hold=1.5, envelope_1_decay_s=0.05, envelope_1_sustain=s, **env)
        sus[str(s)] = round(float(rms_db(x, (1.0, 1.4)) - full), 2)
    cal["juno_sustain_db"] = sus

    vals = list(range(0, 128, 8)) + [127]
    sv = (8, 16, 32, 48, 64, 80, 96, 112)
    ps = [virus_base().set(Amp_Env_Attack=0, Amp_Env_Decay=v, Amp_Env_Sustain=0) for v in vals] \
        + [virus_base().set(Amp_Env_Attack=0, Amp_Env_Decay=127, Amp_Env_Sustain=127, Amp_Env_Release=v) for v in vals] \
        + [virus_base().set(Amp_Env_Attack=0, Amp_Env_Decay=20, Amp_Env_Sustain=s) for s in sv]
    xs_d = virus(ps[:len(vals)], hold=12.0, tail=0.05)
    xs_r = virus(ps[len(vals):2 * len(vals)], hold=0.5, tail=12.0)
    xs_s = virus(ps[2 * len(vals):], hold=1.5)
    vd = {}
    for v, x in zip(vals, xs_d):
        lv = env_curve(x)
        vd[str(v)] = round(fall_ms(lv, np.argmax(lv) / 500, ref=lv.max()), 1)
    cal["virus_decay_ms"] = vd
    cal["virus_release_ms"] = {str(v): round(fall_ms(env_curve(x), 0.5), 1) for v, x in zip(vals, xs_r)}
    peak = rms_db(virus([virus_base()], hold=1.5)[0])
    cal["virus_sustain_db"] = {str(s): round(float(rms_db(x, (1.0, 1.4)) - peak), 2) for s, x in zip(sv, xs_s)}
    for k in ("juno_attack_ms", "juno_decay_ms", "virus_decay_ms", "juno_release_ms", "virus_release_ms",
              "juno_sustain_db", "virus_sustain_db"):
        print(f"  {k}: {cal[k]}")


def high_band(x, frame=220):
    """Level (dB) above 2 kHz in 5 ms frames: tracks the cutoff on a saw through a closed filter."""
    f = np.fft.rfftfreq(frame, 1 / RATE)
    return np.array([10 * np.log10((np.abs(np.fft.rfft(x[i:i + frame] * np.hanning(frame))) ** 2)[f > 2000].sum() + 1e-12)
                     for i in range(0, len(x) - frame, frame)])


def sweep_ms(hb, start, frac):
    """ms from frame `start` until the high band is `frac` of the way to its final value."""
    lo, hi = hb[start], np.median(hb[-60:-10])
    return float(np.argmax((hb[start:] - lo) / (hi - lo + 1e-9) > frac) * 5)


def cal_filter_env(cal):
    """juno_fenv_attack_ms / virus_fenv_attack_ms: env attack -> 50 % of the cutoff rise (high-band
    level, filter closed, full env, gate VCA). juno_fenv_decay_ms / virus_fenv_decay_ms: decay
    (sustain 0) -> 50 % of the fall. The Virus filter envelope is far slower than its amp envelope
    at the same setting (attack 32: 85 ms vs 4 ms), so it needs its own tables."""
    jb = dict(dco_saw=True, vcf_cutoff_hz=10.0, vcf_envelope_modulation=1.0)
    cal["juno_fenv_attack_ms"] = {str(a): sweep_ms(high_band(juno(hold=max(1.5, 4 * a + 0.5), envelope_1_attack_s=a, **jb)), 1, 0.5)
                                  for a in (0.001, 0.01, 0.03, 0.1, 0.3, 1.0)}
    dec = {}
    for d in (0.01, 0.03, 0.1, 0.3, 1.0, 3.0):
        hb = high_band(juno(hold=4 * d + 0.5, envelope_1_decay_s=d, envelope_1_sustain=0.0, **jb))
        pk = int(np.argmax(hb))
        dec[str(d)] = sweep_ms(hb, pk, 0.5)
    cal["juno_fenv_decay_ms"] = dec
    vals = (0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 96)
    vb = lambda **o: virus_base().set(Cutoff=0, Filter1_Env_Amt=127, Amp_Env_Attack=0, **o)  # noqa: E731
    xs = virus([vb(Filter_Env_Attack=a, Filter_Env_Decay=127, Filter_Env_Sustain=127) for a in vals], hold=4.0)
    cal["virus_fenv_attack_ms"] = {str(a): sweep_ms(high_band(x), 1, 0.5) for a, x in zip(vals, xs)}
    xs = virus([vb(Filter_Env_Attack=0, Filter_Env_Decay=v, Filter_Env_Sustain=0) for v in vals], hold=8.0)
    vd = {}
    for v, x in zip(vals, xs):
        hb = high_band(x)
        vd[str(v)] = sweep_ms(hb, int(np.argmax(hb)), 0.5)
    cal["virus_fenv_decay_ms"] = vd
    for k in ("juno_fenv_attack_ms", "virus_fenv_attack_ms", "juno_fenv_decay_ms", "virus_fenv_decay_ms"):
        print(f"  {k}: {cal[k]}")


# ---------------------------------------------------------------- LFO
# The Juno LFO (triangle, with delay) maps to Virus LFO 3, the only one with a fade-in:
# vibrato on its own destination (Osc 1+2 Pitch), cutoff and pulse width through matrix slots.

from scipy.signal import butter, hilbert, sosfiltfilt  # noqa: E402


def pitch_track(x, f0):
    """Instantaneous frequency of the fundamental (band-passed +/-40 %), 5 ms smoothing."""
    sos = butter(4, [f0 * 0.6, f0 * 1.4], btype="band", fs=RATE, output="sos")
    ph = np.unwrap(np.angle(hilbert(sosfiltfilt(sos, x))))
    f = np.diff(ph) * RATE / (2 * np.pi)
    k = int(0.005 * RATE)
    return np.convolve(f, np.ones(k) / k, mode="same")


def mod_rate(track):
    t = track - track.mean()
    n = 8 * len(t)
    s = np.abs(np.fft.rfft(t * np.hanning(len(t)), n))
    f = np.fft.rfftfreq(n, 1 / RATE)
    m = (f > 0.2) & (f < 50)
    return float(f[m][np.argmax(s[m])])


def vib_cents(x, f0=F0, win=(0.8, 3.8)):
    """(rate Hz, peak deviation cents) of the vibrato."""
    tr = pitch_track(x, f0)[int(win[0] * RATE):int(win[1] * RATE)]
    c = 1200 * np.log2(np.maximum(tr, 1) / f0)
    return mod_rate(tr), float((np.percentile(c, 98) - np.percentile(c, 2)) / 2)


def depth_rise_s(x, hold, f0=F0, frac=0.5):
    """When the vibrato first reaches `frac` of its final depth (100 ms windows, note held until `hold`)."""
    c = 1200 * np.log2(np.maximum(pitch_track(x, f0), 1) / f0)[:int((hold - 0.05) * RATE)]
    w = int(0.1 * RATE)
    s0 = int(0.15 * RATE)  # skip the band-pass filter's start-up transient
    dev = np.array([np.ptp(c[i:i + w]) for i in range(s0, len(c) - w, w // 4)])
    final = np.median(dev[-20:])  # the last second before note off
    return float((np.argmax(dev > frac * final) * (w // 4) + s0 + w / 2) / RATE)


def frame_duty(x, f0=F0, frame_s=0.05):
    """Duty per frame from the 2nd/1st harmonic ratio of a lone pulse: H2/H1 = 2 |cos(pi d)|."""
    n = int(frame_s * RATE)
    out = []
    for i in range(0, len(x) - n, n // 2):
        s = np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n), 8 * n))
        f = np.fft.rfftfreq(8 * n, 1 / RATE)
        h1 = s[(f > f0 * 0.8) & (f < f0 * 1.2)].max()
        h2 = s[(f > f0 * 1.8) & (f < f0 * 2.2)].max()
        out.append(np.arccos(np.clip(h2 / (2 * h1 + 1e-12), 0, 1)) / np.pi)
    return np.array(out)


def cut_track(x, frame_s=0.1):
    """Spectral centroid (octaves) per frame: a proxy for cutoff movement on a bright saw."""
    n = int(frame_s * RATE)
    f = np.fft.rfftfreq(n, 1 / RATE)
    out = []
    for i in range(0, len(x) - n, n // 4):
        p = np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n))) ** 2
        out.append(np.log2(np.sum(f * p) / np.sum(p) + 1))
    return np.array(out)


def virus_lfo3(fade=0, **o):
    p = virus_base().set(Lfo3_Shape=1, Lfo3_Mode=0, **o)
    p["Lfo3 Fade-In Time"] = fade
    return p


def cal_lfo(cal):
    """juno_lfo_hz: shown rate -> measured. virus_lfo3_hz: Lfo3 Rate -> Hz (triangle).
    juno_vib_cents: dco_lfo_modulation -> peak cents. virus_lfo3_vib_cents: Osc Lfo3 Amount -> cents.
    juno_lfo_vcf_oct / virus_lfo3_cut_oct: VCF LFO depth / matrix LFO3 -> Filter 1 Cutoff amount ->
    peak centroid swing (octaves) on a saw through a mid cutoff.
    juno_pwm_lfo_duty: PWM knob (LFO mode) -> [min, max] duty. virus_lfo3_pw_duty: matrix LFO3 ->
    Osc 1 Pulse Width amount -> [min, max] duty around Pulsewidth 64.
    juno_pwm_env_duty: PWM knob (Envelope mode, full sustain) -> duty. virus_fenv_pw_duty: matrix
    Filter Envelope -> Osc 1 Pulse Width amount (Pulsewidth 0, sustain full) -> duty.
    juno_lfo_delay_s / virus_lfo3_fade_s: delay / Fade-In -> time to half the final vibrato depth.
    """
    rates = (0.3, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 20.0)
    vib = dict(vcf_cutoff_hz=400.0, dco_lfo_modulation=0.3)  # cutoff low: the fundamental dominates
    cal["juno_lfo_hz"] = {str(r): round(vib_cents(juno(hold=4.0, lfo_1_rate_unsync_hz=r, **vib))[0], 3) for r in rates}
    cal["juno_vib_cents"] = {str(a): round(vib_cents(juno(hold=4.0, lfo_1_rate_unsync_hz=5.0, vcf_cutoff_hz=400.0,
                                                           dco_lfo_modulation=a))[1], 2)
                             for a in (0.01, 0.03, 0.06, 0.1, 0.15, 0.2, 0.3, 0.5)}
    dl = {}
    for d in (0.05, 0.1, 0.3, 0.6, 1.0, 2.0, 3.0):
        dl[str(d)] = round(depth_rise_s(juno(hold=d + 3.0, lfo_1_rate_unsync_hz=5.0, lfo_1_delay_time_s=d, **vib), d + 3.0), 3)
    cal["juno_lfo_delay_s"] = dl
    cv = {}
    for a in (0.01, 0.02, 0.05, 0.1, 0.2, 0.4):
        t = cut_track(juno(hold=4.0, vcf_cutoff_hz=2000.0, lfo_1_rate_unsync_hz=2.0, vcf_lfo_modulation=a)[int(0.5 * RATE):])
        cv[str(a)] = round(float((np.percentile(t, 98) - np.percentile(t, 2)) / 2), 3)
    cal["juno_lfo_vcf_oct"] = cv
    sq = dict(dco_saw=False, dco_square=True)
    pl = {}
    for a in (0.2, 0.4, 0.6, 0.8, 1.0):
        dd = frame_duty(juno(hold=4.0, dco_pulse_width_mode="LFO", dco_pulse_width_modulation=a, lfo_1_rate_unsync_hz=1.0, **sq)[int(0.5 * RATE):])
        pl[str(a)] = [round(float(np.percentile(dd, 3)), 3), round(float(np.percentile(dd, 97)), 3)]
    cal["juno_pwm_lfo_duty"] = pl
    pe = {}
    for a in (0.2, 0.4, 0.6, 0.8, 1.0):
        dd = frame_duty(juno(hold=1.5, dco_pulse_width_mode="Envelope", dco_pulse_width_modulation=a, vca_modulation_source="Gate", **sq)[int(0.5 * RATE):])
        pe[str(a)] = round(float(np.median(dd)), 3)
    cal["juno_pwm_env_duty"] = pe

    vals = list(range(0, 128, 8)) + [127]
    amts = (4, 8, 16, 24, 32, 48, 64, 96, 127)
    fades = (8, 16, 32, 48, 64, 80, 96, 112, 127)
    vib_v = dict(Cutoff=40, Lfo3_Destination=1)
    groups = {"rate": [virus_lfo3(Lfo3_Rate=v, Osc_Lfo3_Amount=40, **vib_v) for v in vals]}
    xs = virus(groups["rate"], hold=4.0)
    cal["virus_lfo3_hz"] = {str(v): round(vib_cents(x)[0], 3) for v, x in zip(vals, xs)}
    r5 = cal_inverse_rate(cal, 5.0, vals)
    groups["vib"] = [virus_lfo3(Lfo3_Rate=r5, Osc_Lfo3_Amount=a, **vib_v) for a in amts]
    groups["fade"] = [virus_lfo3(fade=f, Lfo3_Rate=r5, Osc_Lfo3_Amount=40, **vib_v) for f in fades]
    xs = virus(groups["vib"], hold=4.0)
    cal["virus_lfo3_vib_cents"] = {str(a): round(vib_cents(x)[1], 2) for a, x in zip(amts, xs)}
    xs = virus(groups["fade"], hold=8.0)
    cal["virus_lfo3_fade_s"] = {str(f): round(depth_rise_s(x, 8.0), 3) for f, x in zip(fades, xs)}

    r2 = cal_inverse_rate(cal, 2.0, vals)
    r1 = cal_inverse_rate(cal, 1.0, vals)
    camts = (2, 4, 8, 16, 32, 63)
    cmid = int(round(np.interp(np.log(2000), np.log(list(cal["virus_cutoff_hz"].values())), [int(v) for v in cal["virus_cutoff_hz"]])))
    ps = [virus_lfo3(Lfo3_Rate=r2, Lfo3_Destination=0, Cutoff=cmid, Assign1_Source=23, Assign1_Destination=24, Assign1_Amount=64 + a)
          for a in camts]
    cc = {}
    for a, x in zip(camts, virus(ps, hold=4.0)):
        t = cut_track(x[int(0.5 * RATE):])
        cc[str(a)] = round(float((np.percentile(t, 98) - np.percentile(t, 2)) / 2), 3)
    cal["virus_lfo3_cut_oct"] = cc
    ps = [virus_lfo3(Osc1_Shape=127, Osc1_Pulsewidth=64, Lfo3_Rate=r1, Lfo3_Destination=0,
                     Assign1_Source=23, Assign1_Destination=7, Assign1_Amount=64 + a) for a in camts]
    pv = {}
    for a, x in zip(camts, virus(ps, hold=4.0)):
        dd = frame_duty(x[int(0.5 * RATE):])
        pv[str(a)] = [round(float(np.percentile(dd, 3)), 3), round(float(np.percentile(dd, 97)), 3)]
    cal["virus_lfo3_pw_duty"] = pv
    ps = [virus_base().set(Osc1_Shape=127, Osc1_Pulsewidth=0, Filter_Env_Attack=0, Filter_Env_Sustain=127,
                           Assign1_Source=20, Assign1_Destination=7, Assign1_Amount=64 + a) for a in camts]
    cal["virus_fenv_pw_duty"] = {str(a): round(float(np.median(frame_duty(x[int(0.5 * RATE):]))), 3)
                                 for a, x in zip(camts, virus(ps, hold=1.5))}
    for k in ("juno_lfo_hz", "virus_lfo3_hz", "juno_vib_cents", "virus_lfo3_vib_cents", "juno_lfo_delay_s",
              "virus_lfo3_fade_s", "juno_lfo_vcf_oct", "virus_lfo3_cut_oct", "juno_pwm_lfo_duty", "virus_lfo3_pw_duty",
              "juno_pwm_env_duty", "virus_fenv_pw_duty"):
        print(f"  {k}: {cal.get(k)}")


def cal_inverse_rate(cal, hz, vals):
    """Lfo3 Rate value nearest `hz` (log interpolation in virus_lfo3_hz, if measured yet)."""
    t = cal.get("virus_lfo3_hz")
    if not t:
        return 64
    v = np.array([int(k) for k in t]); h = np.array(list(t.values()))
    o = np.argsort(h)
    return int(round(np.interp(np.log(hz), np.log(np.maximum(h[o], 1e-3)), v[o])))


# ---------------------------------------------------------------- chorus
# Fitted, not measured: Virus chorus settings whose sound on one sustained saw best matches
# each Juno mode. The Juno's BBD wet path is low-passed: it modulates below ~3 kHz and leaves
# the top steady (3 dB down). The Virus Classic chorus modulates the whole band (fit loss 12
# vs 1 run to run); the Vintage type behaves like the Juno, so that is what's fitted. Vintage
# takes its mix from "Chorus/Mix2" (Chorus Mix does nothing) and "Chorus/X Over" keeps the lows dry.
# Features ignore the chorus LFO's phase (free running on the Juno): per third-octave band
# the modulation depth (std of the band level over time) and the average level re the same
# synth's dry saw, plus the modulation rate.

CH_NOTE, CH_HOLD = 48, 6.0
EDGES = [200 * 2 ** (i / 3) for i in range(22)]
CHORUS_FREE = {"Chorus/Mix2": (0, 127), "Chorus Rate": (0, 127), "Chorus Depth": (0, 127), "Chorus Delay": (0, 127),
               "Chorus Feedback": (40, 88), "Chorus/X Over": (0, 80)}


def band_frames(x, frame=0.05):
    n = int(frame * RATE)
    f = np.fft.rfftfreq(n, 1 / RATE)
    fr = np.array([np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n))) ** 2
                   for i in range(int(0.5 * RATE), int((CH_HOLD - 0.1) * RATE) - n, n // 2)])
    return np.array([10 * np.log10(fr[:, (f >= a) & (f < b)].sum(1) + 1e-12) for a, b in zip(EDGES[:-1], EDGES[1:])])


def chorus_features(x, dry_mean):
    b = band_frames(x)
    t = b - b.mean(1, keepdims=True)
    s = np.abs(np.fft.rfft(t * np.hanning(t.shape[1]), 1024, axis=1))[:, 2:200].sum(0)
    rate = float(np.fft.rfftfreq(1024, 0.025)[2:200][np.argmax(s)])
    return b.std(1), b.mean(1) - dry_mean, rate


def chorus_loss(fa, fb):
    return float(np.mean(np.abs(fa[0] - fb[0])) + np.mean(np.abs(fa[1] - fb[1])) + 2 * abs(np.log2(fa[2] / fb[2])))


def virus_chorus(**o):
    p = virus_base()
    p["Chorus/Type"] = 2
    for k, v in o.items():
        p[k] = v
    return p


def cal_chorus(cal):
    """juno_chorus: mode -> Virus chorus settings (Vintage type; keys are Virus parameter names)."""
    from fit import coordinate_search
    jfx = dict(fx_section_on_off=True, delay_on_off=False, reverb_on_off=False, chorus_noise=False)
    jdry = band_frames(juno(notes=(CH_NOTE,), hold=CH_HOLD, **jfx)).mean(1)
    off = virus_base()
    off["Chorus/Type"] = 0
    vdry = band_frames(virus([off], notes=(CH_NOTE,), hold=CH_HOLD)[0]).mean(1)
    out = {}
    for mode in ("Mode 1", "Mode 2"):
        runs = [chorus_features(juno(notes=(CH_NOTE,), hold=CH_HOLD, chorus_modes=mode, **jfx), jdry) for _ in range(3)]
        target = tuple(np.mean([r[i] for r in runs], axis=0) for i in range(3))

        def loss_fn(ps):
            return [chorus_loss(chorus_features(x, vdry), target) for x in virus(ps, notes=(CH_NOTE,), hold=CH_HOLD)]
        start = virus_chorus(**{"Chorus/Mix2": 127, "Chorus Rate": 30, "Chorus Depth": 60, "Chorus Delay": 64,
                                "Chorus Feedback": 64, "Chorus/X Over": 0})
        p, loss = coordinate_search(start, CHORUS_FREE, loss_fn, start_step=16, log=lambda *a: None)
        out[mode] = {k: p[k] for k in CHORUS_FREE}
        print(f"  {mode}: {out[mode]}  loss {loss:.2f} (Juno run-to-run {chorus_loss(runs[0], runs[1]):.2f}, "
              f"rate {target[2]:.2f} Hz)")
    cal["juno_chorus"] = out


BLIP = [(0.0, 0.03, NOTE, 100)]  # a 30 ms note: the echoes stand apart


def echo_db(x, period, n=5):
    """Stereo blip render -> level (dB re the dry blip) of echoes 1..n at multiples of period, per channel."""
    w = int(0.01 * RATE)

    def at(t, c):
        i = int(t * RATE)
        s = x[max(0, i - 2 * w):i + 4 * w, c]
        return max(20 * np.log10(np.sqrt(np.mean(s[j:j + w] ** 2)) + 1e-9) for j in range(0, len(s) - w, w // 2))
    return np.array([[at(k * period, c) - at(0.0, c) for c in (0, 1)] for k in range(1, n + 1)])


def per_echo_db(e):
    """Average level change from one echo to the next (left channel, echoes above -50 dB)."""
    v = e[:, 0][e[:, 0] > -50]
    return float(np.polyfit(np.arange(len(v)), v, 1)[0])


def cal_delay(cal):
    """Delay: wet/send -> first echo re dry, feedback -> dB per repeat, Jun-6 V stereo -> right/left time.

    Tables juno_delay_wet_db / virus_delay_send_db (first echo re dry, dB), juno_delay_fb_db /
    virus_delay_fb_db (per repeat, dB), juno_delay_stereo_ratio, virus_delay_ms. Virus: Classic
    type, Simple Delay, delay modulation 0 (both channels alike)."""
    from render_lib import render_virus_seq
    jfx = dict(fx_section_on_off=True, delay_on_off=True, reverb_on_off=False, chorus_modes="Off",
               delay_sync=False, delay_time_unsync_ms=300.0, delay_stereo=0.0, delay_feedback=0.0, delay_dry_wet=0.5)

    def jrender(**o):
        jun6.load("Default", {**JUNO_BASE, **jfx, **o})
        return jun6.render_seq(BLIP, 2.0, stereo=True)
    cal["juno_delay_wet_db"] = {str(w): round(float(echo_db(jrender(delay_dry_wet=w), 0.3, 1)[0].mean()), 2)
                                for w in (0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9)}
    cal["juno_delay_fb_db"] = {str(f): round(per_echo_db(echo_db(jrender(delay_feedback=f), 0.3)), 2)
                               for f in (0.15, 0.25, 0.35, 0.45, 0.55, 0.7, 0.85)}
    ratios = {}
    for s in (0.0, 0.25, 0.5, 0.75, 1.0):
        x = jrender(delay_stereo=s)
        first = [0.15 + np.argmax(np.abs(x[int(0.15 * RATE):int(0.5 * RATE), c])) / RATE for c in (0, 1)]
        ratios[str(s)] = round(float(first[1] / first[0]), 3)  # first right echo / first left echo
    cal["juno_delay_stereo_ratio"] = ratios
    print("  Juno wet", cal["juno_delay_wet_db"], "\n  Juno fb", cal["juno_delay_fb_db"], "\n  Juno R/L", ratios)

    base = virus_base().set(Amp_Env_Attack=0, Amp_Env_Decay=127, Amp_Env_Sustain=127, Amp_Env_Release=0)
    base.set(Delay_Type=0, Delay_Mode=1, Delay_Time=55, Delay_Feedback=0, Delay_Send=64)
    base["Delay/Tape Delay Modulation"] = 0
    period = 55 * 5.46e-3  # the Virus shows Delay Time in 5.46 ms steps

    def vrender(**o):
        p = base.copy()
        for k, v in o.items():
            p[k.replace("_", " ")] = v
        return render_virus_seq(p, BLIP, tail=2.0, stereo=True)
    sends, fbs, times = (40, 64, 80, 90, 100, 110, 120), (10, 20, 30, 40, 50, 60, 70, 80), (20, 40, 67, 90, 120)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as ex:
        xs = list(ex.map(lambda o: vrender(**o), [dict(Delay_Send=s) for s in sends] + [dict(Delay_Feedback=f, Delay_Send=100) for f in fbs]
                         + [dict(Delay_Time=t) for t in times]))
    cal["virus_delay_send_db"] = {str(s): round(float(echo_db(x, period, 1)[0].mean()), 2) for s, x in zip(sends, xs)}
    cal["virus_delay_fb_db"] = {str(f): round(per_echo_db(echo_db(x, period)), 2) for f, x in zip(fbs, xs[len(sends):])}
    ms = {}
    for t, x in zip(times, xs[-len(times):]):
        onset = lambda m: np.argmax(m > 0.3 * m.max()) / RATE  # noqa: E731
        m = np.abs(x[int(0.05 * RATE):, 0])
        ms[str(t)] = round(1000 * (0.05 + onset(m) - onset(np.abs(x[:int(0.05 * RATE), 0]))), 1)  # echo - dry onset
    cal["virus_delay_ms"] = ms
    print("  Virus send", cal["virus_delay_send_db"], "\n  Virus fb", cal["virus_delay_fb_db"], "\n  Virus ms", ms)


STEPS = {"waves": cal_waves, "levels": cal_levels, "filter": cal_filter, "env": cal_env_amount, "hpf": cal_hpf,
         "times": cal_env_times, "fenv": cal_filter_env, "lfo": cal_lfo, "chorus": cal_chorus, "delay": cal_delay}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("steps", nargs="*", default=list(STEPS))
    a = ap.parse_args()
    cal = json.loads(OUT.read_text())
    for s in a.steps:
        print(s)
        STEPS[s](cal)
        OUT.write_text(json.dumps(cal, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
