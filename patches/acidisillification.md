# Acidisillification (Virus TI)

Translated from OB-Xf's **"Acidisillification"** by `tools/translate.py`. File: `acidisillification.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Common | Unison Mode | 3 | 2 |
| 2 | Common | Unison Detune | 33 | 33 |
| 3 | Common | Key Mode | Mono 1 | 1 |
| 4 | Osc 1 | Osc1 Shape | Spectral Wave | 0 |
| 5 | Osc 1 | Osc1 Wave Select | Triangle | 1 |
| 6 | Osc 2 | Osc2 Shape | Pulse | 127 |
| 7 | Osc 2 | Osc2 Semitone | -5 | 59 |
| 8 | Osc 2 | Osc2 Detune | 116 | 116 |
| 9 | Osc 2 | Osc2 FM Amount | 11.7 % | 15 |
| 10 | Osc 2 | Osc2 Sync | On | 1 |
| 11 | Osc 2 | Osc2 Lfo1 Amount | +100.0 % | 127 |
| 12 | Mixer | Osc Balance | -21.9 % | 50 |
| 13 | Filters | Filter Balance | -64 | 0 |
| 14 | Filter 1 | Cutoff | 50 | 50 |
| 15 | Filter 1 | Filter1 Resonance | 8 | 8 |
| 16 | Filter 1 | Filter1 Env Amt | 100.0 % | 127 |
| 17 | Filter 1 | Filter1 Keyfollow | +1 | 65 |
| 18 | Filter 1 | Filter1 Mode | Analog 2 Pole | 5 |
| 19 | Filter Env | Filter Env Attack | 25 | 25 |
| 20 | Filter Env | Filter Env Decay | 22 | 22 |
| 21 | Filter Env | Filter Env Sustain Time | +2 | 66 |
| 22 | Filter Env | Filter Env Release | 30 | 30 |
| 23 | Amp Env | Amp Env Attack | 25 | 25 |
| 24 | Amp Env | Amp Env Decay | 43 | 43 |
| 25 | Amp Env | Amp Env Sustain | 0 % | 0 |
| 26 | Amp Env | Amp Env Release | 50 | 50 |
| 27 | LFO 1 | Lfo1 Rate | 67 | 67 |
| 28 | LFO 1 | Lfo1 Shape | Sine | 0 |
| 29 | Velocity Map | Flt1 EnvAmt Velocity | -35.9 % | 41 |
| 30 | Velocity Map | Amp Velocity | +28.1 % | 82 |
| 31 | Other | Ringmodulator Volume | 17 | 17 |
| 32 | Other | Osc FM Mode | Wave | 2 |

Everything else stays at INIT.

## Translation notes

- osc1: triangle
- osc2: pulse, duty 0.500
- ring mod -25.5 dB re louder osc -> Ringmodulator Volume 17, Osc Mainvolume 64
- osc2 detune 0.1 cents
- cross-mod +/-5.5 st -> Virus FM 15, osc 2 raised +0.29 st
- unison 3 voices (Virus 3), OB-Xf spread +/-4 c random -> even width 6 c
- OB-Xf LFO2 1.26 Hz, +/-6000.0 c on osc1 +0 / osc2 +1 -> Virus LFO1
- LFO2 waveform [0.5, 1.0, 0.54] not translated (sine used)

## How close it is

- Amp envelope level-shape error 0.5 dB; filter band-shape error 11.62 dB (Obright final was 4.49 dB).
- Cutoff trimmed 46 → 50 so the held note (attack and sustain medians) matches OB-Xf's brightness (gap -0.03 semitones).
- Listening files: `renders/acidisillification/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 2.0 s hold, 1.5 s tail).
- Not yet checked by ear.
