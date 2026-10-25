# OBX Clavinet (Virus TI)

Translated from OB-Xf's **"OBX Clavinet"** by `tools/translate.py`. File: `obx-clavinet.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Shape | Pulse | 127 |
| 2 | Osc 1 | Osc1 Pulsewidth | 97 | 97 |
| 3 | Osc 2 | Osc2 Shape | Pulse | 127 |
| 4 | Osc 2 | Osc2 Pulsewidth | 97 | 97 |
| 5 | Osc 2 | Osc2 Detune | 37 | 37 |
| 6 | Filters | Filter Balance | -64 | 0 |
| 7 | Filter 1 | Cutoff | 51 | 51 |
| 8 | Filter 1 | Filter1 Resonance | 4 | 4 |
| 9 | Filter 1 | Filter1 Env Amt | 50.8 % | 65 |
| 10 | Filter 1 | Filter1 Keyfollow | +27 | 91 |
| 11 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 12 | Filter Env | Filter Env Attack | 6 | 6 |
| 13 | Filter Env | Filter Env Decay | 67 | 67 |
| 14 | Filter Env | Filter Env Sustain | 35.9 % | 46 |
| 15 | Filter Env | Filter Env Sustain Time | -4 | 60 |
| 16 | Filter Env | Filter Env Release | 30 | 30 |
| 17 | Amp Env | Amp Env Attack | 37 | 37 |
| 18 | Amp Env | Amp Env Decay | 65 | 65 |
| 19 | Amp Env | Amp Env Sustain | 0 % | 0 |
| 20 | Amp Env | Amp Env Release | 0 | 0 |
| 21 | Velocity Map | Flt1 EnvAmt Velocity | -4.7 % | 61 |

Everything else stays at INIT.

## Translation notes

- osc1: pulse, duty 0.120
- osc2: pulse, duty 0.120
- osc2 detune 3.1 cents

## How close it is

- Amp envelope level-shape error 0.53 dB; filter band-shape error 3.78 dB (Obright final was 4.49 dB).
- Cutoff trimmed 52 → 51 so the held note (attack and sustain medians) matches OB-Xf's brightness (gap +0.13 semitones).
- Listening files: `renders/obx-clavinet/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 2.0 s hold, 1.5 s tail).
- User: fine as translated (2026-10-24).
