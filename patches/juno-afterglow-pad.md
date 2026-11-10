# Afterglow Pad (Virus TI)

Translated from Jun-6 V (Juno-6/60)'s **"Factory/Afterglow Pad"** by `tools/translate_juno.py`. File: `juno-afterglow-pad.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Osc 1 | Osc1 Shape | Pulse | 127 |
| 2 | Osc 1 | Osc1 Pulsewidth | 2 | 2 |
| 3 | Osc 2 | Osc2 Shape | Pulse | 127 |
| 4 | Osc 2 | Osc2 Semitone | -12 | 52 |
| 5 | Osc 2 | Osc2 Detune | 0 | 0 |
| 6 | Mixer | Osc Balance | -89.1 % | 7 |
| 7 | Mixer | Noise Volume | 13 | 13 |
| 8 | Filters | Filter Balance | -64 | 0 |
| 9 | Filter 1 | Cutoff | 35 | 35 |
| 10 | Filter 1 | Filter1 Env Amt | 39.0 % | 50 |
| 11 | Filter 1 | Filter1 Keyfollow | +31 | 95 |
| 12 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 13 | Filter 1 | Filter1 Env Polarity | Negative | 0 |
| 14 | Filter Env | Filter Env Attack | 61 | 61 |
| 15 | Filter Env | Filter Env Decay | 30 | 30 |
| 16 | Filter Env | Filter Env Sustain | 72.7 % | 93 |
| 17 | Filter Env | Filter Env Release | 91 | 91 |
| 18 | Amp Env | Amp Env Attack | 89 | 89 |
| 19 | Amp Env | Amp Env Decay | 108 | 108 |
| 20 | Amp Env | Amp Env Sustain | 74.2 % | 95 |
| 21 | Amp Env | Amp Env Release | 90 | 90 |
| 22 | Envelope 3 | Envelope 3/Attack | 104 | 104 |
| 23 | Envelope 3 | Envelope 3/Decay | 62 | 62 |
| 24 | Envelope 3 | Envelope 3/Sustain | 27.3 % | 35 |
| 25 | Envelope 3 | Envelope 3/Release | 101 | 101 |
| 26 | LFO 1 | Lfo1 Rate | 39 | 39 |
| 27 | LFO 1 | Lfo1 Shape | Sine | 0 |
| 28 | LFO 1 | Lfo1 Mode | Mono | 1 |
| 29 | LFO 1 | LFO1 Assign Dest | Delay Feedback | 69 |
| 30 | LFO 1 | LFO1 Assign Amount | +37.5 % | 88 |
| 31 | LFO 3 | Lfo3 Rate | 86 | 86 |
| 32 | LFO 3 | Osc Lfo3 Amount | 28.1 % | 36 |
| 33 | LFO 3 | Lfo3 Fade-In Time | 49 | 49 |
| 34 | Mod Matrix | Assign1 Source | Off | 0 |
| 35 | Mod Matrix | Assign1 Amount | Off | 64 |
| 36 | Mod Matrix | Assign 4 Source | Envelope 3 | 38 |
| 37 | Mod Matrix | Assign 4 Destination | Noise Volume | 23 |
| 38 | Mod Matrix | Assign 4 Amount | +63 | 127 |
| 39 | Mod Matrix | Assign 5 Source | Velocity On | 24 |
| 40 | Mod Matrix | Assign 5 Destination | Filter 1 Cutoff | 24 |
| 41 | Mod Matrix | Assign 5 Amount | +9 | 73 |
| 42 | Mod Matrix | Assign 6 Destination | Filter 1 Resonance | 26 |
| 43 | Mod Matrix | Assign 6 Amount | +54 | 118 |
| 44 | Delay | Delay Mode | Ping Pong 8:7 | 5 |
| 45 | Delay | Delay Send | -0.75dB | 93 |
| 46 | Delay | Delay Time | 365.9 ms | 67 |
| 47 | Delay | Delay Feedback | 34.4 % | 44 |
| 48 | Delay | Dly Depth  | 0 % | 0 |

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

## How close it is

- Amp envelope level-shape error 1.54 dB; filter band-shape error 2.66 dB.
- Cutoff trimmed 40 → 35 so the held note (attack and sustain medians) matches the Juno's brightness (gap +0.78 semitones).
- Listening file:`renders/juno-afterglow-pad/listen/demo_AB.wav` (the Juno first, then Virus, loudness-matched).
- Not yet checked by ear.
