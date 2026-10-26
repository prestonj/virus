# Steel String Guitar 2 (Virus TI)

Translated from OB-Xf's **"Steel String Guitar 2"** by `tools/translate.py`. File: `steel-string-guitar-2.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 2 | Osc2 Shape | Pulse | 127 |
| 2 | Osc 2 | Osc2 Pulsewidth | 34 | 34 |
| 3 | Osc 2 | Osc2 Semitone | +16 | 80 |
| 4 | Osc 2 | Osc2 Detune | 127 | 127 |
| 5 | Osc 2 | Osc2 FM Amount | 24.2 % | 31 |
| 6 | Osc 2 | Osc2 Sync | On | 1 |
| 7 | Mixer | Osc Balance | -10.9 % | 57 |
| 8 | Filters | Filter Balance | -64 | 0 |
| 9 | Filter 1 | Cutoff | 51 | 51 |
| 10 | Filter 1 | Filter1 Env Amt | 71.9 % | 92 |
| 11 | Filter 1 | Filter1 Keyfollow | +4 | 68 |
| 12 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 13 | Filter Env | Filter Env Attack | 6 | 6 |
| 14 | Filter Env | Filter Env Decay | 80 | 80 |
| 15 | Filter Env | Filter Env Sustain | 17.2 % | 22 |
| 16 | Filter Env | Filter Env Sustain Time | -32 | 32 |
| 17 | Filter Env | Filter Env Release | 24 | 24 |
| 18 | Amp Env | Amp Env Decay | 99 | 99 |
| 19 | Amp Env | Amp Env Sustain | 0 % | 0 |
| 20 | Amp Env | Amp Env Release | 18 | 18 |
| 21 | Velocity Map | Flt1 EnvAmt Velocity | -29.7 % | 45 |
| 22 | Velocity Map | Amp Velocity | +62.5 % | 104 |
| 23 | Other | Osc FM Mode | Wave | 2 |

Everything else stays at INIT.

## Translation notes

- osc2: pulse, duty 0.367
- osc2 detune 0.1 cents
- cross-mod +/-16.0 st -> Virus FM 31, osc 2 raised +2.41 st
- OscBrightness=0.168 not translated

## How close it is

- Amp envelope level-shape error 0.56 dB; filter band-shape error 3.51 dB (Obright final was 4.49 dB).
- Cutoff trimmed 47 → 51 so the held note (attack and sustain medians) matches OB-Xf's brightness (gap +0.2 semitones).
- Listening files: `renders/steel-string-guitar-2/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 2.0 s hold, 1.5 s tail).
- Not yet checked by ear.
