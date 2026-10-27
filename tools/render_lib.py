"""In-process helpers for rendering both synths and measuring the results.

render_virus() shells out to virusRender (fast, deterministic); render_obxf() runs the
OB-Xf engine in-process. Both return mono float arrays starting at note on, at 44.1 kHz.
"""
import os
import pathlib
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy.io import wavfile
from scipy.signal import stft

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "third_party" / "obxf" / "build" / "src" / "obxf-python"))

import obxfpy  # noqa: E402
from obxf_render import find_patch  # noqa: E402

RATE = 44100
VIRUS = ROOT / "build" / "virusRender" / "virusRender"
ROM = ROOT / "rom" / "firmware.bin"
SLOP_PARAMS = ["EnvelopeSlop", "FilterSlop", "LevelSlop", "PortamentoSlop"]


def render_virus(patch, notes=(60,), hold=1.5, tail=1.5, vel=100):
    with tempfile.TemporaryDirectory() as tmp:
        syx = os.path.join(tmp, "p.syx")
        wav = os.path.join(tmp, "p.wav")
        patch.save(syx)
        subprocess.run([str(VIRUS), "--rom", str(ROM), "--syx", syx, "--notes", ",".join(map(str, notes)),
                        "--vel", str(vel), "--hold", str(hold), "--tail", str(tail), "--out", wav],
                       check=True, capture_output=True, close_fds=False)  # posix_spawn, not fork: see FINDINGS
        _, data = wavfile.read(wav)
    return data.astype(np.float64).mean(axis=1)


def render_virus_seq(patch, seq, tail=2.0, stereo=False):
    """Play a note list: seq = [(start s, length s, note, velocity), ...] from the first note on.
    Mono unless stereo=True (then shape (n, 2))."""
    with tempfile.TemporaryDirectory() as tmp:
        syx, wav, txt = (os.path.join(tmp, f) for f in ("p.syx", "p.wav", "p.seq"))
        patch.save(syx)
        with open(txt, "w") as f:
            f.writelines(f"{t:.6f} {d:.6f} {n} {v}\n" for t, d, n, v in seq)
        subprocess.run([str(VIRUS), "--rom", str(ROM), "--syx", syx, "--seq", txt, "--tail", str(tail),
                        "--out", wav], check=True, capture_output=True, close_fds=False)
        _, data = wavfile.read(wav)
    data = data.astype(np.float64)
    return data if stereo else data.mean(axis=1)


def render_virus_many(patches, **kw):
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as ex:
        return list(ex.map(lambda p: render_virus(p, **kw), patches))


def render_obxf(name, overrides=None, notes=(60,), hold=1.5, tail=1.5, vel=100, slop=False):
    eng = obxfpy.ObxfEngine(float(RATE))
    if name:  # None = the engine's default patch: one saw, filter open, no modulation
        eng.load_patch(str(find_patch(name)))
    if not slop:
        for p in SLOP_PARAMS:
            eng.set_param(p, 0.0)
    for k, v in (overrides or {}).items():
        eng.set_param(k, v)
    eng.process(RATE // 2)
    for n in notes:
        eng.note_on(n, vel)
    a = eng.process(int(hold * RATE))
    for n in notes:
        eng.note_off(n, 64)
    b = eng.process(int(tail * RATE))
    return (np.concatenate([a[0], b[0]]) + np.concatenate([a[1], b[1]])) / 2


def level_db(x, win_ms=10):
    n = int(RATE * win_ms / 1000)
    frames = len(x) // n
    rms = np.sqrt(np.mean(x[: frames * n].reshape(frames, n) ** 2, axis=1) + 1e-12)
    return 20 * np.log10(rms)


def centroid(x, nperseg=2048):
    f, _, z = stft(x, RATE, nperseg=nperseg, noverlap=nperseg * 3 // 4)
    mag = np.abs(z)
    c = (f[:, None] * mag).sum(axis=0) / (mag.sum(axis=0) + 1e-12)
    return np.log2(np.maximum(c, 20.0))  # octaves, so errors weigh evenly across the range


BAND_EDGES = 100 * 2 ** (np.arange(0, 22) / 3)  # third-octave bands, 100 Hz .. ~16 kHz


def band_shape(x, nperseg=2048, smooth_frames=4):
    """Third-octave band levels per frame, in dB relative to that frame's loudest band.

    Captures filter slope and resonant bumps, which a single centroid number can't.
    Frames are smoothed a little so detuned-saw beating doesn't dominate.
    """
    f, _, z = stft(x, RATE, nperseg=nperseg, noverlap=nperseg * 3 // 4)
    p = np.abs(z) ** 2
    bands = np.array([p[(f >= lo) & (f < hi)].sum(axis=0) for lo, hi in zip(BAND_EDGES[:-1], BAND_EDGES[1:])])
    if smooth_frames > 1:
        k = np.ones(smooth_frames) / smooth_frames
        bands = np.array([np.convolve(b, k, mode="same") for b in bands])
    db = 10 * np.log10(bands + 1e-14)
    return db - db.max(axis=0, keepdims=True)  # bands x frames


def band_loss(target_bands, target_level, x, gate_db=-45, floor=-70):
    """Mean |dB| difference of band shapes while the target is audible."""
    b = band_shape(x)
    n = min(target_bands.shape[1], b.shape[1])
    hop = len(target_level) / max(1, target_bands.shape[1])
    lev = np.array([target_level[min(len(target_level) - 1, int(i * hop))] for i in range(n)])
    mask = lev > target_level.max() + gate_db
    d = np.abs(np.maximum(target_bands[:, :n], floor) - np.maximum(b[:, :n], floor))
    return float(d[:, mask].mean()) if mask.any() else 0.0


def shape_loss(level_a, level_b, floor=-60):
    """Compare level envelopes after normalising each to its own peak."""
    a = np.maximum(level_a - level_a.max(), floor)
    b = np.maximum(level_b - level_b.max(), floor)
    n = min(len(a), len(b))
    return float(np.mean(np.abs(a[:n] - b[:n])))


def centroid_loss(x, y, level_x, gate_db=-45):
    """Mean octave distance between brightness curves while the target is audible."""
    cx, cy = centroid(x), centroid(y)
    n = min(len(cx), len(cy))
    # gate on the target's loudness so silent tails don't dominate
    hop = len(level_x) / max(1, len(cx))
    lev = np.array([level_x[min(len(level_x) - 1, int(i * hop))] for i in range(n)])
    mask = lev > level_x.max() + gate_db
    return float(np.mean(np.abs(cx[:n] - cy[:n])[mask])) if mask.any() else 0.0


def render_obxf_seq(name, seq, tail=2.0, slop=True, overrides=None, stereo=False):
    """OB-Xf version of render_virus_seq, sample-accurate. name None = default patch (see render_obxf)."""
    eng = obxfpy.ObxfEngine(float(RATE))
    if name:
        eng.load_patch(str(find_patch(name)))
    if not slop:
        for p in SLOP_PARAMS:
            eng.set_param(p, 0.0)
    for k, v in (overrides or {}).items():
        eng.set_param(k, v)
    eng.process(RATE // 2)
    events = sorted([(int(t * RATE), 1, n, v) for t, d, n, v in seq] +
                    [(int((t + d) * RATE), 0, n, 64) for t, d, n, v in seq])  # offs first at equal times
    end = max(f for f, *_ in events) + int(tail * RATE)
    out, pos = [], 0
    for f, on, n, v in events + [(end, None, 0, 0)]:
        if f > pos:
            out.append(eng.process(f - pos))
            pos = f
        if on == 1:
            eng.note_on(n, v)
        elif on == 0:
            eng.note_off(n, v)
    left, right = np.concatenate([o[0] for o in out]), np.concatenate([o[1] for o in out])
    return np.stack([left, right], axis=1) if stereo else (left + right) / 2
