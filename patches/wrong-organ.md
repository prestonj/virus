# Wrong Organ (Virus TI)

Translated from OB-Xf's **"Wrong Organ"** by `tools/translate.py`. File: `wrong-organ.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Shape | Spectral Wave | 0 |
| 2 | Osc 1 | Osc1 Wave Select | Triangle | 1 |
| 3 | Osc 2 | Osc2 Shape | Spectral Wave | 0 |
| 4 | Osc 2 | Osc2 Wave Select | Triangle | 1 |
| 5 | Osc 2 | Osc2 Semitone | +12 | 76 |
| 6 | Osc 2 | Osc2 FM Amount | 3.9 % | 4 |
| 7 | Osc 2 | Osc2 Lfo1 Amount | +14.1 % | 73 |
| 8 | Mixer | Osc Balance | -26.6 % | 47 |
| 9 | Filters | Filter Balance | -64 | 0 |
| 10 | Filter 1 | Cutoff | 28 | 28 |
| 11 | Filter 1 | Filter1 Resonance | 20 | 20 |
| 12 | Filter 1 | Filter1 Env Amt | 86.7 % | 111 |
| 13 | Filter 1 | Filter1 Keyfollow | +5 | 69 |
| 14 | Filter 1 | Filter1 Mode | Analog 2 Pole | 5 |
| 15 | Filter Env | Filter Env Attack | 7 | 7 |
| 16 | Filter Env | Filter Env Decay | 80 | 80 |
| 17 | Filter Env | Filter Env Sustain | 100.0 % | 127 |
| 18 | Filter Env | Filter Env Release | 30 | 30 |
| 19 | Amp Env | Amp Env Attack | 31 | 31 |
| 20 | Amp Env | Amp Env Decay | 80 | 80 |
| 21 | Amp Env | Amp Env Sustain | 98.4 % | 126 |
| 22 | Amp Env | Amp Env Release | 0 | 0 |
| 23 | LFO 1 | Lfo1 Rate | 96 | 96 |
| 24 | LFO 1 | Lfo1 Shape | Sine | 0 |
| 25 | Velocity Map | Flt1 EnvAmt Velocity | -20.3 % | 51 |
| 26 | Velocity Map | Amp Velocity | +35.9 % | 87 |
| 27 | Other | Osc FM Mode | Wave | 2 |

Everything else stays at INIT.

## Translation notes

- osc1: triangle
- osc2: triangle
- osc2 detune 0.1 cents
- cross-mod +/-1.5 st -> Virus FM 4, osc 2 raised +0.02 st
- OB-Xf LFO2 4.94 Hz, +/-12.5 c on osc1 +0 / osc2 +1 -> Virus LFO1

## How close it is

- Amp envelope level-shape error 0.93 dB; filter band-shape error 2.27 dB (Obright final was 4.49 dB).
- Cutoff trimmed 20 → 28 so the held note (attack and sustain medians) matches OB-Xf's brightness (gap -0.48 semitones).
- Listening files: `renders/wrong-organ/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 2.0 s hold, 1.5 s tail).
- Not yet checked by ear.
