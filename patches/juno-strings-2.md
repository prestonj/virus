# 12 Strings 2 (Virus TI)

Translated from Jun-6 V (Juno-6/60)'s **"Vintage Factory/12 Strings 2"** by `tools/translate_juno.py`. File: `juno-strings-2.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Shape | Saw>Pulse 44 % | 92 |
| 2 | Osc 1 | Osc1 Pulsewidth | 19 | 19 |
| 3 | Mixer | Osc Balance | -100.0 % | 0 |
| 4 | Filters | Filter Balance | -64 | 0 |
| 5 | Filter 1 | Cutoff | 117 | 117 |
| 6 | Filter 1 | Filter1 Resonance | 8 | 8 |
| 7 | Filter 1 | Filter1 Keyfollow | +8 | 72 |
| 8 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 9 | Filter Env | Filter Env Attack | 57 | 57 |
| 10 | Filter Env | Filter Env Decay | 5 | 5 |
| 11 | Filter Env | Filter Env Sustain | 100.0 % | 127 |
| 12 | Filter Env | Filter Env Release | 45 | 45 |
| 13 | Amp Env | Amp Env Attack | 57 | 57 |
| 14 | Amp Env | Amp Env Decay | 1 | 1 |
| 15 | Amp Env | Amp Env Sustain | 80.5 % | 103 |
| 16 | Amp Env | Amp Env Release | 43 | 43 |
| 17 | EQ | LowEQ Gain | -4.5 dB | 46 |
| 18 | EQ | HighEQ Gain | +1.5 dB | 70 |
| 19 | Other | deprecated_112_103 | Vintage | 2 |
| 20 | Other | Chorus Rate | 38 | 38 |
| 21 | Other | Chorus Depth | 87.5 % | 112 |
| 22 | Other | Chorus Delay | 64 | 64 |
| 23 | Other | Lfo3 Rate | 77 | 77 |
| 24 | Other | Lfo3 Fade-In Time | 16 | 16 |
| 25 | Other | Assign1 Source | 0 | 0 |
| 26 | Other | Assign1 Amount | Off | 64 |
| 27 | Other | Assign2 Source | 23 | 23 |
| 28 | Other | Assign2 Destination1 | 7 | 7 |
| 29 | Other | Assign2 Amount1 | +57 | 121 |

Everything else stays at INIT.

## Translation notes

- PWM from LFO: duty 0.36-0.49

## Variant changes (not yet heard)

- Chorus Depth 86 -> 112 (by ear)
- Filter1 Keyfollow 64 -> 72 (phrase fit)
- HighEQ Gain 64 -> 70 (phrase fit)
- LowEQ Gain 64 -> 46 (phrase fit)

## How close it is

- Amp envelope level-shape error 1.66 dB; filter band-shape error 3.06 dB.
- Cutoff trimmed 118 → 117 so the held note (attack and sustain medians) matches the Juno's brightness (gap -0.08 semitones).
- Listening file: `renders/juno-strings-2/listen/demo_AB.wav` (the Juno first, then Virus, loudness-matched).
- Chosen by ear over the first translation (renders/dropped/juno-v1/), 2026-10-27.
