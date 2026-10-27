# 25 Harpsichord (Virus TI)

Translated from Jun-6 V (Juno-6/60)'s **"Vintage Factory/25 Harpsichord"** by `tools/translate_juno.py`. File: `juno-harpsichord.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Shape | Pulse | 127 |
| 2 | Osc 1 | Osc1 Pulsewidth | 28 | 28 |
| 3 | Osc 2 | Osc2 Shape | Pulse | 127 |
| 4 | Osc 2 | Osc2 Semitone | -12 | 52 |
| 5 | Osc 2 | Osc2 Detune | 0 | 0 |
| 6 | Mixer | Osc Balance | -53.1 % | 30 |
| 7 | Filter 1 | Cutoff | 16 | 16 |
| 8 | Filter 1 | Filter1 Env Amt | 60.9 % | 78 |
| 9 | Filter 1 | Filter1 Keyfollow | +33 | 97 |
| 10 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 11 | Filter 2 | Cutoff2 | 42 | 42 |
| 12 | Filter 2 | Filter2 Mode | High Pass | 1 |
| 13 | Filter 2 | Filter2 Cutoff Link | Off | 0 |
| 14 | Filter Env | Filter Env Attack | 2 | 2 |
| 15 | Filter Env | Filter Env Decay | 94 | 94 |
| 16 | Filter Env | Filter Env Sustain | 38.3 % | 49 |
| 17 | Filter Env | Filter Env Release | 0 | 0 |
| 18 | Amp Env | Amp Env Attack | 30 | 30 |
| 19 | Amp Env | Amp Env Decay | 95 | 95 |
| 20 | Amp Env | Amp Env Sustain | 46.9 % | 60 |
| 21 | Amp Env | Amp Env Release | 22 | 22 |
| 22 | EQ | LowEQ Gain | -1.5 dB | 58 |
| 23 | EQ | HighEQ Gain | +1.25 dB | 69 |
| 24 | Other | deprecated_112_103 | Vintage | 2 |
| 25 | Other | Chorus Rate | 17 | 17 |
| 26 | Other | Chorus Depth | 67.2 % | 86 |
| 27 | Other | Chorus Delay | 64 | 64 |
| 28 | Other | Assign1 Source | 0 | 0 |
| 29 | Other | Assign1 Amount | Off | 64 |

Everything else stays at INIT.

## Translation notes

- HPF 201 -> filter 2 high-pass, Cutoff2 26

## Variant changes (not yet heard)

- Cutoff2 26 -> 42 (phrase fit)
- Filter1 Keyfollow 105 -> 97 (phrase fit)
- HighEQ Gain 64 -> 69 (phrase fit)
- LowEQ Gain 64 -> 58 (phrase fit)
- Osc Balance 36 -> 30 (phrase fit)

## How close it is

- Amp envelope level-shape error 1.12 dB; filter band-shape error 6.35 dB.
- Cutoff trimmed 8 → 16 so the held note (attack and sustain medians) matches the Juno's brightness (gap -0.34 semitones).
- Listening file: `renders/juno-harpsichord/listen/demo_AB.wav` (the Juno first, then Virus, loudness-matched).
- Chosen by ear over the first translation (renders/dropped/juno-v1/), 2026-10-27.
