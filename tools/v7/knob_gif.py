import numpy as np, cv2, json, sys
from PIL import Image
import compose as C
S = sys.argv[1]
bg = C.pm(C.ld('background/pedal_background_widgets_free.png'))
L = C.L; k = [i for i in L['knobs']['items'] if i['id'] == 'tone'][0]; pr = [i for i in L['knobs']['items'] if i['id'] == 'presence'][0]
x0, y0, x1, y1 = 1540, 560, 2180, 900        # tone + octave
# trajectoire (deg) a 30 i/s : lent, rapide, tres rapide, arret
traj = list(np.linspace(-135, 135, 45)) + [135] * 6 + list(np.linspace(135, -135, 12)) + [-135] * 6 + list(np.linspace(-135, 135, 5)) + [135] * 8
frames = []; last = traj[0]; span = 0.0
blurMax, step, decay = 40.0, 3.0, 0.6
for a in traj:
    v = a - last; last = a
    span = max(min(abs(v), blurMax), span * decay)
    if span < 0.1: span = 0.0
    n = 1 if span == 0 else int(min(16, max(4, np.ceil(span / step) + 1)))
    sgn = 1 if v >= 0 else -1
    k8 = C.knob800(a, blur=span * sgn, n=n) if span > 0 else C.knob800(a)
    img = bg[y0:y1, x0:x1].copy()
    spr = C.down(k8, k['frame_size']); xx, yy = k['x'] - x0, k['y'] - y0
    img[yy:yy + 271, xx:xx + 271] = C.over(img[yy:yy + 271, xx:xx + 271], spr)
    rgb = (np.clip(img[..., :3] / np.maximum(img[..., 3:4], 1e-4), 0, 1) * 255).astype(np.uint8)
    frames.append(Image.fromarray(rgb).resize((rgb.shape[1] // 2 * 2 // 2 * 1, rgb.shape[0] // 1), Image.LANCZOS) if False else Image.fromarray(rgb))
frames[0].save(S + '/potard_tone.gif', save_all=True, append_images=frames[1:], duration=33, loop=0)
print(len(frames))
