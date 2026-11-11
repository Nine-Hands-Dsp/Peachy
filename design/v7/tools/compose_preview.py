#!/usr/bin/env python3
"""Assemble the full pedal from the pack layers (reference for how the GUI must be layered).
  python tools/compose_preview.py [--knob 0.5] [--switch ON|OFF] [--text "P8  Wall of Sludge"] [--out preview.png]
--knob = normalised value 0..1 applied to ALL knobs (frame = round(v*(N-1))).
Requires: pip install pillow numpy"""
import argparse, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("--knob", type=float, default=0.622); ap.add_argument("--switch", default="ON")
ap.add_argument("--text", default="P8  Wall of Sludge"); ap.add_argument("--out", default="preview.png")
a = ap.parse_args()
L = json.load(open("layout/layout.json"))
canvas = Image.open("background/pedal_background_widgets_free.png").convert("RGBA")

# knobs: one frame of the vertical filmstrip per knob (nothing is rotated at runtime)
N = L["knobs"]["filmstrip"]["frames"]
strips = {}
for k in L["knobs"]["items"]:
    if k["sprite"] not in strips: strips[k["sprite"]] = Image.open(k["sprite"]).convert("RGBA")
    f, s = round(a.knob * (N - 1)), k["frame_size"]
    canvas.alpha_composite(strips[k["sprite"]].crop((0, f * s, s, (f + 1) * s)), (k["x"], k["y"]))

# octave switch (2 states), LEDs (lit)
t = L["octave_switch"]["states"][a.switch.upper()]
canvas.alpha_composite(Image.open(t["file"]).convert("RGBA"), (t["x"], t["y"]))
led = Image.open("sprites/led_lit_65.png").convert("RGBA")
for l in L["leds"]:
    canvas.alpha_composite(led, (l["x"], l["y"]))

# display text: ink box centred horizontally, cap-height band centred vertically (supersampled x4)
d = L["display"]; ss = 4
font = ImageFont.truetype(d["text"]["font"], d["text"]["size_px"] * ss)
layer = Image.new("L", (canvas.width * ss, canvas.height * ss), 0)
bb, cap = font.getbbox(a.text, anchor="ls"), font.getbbox("H", anchor="ls")
cx, cy = d["center"]
ImageDraw.Draw(layer).text((cx * ss - (bb[0] + bb[2]) / 2.0, cy * ss - (cap[1] + cap[3]) / 2.0), a.text, font=font, fill=255, anchor="ls")
layer = layer.resize(canvas.size, Image.LANCZOS)
col = Image.new("RGBA", canvas.size, tuple(d["text"]["color_rgb"]) + (255,)); col.putalpha(layer)
canvas.alpha_composite(col)
canvas.save(a.out); print("saved", a.out)
