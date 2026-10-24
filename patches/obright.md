# Obright TI

Virus TI translation of OB-Xf's **"Obright Original"**, an OB-Xa style
polybrass. File: **`obright.syx`** (rebuild with `.venv/bin/python patches/obright.py`).
Chosen by ear from several variants; see "Variants tried" below.

## Changes from INIT

Start from the TI's `-INIT-` single. Raw values are 0–127 as stored. "Display"
is how bipolar values show on the panel (raw − 64). Percent displays may round
differently on the hardware.

| # | Section | Parameter | Raw | Display | Why |
|---|---|---|---:|---|---|
| 1 | Common | Transpose | 52 | −12 | the reference sounds an octave below the key played |
| 2 | Osc 2 | Detune | 48 | 48 | measured +5.2 cents: the slow OB beating |
| 3 | Mixer | Osc Balance | 55 | −9 | osc 2 a little quieter than osc 1 |
| 4 | Filters | Filter Balance | 0 | −64 (Filter 1 only) | one filter, as on the OB-Xa |
| 5 | Filter 1 | Mode | 7 | Analog 4 Pole | 24 dB/oct |
| 6 | Filter 1 | Cutoff | 40 | 40 | |
| 7 | Filter 1 | Resonance | 14 | 14 | a little emphasis at the knee |
| 8 | Filter 1 | Env Amount | 91 | 91 (≈72%) | |
| 9 | Filter 1 | Keyfollow | 90 | +26 | |
| 10 | Filter Env | Attack | 16 | 16 | |
| 11 | Filter Env | Decay | 95 | 95 | |
| 12 | Filter Env | Sustain | 11 | 11 (≈9%) | |
| 13 | Filter Env | Sustain Time | 56 | −8 (falling) | filter keeps closing slowly through the sustain |
| 14 | Filter Env | Release | 19 | 19 | |
| 15 | Amp Env | Attack | 16 | 16 | |
| 16 | Amp Env | Decay | 83 | 83 | |
| 17 | Amp Env | Sustain | 98 | 98 (≈77%) | |
| 18 | Amp Env | Release | 37 | 37 | |
| 19 | Velocity Map | Flt 1 Env Amt | 44 | −20 | softer notes are darker |

Leave everything else at INIT: both oscillators on Classic saw (Shape 64),
Filter Routing Serial 4, chorus/delay/reverb off.

## Variants tried

All identical except resonance and cutoff (cutoff measured to hold the same
brightness). The user picked **resonance 14** and wanted less than 20.

| Resonance | Cutoff | Verdict |
|---:|---:|---|
| **14** | **40** | **chosen** ("dark") |
| 20 | 39 | too much resonance |
| 24 | 38 | — |
| 30 | 36 | further from the OB than dark |

The files are in `renders/obright/variants/` (not tracked).

## How close it is

- The attack matches OB-Xf within half a semitone of brightness; the middle
  of the note is 2–5 semitones darker.
- **Known gaps:** the Virus gets about 8 dB quieter as the filter closes,
  where OB-Xf stays level. Its analog filter also rolls off less steeply
  above the cutoff.
- Listening files: `renders/obright/listen-final/*_AB_dark.wav` (OB-Xf
  first, then Virus, loudness-matched).
