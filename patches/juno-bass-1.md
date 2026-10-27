# 31 Bass 1 (Virus TI)

Translated from Jun-6 V (Juno-6/60)'s **"Vintage Factory/31 Bass 1"** by `tools/translate_juno.py`. File: `juno-bass-1.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Shape | Saw>Pulse 44 % | 92 |
| 2 | Osc 1 | Osc1 Pulsewidth | 49 | 49 |
| 3 | Osc 2 | Osc2 Shape | Pulse | 127 |
| 4 | Osc 2 | Osc2 Semitone | -12 | 52 |
| 5 | Osc 2 | Osc2 Detune | 0 | 0 |
| 6 | Mixer | Osc Balance | -85.9 % | 9 |
| 7 | Mixer | Osc Mainvolume | -7 | 57 |
| 8 | Filters | Filter Balance | -64 | 0 |
| 9 | Filter 1 | Cutoff | 22 | 22 |
| 10 | Filter 1 | Filter1 Env Amt | 46.9 % | 60 |
| 11 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 12 | Filter Env | Filter Env Decay | 55 | 55 |
| 13 | Filter Env | Filter Env Sustain | 20.3 % | 26 |
| 14 | Filter Env | Filter Env Release | 31 | 31 |
| 15 | Amp Env | Amp Env Release | 0 | 0 |
| 16 | EQ | LowEQ Gain | -5 dB | 44 |
| 17 | EQ | HighEQ Gain | -6 dB | 40 |
| 18 | Other | deprecated_112_103 | Vintage | 2 |
| 19 | Other | Chorus Rate | 17 | 17 |
| 20 | Other | Chorus Depth | 67.2 % | 86 |
| 21 | Other | Chorus Delay | 64 | 64 |
| 22 | Other | Assign1 Source | 0 | 0 |
| 23 | Other | Assign1 Amount | Off | 64 |

Everything else stays at INIT.

## Translation notes

- VCA gate

## Variant changes (not yet heard)

- Cutoff 14 -> 22 (phrase fit)
- Filter1 Env Amt 61 -> 60 (phrase fit)
- Filter1 Keyfollow 70 -> 64 (phrase fit)
- HighEQ Gain 64 -> 40 (phrase fit)
- LowEQ Gain 64 -> 44 (phrase fit)
- Osc Balance 8 -> 9 (phrase fit)
- Osc Mainvolume 64 -> 57 (phrase fit)

## How close it is

- Gate VCA (no amp fit); filter band-shape error 5.39 dB.
- Cutoff trimmed 19 → 14 so the held note (attack and sustain medians) matches the Juno's brightness (gap +0.04 semitones).
- Listening file: `renders/juno-bass-1/listen/demo_AB.wav` (the Juno first, then Virus, loudness-matched).
- Chosen by ear over the first translation (renders/dropped/juno-v1/), 2026-10-27.
