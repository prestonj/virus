# Obright (Virus TI)

Translated from OB-Xf's **"Obright Original"** by `tools/translate.py`. File: `obright.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Common | Transpose | -12 | 52 |
| 2 | Osc 2 | Osc2 Detune | 50 | 50 |
| 3 | Mixer | Osc Balance | -15.6 % | 54 |
| 4 | Filters | Filter Balance | -64 | 0 |
| 5 | Filter 1 | Cutoff | 30 | 30 |
| 6 | Filter 1 | Filter1 Resonance | 8 | 8 |
| 7 | Filter 1 | Filter1 Env Amt | 100.0 % | 127 |
| 8 | Filter 1 | Filter1 Keyfollow | +40 | 104 |
| 9 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 10 | Filter Env | Filter Env Attack | 21 | 21 |
| 11 | Filter Env | Filter Env Decay | 80 | 80 |
| 12 | Filter Env | Filter Env Sustain | 28.1 % | 36 |
| 13 | Filter Env | Filter Env Sustain Time | -22 | 42 |
| 14 | Filter Env | Filter Env Release | 12 | 12 |
| 15 | Amp Env | Amp Env Attack | 50 | 50 |
| 16 | Amp Env | Amp Env Decay | 90 | 90 |
| 17 | Amp Env | Amp Env Sustain | 74.2 % | 95 |
| 18 | Amp Env | Amp Env Release | 35 | 35 |
| 19 | Velocity Map | Flt1 EnvAmt Velocity | -31.3 % | 44 |

Everything else stays at INIT.

## Translation notes

- osc2 detune 5.2 cents
- non-LP filter mode in OB-Xf: translated as low-pass

## How close it is

- Amp envelope level-shape error 2.47 dB; filter band-shape error 4.11 dB.
- Cutoff trimmed 42 → 30 so the held note (attack and sustain medians) matches OB-Xf's brightness (gap +0.1 semitones).
- Listening file: `renders/obright/listen/demo_AB.wav` (OB-Xf first, then Virus, loudness-matched).
- Preferred by ear over the earlier hand-finished version (obright-hand.syx), 2026-10-26.
