# Pursuit Bright (Virus TI)

Translated from OB-Xf's **"Pursuit Bright"** by `tools/translate.py`. File: `pursuit-bright.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Common | Transpose | -12 | 52 |
| 2 | Osc 2 | Osc2 Detune | 50 | 50 |
| 3 | Osc 2 | Osc2 Lfo1 Amount | +12.5 % | 72 |
| 4 | Mixer | Osc Balance | -28.1 % | 46 |
| 5 | Filters | Filter Balance | -64 | 0 |
| 6 | Filter 1 | Cutoff | 33 | 33 |
| 7 | Filter 1 | Filter1 Resonance | 10 | 10 |
| 8 | Filter 1 | Filter1 Env Amt | 76.6 % | 98 |
| 9 | Filter 1 | Filter1 Keyfollow | +23 | 87 |
| 10 | Filter 1 | Filter1 Mode | Analog 2 Pole | 5 |
| 11 | Filter Env | Filter Env Attack | 31 | 31 |
| 12 | Filter Env | Filter Env Decay | 86 | 86 |
| 13 | Filter Env | Filter Env Sustain | 28.1 % | 36 |
| 14 | Filter Env | Filter Env Sustain Time | +13 | 77 |
| 15 | Filter Env | Filter Env Release | 16 | 16 |
| 16 | Amp Env | Amp Env Attack | 27 | 27 |
| 17 | Amp Env | Amp Env Decay | 81 | 81 |
| 18 | Amp Env | Amp Env Sustain | 75.8 % | 97 |
| 19 | Amp Env | Amp Env Release | 38 | 38 |
| 20 | LFO 1 | Lfo1 Rate | 65 | 65 |
| 21 | LFO 1 | Lfo1 Shape | Sine | 0 |
| 22 | Velocity Map | Flt1 EnvAmt Velocity | -31.3 % | 44 |

Everything else stays at INIT.

## Translation notes

- osc2 detune 5.2 cents
- OB-Xf LFO2 1.14 Hz, +/-9.4 c on osc1 +0 / osc2 +1 -> Virus LFO1

## How close it is

- Amp envelope level-shape error 1.75 dB; filter band-shape error 3.57 dB (Obright final was 4.49 dB).
- Cutoff trimmed 39 → 33 so the held note (attack and sustain medians) matches OB-Xf's brightness (gap -0.22 semitones).
- Listening files: `renders/pursuit-bright/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 2.0 s hold, 1.5 s tail).
- User: fine as translated (2026-10-24).
