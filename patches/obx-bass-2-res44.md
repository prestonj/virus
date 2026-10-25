# OBX Bass 2 (fitted, res 44) (Virus TI)

Translated from OB-Xf's **"OBX Bass 2"** by `tools/translate.py`. File: `obx-bass-2-res44.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Common | Unison Mode | 5 | 4 |
| 2 | Common | Unison Detune | 79 | 79 |
| 3 | Common | Transpose | -12 | 52 |
| 4 | Common | Key Mode | Mono 1 | 1 |
| 5 | Osc 1 | Osc1 Shape | Pulse | 127 |
| 6 | Osc 1 | Osc1 Semitone | -12 | 52 |
| 7 | Osc 2 | Osc2 Detune | 5 | 5 |
| 8 | Mixer | Osc Balance | -25.0 % | 48 |
| 9 | Filters | Filter Balance | -64 | 0 |
| 10 | Filter 1 | Cutoff | 18 | 18 |
| 11 | Filter 1 | Filter1 Resonance | 44 | 44 |
| 12 | Filter 1 | Filter1 Env Amt | 57.0 % | 73 |
| 13 | Filter 1 | Filter1 Keyfollow | +23 | 87 |
| 14 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 15 | Filter Env | Filter Env Decay | 50 | 50 |
| 16 | Filter Env | Filter Env Release | 30 | 30 |
| 17 | Amp Env | Amp Env Attack | 4 | 4 |
| 18 | Amp Env | Amp Env Decay | 37 | 37 |
| 19 | Amp Env | Amp Env Sustain | 0 % | 0 |
| 20 | Amp Env | Amp Env Release | 50 | 50 |
| 21 | Velocity Map | Flt1 EnvAmt Velocity | -46.9 % | 34 |

Everything else stays at INIT.

## Translation notes

- osc1: pulse, duty 0.500
- osc2 detune 0.1 cents
- unison 5 voices (Virus 5), OB-Xf spread +/-21 c random -> even width 34 c
- EnvToPWAmount=0.104 not translated

## How close it is

- Amp envelope level-shape error 0.31 dB; filter band-shape error 3.69 dB (Obright final was 4.49 dB).
- Cutoff trimmed 23 → 18 so the held note (attack and sustain medians) matches OB-Xf's brightness (gap +0.28 semitones).
- Listening files: `renders/obx-bass-2-res44/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 2.0 s hold, 1.5 s tail).
- Not used: the user chose the low-resonance version (patches/obx-bass-2).
