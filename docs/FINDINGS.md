# Findings

Running log of what we've learned about the Virus TI, the emulators and the
tooling, so a new session doesn't have to rediscover it. Newest sections are
added at the bottom; each entry says how it was established
(**measured**, **verified**, **inferred**, or **from source**).

---

## SysEx and patch format

- **Single Dump = 524 bytes** (from source, Gearmulator `createSingleDump`):
  `F0 00 20 33 01 <dev> 10 <bank> <prog>` + preset bytes `0..255` + checksum +
  preset bytes `256..511` + checksum + `F7`.
  - Each checksum = sum of all bytes from `<dev>` up to (not including) it, `& 0x7F`.
    The second checksum covers the first one too.
  - The redconfetti doc only describes the final checksum. Messages with a wrong
    middle checksum may be rejected or mis-parsed; `virusRender` fixes both.
- **Parameter address** (from source, verified): page `0x70`/`0x71`/`0x6E`/`0x6F`
  index `i` → preset byte `page_order * 128 + i` (page order A, B, 6E, 6F).
  `tools/virus_patch.py` does this from Gearmulator's
  `parameterDescriptions_TI.json` (563 named params; several names alias the
  same byte depending on oscillator/FX mode).
- **redconfetti "Dump offset" column looks 1 lower than Gearmulator's layout**
  (inferred). E.g. Osc 1 Shape = page A idx `0x11` → message byte `0x1A`, doc
  says `0x19`. Use the doc's live-edit page/param pairs, not its byte offsets.
- **Patch name** = preset bytes 240–249 (page `0x71` idx 112–121), ASCII,
  space padded (verified: reads back `-INIT-` and generated names).
- **Send target**: bank `00` + program `0x40` = Single-mode edit buffer.
  Device ID `0x10` = omni.

## Firmware and ROM

- The firmware the emulator needs is `firmware.bin` (8,569,757 bytes) inside
  *Virus TI Software Suite 5.1.7.00.pkg* →
  `Core_components.pkg/Payload/Library/Application Support/Access Music/Virus TI/Common/`.
  Extract with `pkgutil --expand-full`; no install needed. SHA-256
  `8e3daea8…5cd6a`. Kept in `rom/` (git-ignored).
- ROM `-INIT-` is single index **127** (bank 0, prog 127). Factory Oberheim-ish
  singles: `OberBrssMS` (210), `Ld-OB 82 @` (450). Full list: `renders/rom-singles.txt`.
- **ROM singles are stored in an older format (version byte `08`)**; the
  firmware upgrades them to TI format (`0C`) on load, filling TI-only pages with
  defaults (verified via `--dump-out`). `patches/reference/init-ti.syx` is the
  upgraded INIT and is the template for generated patches. Upgraded patches
  round-trip byte-identical.

## Emulator behaviour

- **Virus renders are bit-identical across runs** (verified), including 12
  renders in parallel — *after* the timing fix below. Any audio change is
  caused by the patch.
- **Timing bug, fixed 2026-10-24**: the first `virusRender` triggered notes when
  the main thread's frame counter crossed a threshold. The DSP thread runs
  ahead of the main thread by a load-dependent amount, so under parallel load
  note-on moved by a few ms. Fit scores before the fix carry that noise (and an
  apparent "saturation helps" result was noise). Now all events are scheduled
  on the DSP thread by ESAI callback count, and recording uses absolute output
  frames. **One ESAI callback = one output frame** (verified: 199,552 callbacks
  vs 199,488 frames read, one block apart). Note onset is a constant 4.6 ms
  after the recording starts (MIDI processing).
- **OB-Xf renders are not repeatable, even with all slop params at 0**
  (verified): it always adds noise to filter cutoff and starts oscillators at
  random phase. Average several renders for targets.
- Both run at 44.1 kHz. `virusRender` and `obxf_render.py` WAVs both start at
  note-on.

## Virus control behaviour (measured unless noted)

### Oscillators
- `Osc1/2 Shape` 64 = sawtooth (INIT default; from param table: 0 = wave,
  64 = saw, 127 = pulse).
- **`Osc2 Detune` is very non-linear** — almost nothing below ~20:

  | value | cents |  | value | cents |
  |------:|------:|--|------:|------:|
  | 0–8   | ≈0    |  | 32    | +2.5  |
  | 16    | +0.4  |  | 48    | +5.2  |
  | 24    | +1.5  |  | 64    | +7.9  |

  (osc 2 soloed via `Osc Balance` 127, A4, FFT pitch vs osc 1.)
- `Transpose` (page A 93): 64 = 0, 1 step = 1 semitone (52 → exactly an octave down).

### Filters
- **INIT routing trap**: INIT is `Filter Routing` Serial 4 with
  `Filter Balance` 64, so audio also passes through filter 2. Filter 2's cutoff
  follows filter 1 (`Filter2 Cutoff Link` on) but has **no envelope**
  (`Filter2 Env Amt` 0), so it stays closed while filter 1 sweeps. For a
  single-filter (OB-style) voice set **`Filter Balance` 0** (filter 1 only).
  Verified: brightness-fit error dropped from 0.84 to 0.41 octaves.
- **With Filter 1 in an Analog mode, `Filter Balance` picks which filters you
  hear** (measured, single note, filter 2 unlinked): **0 = filter 1 only,
  64 = filter 1 → filter 2 in series** (identical to filter 1 alone when
  filter 2 is LP at cutoff 127), **127 = filter 2 only** (filter 1 bypassed: HP
  at 127 went near-silent). `Filter Routing` Serial 4 vs Serial 6 made no
  difference with an Analog filter 1 (outputs identical).
- A fixed filter-2 low-pass after the analog filter ("tone control", balance
  64, unlinked) did not help match OB-Xf: the Virus's extra top end changes
  over the note, so a fixed LP either does nothing (cutoff2 ≥ 112) or dulls
  everything.
- `Filter1 Mode` values: 0 LP, 1 HP, 2 BP, 3 BS, 4–7 Analog 1–4 pole.
  Analog 4 pole (7) is the OB-Xa / CEM3320 analogue.
- Analog 4 pole with `Cutoff` 127 is **not fully open**: sustained-chord
  spectral centroid ≈2 kHz vs ≈3.7 kHz for OB-Xf wide open.
- **Virus Analog 4 pole rolls off less steeply than OB-Xf's 4-pole** (measured,
  harmonic spectra of a single note, `renders/obright/harmonics-v2.png`): at
  0.4 s the Virus had ~10 dB more energy at 3–9 kHz with brightness centroid
  matched. Later in the note OB-Xf shows a flat harmonic plateau up to ~1.5 kHz
  then a sharp knee; the Virus slopes off gradually. The user heard this as
  "brighter, not as much OB filter sound". Spectral centroid can't see it —
  use band shapes (`render_lib.band_shape`).
- Analog 4 pole **loses ~8 dB as it closes** to a brass-sustain cutoff, where
  OB-Xf's 4-pole stays roughly level. Brightness can match while loudness
  dips; compensate with `Patch Volume` / saturation (not yet solved).

### Saturation / drive
- **`Saturation Curve` (page A 49) does nothing on the TI** (measured: output
  bit-identical with curve Off vs Soft vs Light at any `Osc Mainvolume`).
  Matches redconfetti's note that the TI Saturation menu only has Osc Volume.
- `Osc Mainvolume` above 64 drives the oscillators harder into the filter:
  96 → centroid +3%, 127 → +9% (and peak level drops ~2 dB).

### Envelopes
- **Virus filter envelope decays at a different shape than OB-Xf's** (measured):
  matching where the sweep ends left the Virus 4–8 semitones brighter for the
  first second. **`Filter Env Sustain Time` below 64 (sustain keeps falling)
  fixes most of it**: 56 cut the 0.3–1 s gap to about +2 semitones.
  `Sustain Time` 64 = flat sustain; lower falls, higher rises.
- Not directly calibrated yet. Fitted values swing a lot between runs for
  short times (amp attack came out 4, 19, 27, 28 across fits), so short
  attack values are poorly constrained by the level-shape metric.
- `Filter Env Release` fitted to ~2 for Obright: the fit only sees the
  release while the target is above −45 dB, so treat very short fitted
  releases with suspicion.

## OB-Xf notes

- Param scaling (from source, `SynthEngine.h`): env times
  `logsc(v, min, 60000 ms, rolloff 900)` with min 4 ms (amp A/D), 8 ms (amp R),
  1 ms (filter env); `Osc2Detune` = `logsc(v, 0.001, 0.6)` semitones;
  `FilterCutoff` = `v * 120` and `FilterEnvAmount` = `v * 140` in semitone-like
  units; cutoff Hz = `440 * 2^(index/12)` after `-45` offset and keytrack.
  `logsc(p,lo,hi,r) = ((exp(p*ln(r+1))-1)/r)*(hi-lo)+lo`.
- **"Obright Original" sounds an octave below the key played** (`Transpose`
  0.249 ≈ −12; OB-Xd import compensation). Matching Virus patch needs
  `Transpose` 52.
- `obxf_render.py --params` dumps 104 params; slop params:
  `EnvelopeSlop`, `FilterSlop`, `LevelSlop`, `PortamentoSlop`.

## Build gotchas

- Gearmulator: build our tool by injecting it with
  `-DCMAKE_PROJECT_gearmulator_INCLUDE=tools/gearmulator-inject.cmake`.
  `cmake_language(DEFER … add_subdirectory)` is not allowed; a plain
  `add_subdirectory` works because link targets resolve at generate time.
  Qualify `virusLib::Device` (ambiguous with `synthLib::Device`).
- OB-Xf: **configure from inside `third_party/obxf`** — its version stamp runs
  `git rev-parse HEAD` in CMake's working directory and fails inside a repo with
  no commits. Python bindings need
  `tools/third_party_patches/obxf-python-matrix-target.patch` (bindings lag an
  engine type change).
- Gearmulator's `parameterDescriptions_TI.json` is loose JSON (trailing commas,
  one single-quoted string); parse only the `parameterdescriptions` array.

## Fitting method (what works)

1. Fixed voice structure translated by hand from the OB-Xf patch.
2. Amp envelope fitted to the **level envelope** with both filters wide open.
3. Filter fitted to **spectral centroid over time** (octaves, gated to where the
   target is above −45 dB) plus a small level-shape term.
4. Coordinate search, ±step per param rendered in parallel (~1 s per batch).
   A two-stage fit takes ~3 minutes.
5. Always plot (`renders/*/fit.png`) — routing/octave mistakes show up as
   flat or offset curves that no parameter tweak can fix.
6. **Fit the filter over the same examples used for listening** (single note,
   fifth, chord), not one chord. Fitting one low chord passed the metric but
   the user heard every listening example as "a touch brighter"; the error was
   concentrated in the first second.
7. Check brightness per time window (0–0.3 s, 0.3–1 s, 1–2 s), not only the
   overall loss: an average can hide a bright attack.

## Listening feedback log

- Obright v1: "Virus are all a touch brighter" → measured +4–8 semitones in
  the first second → v2 fit over all examples with `Filter Env Sustain Time`
  free.
- Obright v2: "Still bright. Doesn't have as much of the OB filter sound,
  maybe resonance?" → harmonic spectra showed a shallower slope and no
  plateau/knee → v3 fits third-octave band shapes with resonance, filter mode,
  routing and filter 2 free.
- v3 work: each filter structure fitted separately on band shape (fixed
  renderer). Analog 4 pole + filter 1 only won (4.49 dB) over Analog 3 pole
  (4.71) and analog 4 + enveloped filter 2 (4.76, but scored with the wrong
  balance assumption). Best fit added resonance 14. **Resonance raises the
  spectral centroid**, so more resonance alone measures (and likely sounds)
  brighter; pair it with lower cutoff. Sent two variants for listening:
  `obright-dark` (res 14, cutoff 40) and `obright-res` (res 30, cutoff 36),
  same brightness, attack within 0.5 semitone of OB-Xf, middle 2–5 semitones
  darker.
- Band-shape and centroid metrics can disagree; the user's ears decide.
- Obright v3: user picked **dark over res** ("dark is closer, maybe a touch of
  res"). Made `obright-r20` (res 20, cutoff 39) and `obright-r24` (res 24,
  cutoff 38), cutoff chosen by measurement to hold dark's brightness within
  ~0.25 semitone. **Rule of thumb on this patch: +6 resonance ≈ −1 cutoff for
  equal brightness** (14→20: 40→39; 14→24: 40→38; 14→30: ~40→36).
- Obright final: user said **"less res than 20, just go back to dark"** →
  `obright.syx` = resonance 14, cutoff 40. On this patch the OB character
  came from the filter slope and envelope shape more than from resonance;
  resonance above ~14 moved it away from the OB.

## Open questions / next steps

- Calibrate envelope value → time and cutoff value → Hz curves directly
  (sweep renders), so translations start close instead of relying on the fit.
- Level drop of the Virus analog filter at low cutoff (see Filters).
- Confirm on hardware that renders match the real TI2 (send a `.syx`, record).
- Confirm the redconfetti offset discrepancy with a live-edit test.
