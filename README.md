# Volumetric scene render

This is a generic procedural scene. It contains no source footage, studio names, titles, logos, or project files.

The rendered result is one uninterrupted 40-second camera move through a stationary 3D density field. Every frame is computed from the same field and linear scene clock. The rendering pipeline generates 960 frames at 1280 × 720 and 24 fps. It uses a single midnight-blue palette and three distant warm points of light.

To build the density field: `python build_volume.py`.
To check five frames: `node render.cjs preview`.
To render the full video: `node render.cjs full`.

The preview frames are an internal quality gate. A visually weak scene should be revised before full rendering. No output from this repository should be described as a match to any private reference until it has been compared locally.
