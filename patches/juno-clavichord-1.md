# 33 Clavichord 1 (Virus TI)

Translated from Jun-6 V (Juno-6/60)'s **"Vintage Factory/33 Clavichord 1"** by `tools/translate_juno.py`. File: `juno-clavichord-1.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Shape | Pulse | 127 |
| 2 | Osc 1 | Osc1 Pulsewidth | 101 | 101 |
| 3 | Mixer | Osc Balance | -100.0 % | 0 |
| 4 | Filters | Filter Balance | -64 | 0 |
| 5 | Filter 1 | Cutoff | 24 | 24 |
| 6 | Filter 1 | Filter1 Env Amt | 80.5 % | 103 |
| 7 | Filter 1 | Filter1 Keyfollow | +57 | 121 |
| 8 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 9 | Filter Env | Filter Env Decay | 66 | 66 |
| 10 | Filter Env | Filter Env Sustain | 7.0 % | 9 |
| 11 | Filter Env | Filter Env Release | 33 | 33 |
| 12 | Amp Env | Amp Env Decay | 57 | 57 |
| 13 | Amp Env | Amp Env Sustain | 22.7 % | 29 |
| 14 | Amp Env | Amp Env Release | 40 | 40 |
| 15 | Other | deprecated_112_103 | Vintage | 2 |
| 16 | Other | Chorus Rate | 17 | 17 |
| 17 | Other | Chorus Depth | 67.2 % | 86 |
| 18 | Other | Chorus Delay | 64 | 64 |
| 19 | Other | Assign1 Source | 0 | 0 |
| 20 | Other | Assign1 Amount | Off | 64 |

Everything else stays at INIT.

## Translation notes

- none

## Variant changes (not yet heard)

- Amp Env Attack 30 -> 0 (by ear)
- Filter Env Attack 8 -> 0 (by ear)
- Cutoff 8 -> 24 (phrase fit)
- Filter1 Env Amt 93 -> 103 (phrase fit)
- Filter1 Keyfollow 113 -> 121 (phrase fit)

## How close it is

- Amp envelope level-shape error 1.28 dB; filter band-shape error 6.9 dB.
- Cutoff trimmed 0 → 8 so the held note (attack and sustain medians) matches the Juno's brightness (gap -2.17 semitones).
- Listening file: `renders/juno-clavichord-1/listen/demo_AB.wav` (the Juno first, then Virus, loudness-matched).
- Chosen by ear over the first translation (renders/dropped/juno-v1/), 2026-10-27.
