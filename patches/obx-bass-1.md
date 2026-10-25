# OBX Bass 1 (Virus TI)

Translated from OB-Xf's **"OBX Bass 1"** by `tools/translate.py`. File: `obx-bass-1.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Common | Unison Mode | 8 | 7 |
| 2 | Common | Unison Detune | 80 | 80 |
| 3 | Common | Transpose | -12 | 52 |
| 4 | Common | Key Mode | Mono 1 | 1 |
| 5 | Osc 1 | Osc1 Shape | Pulse | 127 |
| 6 | Osc 1 | Osc1 Pulsewidth | 14 | 14 |
| 7 | Osc 2 | Osc2 Shape | Pulse | 127 |
| 8 | Osc 2 | Osc2 Pulsewidth | 14 | 14 |
| 9 | Osc 2 | Osc2 Detune | 5 | 5 |
| 10 | Osc 2 | Osc2 Sync | On | 1 |
| 11 | Mixer | Osc Balance | +100.0 % | 127 |
| 12 | Filters | Filter Balance | -64 | 0 |
| 13 | Filter 1 | Cutoff | 42 | 42 |
| 14 | Filter 1 | Filter1 Resonance | 25 | 25 |
| 15 | Filter 1 | Filter1 Env Amt | 53.9 % | 69 |
| 16 | Filter 1 | Filter1 Keyfollow | +17 | 81 |
| 17 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 18 | Filter Env | Filter Env Attack | 1 | 1 |
| 19 | Filter Env | Filter Env Decay | 60 | 60 |
| 20 | Filter Env | Filter Env Sustain | 17.2 % | 22 |
| 21 | Filter Env | Filter Env Sustain Time | +2 | 66 |
| 22 | Filter Env | Filter Env Release | 30 | 30 |
| 23 | Amp Env | Amp Env Attack | 37 | 37 |
| 24 | Amp Env | Amp Env Decay | 36 | 36 |
| 25 | Amp Env | Amp Env Sustain | 0 % | 0 |
| 26 | Amp Env | Amp Env Release | 50 | 50 |
| 27 | Velocity Map | Flt1 EnvAmt Velocity | -10.9 % | 57 |

Everything else stays at INIT.

## Translation notes

- osc1: pulse, duty 0.444
- osc2: pulse, duty 0.444
- osc2 detune 0.1 cents
- unison 8 voices (Virus 8), OB-Xf spread +/-21 c random -> even width 37 c
- EnvToPitchAmount=0.036 not translated

## Changes made by ear

- Unison Detune 121 -> 80: user heard the Virus wobble more; 80 matches OB-Xf's typical wobble (measured)
- Cutoff 36 -> 42: user: 'a touch brighter' (picked c42 over c39)

## How close it is

- Amp envelope level-shape error 0.59 dB; filter band-shape error 3.09 dB (Obright final was 4.49 dB).
- Cutoff trimmed 38 → 36 so the first 0.3 s matches OB-Xf's brightness (gap -0.0 semitones).
- Listening files: `renders/obx-bass-1/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 2.0 s hold, 1.5 s tail).
- Chosen by ear (2026-10-24): cutoff 42 picked over 39 after the wobble fix; no final verdict yet.
