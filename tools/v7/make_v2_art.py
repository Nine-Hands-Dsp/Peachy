#!/usr/bin/env python3
"""Peachy v2 (pack design v7) : prepare toutes les images du plugin a partir du pack du designer.
  - background.png : fond 2350 x 1800 du pack (ombres cuites), inscriptions des jacks echangees (OUT a gauche, IN a droite)
  - knob_*.png     : calques 800 px du pack (couronne, reflet masque, centre, index), grade d'exposition x0.80 deja applique
  - led_on.png / led_off.png (65 px) + glow_led_l.png / glow_led_r.png (lumiere de la LED recue par la facade, alpha)
  - fs_down_l.png / fs_down_r.png : footswitch du pack enfonce (bouton plus petit et plus sombre, gorge ombree)
  - toggle_strip.png : inverseur du kit photo NINE HANDS | DSP (haut / milieu / bas)
  - Layout.h : reperes en unites du plugin (image / 2 = 1175 x 900)"""
import os, sys, json
import numpy as np, cv2
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.abspath(os.path.join(H, '..', '..')); D = os.path.join(P, 'design', 'v7')
L = json.load(open(os.path.join(D, 'layout.json')))
rd = lambda p: np.array(Image.open(os.path.join(D, p)).convert('RGBA')).astype(np.float32)
def save(a, name): Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(P, name), optimize=True)

# ---------------------------------------------------------------- fond : echange des inscriptions in / out
bg = rd('background/pedal_background_widgets_free.png')
cxL, cxR = 450 + 85, 1739 + 85                     # centres des jacks du haut
y0, y1, hw = 58, 102, 44
def patch(cx): return bg[y0:y1, cx - hw:cx + hw].copy()
pl, pr = patch(cxL), patch(cxR)
yy, xx = np.mgrid[0:y1 - y0, 0:2 * hw].astype(np.float32)
fe = np.clip(np.minimum.reduce([xx, 2 * hw - 1 - xx, yy * 2.5, (y1 - y0 - 1 - yy) * 2.5]) / 10.0, 0, 1)[..., None]
bg[y0:y1, cxL - hw:cxL + hw] = pr * fe + pl * (1 - fe)
bg[y0:y1, cxR - hw:cxR + hw] = pl * fe + pr * (1 - fe)
save(bg, 'background.png')

# ---------------------------------------------------------------- potards : calques du pack, exposition x0.80
for src, dst in (('crown_rotating', 'knob_crown'), ('reflect_masked', 'knob_reflect'), ('center_fixed', 'knob_center'), ('indicator_08', 'knob_indicator')):
    a = rd(f'knob/{src}.png'); a[..., :3] *= 0.80; save(a, dst + '.png')

# ---------------------------------------------------------------- LED : allumee (pack) et eteinte (rendue a partir de la meme source)
led = rd('sprites/led_lit_65.png'); save(led, 'led_on.png')
n = 65; c = (n - 1) / 2.0
yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); r = np.hypot(xx - c, yy - c) / (n / 2.0)
lum = led[..., :3].mean(-1) / 255.0
detail = cv2.GaussianBlur(lum, (0, 0), 0.8) - cv2.GaussianBlur(lum, (0, 0), 4.0)          # relief de la lentille alveolee
dome = np.clip(1 - r ** 2, 0, 1) ** 0.5
lightdir = np.clip(1.0 - 0.55 * np.hypot((xx - c) / (n / 2) + 0.35, (yy - c) / (n / 2) + 0.35), 0, 1)   # lumiere en haut a gauche
body = np.stack([0.30, 0.035, 0.03]) * 255
off = body[None, None, :] * (0.35 + 0.65 * dome[..., None]) * (0.55 + 0.6 * lightdir[..., None])
off += (detail[..., None] * np.array([140, 40, 30]))
spec = np.exp(-(((xx - c * 0.62) ** 2 + (yy - c * 0.55) ** 2) / (2 * (n * 0.07) ** 2)))   # reflet fixe sur le dome
off += spec[..., None] * 150
offA = np.dstack([np.clip(off, 0, 255), led[..., 3]]); save(offA, 'led_off.png')

# ---------------------------------------------------------------- halo des LED : la facade recoit la lumiere (calque alpha)
col = np.array([1.0, 0.16, 0.08])
glow_rects = []
for i, l in enumerate(L['leds']):
    cx, cy = l['center']; R = 240
    x0, ya = int(cx - R), int(cy - R)
    crop = bg[ya:ya + 2 * R, x0:x0 + 2 * R, :3]
    yy, xx = np.mgrid[0:2 * R, 0:2 * R].astype(np.float32)
    d = np.hypot(xx + x0 - cx, yy + ya - cy)
    h = 30.0                                                     # hauteur de la source au-dessus de la facade (px)
    E = 2.6 * (h / np.sqrt(d ** 2 + h ** 2)) ** 3 + 0.25 * np.exp(-d / 95.0)      # cos / d^2 + diffusion large
    fo = np.clip((R - 8 - d) / 110.0, 0, 1); E *= fo * fo * (3 - 2 * fo)          # retombe a zero bien avant le bord : aucun carre visible
    E[d < 30] *= np.clip((d[d < 30] - 24) / 6.0, 0, 1)            # sous la lentille : rien (la LED est dessinee par-dessus)
    T = np.clip(crop * (1 + E[..., None] * col * 2.2) + (E[..., None] ** 2) * col * 18, 0, 255)
    optical = 70 * np.exp(-((d - 33) / 7.0) ** 2) * (d > 30)     # tres faible halo optique autour de la lentille
    T = np.clip(T + optical[..., None] * col, 0, 255)
    dlt = np.clip(T - crop, 0, None)
    A = np.max(dlt / np.maximum(255 - crop, 1e-3), axis=-1); A = np.clip(A, 0, 1)
    C = np.where(A[..., None] > 1e-4, crop + dlt / np.maximum(A[..., None], 1e-4), 0)
    save(np.dstack([np.clip(C, 0, 255), A * 255]), f'glow_led_{"lr"[i]}.png')
    glow_rects.append((x0, ya, 2 * R, 2 * R))

# ---------------------------------------------------------------- footswitch enfonce (photo du pack)
FS_R = 112; CAP_R = 101.0
fs_rects = []
for i, f in enumerate(L['footswitches']):
    cx, cy = f['center']
    x0, ya = int(round(cx - FS_R)), int(round(cy - FS_R)); S = 2 * FS_R
    crop = bg[ya:ya + S, x0:x0 + S].copy()
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); ccx, ccy = cx - x0, cy - ya
    d = np.hypot(xx - ccx, yy - ccy)
    k = 0.965
    M = np.float32([[k, 0, ccx * (1 - k)], [0, k, ccy * (1 - k) + 1.5]])          # descend un peu (lumiere haute)
    shr = cv2.warpAffine(crop, M, (S, S), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
    gap = crop.copy(); gap[..., :3] *= 0.22                                         # gorge plus profonde, plus sombre
    out = crop.copy()
    m_gap = np.clip((CAP_R + 4 - d) / 1.5, 0, 1)[..., None]
    out = gap * m_gap + out * (1 - m_gap)
    dd = np.hypot(xx - ccx, yy - (ccy + 1.5))
    m_cap = np.clip((CAP_R * k - dd) / 1.2, 0, 1)[..., None]
    capc = shr.copy(); capc[..., :3] *= 0.72
    # ombre interne cote lumiere (le rebord de la bague masque le haut gauche du bouton)
    ang = np.arctan2(yy - ccy, xx - ccx); edge = np.clip((dd - CAP_R * k * 0.80) / (CAP_R * k * 0.2), 0, 1)
    side = np.clip(0.5 - 0.5 * np.cos(ang - np.radians(-135)), 0, 1)
    capc[..., :3] *= (1 - 0.35 * (edge * side)[..., None])
    out = capc * m_cap + out * (1 - m_cap)
    a = np.clip((FS_R - 1 - d) / 1.5, 0, 1)                      # disque, transparent ailleurs
    out[..., 3] = 255 * a
    save(out, f'fs_down_{"lr"[i]}.png'); fs_rects.append((x0, ya, S, S))

# ---------------------------------------------------------------- inverseur : kit photo
sys.path.insert(0, H)
import toggle_kit
fr = toggle_kit.frames(); TS = fr[0].shape[0]
save(np.vstack(fr), 'toggle_strip.png')

# ---------------------------------------------------------------- Layout.h (unites = px / 2)
u = lambda v: v / 2.0
o = ['#pragma once', '#include <juce_graphics/juce_graphics.h>', '',
     '// Peachy v2 : reperes generes par tools/v7/make_v2_art.py a partir du pack design v7 (layout.json, 2350 x 1800 px)',
     '// unites du plugin = pixels du design / 2 (repere 1175 x 900)', 'namespace layout', '{',
     '    constexpr float baseW = 1175.0f, baseH = 900.0f;']
kn = L['knobs']['items']
o.append('    const juce::Point<float> knobPos[9] = { ' + ', '.join(f'{{ {u(k["center"][0]):.2f}f, {u(k["center"][1]):.2f}f }}' for k in kn) + ' };')
o.append('    const float knobFrame[9] = { ' + ', '.join(f'{u(k["frame_size"]):.2f}f' for k in kn) + ' };   // cote du calque 800 px (271 / 148 px)')
o.append('    const float knobHit[9] = { ' + ', '.join(f'{u(k["body_diameter"] if "body_diameter" in k else k["frame_size"] * 0.975) / 2:.2f}f' for k in kn) + ' };')
t = L['octave_switch']
o.append(f'    const juce::Point<float> togglePos {{ {u(t["washer_center"][0]):.2f}f, {u(t["washer_center"][1]):.2f}f }};')
o.append(f'    constexpr float toggleS = {u(TS):.2f}f;')
for i, l in enumerate(L['leds']):
    o.append(f'    const juce::Rectangle<float> led{"LR"[i]} {{ {u(l["x"]):.2f}f, {u(l["y"]):.2f}f, {u(l["size"]):.2f}f, {u(l["size"]):.2f}f }};')
    g = glow_rects[i]; o.append(f'    const juce::Rectangle<float> glow{"LR"[i]} {{ {u(g[0]):.2f}f, {u(g[1]):.2f}f, {u(g[2]):.2f}f, {u(g[3]):.2f}f }};')
for i, f in enumerate(L['footswitches']):
    o.append(f'    const juce::Point<float> fs{"LR"[i]} {{ {u(f["center"][0]):.2f}f, {u(f["center"][1]):.2f}f }};')
    g = fs_rects[i]; o.append(f'    const juce::Rectangle<float> fsDown{"LR"[i]} {{ {u(g[0]):.2f}f, {u(g[1]):.2f}f, {u(g[2]):.2f}f, {u(g[3]):.2f}f }};')
o.append(f'    constexpr float footR = {u(CAP_R + 8):.2f}f;           // zone d\'appui (bouton + bague)')
d = L['display']
o.append(f'    const juce::Rectangle<float> display {{ {u(d["rect"][0]):.2f}f, {u(d["rect"][1]):.2f}f, {u(d["rect"][2]):.2f}f, {u(d["rect"][3]):.2f}f }};')
o.append(f'    const juce::Point<float> displayCentre {{ {u(d["center"][0]):.2f}f, {u(d["center"][1]):.2f}f }};')
o.append(f'    constexpr float displayFont = {u(d["text"]["size_px"]):.2f}f;   // Inter Medium 50 px du design')
o.append(f'    const juce::Point<float> arrowL {{ {u(d["arrows"]["left_center"][0]):.2f}f, {u(d["arrows"]["left_center"][1]):.2f}f }}, arrowR {{ {u(d["arrows"]["right_center"][0]):.2f}f, {u(d["arrows"]["right_center"][1]):.2f}f }};')
o += ['}', '']
open(os.path.join(P, 'Layout.h'), 'w').write('\n'.join(o))
json.dump({'image': [2350, 1800], 'units': [1175, 900], 'knobs': [[k['id'], u(k['center'][0]), u(k['center'][1])] for k in kn],
           'toggle': [u(t['washer_center'][0]), u(t['washer_center'][1])], 'leds': [[u(l['center'][0]), u(l['center'][1])] for l in L['leds']],
           'footswitches': [[u(f['center'][0]), u(f['center'][1])] for f in L['footswitches']], 'display': [u(v) for v in d['rect']]},
          open(os.path.join(P, 'tools', 'layout.json'), 'w'), indent=1)
print('ok', TS)
