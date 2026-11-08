"""Create a deterministic, continuous 3D density field from gradient noise.

This code contains no external footage, names, titles, or private assets.
"""
from pathlib import Path

import numpy as np
from scipy.ndimage import zoom


SHAPE = (512, 144, 256)  # depth, height, width
OUT = Path(__file__).with_name("density.r8")
rng = np.random.default_rng(28175)


def octave(coarse, strength):
    grid = rng.random(coarse, dtype=np.float32)
    scaled = zoom(grid, tuple(s / c for s, c in zip(SHAPE, coarse)), order=3, mode="reflect")
    scaled = scaled[: SHAPE[0], : SHAPE[1], : SHAPE[2]]
    lo, hi = np.percentile(scaled, (7, 93))
    return np.clip((scaled - lo) / (hi - lo), 0, 1).astype(np.float32) * strength


# All three axes are continuous. Broad banks contain finer folds, without
# spherical objects, cellular noise, repeated video slices, or a loop boundary.
field = octave((12, 5, 8), 0.48)
field += octave((33, 12, 22), 0.32)
field += octave((92, 36, 64), 0.20)
density = np.clip((field - 0.48) / 0.30, 0, 1)
density = density * density * (3 - 2 * density)
OUT.write_bytes(np.rint(density * 255).astype(np.uint8).tobytes())
print(f"Wrote {OUT.name}: {OUT.stat().st_size} bytes, mean density={density.mean():.3f}")
