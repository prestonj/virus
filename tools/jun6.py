"""Arturia Jun-6 V (Juno-6 emulation) as a headless reference, via pedalboard.

    .venv/bin/python tools/jun6.py --list [regex]               # factory presets
    .venv/bin/python tools/jun6.py "Vintage Factory/23 Celesta" --params
    .venv/bin/python tools/jun6.py "Vintage Factory/23 Celesta" --notes 55,60,64,67 --out x.wav

Gotchas (FINDINGS, "Arturia Jun-6 V"):
- Render with buffer_size=512: at pedalboard's default block size (8192) the plugin
  plays nothing.
- After loading a preset the first render is silent: do one throwaway render.
- A preset file is the plugin's own state text (boost archive), so loading one means
  putting the file into the VST3 state (tools/juce_state.py).
- Not deterministic (voice calibration, chorus noise): average renders when fitting.
- Arturia presets and renders are Arturia's content: keep them out of git.
"""
import argparse
import pathlib
import re
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from juce_state import rewrap, unwrap  # noqa: E402

PLUGIN = "/Library/Audio/Plug-Ins/VST3/Jun-6 V.vst3"
PRESETS = pathlib.Path("/Library/Arturia/Presets/Jun-6 V")
RATE, BLOCK = 44100, 512

_plugin = None
_xml = None


def plugin():
    global _plugin, _xml
    if _plugin is None:
        from pedalboard import load_plugin
        _plugin = load_plugin(PLUGIN)
        _xml, _ = unwrap(_plugin.raw_state)
    return _plugin


def find_preset(name):
    """'Vintage Factory/23 Celesta', or a unique preset name."""
    p = PRESETS / "Factory" / name
    if p.is_file():
        return p
    hits = [f for f in (PRESETS / "Factory").rglob("*") if f.is_file() and f.name.lower() == name.lower()]
    if len(hits) != 1:
        raise SystemExit(f"preset {name!r}: {len(hits)} matches")
    return hits[0]


def preset_state(name):
    """Every numeric value stored in a preset file, by key (0-1 normalised, as the plugin saves them).

    Holds what the plugin's parameters don't show: modulation routings
    ("Modulations_<section> <param>_<source>_Amount", 0.5 = off; sources Env 2, LFO 2,
    Velocity, AfterTouch, ModWheel), the macro matrix (ModMatrixDest*, ModMatrixAmount_Src*_Dest*),
    voice settings and hidden chorus/HPF options. See FINDINGS ("Jun-6 V extended features").
    The archive is "<length> <key> <value>" text; keys may contain spaces, so read by length.
    """
    s = find_preset(name).read_text(encoding="latin-1")
    out = {}
    for m in re.finditer(r"(?<!\S)(\d+) ", s):
        n, a = int(m.group(1)), m.end()
        key = s[a:a + n]
        if 3 < n < 60 and re.fullmatch(r"[A-Za-z][\w ]*", key) and s[a + n:a + n + 1] == " ":
            try:
                out[key] = float(s[a + n + 1:].split(" ", 1)[0])
            except ValueError:
                pass
    return out


def list_presets(pattern=""):
    rx = re.compile(pattern, re.I)
    return sorted(str(f.relative_to(PRESETS / "Factory")) for f in (PRESETS / "Factory").rglob("*")
                  if f.is_file() and rx.search(str(f)))


def _render(msgs, duration, stereo=False):
    x = plugin()(msgs, duration=duration, sample_rate=RATE, num_channels=2, buffer_size=BLOCK).astype(np.float64)
    return x.T if stereo else x.mean(axis=0)


def load(name, overrides=None):
    """Load a factory preset (then parameter overrides, by pedalboard name) and warm the plugin up."""
    p = plugin()
    p.raw_state = rewrap(_xml, find_preset(name).read_bytes())
    for k, v in (overrides or {}).items():
        setattr(p, k, v)
    _render([], 0.3)  # the first render after a state change is silent
    return p


def params():
    """Every plugin parameter, in display units (Hz, s, dB, switch names)."""
    p = plugin()

    def plain(v):  # pedalboard wraps values; unwrap so they compare, JSON-encode and pickle normally
        if isinstance(v, str):
            return str(v)
        if any(c.__name__ == "WrappedBool" for c in type(v).__mro__):
            return bool(v)
        try:
            return float(v)
        except (TypeError, ValueError):
            return v
    return {k: plain(getattr(p, k)) for k in p.parameters}


def render(notes=(60,), hold=1.5, tail=1.5, vel=100):
    """Current preset: hold `notes`, release, record the tail. Mono, from note on."""
    msgs = [(bytes([0x90, n, vel]), 0.0) for n in notes] + [(bytes([0x80, n, 64]), hold) for n in notes]
    return _render(msgs, hold + tail)


def render_seq(seq, tail=2.0, stereo=False):
    """Note list [(start s, length s, note, vel)], like render_lib.render_virus_seq."""
    msgs = sorted([(bytes([0x90, n, v]), t) for t, d, n, v in seq] + [(bytes([0x80, n, 64]), t + d) for t, d, n, v in seq],
                  key=lambda m: (m[1], m[0][0] != 0x80))  # note offs first at equal times
    return _render(msgs, max(t + d for t, d, _, _ in seq) + tail, stereo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("preset", nargs="?")
    ap.add_argument("--list", nargs="?", const="", metavar="REGEX")
    ap.add_argument("--params", action="store_true")
    ap.add_argument("--notes", default="60")
    ap.add_argument("--hold", type=float, default=1.5)
    ap.add_argument("--tail", type=float, default=1.5)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.list is not None:
        print("\n".join(list_presets(a.list)))
        return
    load(a.preset)
    if a.params:
        for k, v in params().items():
            print(f"{k:32} {v}")
    if a.out:
        x = render(tuple(int(n) for n in a.notes.split(",")), a.hold, a.tail)
        wavfile.write(a.out, RATE, x.astype(np.float32))
        print(f"wrote {a.out}  peak {np.abs(x).max():.3f}")


if __name__ == "__main__":
    main()
