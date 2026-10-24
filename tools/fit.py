"""Fit Virus parameters so its render matches an OB-Xf reference.

Coordinate search: each round tries +/- step on every free parameter (rendered in
parallel), keeps any improvement, and halves the step when nothing improves.
"""
import numpy as np

from render_lib import (band_loss, band_shape, centroid, centroid_loss, level_db, render_obxf,
                        render_virus_many, shape_loss)


def obxf_target(name, overrides=None, runs=3, **kw):
    """Average several OB-Xf renders: it adds a little noise and random phase each run."""
    xs = [render_obxf(name, overrides, **kw) for _ in range(runs)]
    n = min(len(x) for x in xs)
    levels = np.mean([level_db(x[:n]) for x in xs], axis=0)
    return xs[0][:n], levels


def coordinate_search(base, free, loss_fn, start_step=16, min_step=1, max_rounds=40, log=print):
    """base: Patch. free: {param name: (lo, hi)}. loss_fn(list of renders) -> list of losses."""
    current = base
    best = loss_fn([current])[0]
    step = start_step
    rounds = 0
    log(f"start loss {best:.4f}")
    while step >= min_step and rounds < max_rounds:
        rounds += 1
        candidates, labels = [], []
        for name, (lo, hi) in free.items():
            for d in (-step, step):
                v = min(hi, max(lo, current[name] + d))
                if v == current[name]:
                    continue
                c = current.copy()
                c[name] = v
                candidates.append(c)
                labels.append((name, v))
        losses = loss_fn(candidates)
        i = int(np.argmin(losses))
        if losses[i] < best - 1e-4:
            best = losses[i]
            current = candidates[i]
            log(f"  step {step:2d}: {labels[i][0]} = {labels[i][1]}  loss {best:.4f}")
        else:
            step //= 2
    return current, best


def level_fit_loss(target_level, **render_kw):
    def fn(patches):
        return [shape_loss(target_level, level_db(x)) for x in render_virus_many(patches, **render_kw)]
    return fn


def obxf_band_target(name, overrides=None, runs=3, **kw):
    """Averaged band shapes and level for an OB-Xf reference (see render_lib.band_shape)."""
    xs = [render_obxf(name, overrides, **kw) for _ in range(runs)]
    n = min(len(x) for x in xs)
    bands = np.mean([band_shape(x[:n]) for x in xs], axis=0)
    levels = np.mean([level_db(x[:n]) for x in xs], axis=0)
    return bands, levels


def spectral_fit_loss_multi(targets, level_weight=0.1):
    """Band-shape match (dB) over several examples, plus a little level-shape match.

    targets: [(bands, level, render_kw)] from obxf_band_target.
    """
    def fn(patches):
        total = np.zeros(len(patches))
        for bands, level, kw in targets:
            for i, x in enumerate(render_virus_many(patches, **kw)):
                total[i] += band_loss(bands, level, x) + level_weight * shape_loss(level, level_db(x))
        return list(total / len(targets))
    return fn


def tone_fit_loss_multi(targets, level_weight=0.05):
    """Sum of tone_fit_loss over several examples. targets: [(target_x, target_level, render_kw)]."""
    fns = [tone_fit_loss(x, lv, level_weight, **kw) for x, lv, kw in targets]

    def fn(patches):
        return list(np.sum([f(patches) for f in fns], axis=0) / len(fns))
    return fn


def tone_fit_loss(target_x, target_level, level_weight=0.05, **render_kw):
    """Brightness-over-time match plus a little level-shape match (dB -> comparable scale)."""
    def fn(patches):
        out = []
        for x in render_virus_many(patches, **render_kw):
            lv = level_db(x)
            out.append(centroid_loss(target_x, x, target_level) + level_weight * shape_loss(target_level, lv))
        return out
    return fn
