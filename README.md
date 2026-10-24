# virus

Oberheim-style patches for the Access Virus TI2, generated as SysEx and
auditioned through an emulator before loading onto the hardware.

## Plan

1. **Generate** — write Single Dump `.syx` files by patching documented bytes
   into a real INIT dump captured from the TI2, then recalculating the checksum.
2. **Render** — load each `.syx` into a headless OsTIrus build (Gearmulator,
   running the original TI firmware), play notes, and write a WAV.
3. **Analyze** — measure the render (spectrum over time, envelopes, detune beat
   rate) against reference recordings and adjust the patch.
4. **Audition** — send the finished `.syx` to the TI2 edit buffer and save the
   keepers by hand.

**Read [docs/FINDINGS.md](docs/FINDINGS.md) first** — it records what we've
learned about the format, the controls and the tooling.

## Setup

```sh
python3 -m venv .venv && .venv/bin/pip install numpy scipy matplotlib
./build.sh      # clones Gearmulator + OB-Xf into third_party/, builds virusRender and the obxfpy module
```

`tools/third_party_patches/` holds a small fix applied to OB-Xf's Python
bindings (they lagged an engine type change in the mod matrix).

Put the TI firmware at `rom/firmware.bin`. It ships inside the Virus TI
Software Suite installer at
`Library/Application Support/Access Music/Virus TI/Common/firmware.bin`
(`pkgutil --expand-full` the `.pkg` to get it without installing).

## Rendering

```sh
R=build/virusRender/virusRender
$R --rom rom/firmware.bin --list                                   # ROM singles
$R --rom rom/firmware.bin --preset OberBrssMS --export-syx x.syx   # ROM single -> .syx
$R --rom rom/firmware.bin --syx x.syx --notes 48,55,60,64 \
   --hold 1.5 --tail 1.5 --out renders/x.wav --dump-out renders/x-ti.syx
.venv/bin/python tools/analyze.py renders/x.wav --png renders/x.png
```

`--dump-out` saves the edit buffer as the firmware holds it after loading.
ROM singles in the older format come back upgraded to TI format (version
byte `0C`); `patches/reference/init-ti.syx` is the upgraded `-INIT-` and is
the template for generated patches. Renders are bit-identical across runs.

## OB-Xf reference renders

```sh
.venv/bin/python tools/obxf_render.py --list Brass
.venv/bin/python tools/obxf_render.py "Obright Original" --notes 48,55,60,64 \
   --hold 1.5 --tail 1.5 --out renders/obxf_obright.wav --params renders/obxf_obright.json
```

Same timing and sample rate as `virusRender`, so renders line up in
`tools/analyze.py`. `--params` dumps the patch's 104 parameter values, which
is what gets translated to Virus settings. OB-Xf renders are *not*
bit-identical between runs: its "slop" parameters add random analog drift.

## Single Dump layout (from Gearmulator)

524 bytes: `F0 00 20 33 01 <dev> 10 <bank> <prog>`, preset bytes `0..255`,
checksum, preset bytes `256..511`, checksum, `F7`. Each checksum is the sum
of everything from `<dev>` up to it, `& 0x7F`. A parameter at live-edit page
`70`/`71`/`6E`/`6F`, param `p` lives at preset byte `page_index * 128 + p`.

## References

- SysEx spec: <https://github.com/redconfetti/access-virus-ti-sysex>
- Emulator: <https://github.com/dsp56300/gearmulator> (OsTIrus, GPLv3)

## Not in the repo

- Virus TI firmware / ROM files — supplied locally from Access's official OS
  updater, never committed.
