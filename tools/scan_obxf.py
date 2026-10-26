"""Scan every OB-Xf factory patch for features translate.py can't map yet.

usage: .venv/bin/python tools/scan_obxf.py            # summary: feature counts + clean patches
       .venv/bin/python tools/scan_obxf.py --all      # one line per patch: blockers (or mapping notes)

A patch is "clean" when map_structure() reports nothing untranslated. See FINDINGS
("Unsupported OB-Xf features") for which blockers the fit absorbs anyway.
"""
import argparse
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from obxf_render import PATCHES  # noqa: E402
from render_lib import RATE, obxfpy  # noqa: E402
from translate import map_structure  # noqa: E402

BLOCKER = ("not translated", "saw+pulse", "non-LP")


def feature(note):
    """Collapse a mapping note to its feature name for counting."""
    if "pulse cross-mod" in note:
        return "pulse cross-mod"
    if "saw+pulse" in note:
        return "saw+pulse on one osc"
    if "waveform" in note:
        return note.split(" waveform")[0] + " waveform"
    return re.sub(r"=[-0-9.]+| not translated.*|: translated as low-pass", "", note)


def scan():
    seen, rows = set(), []
    for f in sorted(PATCHES.rglob("*.fxp")):
        if f.stem.lower() in seen:
            continue
        seen.add(f.stem.lower())
        e = obxfpy.ObxfEngine(float(RATE))
        e.load_patch(str(f))
        _, notes = map_structure({k: e.get_param(k) for k in e.get_param_ids()}, f.stem)
        rows.append((f.parent.relative_to(PATCHES), f.stem, notes,
                     [n for n in notes if any(b in n for b in BLOCKER)]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    rows = scan()
    if a.all:
        for cat, name, notes, issues in rows:
            print(f"{len(issues)}\t{cat}\t{name}\t{' | '.join(issues or notes)}")
        return
    uses = collections.Counter(feature(n) for *_, issues in rows for n in issues)
    only = collections.Counter(feature(issues[0]) for *_, issues in rows if len(issues) == 1)
    print(f"{len(rows)} patches, {sum(1 for r in rows if not r[3])} clean\n")
    print(f"{'feature':32} uses  only blocker")
    for k, n in uses.most_common():
        print(f"{k:32} {n:4}  {only.get(k, 0):4}")
    print("\nclean:", ", ".join(f"{c}/{n}" for c, n, _, i in rows if not i))


if __name__ == "__main__":
    main()
