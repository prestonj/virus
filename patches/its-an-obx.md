# It's an OB-X! (Virus TI)

Translated from OB-Xf's **"It's an OB-X!"** by `tools/translate.py`. File: `its-an-obx.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Lfo1 Amount | +12.5 % | 72 |
| 2 | Osc 2 | Osc2 Detune | 101 | 101 |
| 3 | Osc 2 | Osc2 Lfo1 Amount | +12.5 % | 72 |
| 4 | Filters | Filter Balance | -64 | 0 |
| 5 | Filter 1 | Cutoff | 45 | 45 |
| 6 | Filter 1 | Filter1 Resonance | 17 | 17 |
| 7 | Filter 1 | Filter1 Env Amt | 80.5 % | 103 |
| 8 | Filter 1 | Filter1 Keyfollow | +15 | 79 |
| 9 | Filter 1 | Filter1 Mode | Analog 2 Pole | 5 |
| 10 | Filter Env | Filter Env Decay | 89 | 89 |
| 11 | Filter Env | Filter Env Sustain Time | +1 | 65 |
| 12 | Filter Env | Filter Env Release | 80 | 80 |
| 13 | Amp Env | Amp Env Attack | 32 | 32 |
| 14 | Amp Env | Amp Env Decay | 123 | 123 |
| 15 | Amp Env | Amp Env Sustain | 83.6 % | 107 |
| 16 | Amp Env | Amp Env Release | 82 | 82 |
| 17 | LFO 1 | Lfo1 Rate | 91 | 91 |
| 18 | LFO 1 | Lfo1 Shape | Sine | 0 |
| 19 | Velocity Map | Flt1 EnvAmt Velocity | -46.9 % | 34 |

Everything else stays at INIT.

## Translation notes

- osc2 detune 18.9 cents
- LFO1 3.87 Hz, +/-10.5 c on osc1 +1 / osc2 +1

## How close it is

- Amp envelope level-shape error 1.8 dB; filter band-shape error 3.14 dB (Obright final was 4.49 dB).
- Cutoff trimmed 44 → 45 so the first 0.3 s matches OB-Xf's brightness (gap -0.07 semitones).
- Listening files: `renders/its-an-obx/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 2.0 s hold, 4.0 s tail).
- **Approved by ear** (2026-10-24): "sounds good".
