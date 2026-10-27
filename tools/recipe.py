"""Write a recipe card (patches/<slug>.md) from a translated patch and its report.

    .venv/bin/python tools/recipe.py <slug> ["Display Name"]
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from virus_patch import PARAMS, PARAM_JSON, Patch  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIPOLAR = {"signed", "biPolarPercent", "pan", "panPercent", "signedNorm", "signedMidOff", "envSustainTime"}
SECTIONS = [  # (regex on parameter name, section)
    (r"^Transpose|^Key Mode|^Patch Volume|^Unison", "Common"),
    (r"^Osc1", "Osc 1"), (r"^Osc2", "Osc 2"), (r"^Osc Balance|^Osc Mainvolume|^Sub|^Noise", "Mixer"),
    (r"^Filter Env", "Filter Env"), (r"^Filter1|^Cutoff$", "Filter 1"), (r"^Filter2|^Cutoff2", "Filter 2"),
    (r"^Filter", "Filters"), (r"^Amp Env", "Amp Env"), (r"^Lfo1", "LFO 1"),
    (r"Velocity$", "Velocity Map"), (r"EQ ", "EQ"),
]
ORDER = ["Common", "Osc 1", "Osc 2", "Mixer", "Filters", "Filter 1", "Filter 2", "Filter Env", "Amp Env",
         "LFO 1", "Velocity Map", "EQ", "Other"]


def value_lists():
    text = PARAM_JSON.read_text()
    out = {}
    for m in re.finditer(r'"([\w-]+)"\s*:\s*\[\s*((?:"[^"]*"\s*,?\s*)+)\]', text):
        out[m.group(1)] = re.findall(r'"([^"]*)"', m.group(2))
    return out


VALUES = value_lists()


def display(name, raw):
    t = PARAMS[name].get("toText", "")
    if t in VALUES and raw < len(VALUES[t]):
        return VALUES[t][raw]
    if t in BIPOLAR:
        return f"{raw - 64:+d}"
    if PARAMS[name]["max"] == 1:
        return "On" if raw else "Off"
    return str(raw)


def section(name):
    for rx, s in SECTIONS:
        if re.search(rx, name):
            return s
    return "Other"


def card(slug, title=None):
    patch = Patch.from_syx(ROOT / "patches" / f"{slug}.syx")
    report = json.loads((ROOT / "patches" / f"{slug}.json").read_text())
    rows = sorted(patch.diff(Patch.from_syx()).items(), key=lambda kv: (ORDER.index(section(kv[0])),
                                                                      PARAMS[kv[0]]["page"], PARAMS[kv[0]]["index"]))
    juno = report["reference"].startswith("Jun-6 V: ")
    ref = report["reference"].removeprefix("Jun-6 V: ")
    synth, tool = ("Jun-6 V (Juno-6/60)", "translate_juno.py") if juno else ("OB-Xf", "translate.py")
    short = "the Juno" if juno else "OB-Xf"
    title = title or ref.split("/")[-1]
    lines = [f"# {title} (Virus TI)", "",
             f"Translated from {synth}'s **\"{ref}\"** by `tools/{tool}`. "
             f"File: `{slug}.syx`.", "",
             "## Changes from INIT", "",
             "Start from the TI's `-INIT-` single. Panel = how the value shows on the TI "
             "(bipolar values are raw − 64); Raw = stored 0–127.", "",
             "| # | Section | Parameter | Panel | Raw |", "|---|---|---|---|---:|"]
    for i, (name, (_, raw)) in enumerate(rows, 1):
        lines.append(f"| {i} | {section(name)} | {name} | {display(name, raw)} | {raw} |")
    lines += ["", "Everything else stays at INIT.", "", "## Translation notes", ""]
    lines += [f"- {n}" for n in report["mapping_notes"]] or ["- none"]
    if report.get("listening_edits"):
        lines += ["", "## Changes made by ear", ""] + [f"- {e}" for e in report["listening_edits"]]
    if report.get("variant_edits"):
        lines += ["", "## Variant changes (not yet heard)", ""] + [f"- {e}" for e in report["variant_edits"]]
    amp = (f"Amp envelope level-shape error {report['amp_level_error_db']} dB; filter"
           if "amp_level_error_db" in report else "Gate VCA (no amp fit); filter")
    gap = report.get("attack_brightness_gap_semitones", report.get("brightness_gap_semitones"))
    lines += ["", "## How close it is", "",
              f"- {amp} band-shape error {report['band_shape_error_db']} dB.",
              f"- Cutoff trimmed {report['cutoff_fit']} → {report['cutoff_trimmed']} so the held note (attack and "
              f"sustain medians) matches {short}'s brightness (gap {gap:+} semitones).",
              f"- Listening file: `renders/{slug}/listen/demo_AB.wav` ({short} first, then Virus, "
              f"loudness-matched).",
              "- " + report.get("verdict", "Not yet checked by ear."), ""]
    out = ROOT / "patches" / f"{slug}.md"
    out.write_text("\n".join(lines))
    return out


if __name__ == "__main__":
    print("wrote", card(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
