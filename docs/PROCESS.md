# Process and guidelines

How we make Oberheim-style Virus TI patches, and what the user wants from each
round. Read this and [FINDINGS.md](FINDINGS.md) before starting a new session.
FINDINGS records *facts* (measurements, quirks); this file records *how we work*.

## What the user wants

- **Goal:** Virus TI2 patches that sound like vintage Oberheims (OB-X, OB-Xa,
  SEM, OB-8). References come from OB-Xf factory patches (OB-Xd lineage).
- **Listening files: one musical phrase per patch, all patches in one file.**
  Since 2026-10-25 the user wants a single WAV: for each patch a short
  melodic-techno phrase (124 BPM, A minor, Am7–Fmaj7–C–G) in the part that
  suits it (bass line, arp, stabs, swells, pad, lead), **OB-Xf first, then
  the Virus**, patch after patch, **loudness-matched**. `tools/demo.py`
  builds it (`renders/suite_AB.wav` + timestamps in `.json`); add new
  patches to its `ROLES`. `translate.py` writes a one-patch
  `renders/<slug>/listen/demo_AB.wav`. Send with `SendUserFile`
  (`display: attach`), with the timestamps in the caption — they listen
  remotely; files over 30 MB don't reach the phone, so send long suites as
  AAC (`afconvert -f m4af -d aac -b 256000 in.wav out.m4a`). (Single note / fifth / chord files via `tools/ab_render.py` are
  still what the fit uses, but no longer the listening deliverable.)
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
- **Resonance: stay near the OB-Xf patch's own value.** OBX Bass 2's fit
  chose 44 against OB-Xf's ~7; the user picked res 8 at equal brightness.
  Twice now (Obright, Bass 2) extra resonance from the fit was rejected.
  `translate.py` caps stage-2 resonance at `60 × FilterResonance + 8`.
- Batch 2 (OBX Clavinet, Pursuit Bright) was accepted as translated: the
  level-gated held-note brightness trim seems to hit the user's brightness.
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
- **Skip patches with pulse cross-mod** (user, 2026-10-26: "they just don't
  work"). The Virus FMs with osc 1's saw even when osc 1 is a pulse, so OB-Xf's
  two-pitch pulse cross-mod can't be made. `map_structure` flags it as not
  translated, so the scan treats it as a blocker. Tubular Bells and Rock Unison
  were set aside (`renders/dropped/`).
- **Ring mod** (user, 2026-10-26): isolated ring is "closer for sure"; high EQ
  helped, noise FM didn't; ring 64 slightly better than 127; per-note random
  osc 2 tuning helped ("the beats change per note" on the OB). OB-Xf still
  sounds better: the Virus can't jitter both oscillators at audio rate.
- **No sub oscillators.** The user: "don't use sub oscs, they don't fit well".
  Use the EQ section for low end instead. (Juno patches play the Juno's sub on
  osc 2, a real oscillator, not the Virus sub oscillator.)
- **Juno batch 1 by ear** (2026-10-26): Brass 1 "needs to be brighter"; Phase
  Brass "not as thick (maybe EQ?)"; Strings 2 "could use a bit more chorus";
  Bass 1 "more sine-wavey"; Clavichord "slightly sharper attack"; Harpsichord
  "not as smooth". Measured on the phrase, these were real: fits on middle C
  missed the phrase's register and note lengths (Bass 1 5–20 dB dull above
  200 Hz; brass 8–16 dB dark above 5 kHz; Harpsichord 3–9 dB too bright up
  top, sub too loud). Hence `tools/phrase_fit.py`: a last fit on the demo
  phrase's long-term spectrum, plus `--set` for by-ear edits.
- **Juno batch 1 v2** (2026-10-27): after hearing Juno / v1 / v2, the user
  switched all six to v2 (phrase fit + by-ear edits). The first translations
  are in `renders/dropped/juno-v1/`. Phase Brass v2's fit cut LowEQ to 40,
  against the "thicker" note: if it still sounds thin, try a low/mid EQ boost.
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
               stage 1: amp D/S/R ← level envelope, both filters wide open (chord);
                        attack (amp and filter env) from measured rise times, not fitted
               stage 2: filter    ← third-octave band shapes over single/fifth/chord
                        (resonance capped at 60 × OB-Xf resonance + 8)
               stage 3: cutoff trim ← held-note brightness = OB-Xf: mean of the attack
                        (0–0.3 s) and sustain medians, cutoff searched ±12 (was attack-only;
                        changed after Warmth/OBX Bass 1 needed +6…+8 by ear)
                         ▼
               patches/<slug>.syx + .json, renders/<slug>/listen/*.wav
```

What `map_structure` translates: transpose, osc pitch, saw/pulse/triangle + PW
(duty tables), osc mix → balance, Osc2 detune (table), sync, cross-mod → Virus
FM mode Wave (tables from `tools/calibrate_xmod.py`; clamps past ~±17 st), mixer levels
(Osc Balance, ring mod → Ringmodulator Volume / Osc Mainvolume, from
`calibrate.py mixer`; pure ring uses ring 64 + Mainvolume 0; audible ring gets
high EQ +9 dB), per-note random osc 2 tuning (non-unison two-osc or ring
patches: LFO 3 S&H on osc 2, amount from `calibrate.py pernote`), filter 4-pole → Analog 4
Pole / 2-pole → Analog 2 Pole, keyfollow, velocity → filter env / amp, unison
(voices, ⅔ of std-matched detune, Key Mode Mono 1), LFO → osc pitch (OB-Xf
LFO 1, else its LFO 2, onto Virus LFO 1). **Not yet**: OB-Xf
Xpander/notch filter modes, LFO → cutoff (needs Virus LFO 2), LFO/env → PW
(needs mod matrix), env → pitch, portamento, saw+pulse on one osc (saw wins).
Full list with counts: FINDINGS "Unsupported OB-Xf features"; rerun
`tools/scan_obxf.py` after adding a mapping.

**Plan (the user's proposal, 2026-10-25): reach translator parity before translating more.**
For each missing feature, most-used first: (1) build a minimal OB-Xf patch
with only that feature on and measure it against candidate Virus controls at
several amounts, like `tools/calibrate.py`; (2) add the mapping to
`map_structure`, plus tables in `calibration.json`; (3) check by ear with a
factory patch where it is the only blocker (scan "alone" column); (4) rescan.
Then move to multi-feature patches.

After a translation: check the report (a brightness gap above ~1 semitone or
a resonance far above OB-Xf's means a problem), run `tools/recipe.py <slug>
"<name>"` for the card, copy the `*_AB.wav` files under patch-prefixed names
(they all share the name `1_single_AB.wav` otherwise), and send them. If stage 2
picked a resonance much higher than OB-Xf's, also send a low-res variant at
equal brightness (user prefers low resonance). Variants go in the report as
`variant_edits`, not `listening_edits` (those are the user's changes by ear).

Run: `.venv/bin/python tools/translate.py "<OB-Xf name>" --slug <slug> [--hold s --tail s]`.
Hold and tail are measured per patch on OB-Xf's chord (`timing(d, name)`): hold =
when loudness and brightness settle + 0.3 s (0.8–2.5 s), tail = 40 dB fall after
release + 0.2 s (0.4–4 s). **Speed**: a Virus render costs ~0.37 s fixed (boot +
1 s settle) + ~0.2 s per audio second; render time is the whole cost of a
translation. Booting once per many renders would save the fixed part, but the
Virus carries voice-allocation and per-voice-detune state between notes, so
renders would stop being bit-identical, and the fit depends on that. Not done.

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
5. **Fit on a single note and a chord** (`EXAMPLES` 1_single and 3_chord).
   The fifth was dropped 2026-10-26 for speed; listening uses a melodic
   phrase now (`tools/demo.py`).
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
12. Launch subprocesses from threads with `close_fds=False` (`posix_spawn`).
    A plain fork can deadlock on SciPy's FFT thread pool (see FINDINGS). A
    run that shows no progress at ~0% CPU is hung: `sample <pid>`, don't wait.
    Log long runs straight to a file (no `| tail`) so progress is visible.
13. **Juno pipeline** (2026-10-26, user: "let's move on to Juno 6"): same
    method as OB-Xf. `tools/calibrate_juno.py` measures every Juno control and
    its Virus counterpart on bare test voices; `tools/translate_juno.py` maps a
    Jun-6 V preset through those tables, then fits amp D/S/R and the filter
    against Jun-6 V renders with effects off, and adds the chorus last.
    Targets: the 56 "Vintage Factory" presets (the original Juno-60 sounds).
    Python buffers stdout into a file: run with `-u` to see progress.

## Files

| Path | What |
|---|---|
| `tools/virusRender/` | headless TI firmware renderer (C++, built by `build.sh`) |
| `tools/virus_patch.py` | named params → `.syx`; `python tools/virus_patch.py <regex>` lists params |
| `tools/obxf_render.py` | OB-Xf renders and `--params` dumps |
| `tools/render_lib.py` | render helpers and metrics (level, centroid, band shapes) |
| `tools/fit.py` | coordinate search and loss functions |
| `tools/calibrate.py` | measured control scales → `tools/calibration.json` |
| `tools/calibrate_xmod.py` | OB-Xf cross-mod → Virus FM Amount tables (merged into calibration.json) |
| `tools/translate.py` | full OB-Xf → Virus translation (map + 3 fit stages + A/B) |
| `tools/ab_render.py` | single/fifth/chord A/B files (old listening format; `EXAMPLES` drive the fit) |
| `tools/scan_obxf.py` | which OB-Xf patches use features the translator can't map |
| `tools/jun6.py`, `tools/juce_state.py` | Arturia Jun-6 V headless (presets, params, renders) |
| `tools/demo.py` | melodic phrase per patch; whole suite as one A-then-B file (stereo; OB-Xf or `jun6:` references) |
| `tools/calibrate_juno.py` | Juno (Jun-6 V) ↔ Virus control tables (merged into calibration.json) |
| `tools/translate_juno.py` | Jun-6 V preset → Virus translation (map + fit + demo) |
| `patches/<slug>.{syx,md,json}` | patch, recipe card, translation report |
| `patches/obright-hand.py` | the earlier hand-finished Obright (FINAL values chosen by ear); superseded by the v3 translation |
