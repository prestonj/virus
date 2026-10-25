# Process and guidelines

How we make Oberheim-style Virus TI patches, and what the user wants from each
round. Read this and [FINDINGS.md](FINDINGS.md) before starting a new session.
FINDINGS records *facts* (measurements, quirks); this file records *how we work*.

## What the user wants

- **Goal:** Virus TI2 patches that sound like vintage Oberheims (OB-X, OB-Xa,
  SEM, OB-8). References come from OB-Xf factory patches (OB-Xd lineage).
- **Every patch gets listening files**: a **single note, a simple interval
  (fifth) and a chord**, each as OB-Xf first, then a short gap, then the Virus
  (`*_AB.wav`), plus each synth on its own. **Loudness-matched**, so differences
  are tone, not volume. Send them to the user's device with `SendUserFile`
  (`display: attach`) — they listen remotely.
- **Every patch gets a recipe card** (`patches/<slug>.md`): every change from
  `-INIT-` as a numbered table with the panel value (bipolar = raw − 64) and the
  raw 0–127 value, plus a short "why". The user asked for this list explicitly.
- **Ears beat metrics.** When the user's verdict disagrees with a number, trust
  the user, find the measurement that explains it, and log both in FINDINGS
  ("Listening feedback log").
- **Taste so far** (Obright): fitted patches sounded *brighter* than the OB;
  the user chose the darker version whose **attack brightness matches the
  OB-Xf** and the middle is a bit darker. They preferred **low resonance**
  (14 over 20/24/30): the OB character came from slope and envelope shape, not
  resonance. Start from that bias.
- **The translator's stage 3 lands a little dark.** On every patch so far
  the user asked for "a touch brighter" (Obright excepted, which started too
  bright). For pads match sustain brightness, not just the first 0.3 s.
  Don't shorten a pad's filter attack unprompted: the user first asked for
  it, then preferred the original.
- **Unison**: keep Virus unison detune modest (≈2/3 of the std-matched value)
  — the user hears even-spaced Virus voices as wobblier than OB-Xf's.
- "**Bassier / warmer**" so far meant OB-Xf's stronger 2nd–4th harmonics
  (250–550 Hz body). Check harmonic balance re the fundamental. For Warmth
  the user picked **Mid EQ boost around 400 Hz + a gentle low shelf**
  ("bodylow") over mid-only.
- **No sub oscillators.** The user: "don't use sub oscs, they don't fit well".
  Use the EQ section for low end instead.
- **Never commit factory content.** Anything exported from the Access ROM
  (factory singles, the ROM INIT) stays out of git; `build.sh` regenerates
  `patches/reference/init-ti.syx` from the user's own firmware.
- Don't call a patch "approved" unless the user said so — picking one
  variant over another is a choice, not a final verdict.
- Users revise verdicts after re-listening ("actually I was wrong"): keep the
  previous version's files so you can go back instantly.
- When offering choices, make variants that differ in **one thing**, with
  everything else (e.g. brightness) held equal by measurement, and give each a
  short name (dark / res / r20 …).
- **Write discoveries down as they happen** — FINDINGS for facts, this file
  for process. The user doesn't want to re-derive anything next session.
- Commit only when asked. Repo author is set locally to the user.

## Pipeline

```
OB-Xf patch ──params──▶ map_structure()  (tools/translate.py, uses tools/calibration.json)
                         │  fixed: transpose, osc pitch, waves, PW, balance, detune,
                         │  filter type, keyfollow, velocity, unison, LFO→pitch
                         ▼
               stage 1: amp ADSR  ← level envelope, both filters wide open (chord)
               stage 2: filter    ← third-octave band shapes over single/fifth/chord
               stage 3: cutoff trim ← first 0.3 s brightness = OB-Xf (the "dark" rule)
                         ▼
               patches/<slug>.syx + .json, renders/<slug>/listen/*.wav
```

Run: `.venv/bin/python tools/translate.py "<OB-Xf name>" --slug <slug> [--hold s --tail s]`
(~5–10 min per patch on 10 cores). Pads: use a longer hold (3 s) and tail (4 s).

### Rules learned the hard way

1. **Measure a control's scale before using it.** Never guess a Virus value
   from its 0–127 position: Osc2 Detune 8 ≈ no detune; 48 ≈ 5 cents. Add new
   tables to `tools/calibrate.py` → `tools/calibration.json` and FINDINGS.
2. **Use precise measurement methods**: phase-slope frequency on sine
   oscillators (sub-millihertz), not FFT peaks (±0.5 cent).
3. **Check pitch/octave first.** OB-Xd-imported patches often carry
   Transpose −12. Compare a single note's fundamental before fitting.
4. **Check routing before fitting.** Filter 2 in the path (INIT's balance 64)
   kept the sweep closed; no parameter tweak can fix a structural mistake.
5. **Fit the same examples you'll listen to** (single, fifth, chord), not one
   chord.
6. **Brightness centroid isn't enough** — it can't see slope or resonance.
   Match third-octave band shapes, and check brightness per time window
   (0–0.3 s, 0.3–1 s, 1–2 s).
7. **Coordinate search gets stuck on structure.** For discrete or coupled
   choices (filter mode, routing, balance + filter 2 env), fit each structure
   separately and compare the fitted scores.
8. **Average OB-Xf targets over 3 renders** (it adds cutoff noise and random
   phase even with slop off). Virus renders are deterministic.
9. **Always plot** brightness and level curves (and harmonic spectra when the
   user says "filter character") before trusting a score.
10. Shell is **zsh**: unquoted `$var` is *not* word-split, so passing
    `extra="--hold 3 --tail 4"` as `$extra` sends one argument. Use arrays or
    write the arguments out.
11. Keep `virusRender` events on the DSP thread — main-thread timing made
    parallel renders jitter (fixed; see FINDINGS).

## Files

| Path | What |
|---|---|
| `tools/virusRender/` | headless TI firmware renderer (C++, built by `build.sh`) |
| `tools/virus_patch.py` | named params → `.syx`; `python tools/virus_patch.py <regex>` lists params |
| `tools/obxf_render.py` | OB-Xf renders and `--params` dumps |
| `tools/render_lib.py` | render helpers and metrics (level, centroid, band shapes) |
| `tools/fit.py` | coordinate search and loss functions |
| `tools/calibrate.py` | measured control scales → `tools/calibration.json` |
| `tools/translate.py` | full OB-Xf → Virus translation (map + 3 fit stages + A/B) |
| `tools/ab_render.py` | loudness-matched A/B listening files |
| `patches/<slug>.{syx,md,json}` | patch, recipe card, translation report |
| `patches/obright.py` | hand-finished Obright (FINAL values chosen by ear) |
