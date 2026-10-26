"""Listening demos: a short melodic-techno phrase per patch, OB-Xf then Virus, loudness-matched.

usage: .venv/bin/python tools/demo.py                    # whole suite -> renders/suite_AB.wav
       .venv/bin/python tools/demo.py obx-bass-2 warmth  # just these, in this order

124 BPM, A minor, four bars of Am7 - Fmaj7 - C - G. Each patch plays the part that suits it
(ROLES). The suite is one file: patch 1 OB-Xf, gap, patch 1 Virus, longer gap, patch 2 ...
Timestamps for each part are printed and written next to the WAV.
"""
import argparse
import json
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ab_render import write  # noqa: E402
from render_lib import RATE, ROOT, render_obxf_seq, render_virus_seq  # noqa: E402
from virus_patch import Patch  # noqa: E402

BPM = 124
BEAT = 60 / BPM
S16 = BEAT / 4
BAR = 4 * BEAT
CHORDS = [(57, 60, 64, 67), (53, 57, 60, 64), (55, 60, 64, 67), (55, 59, 62, 67)]  # Am7 Fmaj7 C/G G
ROOTS = [45, 41, 48, 43]  # A F C G
TARGET_RMS_DB = -20.0
AB_GAP, PATCH_GAP = 0.8, 2.0


def bass():
    """Rolling offbeat 16ths, leaving the downbeat to the kick; octave jump on beats 2 and 4."""
    seq = []
    for bar, root in enumerate(ROOTS):
        for beat in range(4):
            for step in (1, 2, 3):
                note = root + 12 if (step == 3 and beat % 2) else root
                seq.append((bar * BAR + beat * BEAT + step * S16, 0.8 * S16, note, 115 if step == 2 else 95))
    return seq


def arp():
    """Three-note cycle over 16ths (3 against 4), chord tones an octave up."""
    seq = []
    for bar, chord in enumerate(CHORDS):
        tones = [n + 12 for n in chord]
        cycle = [tones[0], tones[2], tones[3]]
        for step in range(16):
            note = cycle[step % 3] + (12 if step == 15 else 0)
            seq.append((bar * BAR + step * S16, 0.5 * S16, note, 110 if step % 4 == 0 else 85))
    return seq


def stabs():
    """Chord stabs on a 3-3-3-3-4 sixteenth grid."""
    seq = []
    for bar, chord in enumerate(CHORDS):
        for step in (0, 3, 6, 9, 12):
            seq += [(bar * BAR + step * S16, 1.5 * S16, n, 105) for n in chord]
    return seq


def swells():
    """Chord on beat 1 for 1.5 beats, re-hit on the and-of-2 to the end of the bar."""
    seq = []
    for bar, chord in enumerate(CHORDS):
        t = bar * BAR
        seq += [(t, 1.5 * BEAT, n, 100) for n in chord]
        seq += [(t + 1.5 * BEAT, 2.4 * BEAT, n, 90) for n in chord]
    return seq


def pad():
    """Whole-bar chords."""
    return [(bar * BAR, BAR * 0.98, n, 100) for bar, chord in enumerate(CHORDS) for n in chord]


def lead():
    """A melody over the progression, mostly quarters and halves."""
    melody = [(76, 1.5), (74, 0.5), (72, 1), (74, 1),
              (72, 2), (69, 1), (72, 1),
              (76, 1.5), (79, 0.5), (76, 1), (74, 1),
              (74, 3), (71, 1)]
    seq, t = [], 0.0
    for note, beats in melody:
        seq.append((t, beats * BEAT * 0.95, note, 100))
        t += beats * BEAT
    return seq


PHRASES = {"bass": (bass, 2.0), "arp": (arp, 2.0), "stabs": (stabs, 2.0),
           "swells": (swells, 3.0), "pad": (pad, 3.5), "lead": (lead, 2.5)}  # role -> (phrase, tail s)

# slug -> (OB-Xf patch, role, title)
ROLES = {
    "obright": ("Obright Original", "stabs", "Obright"),
    "its-an-obx": ("It's an OB-X!", "swells", "It's an OB-X!"),
    "warmth": ("Warmth", "pad", "Warmth"),
    "pursuit-bright": ("Pursuit Bright", "lead", "Pursuit Bright"),
    "obx-clavinet": ("OBX Clavinet", "arp", "OBX Clavinet"),
    "obx-bass-1": ("OBX Bass 1", "bass", "OBX Bass 1"),
    "obx-bass-2": ("OBX Bass 2", "bass", "OBX Bass 2"),
    "wrong-organ": ("Wrong Organ", "swells", "Wrong Organ"),
    "steel-string-guitar-2": ("Steel String Guitar 2", "arp", "Steel String Guitar 2"),
    "kawari": ("Kawari", "stabs", "Kawari"),
    "acidisillification": ("Acidisillification", "arp", "Acidisillification"),
}


def guess_role(patch):
    """For new translations without a ROLES entry."""
    if patch["Key Mode"] or patch["Unison Mode"] > 2:
        return "bass"
    if patch["Amp Env Sustain"] < 20:
        return "arp"
    return "pad" if patch["Amp Env Attack"] >= 50 else "stabs"


def level_match(x):
    rms = np.sqrt(np.mean(x[np.abs(x) > 1e-4] ** 2)) + 1e-12  # ignore the silent tail
    return x * (10 ** (TARGET_RMS_DB / 20) / rms)


def demo_pair(ref, syx, role):
    """Return (OB-Xf, Virus) renders of the role's phrase, loudness-matched."""
    phrase, tail = PHRASES[role]
    seq = phrase()
    a = level_match(render_obxf_seq(ref, seq, tail=tail))
    b = level_match(render_virus_seq(Patch.from_syx(syx), seq, tail=tail))
    return a, b


def demo(slug, ref=None, role=None, out=None):
    """One patch: renders/<slug>/listen/demo_AB.wav (OB-Xf, gap, Virus)."""
    syx = ROOT / "patches" / f"{slug}.syx"
    ref = ref or ROLES[slug][0]
    role = role or (ROLES[slug][1] if slug in ROLES else guess_role(Patch.from_syx(syx)))
    a, b = demo_pair(ref, syx, role)
    out = pathlib.Path(out or ROOT / "renders" / slug / "listen")
    out.mkdir(parents=True, exist_ok=True)
    write(out / "demo_AB.wav", np.concatenate([a, np.zeros(int(AB_GAP * RATE)), b]))
    print("wrote", out / "demo_AB.wav")


def suite(slugs, out):
    # Virus renders run as parallel subprocesses; OB-Xf runs in-process, one at a time
    seqs = [(PHRASES[ROLES[s][1]][0](), PHRASES[ROLES[s][1]][1]) for s in slugs]
    with ThreadPoolExecutor() as ex:
        vs = list(ex.map(lambda i: render_virus_seq(Patch.from_syx(ROOT / "patches" / f"{slugs[i]}.syx"),
                                                    *seqs[i]), range(len(slugs))))
    pairs = [(level_match(render_obxf_seq(ROLES[s][0], seq, tail=tail)), level_match(v))
             for s, (seq, tail), v in zip(slugs, seqs, vs)]
    parts, marks, t = [], [], 0.0
    for slug, (a, b) in zip(slugs, pairs):
        title = ROLES[slug][2]
        for label, x, gap in ((f"{title}: OB-Xf", a, AB_GAP), (f"{title}: Virus", b, PATCH_GAP)):
            marks.append((round(t, 1), label))
            parts += [x, np.zeros(int(gap * RATE))]
            t += len(x) / RATE + gap
    write(out, np.concatenate(parts))
    out.with_suffix(".json").write_text(json.dumps(marks, indent=1))
    for s, label in marks:
        print(f"{int(s // 60)}:{s % 60:04.1f}  {label}")
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*", default=list(ROLES))
    ap.add_argument("--out", default=str(ROOT / "renders" / "suite_AB.wav"))
    a = ap.parse_args()
    suite(a.slugs, pathlib.Path(a.out))


if __name__ == "__main__":
    main()
