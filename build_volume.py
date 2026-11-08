"""Build a continuous 3D cloud density field from generic cloud materials."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, zoom


ROOT = Path(__file__).parent
SHAPE = (512, 216, 384)  # depth, height, width
OUT = ROOT / "density.r8"
rng = np.random.default_rng(28175)


def material(name):
    image = Image.open(ROOT / name).convert("RGB")
    image = image.resize((SHAPE[2], SHAPE[1]), Image.Resampling.LANCZOS)
    rgb = np.asarray(image, dtype=np.float32) / 255.0
    blue = rgb[:, :, 2]
    return np.clip((blue - 0.025) / 0.69, 0, 1)


materials = [material(f"cloud_{letter}.png") for letter in "abc"]
rough_grid = rng.random((64, 36, 64), dtype=np.float32)
rough = zoom(rough_grid, (8, 6, 6), order=1, mode="reflect")
rough = rough[: SHAPE[0], : SHAPE[1], : SHAPE[2]]
out = np.memmap(OUT, dtype=np.uint8, mode="w+", shape=SHAPE)
y, x = np.mgrid[0 : SHAPE[1], 0 : SHAPE[2]].astype(np.float32)
centers = np.array((0.07, 0.48, 0.91), dtype=np.float32)

for z in range(SHAPE[0]):
    phase = z / (SHAPE[0] - 1)
    weights = np.exp(-((phase - centers) / 0.25) ** 2)
    weights /= weights.sum()
    dx = 12 * np.sin(phase * 7.7 + y * 0.013) + 5 * np.sin(phase * 15.9 + y * 0.041)
    dy = 8 * np.sin(phase * 9.1 + x * 0.012) + 3 * np.sin(phase * 19.2 + x * 0.037)
    coords = (y + dy, x + dx)
    plane = sum(
        weight * map_coordinates(image, coords, order=1, mode="reflect")
        for weight, image in zip(weights, materials)
    )
    density = np.clip(plane * (0.88 + 0.44 * rough[z]) + 0.17 * (rough[z] - 0.5), 0, 1)
    density = density * density * (3 - 2 * density)
    out[z] = np.rint(density * 255).astype(np.uint8)

out.flush()
print(f"Wrote {OUT.name}: {OUT.stat().st_size} bytes, mean density={out.mean():.3f}")
