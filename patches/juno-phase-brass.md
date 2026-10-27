# 18 Phase Brass (Virus TI)

Translated from Jun-6 V (Juno-6/60)'s **"Vintage Factory/18 Phase Brass"** by `tools/translate_juno.py`. File: `juno-phase-brass.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Shape | Saw>Pulse 44 % | 92 |
| 2 | Osc 1 | Osc1 Pulsewidth | 2 | 2 |
| 3 | Mixer | Osc Balance | -100.0 % | 0 |
| 4 | Mixer | Osc Mainvolume | -5 | 59 |
| 5 | Filters | Filter Balance | -64 | 0 |
| 6 | Filter 1 | Cutoff | 3 | 3 |
| 7 | Filter 1 | Filter1 Env Amt | 71.1 % | 91 |
| 8 | Filter 1 | Filter1 Keyfollow | +63 | 127 |
| 9 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 10 | Filter Env | Filter Env Attack | 8 | 8 |
| 11 | Filter Env | Filter Env Decay | 62 | 62 |
| 12 | Filter Env | Filter Env Sustain | 37.5 % | 48 |
| 13 | Filter Env | Filter Env Release | 31 | 31 |
| 14 | Amp Env | Amp Env Release | 0 | 0 |
| 15 | EQ | LowEQ Gain | -6 dB | 40 |
| 16 | EQ | HighEQ Gain | +0.75 dB | 67 |
| 17 | Other | deprecated_112_103 | Vintage | 2 |
| 18 | Other | Chorus Rate | 17 | 17 |
| 19 | Other | Chorus Depth | 67.2 % | 86 |
| 20 | Other | Chorus Delay | 64 | 64 |
| 21 | Other | Assign1 Source | 0 | 0 |
| 22 | Other | Assign1 Amount | Off | 64 |

Everything else stays at INIT.

## Translation notes

- VCA gate

## Variant changes (not yet heard)

- Filter1 Env Amt 83 -> 91 (phrase fit)
- HighEQ Gain 64 -> 67 (phrase fit)
- LowEQ Gain 64 -> 40 (phrase fit)
- Osc Mainvolume 64 -> 59 (phrase fit)

## How close it is

- Gate VCA (no amp fit); filter band-shape error 2.39 dB.
- Cutoff trimmed 0 → 3 so the held note (attack and sustain medians) matches the Juno's brightness (gap +0.14 semitones).
- Listening file: `renders/juno-phase-brass/listen/demo_AB.wav` (the Juno first, then Virus, loudness-matched).
- Chosen by ear over the first translation (renders/dropped/juno-v1/), 2026-10-27.
