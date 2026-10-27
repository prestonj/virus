# 17 Brass 1 (Virus TI)

Translated from Jun-6 V (Juno-6/60)'s **"Vintage Factory/17 Brass 1"** by `tools/translate_juno.py`. File: `juno-brass-1.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Mixer | Osc Balance | -100.0 % | 0 |
| 2 | Filters | Filter Balance | -64 | 0 |
| 3 | Filter 1 | Cutoff | 5 | 5 |
| 4 | Filter 1 | Filter1 Resonance | 6 | 6 |
| 5 | Filter 1 | Filter1 Env Amt | 72.7 % | 93 |
| 6 | Filter 1 | Filter1 Keyfollow | +51 | 115 |
| 7 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 8 | Filter Env | Filter Env Attack | 12 | 12 |
| 9 | Filter Env | Filter Env Decay | 82 | 82 |
| 10 | Filter Env | Filter Env Sustain | 60.9 % | 78 |
| 11 | Filter Env | Filter Env Release | 18 | 18 |
| 12 | Amp Env | Amp Env Attack | 56 | 56 |
| 13 | Amp Env | Amp Env Decay | 67 | 67 |
| 14 | Amp Env | Amp Env Sustain | 66.4 % | 85 |
| 15 | Amp Env | Amp Env Release | 22 | 22 |
| 16 | EQ | LowEQ Gain | +6 dB | 88 |
| 17 | EQ | HighEQ Gain | +2.75 dB | 75 |
| 18 | Other | deprecated_112_103 | Vintage | 2 |
| 19 | Other | Chorus Rate | 17 | 17 |
| 20 | Other | Chorus Depth | 67.2 % | 86 |
| 21 | Other | Chorus Delay | 64 | 64 |
| 22 | Other | Lfo3 Rate | 88 | 88 |
| 23 | Other | Osc Lfo3 Amount | 14.8 % | 19 |
| 24 | Other | Lfo3 Fade-In Time | 60 | 60 |
| 25 | Other | Assign1 Source | 0 | 0 |
| 26 | Other | Assign1 Amount | Off | 64 |

Everything else stays at INIT.

## Translation notes

- vibrato 3.5 c at 3.20 Hz -> LFO 3 amount 19

## Variant changes (not yet heard)

- Filter1 Env Amt 85 -> 93 (phrase fit)
- Filter1 Keyfollow 107 -> 115 (phrase fit)
- HighEQ Gain 64 -> 75 (phrase fit)
- LowEQ Gain 64 -> 88 (phrase fit)

## How close it is

- Amp envelope level-shape error 1.3 dB; filter band-shape error 4.3 dB.
- Cutoff trimmed 0 → 5 so the held note (attack and sustain medians) matches the Juno's brightness (gap +0.24 semitones).
- Listening file: `renders/juno-brass-1/listen/demo_AB.wav` (the Juno first, then Virus, loudness-matched).
- Chosen by ear over the first translation (renders/dropped/juno-v1/), 2026-10-27.
