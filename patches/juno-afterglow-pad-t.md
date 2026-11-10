# Afterglow Pad (Virus TI)

Translated from Jun-6 V (Juno-6/60)'s **"Factory/Afterglow Pad"** by `tools/translate_juno.py`. File: `juno-afterglow-pad-t.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Shape | Pulse | 127 |
| 2 | Osc 1 | Osc1 Pulsewidth | 2 | 2 |
| 3 | Osc 2 | Osc2 Shape | Pulse | 127 |
| 4 | Osc 2 | Osc2 Semitone | -12 | 52 |
| 5 | Osc 2 | Osc2 Detune | 0 | 0 |
| 6 | Mixer | Osc Balance | -98.4 % | 1 |
| 7 | Mixer | Osc Mainvolume | -2 | 62 |
| 8 | Mixer | Noise Volume | 13 | 13 |
| 9 | Mixer | Noise Color | -8 | 56 |
| 10 | Filters | Filter Balance | -64 | 0 |
| 11 | Filter 1 | Cutoff | 35 | 35 |
| 12 | Filter 1 | Filter1 Env Amt | 40.6 % | 52 |
| 13 | Filter 1 | Filter1 Keyfollow | +39 | 103 |
| 14 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 15 | Filter 1 | Filter1 Env Polarity | Negative | 0 |
| 16 | Filter Env | Filter Env Attack | 69 | 69 |
| 17 | Filter Env | Filter Env Decay | 22 | 22 |
| 18 | Filter Env | Filter Env Sustain | 72.7 % | 93 |
| 19 | Filter Env | Filter Env Release | 91 | 91 |
| 20 | Amp Env | Amp Env Attack | 89 | 89 |
| 21 | Amp Env | Amp Env Decay | 108 | 108 |
| 22 | Amp Env | Amp Env Sustain | 74.2 % | 95 |
| 23 | Amp Env | Amp Env Release | 89 | 89 |
| 24 | Envelope 3 | Envelope 3/Attack | 104 | 104 |
| 25 | Envelope 3 | Envelope 3/Decay | 62 | 62 |
| 26 | Envelope 3 | Envelope 3/Sustain | 27.3 % | 35 |
| 27 | Envelope 3 | Envelope 3/Release | 109 | 109 |
| 28 | LFO 1 | Lfo1 Rate | 39 | 39 |
| 29 | LFO 1 | Lfo1 Shape | Sine | 0 |
| 30 | LFO 1 | Lfo1 Mode | Mono | 1 |
| 31 | LFO 1 | LFO1 Assign Dest | Delay Feedback | 69 |
| 32 | LFO 1 | LFO1 Assign Amount | +37.5 % | 88 |
| 33 | LFO 3 | Lfo3 Rate | 86 | 86 |
| 34 | LFO 3 | Osc Lfo3 Amount | 28.1 % | 36 |
| 35 | LFO 3 | Lfo3 Fade-In Time | 49 | 49 |
| 36 | Mod Matrix | Assign1 Source | Off | 0 |
| 37 | Mod Matrix | Assign1 Amount | Off | 64 |
| 38 | Mod Matrix | Assign 4 Source | Envelope 3 | 38 |
| 39 | Mod Matrix | Assign 4 Destination | Noise Volume | 23 |
| 40 | Mod Matrix | Assign 4 Amount | +63 | 127 |
| 41 | Mod Matrix | Assign 5 Source | Velocity On | 24 |
| 42 | Mod Matrix | Assign 5 Destination | Filter 1 Cutoff | 24 |
| 43 | Mod Matrix | Assign 5 Amount | +9 | 73 |
| 44 | Mod Matrix | Assign 6 Destination | Filter 1 Resonance | 26 |
| 45 | Mod Matrix | Assign 6 Amount | +54 | 118 |
| 46 | EQ | LowEQ Gain | -6 dB | 40 |
| 47 | EQ | HighEQ Gain | +1 dB | 68 |
| 48 | Delay | Delay Mode | Ping Pong 8:7 | 5 |
| 49 | Delay | Delay Send | -0.75dB | 93 |
| 50 | Delay | Delay Time | 365.9 ms | 67 |
| 51 | Delay | Delay Feedback | 46.9 % | 60 |
| 52 | Delay | Dly Depth  | 0 % | 0 |

Everything else stays at INIT.

## Translation notes

- noise -30.9 dB re saw -> Noise Volume 13
- LFO delay mode Rise treated as delay + rise
- vibrato 11.0 c at 2.90 Hz -> LFO 3 amount 36
- portamento 31 ms not translated
- Env 2 -> DCO Noise Vol +1.00 -> Envelope 3 -> matrix slot 4
- LFO 2 (Sine, 0.33 Hz) -> delay feedback +0.38 -> LFO 1 assign (not calibrated)
- AfterTouch -> HPF Freq +0.12 not translated
- velocity -> VCF +0.14 -> matrix slot 5 (fitted)
- mod wheel -> VCF resonance +0.86 -> matrix slot 6 (not calibrated)
- delay 364 ms, feedback 0.35, wet 0.51, right/left 1.13 -> Delay Time 67, Feedback 44, Send 93, mode 5 (right echoes at 1/1.14 of the time)
- Env 2 -> noise: no swell in the Jun-6 V render (2.3 dB), Envelope 3 kept from the tables
- velocity -> VCF: no response in the Jun-6 V render (-0.08 oct), amount kept as mapped

## Variant changes (not yet heard)

- Amp Env Release 90 -> 89 (phrase fit)
- Delay Feedback 44 -> 60 (phrase fit)
- Envelope 3/Release 101 -> 109 (phrase fit)
- Filter Env Attack 61 -> 69 (phrase fit)
- Filter Env Decay 30 -> 22 (phrase fit)
- Filter1 Env Amt 50 -> 52 (phrase fit)
- Filter1 Keyfollow 95 -> 103 (phrase fit)
- HighEQ Gain 64 -> 68 (phrase fit)
- LowEQ Gain 64 -> 40 (phrase fit)
- Noise Color 64 -> 56 (phrase fit)
- Osc Balance 7 -> 1 (phrase fit)
- Osc Mainvolume 64 -> 62 (phrase fit)

## How close it is

- Amp envelope level-shape error 1.54 dB; filter band-shape error 2.66 dB.
- Cutoff trimmed 40 → 35 so the held note (attack and sustain medians) matches the Juno's brightness (gap +0.78 semitones).
- Demo phrase (effects on): error 7.97 → 3.59 dB after the phrase fit (spectrum + loudness over time).
- Listening file:`renders/juno-afterglow-pad-t/listen/demo_AB.wav` (the Juno first, then Virus, loudness-matched).
- Not yet checked by ear.
