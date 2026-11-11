"""Inverseur OCTAVE : photos du kit NINE HANDS | DSP (haut / milieu / bas) via toggle_photo.aligned_frames de Strong Pickle,
cale sur la rondelle du design (rayon 41,5 px, centre 2042,5 / 765), sans ombre ajoutee : l'ombre de la rondelle est cuite
dans le fond du pack et le levier n'en porte pas (regle du designer)."""
import os, sys
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, H)
import toggle_photo as TP
TP.KIT = os.path.abspath(os.path.join(H, '..', '..', 'assets', 'kit_photo'))
WR, SIZE = 41.5, 168        # rayon de rondelle et cote du sprite (px du design 2350 x 1800)
def frames():
    TP._shift = lambda a, dx, dy: np.zeros_like(a)          # pas d'ombre portee ni de contact : deja dans le fond
    return TP.aligned_frames(WR, SIZE, 1)
