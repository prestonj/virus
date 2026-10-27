# Vintage targets beyond Oberheim: where the Virus TI fits

Written 2026-10-26, from what we measured translating OB-Xf (FINDINGS) plus each
synth's published architecture (from general knowledge, not measured here). Two
questions per synth: **can the Virus do its voice structure**, and **is there a
free, scriptable emulation** to render reference audio from (our pipeline fits
against one; without it we'd be working by ear only).

## What we know the Virus can and can't do (measured)

- Can: saw, pulse with PWM, triangle/sine and 60+ spectral waves; osc 3; sub
  oscillator; noise; true ring mod (osc 1 × osc 2); hard sync; linear FM
  osc 1 → osc 2; analog-style 1–4 pole low-pass with real saturation; digital
  HP/BP/notch; 3 LFOs (to ~87 Hz) incl. S&H; unison; chorus; EQ; per-voice drift.
- Can't: FM from a square (FM always uses osc 1's saw unless osc 1 is a "wave"
  shape); exponential FM (it's linear; we shift the carrier to compensate);
  audio-rate pitch jitter; LFOs at audio rate; independent per-oscillator drift
  (we add it with LFO 3); analog filter modes other than low-pass; analog-clean
  filtering at full level (it saturates; lower Osc Mainvolume to tame it).
- Untested: Osc Shape between saw (64) and pulse (127) may blend the two, which
  would give saw + pulse on one oscillator. Several targets below need that.

## Candidates

| Synth | Voice structure | Virus fit | Free emulation to fit against |
|---|---|---|---|
| **Roland Juno-6 / 60 / 106** | 1 DCO per voice: saw + pulse (PWM) + sub square + noise, mixed; HPF; 24 dB LPF; one ADSR; triangle LFO with delay; chorus I/II | **Very good.** Everything is native: saw/pulse/sub/noise mix, PW Lfo1 Amount, analog LP, filter 2 as HP, chorus. DCOs are stable, so none of the OB drift problems. Needs: chorus calibrated; saw + pulse together (shape blend or a synced second osc) | **Yes: Ultramaster KR-106** (GPL-3, Juno-6/60/106, VST3/AU/CLAP/LV2, modelled from schematics, firmware and measurements). Also Hera (Juno-60, GPL, alpha) |
| **Roland SH-101** | Juno-like single osc (saw + pulse + sub + noise), mono, 24 dB LPF | Very good, as Juno | None open found |
| **Minimoog Model D** | 3 VCOs (osc 3 can be an LFO), mono, ladder 24 dB, two ADS contours, noise, feedback overdrive trick, glide | **Good** for classic bass and lead: osc 3, mono/legato, glide, and the Virus filter's saturation suits a Moog. Gaps: osc 3 / noise → filter at audio rate; osc 3 as a pitch modulator above ~87 Hz | **Yes: CA-72** (Idle Foundry, GPL, SPICE-derived from the service manual, v0.1.0, VST3/CLAP). Also Faug (Faust) |
| **Sequential Prophet-5 / 10** | 2 VCOs (A: saw + pulse; B: saw/tri/pulse, low-freq mode), sync, 24 dB LPF, 2 ADSRs; Poly-Mod (filter env and osc B → osc A pitch, PW, filter); wheel mod | **Moderate–good**: like the OB, but Poly-Mod brings back what failed for OB: osc B → osc A FM (fine from saw/tri, not from pulse) and audio-rate filter FM (no Virus equivalent). Filter env → pitch is fine | **Partly: Pro-54**, an open-source Cmajor port of NI's Pro-53 (GPL/commercial). Browser-only so far; Cmajor can build a native plugin. Commercial: GForce (official), Softube Model 80 |
| **Moog Memorymoog** | 3 VCOs per voice, poly, ladder, osc 3 as mod source, sync | Moderate: same osc 3 modulation limits as the Model D | None found |
| **Roland Jupiter-8** | 2 VCOs, cross-mod VCO 2 → VCO 1, sync, HPF + 12/24 dB LPF, 2 envs | Moderate: cross-mod from VCO 2's sine is possible (Virus wave shapes do pass through FM); from square it isn't | None open found (Roland's own is commercial) |
| **Oberheim Matrix-12 / Xpander** | 2 VCOs (waves mixed), VCO and VCF FM, 15 filter modes, 5 envelopes, 5 LFOs, ramps, tracking generators, lag, 20 matrix routings | **Poor.** Far more modulation than the Virus matrix holds; most filter modes have no analog Virus equivalent; audio-rate VCF FM | None open found (Arturia Matrix-12 V is commercial) |

## Recommendation

1. **Juno (60/106) next.** It's the best structural fit by a distance, the
   reference emulation is serious and free, and it avoids every Virus limit we
   hit with Oberheims (cross-mod, slop, ring mod). Expect close matches.
2. **Minimoog Model D second.** Strong fit for bass/lead; CA-72 is circuit-
   derived but very new (0.1.0), so treat it as a less certain reference.
3. Prophet-5 only for patches without Poly-Mod (or with filter-env → pitch
   only), and only once Pro-54 renders natively.
4. Skip Matrix-12, Memorymoog, Jupiter-8 and SH-101 for now: no reference to
   fit against (SH-101 sounds would be covered by Juno-style work anyway).

## Practical notes for a Juno/Moog pipeline

- These are plugins, not Python modules like obxfpy. Hosting them headless
  (e.g. Spotify's `pedalboard` loads VST3/AU and renders MIDI from Python) would
  replace `render_obxf`; parameters are set by plugin parameter names.
- Check each plugin's patch format (KR-106 presets, CA-72 factory presets) to
  get the factory patches as translation targets, like OB-Xf's `.fxp` files.

Sources: [KR-106](https://kayrock.org/kr106/) ([source](https://github.com/kayrockscreenprinting/ultramaster_kr106));
[Synth Anatomy on KR-106](https://synthanatomy.com/2026/03/ultramaster-kr-106-an-open-source-roland-juno-106-synthesizer-emulation.html);
[Hera](https://www.github.com/jpcima/Hera);
[CA-72 (MusicTech)](https://musictech.com/news/gear/minimoog-model-d-plugin-model-ca-72-free/);
[CA-72 (Dubspot)](https://blog.dubspot.com/ca-72-idle-foundry-2026);
[Faug](https://github.com/t2techno/Faug);
[Pro-54 (Synth Anatomy)](https://synthanatomy.com/?p=82491);
[Arturia Matrix-12 V](https://www.arturia.com/fr/products/software-instruments/matrix-12-v/overview).
