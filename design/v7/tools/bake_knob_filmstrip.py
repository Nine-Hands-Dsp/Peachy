#!/usr/bin/env python3
"""
Bake a vertical knob filmstrip from the layered 800 px knob sprites (rules: see docs/RULES.md, section KNOBS).

Layers (bottom -> top):  crown (ROTATES) -> reflect_masked (STATIC, alpha multiplied by the ROTATED crown alpha)
                         -> center (STATIC) -> indicator (ROTATES, same angle as the crown).
Rotation is clockwise-positive, 0 deg = 12 o'clock, pivot = (400, 400).
Each frame is composited at 800 px and downscaled ONCE (area filter) - never rotate pre-downscaled layers.

Requires: pip install pillow numpy opencv-python
Example (what the pedal design uses):
  python bake_knob_filmstrip.py --layers ../knob_sources_800px \
      --prefix knob_12_peachy02_metal_bevel_lip_ --indicator indicator_08_dash_white_half_radius.png \
      --body-diameter 264 --frames 128 --min-deg -135 --max-deg 135 --exposure 0.80 \
      --out ../sprites/knob_big_filmstrip_128.png
"""
import argparse, os
import numpy as np
import cv2
from PIL import Image

def render_frame(crown, reflect_masked, center, indicator, deg):
    c = crown.rotate(-deg, resample=Image.BICUBIC, center=(400, 400))
    rf = reflect_masked.copy()
    a = np.asarray(rf)[..., 3].astype(np.float32) * np.asarray(c)[..., 3].astype(np.float32) / 255.0
    rf.putalpha(Image.fromarray(np.round(a).astype(np.uint8)))
    out = Image.new("RGBA", (800, 800), (0, 0, 0, 0))
    out.alpha_composite(c)
    out.alpha_composite(rf)
    out.alpha_composite(center)
    out.alpha_composite(indicator.rotate(-deg, resample=Image.BICUBIC, center=(400, 400)))
    return out

def downscale(img800, size, exposure):
    arr = np.asarray(img800).astype(np.float32)
    rgb, al = arr[..., :3] * exposure, arr[..., 3] / 255.0           # exposure = design-level grade (0.80 for the Peachy pedal)
    pm = cv2.resize(rgb * al[..., None], (size, size), interpolation=cv2.INTER_AREA)   # premultiplied -> no dark fringes
    aa = cv2.resize(al.astype(np.float32), (size, size), interpolation=cv2.INTER_AREA)
    out_rgb = np.clip(pm / np.maximum(aa[..., None], 1e-4), 0, 255)
    return np.dstack([out_rgb, aa * 255.0]).round().astype(np.uint8)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", required=True); ap.add_argument("--prefix", required=True)
    ap.add_argument("--indicator", required=True)
    ap.add_argument("--body-diameter", type=float, required=True, help="final diameter in px of the continuous body (lip, r=390 of 400)")
    ap.add_argument("--frames", type=int, default=128)
    ap.add_argument("--min-deg", type=float, default=-135.0); ap.add_argument("--max-deg", type=float, default=135.0)
    ap.add_argument("--exposure", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    L = lambda n: Image.open(os.path.join(a.layers, n)).convert("RGBA")
    crown, reflect, center = L(a.prefix + "crown_rotating.png"), L(a.prefix + "reflect_masked.png"), L(a.prefix + "center_fixed.png")
    indicator = L(a.indicator)
    size = int(round(a.body_diameter * 800.0 / 780.0))
    frames = []
    for i in range(a.frames):
        deg = a.min_deg + (a.max_deg - a.min_deg) * i / max(a.frames - 1, 1)
        frames.append(downscale(render_frame(crown, reflect, center, indicator, deg), size, a.exposure))
    strip = np.concatenate(frames, axis=0)
    Image.fromarray(strip, "RGBA").save(a.out, optimize=True)
    print(f"{a.out}: {a.frames} frames of {size}x{size}px, {a.min_deg}..{a.max_deg} deg, exposure {a.exposure}")

if __name__ == "__main__":
    main()
