"""Generates rift_flow.png, the flowing-energy texture on the rift ribbons
(build spec §7.8, GameConfig.Rift.FlowTexture).

White with an alpha pattern: the Beam's Color tints it, so one texture serves
the rarity-coloured entrance and the crimson exit. U runs ALONG the beam and
wraps exactly (every wave has a whole number of cycles), so a scrolling
TextureSpeed never shows a seam. V runs across the beam and fades to nothing
at both edges, so the ribbon has soft sides.

    python make_rift_flow.py        (needs numpy and pillow)
"""

import os

import numpy as np
from PIL import Image

W, H = 512, 128
HERE = os.path.dirname(os.path.abspath(__file__))

u = np.linspace(0.0, 1.0, W, endpoint=False)[None, :]
v = np.linspace(0.0, 1.0, H)[:, None]
rng = np.random.default_rng(7)

alpha = np.zeros((H, W))
# Soft streaks that meander across the ribbon. Integer frequencies wrap in U.
for i in range(9):
    k = int(rng.integers(1, 4))                  # meander cycles along the beam
    m = int(rng.integers(2, 7))                  # brightness cycles along the beam
    centre = 0.5 + 0.30 * np.sin(2 * np.pi * (k * u + rng.random())) * (0.4 + 0.6 * rng.random())
    width = 0.035 + 0.05 * rng.random()
    streak = np.exp(-(((v - centre) / width) ** 2))
    pulse = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2 * np.pi * (m * u + rng.random())))
    alpha += streak * pulse * (0.45 + 0.4 * rng.random())

# A bright core thread down the middle, so the ribbon has a spine.
core_c = 0.5 + 0.08 * np.sin(2 * np.pi * (2 * u + 0.3))
alpha += 0.55 * np.exp(-(((v - core_c) / 0.045) ** 2))

# Fine periodic grain, so the flow reads as moving energy and not smooth bands.
grain = 0.5 + 0.5 * np.sin(2 * np.pi * (23 * u + 5 * v) + 2 * np.sin(2 * np.pi * (3 * u)))
alpha *= 0.82 + 0.18 * grain

# Soft sides.
alpha *= np.clip(np.sin(np.pi * v), 0, 1) ** 1.4

alpha = np.clip(alpha, 0.0, 1.0)
rgba = np.zeros((H, W, 4), dtype=np.uint8)
rgba[..., :3] = 255
rgba[..., 3] = (alpha * 255).astype(np.uint8)
Image.fromarray(rgba, "RGBA").save(os.path.join(HERE, "rift_flow.png"))
print("wrote rift_flow.png", W, "x", H)
