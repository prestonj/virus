"""Measure how Virus (and OB-Xf) control values map to real units; saves tools/calibration.json.

    .venv/bin/python tools/calibrate.py

Tables (value -> unit), all measured from renders:
  virus_osc2_detune_cents   Osc2 Detune -> cents
  virus_lfo1_rate_hz        Lfo1 Rate (sine) -> Hz
  virus_lfo1_osc_depth_cents  Osc1 Lfo1 Amount (64 = 0) -> peak cents
  virus_pulse_duty          Osc Pulsewidth (Shape 127) -> duty cycle (0.5 = square)
  obxf_pulse_duty           OscPW -> duty cycle
  virus_attack_ms / obxf_attack_ms  amp attack value -> 10-90 % rise time, ms
                            (`calibrate.py attack` measures just these)
  mixer tables (`calibrate.py mixer`), levels in dB re a full-scale sine, from triangle
  oscillators a fifth apart so osc 1, osc 2 and the ring products sit on separate frequencies:
    virus_balance_db    Osc Balance -> [osc 1 dB, osc 2 dB]
    virus_mainvol_db    Osc Mainvolume -> osc 1 dB (balance 0; the ring is unaffected)
    virus_ring_db       Ringmodulator Volume -> ring (sum component) dB; independent of balance
    obxf_mix_db         Osc1Mix -> osc 1 dB
    obxf_ring_db        RingModMix -> ring (sum component) dB, osc mixes 1
  per-note tuning (`calibrate.py pernote`): std over 24 notes of the osc 2 - osc 1 interval, cents
    obxf_pernote_interval_cents   UnisonDetune -> interval std (OB-Xf re-detunes each osc at note on)
    virus_lfo3_sh_interval_cents  Osc Lfo3 Amount (LFO 3 S&H, rate 32, dest Osc 2 Pitch) -> interval std
"""
import json
import pathlib

import numpy as np
from scipy.signal import hilbert

from render_lib import RATE, render_obxf, render_virus_many
from virus_patch import Patch

OUT = pathlib.Path(__file__).resolve().parent / "calibration.json"
A3 = 57  # 220 Hz


def inst_freq(x):
    """Instantaneous frequency of a near-sinusoidal signal, smoothed to 5 ms."""
    ph = np.unwrap(np.angle(hilbert(x)))
    f = np.diff(ph) * RATE / (2 * np.pi)
    k = int(0.005 * RATE)
    return np.convolve(f, np.ones(k) / k, mode="same")


def sine_patch():
    # Osc 1 alone as a sine (Shape 0 = Wave, Wave Select 0 = sine), filter open
    return Patch.from_syx().set(Osc1_Shape=0, Osc1_Wave_Select=0, Osc_Balance=0)


def fine_pitch(x, lo, hi):
    seg = x * np.hanning(len(x))
    n = 16 * len(seg)
    s = np.abs(np.fft.rfft(seg, n))
    f = np.fft.rfftfreq(n, 1 / RATE)
    m = (f > lo) & (f < hi)
    return f[m][np.argmax(s[m])]


def phase_freq(x):
    """Mean frequency from the slope of the unwrapped analytic phase (sub-millihertz precise)."""
    ph = np.unwrap(np.angle(hilbert(x)))
    t = np.arange(len(ph)) / RATE
    return float(np.polyfit(t, ph, 1)[0] / (2 * np.pi))


def detune_table():
    """Osc2 Detune -> cents, each oscillator soloed as a sine; phase-slope frequency over 6 s."""
    vals = list(range(0, 128, 8)) + [127]
    base = Patch.from_syx().set(Osc1_Shape=0, Osc1_Wave_Select=0, Osc2_Shape=0, Osc2_Wave_Select=0)
    ref = base.copy().set(Osc_Balance=0)
    ps = [base.copy().set(Osc_Balance=127, Osc2_Detune=v) for v in vals]
    outs = render_virus_many([ref] + ps, notes=(69,), hold=7.0, tail=0.1)
    seg = slice(int(0.5 * RATE), int(6.5 * RATE))
    r = phase_freq(outs[0][seg])
    return {v: round(1200 * np.log2(phase_freq(o[seg]) / r), 2) for v, o in zip(vals, outs[1:])}


def lfo_rate_table():
    vals = list(range(0, 128, 8)) + [127]
    # deep pitch modulation so the rate is easy to read off the frequency track
    ps = [sine_patch().set(Lfo1_Rate=v, Lfo1_Shape=0, Osc1_Lfo1_Amount=100) for v in vals]
    outs = render_virus_many(ps, notes=(A3,), hold=6.0, tail=0.1)
    table = {}
    for v, x in zip(vals, outs):
        f = inst_freq(x[int(0.2 * RATE):int(5.9 * RATE)])
        f = f - f.mean()
        spec = np.abs(np.fft.rfft(f * np.hanning(len(f)), 8 * len(f)))
        freqs = np.fft.rfftfreq(8 * len(f), 1 / RATE)
        m = (freqs > 0.03) & (freqs < 200)
        table[v] = round(float(freqs[m][np.argmax(spec[m])]), 3)
    return table


def lfo_depth_table(rate_value=40):
    vals = [64, 66, 68, 70, 72, 76, 80, 88, 96, 112, 127]
    ps = [sine_patch().set(Lfo1_Rate=rate_value, Lfo1_Shape=0, Osc1_Lfo1_Amount=v) for v in vals]
    outs = render_virus_many(ps, notes=(A3,), hold=6.0, tail=0.1)
    table = {}
    for v, x in zip(vals, outs):
        f = inst_freq(x[int(0.5 * RATE):int(5.8 * RATE)])
        cents = 1200 * np.log2(np.maximum(f, 1) / 220.0)
        # peak deviation ~ half the 2nd..98th percentile range (robust to edge noise)
        table[v] = round(float((np.percentile(cents, 98) - np.percentile(cents, 2)) / 2), 2)
    return table


def duty_from_spectrum(x, f0):
    """Pulse duty d from harmonic amplitudes |sin(pi n d)| / n (fit over first 24 harmonics)."""
    seg = x[int(0.3 * RATE):int(1.3 * RATE)]
    seg = seg * np.hanning(len(seg))
    n = 8 * len(seg)
    s = np.abs(np.fft.rfft(seg, n))
    f = np.fft.rfftfreq(n, 1 / RATE)
    h = np.array([s[(f > k * f0 * 0.98) & (f < k * f0 * 1.02)].max() for k in range(1, 25)])
    h = h / h.max()
    best, err = 0.5, 1e9
    k = np.arange(1, 25)
    for d in np.linspace(0.01, 0.5, 491):
        model = np.abs(np.sin(np.pi * k * d)) / k
        model = model / model.max()
        e = np.sum((np.log(h + 1e-4) - np.log(model + 1e-4)) ** 2)
        if e < err:
            best, err = d, e
    return round(float(best), 3)


def pulse_tables():
    f0 = 440 * 2 ** ((A3 - 69) / 12)
    vals = list(range(0, 128, 16)) + [127]
    ps = [Patch.from_syx().set(Osc1_Shape=127, Osc1_Pulsewidth=v, Osc_Balance=0) for v in vals]
    virus = {v: duty_from_spectrum(x, f0) for v, x in zip(vals, render_virus_many(ps, notes=(A3,), hold=1.5, tail=0.1))}
    obxf = {}
    for pw in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        ov = {"Osc1SawWave": 0.0, "Osc1PulseWave": 1.0, "Osc1Mix": 1.0, "Osc2Mix": 0.0, "OscPW": pw,
              "FilterCutoff": 1.0, "FilterEnvAmount": 0.0, "Transpose": 0.5, "Osc1Pitch": 0.5,
              "AmpEnvAttack": 0.0, "AmpEnvSustain": 1.0, "LFO1ToOsc1PW": 0.0, "EnvToPWAmount": 0.0}
        obxf[pw] = duty_from_spectrum(render_obxf("Obright Original", ov, notes=(A3,), hold=1.5, tail=0.1), f0)
    return virus, obxf


def beat_cents(x, f0):
    """Frequency spread of two detuned voices: the beat rate of the band around f0, in cents."""
    from scipy.signal import butter, sosfiltfilt
    sos = butter(4, [f0 * 0.8, f0 * 1.2], btype="band", fs=RATE, output="sos")
    env = np.abs(hilbert(sosfiltfilt(sos, x)))
    env = env - env.mean()
    spec = np.abs(np.fft.rfft(env * np.hanning(len(env)), 8 * len(env)))
    freqs = np.fft.rfftfreq(8 * len(env), 1 / RATE)
    m = (freqs > 0.05) & (freqs < 40)
    beat = freqs[m][np.argmax(spec[m])]
    return round(float(1200 * np.log2((f0 + beat) / f0)), 2)


def unison_tables():
    """Two-voice unison detune -> cents between the voices, for both synths."""
    f0 = 440.0
    seg = slice(int(0.3 * RATE), int(7.8 * RATE))
    vals = [8, 16, 24, 32, 48, 64, 80, 96, 112, 127]
    ps = [sine_patch().set(Unison_Mode=1, Unison_Detune=v, Unison_Pan_Spread=0) for v in vals]
    virus = {v: beat_cents(x[seg], f0) for v, x in zip(vals, render_virus_many(ps, notes=(69,), hold=8.0, tail=0.1))}
    obxf = {}
    for d in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        ov = {"Osc1SawWave": 1.0, "Osc1Mix": 1.0, "Osc2Mix": 0.0, "Unison": 1.0, "UnisonVoices": 1 / 32,
              "UnisonDetune": d, "FilterCutoff": 1.0, "FilterEnvAmount": 0.0, "Transpose": 0.5,
              "Osc1Pitch": 0.5, "AmpEnvAttack": 0.0, "AmpEnvSustain": 1.0}
        for k in range(1, 9):
            ov[f"PanVoice{k}"] = 0.5
        obxf[d] = beat_cents(render_obxf("Obright Original", ov, notes=(69,), hold=8.0, tail=0.1)[seg], f0)
    return virus, obxf


def rise_ms(x):
    """10 % -> 90 % of peak amplitude, 1 ms RMS envelope."""
    k = int(0.001 * RATE)
    e = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, "same"))
    return float((np.argmax(e > 0.9 * e.max()) - np.argmax(e > 0.1 * e.max())) / RATE * 1000)


def attack_tables():
    """Amp attack -> rise time on both synths (the filter envelopes use the same generators)."""
    vals = [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 127]
    ps = [sine_patch().set(Amp_Env_Attack=v, Amp_Env_Decay=127, Amp_Env_Sustain=127) for v in vals]
    virus = {str(v): round(rise_ms(x), 2) for v, x in zip(vals, render_virus_many(ps, notes=(A3 + 12,), hold=6.0, tail=0.05))}
    obxf = {}
    for v in (0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
        x = render_obxf(None, {"AmpEnvAttack": v, "AmpEnvSustain": 1.0, "AmpEnvDecay": 1.0}, notes=(A3 + 12,), hold=6.0, tail=0.05)
        obxf[str(v)] = round(rise_ms(x), 2)
    return virus, obxf


F1 = 130.81  # note 48


def mixer_levels(x):
    """dB of osc 1 (f1), osc 2 (f2 = f1 x 1.498) and the ring sum product (f1 + f2)."""
    s = x[int(0.3 * RATE):int(1.3 * RATE)]
    m = np.abs(np.fft.rfft(s * np.hanning(len(s)))) / (len(s) / 4)
    f = np.fft.rfftfreq(len(s), 1 / RATE)
    f2 = F1 * 2 ** (7 / 12)
    return [round(float(20 * np.log10(m[(f > fr - 6) & (f < fr + 6)].max() + 1e-9)), 2) for fr in (F1, f2, F1 + f2)]


def mixer_tables():
    tri = dict(Osc1_Shape=0, Osc1_Wave_Select=1, Osc2_Shape=0, Osc2_Wave_Select=1, Osc2_Semitone=71)
    bals, mains, rings = list(range(0, 128, 8)) + [127], list(range(0, 65, 8)), list(range(0, 128, 8)) + [127]
    ps = ([Patch.from_syx().set(Osc_Balance=b, **tri) for b in bals]
          + [Patch.from_syx().set(Osc_Balance=0, Osc_Mainvolume=v, **tri) for v in mains]
          + [Patch.from_syx().set(Ringmodulator_Volume=r, **tri) for r in rings])
    lv = [mixer_levels(x) for x in render_virus_many(ps, notes=(48,), hold=1.4, tail=0.05)]
    cal = {"virus_balance_db": {str(b): l[:2] for b, l in zip(bals, lv)},
           "virus_mainvol_db": {str(v): l[0] for v, l in zip(mains, lv[len(bals):])},
           "virus_ring_db": {str(r): l[2] for r, l in zip(rings, lv[len(bals) + len(mains):])}}
    ob = {"Osc1SawWave": 0.0, "Osc2SawWave": 0.0, "Osc2Pitch": 0.5 + 7 / 48}
    avg = lambda o: np.mean([mixer_levels(render_obxf(None, {**ob, **o}, notes=(48,), hold=1.4, tail=0.05))  # noqa: E731
                             for _ in range(2)], axis=0)
    cal["obxf_mix_db"] = {str(m): round(float(avg({"Osc1Mix": m, "Osc2Mix": 0.0})[0]), 2)
                          for m in (0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0)}
    cal["obxf_ring_db"] = {str(r): round(float(avg({"Osc1Mix": 1.0, "Osc2Mix": 1.0, "RingModMix": r})[2]), 2)
                           for r in (0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0)}
    return cal


def pernote_interval_std(x, n, step):
    """Std of the osc 2 (a fifth up) - osc 1 interval across n notes, `step` s apart, sines/triangles."""
    from scipy.signal import butter, sosfiltfilt
    f1, f2, c = F1, F1 * 2 ** (7 / 12), []
    for f0 in (f1, f2):
        y = sosfiltfilt(butter(4, [f0 * 0.9, f0 * 1.1], btype="band", fs=RATE, output="sos"), x)
        c.append(np.array([1200 * np.log2(phase_freq(y[int((i * step + 0.15) * RATE):int((i * step + 0.7) * RATE)]) / f0)
                           for i in range(n)]))
    return round(float(np.std(c[1] - c[0])), 2)


def pernote_tables():
    from render_lib import render_obxf_seq, render_virus_seq
    n, step = 24, 0.9
    seq = [(i * step, 0.8, 48, 100) for i in range(n)]
    ob = {"Osc1SawWave": 0.0, "Osc2SawWave": 0.0, "Osc2Mix": 1.0, "Osc2Pitch": 0.5 + 7 / 48, "AmpEnvSustain": 1.0}
    obxf = {str(v): pernote_interval_std(render_obxf_seq(None, seq, tail=0.3, overrides={**ob, "UnisonDetune": v}), n, step)
            for v in (0.0, 0.1, 0.25, 0.4, 0.6)}
    base = Patch.from_syx().set(Osc_Balance=72, Osc1_Shape=0, Osc1_Wave_Select=0, Osc2_Shape=0, Osc2_Wave_Select=0,
                                Osc2_Semitone=71, Amp_Env_Release=10, Lfo3_Shape=4, Lfo3_Rate=32, Lfo3_Destination=2)
    amts = (0, 8, 12, 16, 18, 20, 24, 32)
    virus = {str(a): pernote_interval_std(render_virus_seq(base.copy().set(Osc_Lfo3_Amount=a), seq, tail=0.3), n, step)
             for a in amts}
    return {"obxf_pernote_interval_cents": obxf, "virus_lfo3_sh_interval_cents": virus}


def main():
    import sys
    if sys.argv[1:] == ["pernote"]:
        cal = json.loads(OUT.read_text())
        for k, v in pernote_tables().items():
            cal[k] = v
            print(k, v)
        OUT.write_text(json.dumps(cal, indent=1))
        return
    if sys.argv[1:] == ["mixer"]:
        cal = json.loads(OUT.read_text())
        for k, v in mixer_tables().items():
            cal[k] = v
            print(k, v)
        OUT.write_text(json.dumps(cal, indent=1))
        return
    if sys.argv[1:] == ["attack"]:
        cal = json.loads(OUT.read_text())
        cal["virus_attack_ms"], cal["obxf_attack_ms"] = attack_tables()
        print("virus attack", cal["virus_attack_ms"])
        print("obxf attack", cal["obxf_attack_ms"])
        OUT.write_text(json.dumps(cal, indent=1))
        return
    cal = json.loads(OUT.read_text()) if OUT.exists() else {}  # keep tables other scripts add
    cal["virus_osc2_detune_cents"] = detune_table()
    print("detune", cal["virus_osc2_detune_cents"])
    cal["virus_lfo1_rate_hz"] = lfo_rate_table()
    print("lfo rate", cal["virus_lfo1_rate_hz"])
    cal["virus_lfo1_osc_depth_cents"] = lfo_depth_table()
    print("lfo depth", cal["virus_lfo1_osc_depth_cents"])
    cal["virus_pulse_duty"], cal["obxf_pulse_duty"] = pulse_tables()
    print("virus duty", cal["virus_pulse_duty"])
    print("obxf duty", cal["obxf_pulse_duty"])
    OUT.write_text(json.dumps(cal, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
