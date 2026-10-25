# Warmth (Virus TI)

Translated from OB-Xf's **"Warmth"** by `tools/translate.py`. File: `warmth.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Semitone | -12 | 52 |
| 2 | Osc 1 | Osc1 Lfo1 Amount | +10.9 % | 71 |
| 3 | Osc 2 | Osc2 Semitone | -12 | 52 |
| 4 | Osc 2 | Osc2 Detune | 25 | 25 |
| 5 | Osc 2 | Osc2 Lfo1 Amount | -10.9 % | 57 |
| 6 | Filters | Filter Balance | -64 | 0 |
| 7 | Filter 1 | Cutoff | 48 | 48 |
| 8 | Filter 1 | Filter1 Resonance | 15 | 15 |
| 9 | Filter 1 | Filter1 Env Amt | 28.9 % | 37 |
| 10 | Filter 1 | Filter1 Keyfollow | +28 | 92 |
| 11 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 12 | Filter Env | Filter Env Attack | 53 | 53 |
| 13 | Filter Env | Filter Env Decay | 99 | 99 |
| 14 | Filter Env | Filter Env Sustain | 10.9 % | 14 |
| 15 | Filter Env | Filter Env Release | 72 | 72 |
| 16 | Amp Env | Amp Env Attack | 64 | 64 |
| 17 | Amp Env | Amp Env Decay | 80 | 80 |
| 18 | Amp Env | Amp Env Sustain | 98.4 % | 126 |
| 19 | Amp Env | Amp Env Release | 71 | 71 |
| 20 | LFO 1 | Lfo1 Rate | 73 | 73 |
| 21 | LFO 1 | Lfo1 Shape | Sine | 0 |
| 22 | Velocity Map | Flt1 EnvAmt Velocity | -15.6 % | 54 |
| 23 | Velocity Map | Amp Velocity | +21.9 % | 78 |
| 24 | EQ | LowEQ Frequency | 82 | 44 |
| 25 | EQ | MidEQ Gain | +8 dB | 96 |
| 26 | EQ | MidEQ Frequency | 404 | 54 |
| 27 | EQ | MidEQ Q-Factor | 0.74 | 35 |
| 28 | EQ | LowEQ Gain | +6 dB | 88 |

Everything else stays at INIT.

## Translation notes

- osc2 detune 1.6 cents
- LFO1 1.61 Hz, +/-8.3 c on osc1 +1 / osc2 -1

## Changes made by ear

- Cutoff 40 -> 48: user: 'a touch brighter' (picked c48 over c44); 48 also matches OB-Xf sustain brightness
- Filter attack kept at the fitted 53 (a shorter attack was tried and rejected)
- EQ for more low end: Mid EQ +8 dB at 404 Hz (Q 0.74) plus Low shelf +6 dB at 82 Hz. User: OB 'seems bassier'; picked this 'bodylow' version over mid-EQ only and a sub-osc version

## How close it is

- Amp envelope level-shape error 2.4 dB; filter band-shape error 2.48 dB (Obright final was 4.49 dB).
- Cutoff trimmed 43 → 40 so the first 0.3 s matches OB-Xf's brightness (gap +0.15 semitones).
- Listening files: `renders/warmth/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 3.0 s hold, 4.0 s tail).
- Brightness, attack and low end chosen by ear (2026-10-24); no final verdict yet.
