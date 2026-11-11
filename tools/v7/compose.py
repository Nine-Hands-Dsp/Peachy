#!/usr/bin/env python3
"""Peachy v2 (design v7 du pack NINE HANDS | DSP) : composition de l'apercu a partir des calques du pack.
Potard = couronne (tourne) -> reflet masque par l'alpha de la couronne tournee (fixe) -> centre (fixe) -> index (tourne),
grade d'exposition x0.80 du designer, reduction en une fois (alpha premultiplie). Inverseur : kit photo (3 positions)."""
import json, sys, os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.abspath(os.path.join(H, '..', '..'))
D = os.path.join(P, 'design', 'v7')
L = json.load(open(os.path.join(D, 'layout.json')))
ld = lambda p: np.array(Image.open(os.path.join(D, p)).convert('RGBA')).astype(np.float32) / 255.0
KN = {n: ld(f'knob/{n}.png') for n in ('crown_rotating', 'reflect_masked', 'center_fixed', 'indicator_08')}

def rot(a, deg):   # rotation horaire positive autour de (399.5, 399.5), alpha premultiplie
    pm = a.copy(); pm[..., :3] *= pm[..., 3:4]
    M = cv2.getRotationMatrix2D((399.5, 399.5), -deg, 1.0)
    r = cv2.warpAffine(pm, M, (800, 800), flags=cv2.INTER_CUBIC, borderValue=0)
    return np.clip(r, 0, 1)

def over(dst, src):  # premultiplie
    return src + dst * (1 - src[..., 3:4])

def pm(a):
    b = a.copy(); b[..., :3] *= b[..., 3:4]; return b

def knob800(deg, blur=0.0, n=1):
    """blur = demi-amplitude du flou (deg) ; n positions moyennees (couronne + index flous ensemble)"""
    angs = [deg] if blur <= 0 else [deg - blur * (k / (n - 1)) for k in range(n)]
    cr = sum(rot(KN['crown_rotating'], a) for a in angs) / len(angs)
    ind = sum(rot(KN['indicator_08'], a) for a in angs) / len(angs)
    rf = pm(KN['reflect_masked']); rf *= cr[..., 3:4]          # A_reflect * A_crown_rotated
    out = cr.copy(); out = over(out, rf); out = over(out, pm(KN['center_fixed'])); out = over(out, ind)
    return out

def down(pm800, size, exposure=0.80):
    s = cv2.resize(pm800, (size, size), interpolation=cv2.INTER_AREA)
    s[..., :3] *= exposure
    return s

def composite(bg, spr_pm, x, y):
    h, w = spr_pm.shape[:2]
    bg[y:y + h, x:x + w] = over(bg[y:y + h, x:x + w], spr_pm)

def straight_to_pm(u8):
    a = u8.astype(np.float32) / 255.0; return pm(a)

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--deg', type=float, default=33); ap.add_argument('--out', default='preview.png')
    ap.add_argument('--switch', default='ON'); ap.add_argument('--text', default='P8  Wall of Sludge'); ap.add_argument('--leds', default='11')
    a = ap.parse_args()
    bg = pm(ld('background/pedal_background_widgets_free.png'))
    k8 = knob800(a.deg)
    for k in L['knobs']['items']:
        composite(bg, down(k8, k['frame_size']), k['x'], k['y'])
    # inverseur : kit photo (haut / milieu / bas superposes), sans ombre ajoutee (ombre de la rondelle cuite dans le fond)
    sys.path.insert(0, os.path.join(P, 'tools', 'v7'))
    import toggle_kit
    fr = toggle_kit.frames()
    t = L['octave_switch']; wx, wy = t['washer_center']
    f = {'ON': fr[0], 'MID': fr[1], 'OFF': fr[2]}[a.switch.upper()]
    s = f.shape[0]; composite(bg, straight_to_pm(f), int(round(wx - s / 2)), int(round(wy - s / 2)))
    led = pm(ld('sprites/led_lit_65.png'))
    for i, l in enumerate(L['leds']):
        if a.leds[i] == '1': composite(bg, led, l['x'], l['y'])
    out = Image.fromarray((np.clip(bg[..., :3] / np.maximum(bg[..., 3:4], 1e-4), 0, 1) * 255).astype(np.uint8))
    out.putalpha(Image.fromarray((bg[..., 3] * 255).astype(np.uint8)))
    d = L['display']; ss = 4
    font = ImageFont.truetype(os.path.join(D, 'fonts', 'Inter-Medium.otf'), d['text']['size_px'] * ss)
    lay = Image.new('L', (out.width * ss, out.height * ss), 0)
    bb, cap = font.getbbox(a.text, anchor='ls'), font.getbbox('H', anchor='ls'); cx, cy = d['center']
    ImageDraw.Draw(lay).text((cx * ss - (bb[0] + bb[2]) / 2.0, cy * ss - (cap[1] + cap[3]) / 2.0), a.text, font=font, fill=255, anchor='ls')
    lay = lay.resize(out.size, Image.LANCZOS)
    col = Image.new('RGBA', out.size, tuple(d['text']['color_rgb']) + (255,)); col.putalpha(lay)
    out.alpha_composite(col); out.save(a.out)
