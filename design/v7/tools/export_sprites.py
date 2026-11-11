#!/usr/bin/env python3
"""Export the octave-switch sprites (ON / OFF) and the LED sprite at their final pedal size.
Requires: pip install pillow numpy opencv-python        Run from the pack root:  python tools/export_sprites.py"""
import json, numpy as np, cv2
from PIL import Image

def premul_resize(rgb, a, size):
    pm = cv2.resize(rgb * a[..., None], size, interpolation=cv2.INTER_AREA)
    aa = cv2.resize(a, size, interpolation=cv2.INTER_AREA)
    return np.clip(pm / np.maximum(aa[..., None], 1e-4), 0, 255), aa

def save_rgba(rgb, a, path):
    Image.fromarray(np.dstack([rgb, a * 255.0]).round().astype(np.uint8), "RGBA").save(path, optimize=True)

TOGGLE_CENTER = (2042.5, 765.0)      # centre of the washer in the design (px)
WASHER_R = 41.5                      # washer radius in the design (px)
ix = lambda v: int(round(v))
out = {}

# --- octave switch: washer of the source image fitted to the design's 41.5 px disc, lever sticks out (down in OFF, up in ON)
for state, (f, (ccx, ccy, rr)) in {"OFF": ("switch_OFF_4K.png", (1923.9, 1078.3, 662.8)), "ON": ("switch_ON_4K.png", (1924.1, 1148.0, 661.6))}.items():
    k = np.array(Image.open("source_assets/" + f).convert("RGBA")).astype(np.float32)
    rgb, al = k[..., :3], k[..., 3] / 255.0
    ys, xs = np.where(al > 0.04)
    bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    sc = WASHER_R / rr
    nw, nh = int(round((bx1 - bx0) * sc)), int(round((by1 - by0) * sc))
    r, a = premul_resize(rgb[by0:by1, bx0:bx1], al[by0:by1, bx0:bx1].astype(np.float32), (nw, nh))
    x0 = ix(TOGGLE_CENTER[0] - (ccx - bx0) * sc); y0 = ix(TOGGLE_CENTER[1] - (ccy - by0) * sc)
    save_rgba(r, a, f"sprites/toggle_{state}.png")
    out[f"toggle_{state}"] = {"file": f"sprites/toggle_{state}.png", "x": x0, "y": y0, "w": nw, "h": nh}

# --- LED (lit): Diode_Rouge_Custom.png scaled to 65 px
im = np.array(Image.open("source_assets/Diode_Rouge_Custom.png").convert("RGBA")).astype(np.float32)
rgb, al = im[..., :3], im[..., 3] / 255.0
ys, xs = np.where(al > 0.5)
x0_, x1_, y0_, y1_ = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
r, a = premul_resize(rgb[y0_:y1_, x0_:x1_], al[y0_:y1_, x0_:x1_].astype(np.float32), (65, 65))
save_rgba(r, a, "sprites/led_lit_65.png")
out["led"] = {"file": "sprites/led_lit_65.png", "w": 65, "h": 65}
json.dump(out, open("layout/_sprite_offsets.json", "w"), indent=2)
print(json.dumps(out, indent=2))
