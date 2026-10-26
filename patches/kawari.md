# Kawari (Virus TI)

Translated from OB-Xf's **"Kawari"** by `tools/translate.py`. File: `kawari.syx`.

## Changes from INIT

Start from the TI's `-INIT-` single. Panel = how the value shows on the TI (bipolar values are raw − 64); Raw = stored 0–127.

| # | Section | Parameter | Panel | Raw |
|---|---|---|---|---:|
| 1 | Common | Unison Mode | Twin | 1 |
| 2 | Common | Unison Detune | 57 | 57 |
| 3 | Common | Transpose | +12 | 76 |
| 4 | Common | Key Mode | Mono 1 | 1 |
| 5 | Osc 1 | Osc1 Shape | Spectral Wave | 0 |
| 6 | Osc 1 | Osc1 Wave Select | Triangle | 1 |
| 7 | Osc 1 | Osc1 Semitone | -12 | 52 |
| 8 | Osc 2 | Osc2 Shape | Pulse | 127 |
| 9 | Osc 2 | Osc2 Pulsewidth | 84 | 84 |
| 10 | Osc 2 | Osc2 Semitone | +12 | 76 |
| 11 | Osc 2 | Osc2 Detune | 127 | 127 |
| 12 | Osc 2 | Osc2 FM Amount | 14.1 % | 18 |
| 13 | Osc 2 | Osc2 Lfo1 Amount | -14.1 % | 55 |
| 14 | Mixer | Osc Balance | -10.9 % | 57 |
| 15 | Filters | Filter Balance | -64 | 0 |
| 16 | Filter 1 | Cutoff | 57 | 57 |
| 17 | Filter 1 | Filter1 Resonance | 23 | 23 |
| 18 | Filter 1 | Filter1 Env Amt | 87.5 % | 112 |
| 19 | Filter 1 | Filter1 Keyfollow | +22 | 86 |
| 20 | Filter 1 | Filter1 Mode | Analog 4 Pole | 7 |
| 21 | Filter Env | Filter Env Attack | 25 | 25 |
| 22 | Filter Env | Filter Env Decay | 77 | 77 |
| 23 | Filter Env | Filter Env Sustain Time | +16 | 80 |
| 24 | Filter Env | Filter Env Release | 68 | 68 |
| 25 | Amp Env | Amp Env Attack | 25 | 25 |
| 26 | Amp Env | Amp Env Decay | 85 | 85 |
| 27 | Amp Env | Amp Env Sustain | 0 % | 0 |
| 28 | Amp Env | Amp Env Release | 86 | 86 |
| 29 | LFO 1 | Lfo1 Rate | 85 | 85 |
| 30 | LFO 1 | Lfo1 Shape | Sine | 0 |
| 31 | Velocity Map | Flt1 EnvAmt Velocity | -46.9 % | 34 |
| 32 | Other | Ringmodulator Volume | 43 | 43 |
| 33 | Other | Osc FM Mode | Wave | 2 |

Everything else stays at INIT.

## Translation notes

- osc1: triangle
- osc2: pulse, duty 0.168
- ring mod -14.5 dB re louder osc -> Ringmodulator Volume 43, Osc Mainvolume 64
- osc2 detune 1.9 cents
- cross-mod +/-6.5 st -> Virus FM 18, osc 2 raised +0.41 st
- unison 2 voices (Virus 2), OB-Xf spread +/-12 c random -> even width 14 c
- OB-Xf LFO1 2.86 Hz, +/-12.3 c on osc1 +0 / osc2 -1 -> Virus LFO1
- EnvLegatoMode=1.00 not translated

## How close it is

- Amp envelope level-shape error 2.77 dB; filter band-shape error 10.32 dB (Obright final was 4.49 dB).
- Cutoff trimmed 50 → 57 so the held note (attack and sustain medians) matches OB-Xf's brightness (gap -0.11 semitones).
- Listening files: `renders/kawari/listen/*_AB.wav` (OB-Xf first, then Virus, loudness-matched; 2.0 s hold, 4.0 s tail).
- Not yet checked by ear.
