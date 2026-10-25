"""Measure how Virus (and OB-Xf) control values map to real units; saves tools/calibration.json.

    .venv/bin/python tools/calibrate.py

Tables (value -> unit), all measured from renders:
  virus_osc2_detune_cents   Osc2 Detune -> cents
  virus_lfo1_rate_hz        Lfo1 Rate (sine) -> Hz
  virus_lfo1_osc_depth_cents  Osc1 Lfo1 Amount (64 = 0) -> peak cents
  virus_pulse_duty          Osc Pulsewidth (Shape 127) -> duty cycle (0.5 = square)
  obxf_pulse_duty           OscPW -> duty cycle
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


def main():
    cal = {}
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
