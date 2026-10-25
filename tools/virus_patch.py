"""Build Virus TI Single Dump (.syx) files from named parameters.

Parameter names, pages, ranges and defaults come from Gearmulator's
parameterDescriptions_TI.json. A parameter on page P (0x70, 0x71, 0x6E, 0x6F)
with index I lives at preset byte PAGE_ORDER.index(P) * 128 + I.

    from virus_patch import Patch
    p = Patch.from_syx("patches/reference/init-ti.syx")
    p["Cutoff"] = 40
    p.name = "My Patch"
    p.save("patches/my-patch.syx")
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PARAM_JSON = ROOT / "third_party" / "gearmulator" / "source" / "axel" / "osTIrusJucePlugin" / "parameterDescriptions_TI.json"
TEMPLATE = ROOT / "patches" / "reference" / "init-ti.syx"

PAGE_ORDER = [0x70, 0x71, 0x6E, 0x6F]
DUMP_SIZE = 524
HEADER = 9          # F0 00 20 33 01 dev 10 bank prog
NAME_INDEX = 128 + 112  # page B (0x71) params 112..121 hold the 10-char name
NAME_LEN = 10


def _load_params():
    text = PARAM_JSON.read_text()
    # Only the parameter array is needed; the rest of the file is loose JSON
    start = text.index("[", text.index('"parameterdescriptions"'))
    end = text.index('"regions"')
    body = text[start:end].rstrip().rstrip(",")
    body = re.sub(r",(\s*[\]}])", r"\1", body)
    params = {}
    for p in json.loads(body):
        page = p.get("page")
        if page not in PAGE_ORDER:
            continue
        p.setdefault("min", 0)
        p.setdefault("max", 127)
        p["offset"] = PAGE_ORDER.index(page) * 128 + p["index"]
        # First definition wins; later duplicates are aliases for other modes
        params.setdefault(p["name"], p)
    return params


PARAMS = _load_params()

# Names that alias a byte only in vocoder / filter-bank / input-follower modes
_MODE_ALIAS = re.compile(r"Vocoder|Carrier|Modulator|Input Follower|Filter Bank|Backup")
# offset -> most useful name for that byte in a normal (non-vocoder) patch
def _alias_rank(name):
    # lower is better: plain names, then mode-prefixed ("Osc1 HyperSaw/Density"), then vocoder etc.
    return (2 if _MODE_ALIAS.search(name) else 0) + (1 if "/" in name else 0)


PRIMARY = {}
for _n, _p in PARAMS.items():
    if _p["offset"] not in PRIMARY or _alias_rank(_n) < _alias_rank(PRIMARY[_p["offset"]]):
        PRIMARY[_p["offset"]] = _n


def find(pattern):
    """List parameter names matching a regex (case-insensitive)."""
    rx = re.compile(pattern, re.I)
    return [n for n in PARAMS if rx.search(n)]


class Patch:
    def __init__(self, preset: bytes):
        assert len(preset) == 512
        self.preset = bytearray(preset)
        self.touched = {}  # offset -> name last used to set it, for readable diffs

    @classmethod
    def from_syx(cls, path=TEMPLATE):
        msg = pathlib.Path(path).read_bytes()
        if len(msg) != DUMP_SIZE or msg[0] != 0xF0 or msg[6] != 0x10:
            raise ValueError(f"{path} is not a 524-byte Virus TI Single Dump")
        first = msg[HEADER:HEADER + 256]
        second = msg[HEADER + 257:HEADER + 257 + 256]
        return cls(first + second)

    def copy(self):
        c = Patch(bytes(self.preset))
        c.touched = dict(self.touched)
        return c

    def __getitem__(self, name):
        return self.preset[PARAMS[name]["offset"]]

    def __setitem__(self, name, value):
        p = PARAMS[name]
        v = int(round(value))
        if not p["min"] <= v <= p["max"]:
            raise ValueError(f"{name}={v} outside {p['min']}..{p['max']}")
        self.preset[p["offset"]] = v
        self.touched[p["offset"]] = name

    def set(self, **kwargs):
        """Set by Python-friendly names: Filter_Env_Amount=60 -> 'Filter Env Amount'."""
        for k, v in kwargs.items():
            self[k.replace("_", " ")] = v
        return self

    @property
    def name(self):
        return bytes(self.preset[NAME_INDEX:NAME_INDEX + NAME_LEN]).decode("ascii", "replace")

    @name.setter
    def name(self, value):
        raw = value.encode("ascii")[:NAME_LEN].ljust(NAME_LEN, b" ")
        self.preset[NAME_INDEX:NAME_INDEX + NAME_LEN] = raw

    def to_syx(self, bank=0x00, program=0x40, device=0x10):
        msg = bytearray([0xF0, 0x00, 0x20, 0x33, 0x01, device, 0x10, bank, program])
        msg += self.preset[:256]
        msg.append(sum(msg[5:]) & 0x7F)
        msg += self.preset[256:]
        msg.append(sum(msg[5:]) & 0x7F)
        msg.append(0xF7)
        assert len(msg) == DUMP_SIZE
        return bytes(msg)

    def save(self, path, **kw):
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(path).write_bytes(self.to_syx(**kw))

    def diff(self, other):
        """Named parameters whose values differ from another Patch."""
        out = {}
        seen = set()
        for n, p in PARAMS.items():
            # several names alias one byte (per oscillator/FX mode); report the first
            if p["offset"] in seen or n.startswith("SingleName"):
                continue
            seen.add(p["offset"])
            a, b = self.preset[p["offset"]], other.preset[p["offset"]]
            if a != b:
                out[self.touched.get(p["offset"], PRIMARY[p["offset"]])] = (b, a)
        return out


if __name__ == "__main__":
    import sys
    pat = sys.argv[1] if len(sys.argv) > 1 else "."
    init = Patch.from_syx()
    for n in find(pat):
        p = PARAMS[n]
        print(f"{p['page']:#x}/{p['index']:3d}  {n:32s} {p['min']:3d}..{p['max']:3d}  init={init[n]:3d}  {p.get('toText', '')}")
