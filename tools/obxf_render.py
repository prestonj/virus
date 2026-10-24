"""Render OB-Xf patches as reference targets, matching virusRender's timing and WAV format.

usage:
  .venv/bin/python tools/obxf_render.py --list Brass
  .venv/bin/python tools/obxf_render.py "Obright Original" --notes 48,55,60,64 --hold 1.5 --tail 1.5 \
      --out renders/obxf_obright.wav [--params renders/obxf_obright.json]

The WAV starts at note on, like virusRender's output.
"""
import argparse
import json
import pathlib
import sys

import numpy as np
from scipy.io import wavfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OBXF = ROOT / "third_party" / "obxf"
PATCHES = OBXF / "assets" / "installer" / "Surge Synth Team" / "OB-Xf" / "Patches"
sys.path.insert(0, str(OBXF / "build" / "src" / "obxf-python"))

import obxfpy  # noqa: E402

RATE = 44100  # same as the Virus TI


def find_patch(name):
    p = pathlib.Path(name)
    if p.is_file():
        return p
    matches = [f for f in PATCHES.rglob("*.fxp") if f.stem.lower() == name.lower()]
    if not matches:
        raise SystemExit(f"no OB-Xf factory patch named '{name}'")
    return matches[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patch", nargs="?", help="factory patch name or .fxp path")
    ap.add_argument("--list", metavar="CATEGORY", nargs="?", const="", help="list factory patches")
    ap.add_argument("--notes", default="60")
    ap.add_argument("--vel", type=int, default=100)
    ap.add_argument("--hold", type=float, default=2.0)
    ap.add_argument("--tail", type=float, default=2.0)
    ap.add_argument("--out", default="renders/obxf.wav")
    ap.add_argument("--params", help="write the patch's parameter values as JSON")
    args = ap.parse_args()

    if args.list is not None:
        for f in sorted(PATCHES.rglob("*.fxp")):
            if args.list.lower() in f.parent.name.lower():
                print(f"{f.parent.name:12s} {f.stem}")
        return

    if not args.patch:
        ap.error("patch name required")

    path = find_patch(args.patch)
    eng = obxfpy.ObxfEngine(float(RATE))
    eng.load_patch(str(path))
    eng.process(RATE // 2)  # let parameter smoothing settle before playing

    notes = [int(n) for n in args.notes.split(",")]
    for n in notes:
        eng.note_on(n, args.vel)
    held = eng.process(int(args.hold * RATE))
    for n in notes:
        eng.note_off(n, 64)
    tail = eng.process(int(args.tail * RATE))

    left = np.concatenate([held[0], tail[0]])
    right = np.concatenate([held[1], tail[1]])
    stereo = np.stack([left, right], axis=1).astype(np.float32)
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(args.out, RATE, stereo)
    print(f"rendered '{path.stem}' -> {args.out}  ({len(left) / RATE:.2f}s, peak {np.abs(stereo).max():.3f})")

    if args.params:
        values = {pid: eng.get_param(pid) for pid in eng.get_param_ids()}
        pathlib.Path(args.params).write_text(json.dumps(values, indent=1, sort_keys=True))
        print(f"params -> {args.params}")


if __name__ == "__main__":
    main()
