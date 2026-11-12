# PEACHY (NINE HANDS | DSP) - notice PDF en francais, illustree avec le rendu reel du plugin.
# Usage : python3 tools/manual.py [<dossier des captures (tools/render)>] <fichier PDF de sortie>
#   avec captures : recompose les images et les copie dans tools/manual_assets/ ;
#   sans captures : reprend les images composees de tools/manual_assets/ (extraites de la notice precedente).
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, CondPageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = sys.argv[1] if len(sys.argv) > 2 else None
OUT = sys.argv[-1]
VERSION = "2.0.1"
TMP = os.path.dirname(os.path.abspath(OUT))
FONTS = os.path.join(ROOT, "assets", "fonts")
for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"),
             ("Title", "BarlowCondensed-ExtraBold")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))

ACC = colors.HexColor("#D8262C"); ACC_L = colors.HexColor("#FF5A50")
DARK = colors.HexColor("#1A1516"); GREY = colors.HexColor("#6B6466"); LIGHT = colors.HexColor("#F6E9E8")

# ---------- geometrie (tools/layout.json : repere du plugin 1175 x 900 unites = fond 2350 x 1800 / 2) ----------
import json, subprocess
LAY = json.load(open(os.path.join(ROOT, "tools", "layout.json")))
KP = [(x, y) for _, x, y in LAY["knobs"]]
OCT = LAY["toggle"]; LEDL, LEDR = LAY["leds"]; FSL, FSR = LAY["footswitches"]
DX, DY, DW, DH = LAY["display"]
LOGO_PNG = os.path.join(TMP, "nine_hands_logo_blanc.png")
def render_logo(svg, png, width=1200):
    """logo officiel (SVG) rendu par Chromium, fond transparent, recadre sur l'alpha"""
    from playwright.sync_api import sync_playwright
    data = open(svg).read()
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": width + 40, "height": width // 4})
        pg.set_content(f'<html><body style="margin:0;background:transparent"><div style="width:{width}px;padding:20px">{data}</div></body></html>')
        pg.eval_on_selector("svg", "e => { e.setAttribute('width', '%d'); e.removeAttribute('height'); }" % width)
        pg.screenshot(path=png, omit_background=True, full_page=True); b.close()
    im = Image.open(png); im.crop(im.getbbox()).save(png)
render_logo(os.path.join(ROOT, "NineHandsLogoWhite.svg"), LOGO_PNG)

ASSETS = os.path.join(ROOT, "tools", "manual_assets")
NAMES = ["peachy_annotated.png", "peachy_octave.png", "peachy_leds.png", "peachy_bar.png", "peachy_cover_cutout.png"]
if SHOTS:
    def shot(n): return Image.open(os.path.join(SHOTS, n)).convert("RGB")
    src = shot("peachy_both.png")
    k = src.height / 900.0

    # ---------- capture annotee ----------
    marks = [(1, *KP[0]), (2, *KP[1]), (3, *KP[2]), (4, *KP[3]), (5, *KP[4]), (6, *KP[5]), (7, *KP[6]), (8, *KP[7]),
             (9, *KP[8]), (10, *OCT), (11, *LEDL), (12, *LEDR), (13, *FSL), (14, *FSR), (15, DX + DW / 2, DY + DH / 2),
             (16, 912, 18), (17, 267, 18)]
    off = {1: (-62, -52), 2: (-62, -52), 3: (-62, -52), 4: (-62, -52), 5: (-62, -52), 6: (-62, -52), 7: (-62, -52), 8: (-62, -52),
           9: (-46, -30), 10: (40, 0), 11: (0, -34), 12: (0, -34), 13: (82, -40), 14: (-82, -40), 15: (-226, 0), 16: (40, 6), 17: (-40, 6)}
    ann = src.copy(); dr = ImageDraw.Draw(ann)
    fnt = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), int(19 * k))
    for n, x, y in marks:
        ox, oy = off[n]
        cx, cy, r = (x + ox) * k, (y + oy) * k, 15 * k
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=(216, 38, 44), width=int(3 * k))
        dr.text((cx, cy + 1), str(n), font=fnt, fill=(26, 21, 22), anchor="mm")
    annotated = os.path.join(TMP, "peachy_annotated.png"); ann.save(annotated)

    def crop_u(name, box):
        im = shot(name); kk = im.height / 900.0
        return im.crop(tuple(int(v * kk) for v in box))
    gap = 18
    def strip(ims, name):
        s = Image.new("RGB", (sum(m.width for m in ims) + gap * (len(ims) - 1), ims[0].height), (255, 255, 255))
        x = 0
        for m in ims: s.paste(m, (x, 0)); x += m.width + gap
        p = os.path.join(TMP, name); s.save(p); return p
    ob = (OCT[0] - 70, OCT[1] - 80, OCT[0] + 70, OCT[1] + 56)
    oct_img = strip([crop_u("peachy_off.png", ob), crop_u("peachy_both.png", ob)], "peachy_octave.png")
    lb = (LEDL[0] - 110, LEDL[1] - 50, LEDL[0] + 60, FSL[1] + 66)
    led_img = strip([crop_u("peachy_off.png", lb), crop_u("peachy_both.png", lb)], "peachy_leds.png")
    bb = (DX - 8, DY - 8, DX + DW + 8, DY + DH + 8)
    bar_img = os.path.join(TMP, "peachy_bar.png")
    a1, a2 = crop_u("peachy_both.png", bb), crop_u("peachy_status.png", bb)
    s2 = Image.new("RGB", (a1.width, a1.height * 2 + 12), (255, 255, 255)); s2.paste(a1, (0, 0)); s2.paste(a2, (0, a1.height + 12)); s2.save(bar_img)

    # ---------- couverture : pedale detouree avec le canal alpha du fond (boitier + jacks), reflet au sol, halo rouge tres doux ----------
    bg_a = Image.open(os.path.join(ROOT, "background.png")).split()[3].resize(src.size, Image.LANCZOS)
    cut = Image.new("RGBA", src.size, (0, 0, 0, 0)); cut.paste(src, (0, 0), bg_a)
    cut = cut.crop(cut.getbbox())
    cw, ch = cut.size
    pad = int(cw * 0.16)
    canvas = Image.new("RGBA", (cw + 2 * pad, int(ch * 1.30) + pad), (0, 0, 0, 255))
    yy, xx = np.mgrid[0:canvas.height, 0:canvas.width].astype(np.float64)
    gcx, gcy = canvas.width / 2, pad + ch * 0.45
    glow = np.exp(-(((xx - gcx) / (cw * 0.62)) ** 2 + ((yy - gcy) / (ch * 0.48)) ** 2)) * 36
    edge = np.clip(np.minimum.reduce([xx, canvas.width - 1 - xx, yy, canvas.height - 1 - yy]) / (pad * 0.9), 0, 1)
    glow *= edge ** 2
    halo = np.dstack([glow * 0.95, glow * 0.12, glow * 0.12, np.full_like(glow, 255)]).astype(np.uint8)
    canvas = Image.alpha_composite(canvas, Image.fromarray(halo, "RGBA"))
    refl = cut.transpose(Image.FLIP_TOP_BOTTOM)
    ra = np.array(refl).astype(np.float64)
    fade = np.clip(1 - np.arange(refl.height) / (refl.height * 0.22), 0, 1) ** 1.6 * 0.22
    ra[..., 3] *= fade[:, None]
    canvas.alpha_composite(Image.fromarray(ra.astype(np.uint8), "RGBA"), (pad, pad + ch + 6))
    canvas.alpha_composite(cut, (pad, pad))
    canvas = canvas.crop((0, 0, canvas.width, pad + int(ch * 1.20)))
    cover = os.path.join(TMP, "peachy_cover_cutout.png"); canvas.convert("RGB").save(cover)
    import shutil
    os.makedirs(ASSETS, exist_ok=True)
    for n in NAMES: shutil.copy(os.path.join(TMP, n), os.path.join(ASSETS, n))
else:
    annotated, oct_img, led_img, bar_img, cover = [os.path.join(ASSETS, n) for n in NAMES]

def img(path, width):
    im = Image.open(path); h = width * im.height / im.width
    return RLImage(path, width=width, height=h)

st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=20, leading=24, textColor=ACC, spaceAfter=8, spaceBefore=4, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="PopM", fontSize=13, leading=17, textColor=DARK, spaceAfter=4, spaceBefore=10, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9.6, leading=14, textColor=DARK, spaceAfter=5),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=8.2, leading=11.5, textColor=GREY),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.4, leading=11, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.4, leading=11, textColor=DARK),
    "cover": ParagraphStyle("cover", fontName="PopL", fontSize=40, leading=48, textColor=colors.white, alignment=TA_CENTER),
    "coversub": ParagraphStyle("coversub", fontName="Pop", fontSize=12, leading=16, textColor=colors.HexColor("#C9BFBF"), alignment=TA_CENTER),
    "coverlang": ParagraphStyle("coverlang", fontName="PopM", fontSize=8.5, leading=11, textColor=ACC_L),
}
def P(t, s="p"): return Paragraph(t, st[s])
def bullets(items): return [P("&bull;&nbsp;&nbsp;" + i) for i in items]
def table(rows, widths, header=True):
    data = [[P(c, "cellb" if (header and r == 0) else "cell") for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#E3D2D0")),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header: style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t

# ---------- donnees (identiques a PluginProcessor.cpp) ----------
FACTORY = [  # nom, master, gain, vol, dist, bass, mid, treb, tone, pres, oct, pre, fuzz
    ("Indigo Crunch",            5.0, 6.5, 5.0, 7.5, 6.0, 4.0, 6.5, 5.0, 6.0, 0, 1, 0),
    ("Seven String Chug",        5.0, 7.8, 5.0, 7.5, 5.5, 3.2, 6.2, 5.0, 6.8, 0, 1, 0),
    ("Scooped Rhythm",           5.2, 8.5, 5.0, 7.5, 7.0, 2.0, 7.0, 5.0, 6.0, 0, 1, 0),
    ("Woolly Fuzz",              5.0, 6.0, 5.0, 7.5, 5.0, 5.0, 5.0, 5.0, 5.0, 0, 0, 1),
    ("Fuzz Octave Sludge",       5.0, 6.0, 5.0, 9.0, 5.0, 5.0, 5.0, 3.5, 5.0, 1, 0, 1),
    ("Bright Fuzz Lead",         5.0, 6.0, 5.3, 10., 5.0, 5.0, 5.0, 8.0, 5.0, 0, 0, 1),
    ("Fuzz Into Preamp",         4.6, 5.0, 4.0, 7.0, 5.5, 4.5, 6.0, 4.5, 5.5, 0, 1, 1),
    ("Wall of Sludge",           4.6, 6.0, 4.0, 9.0, 6.5, 3.5, 6.0, 4.0, 6.0, 1, 1, 1),
    ("Gritty Boost",             6.0, 2.2, 5.0, 7.5, 5.0, 6.0, 6.0, 5.0, 5.5, 0, 1, 0),
    ("Capture Reference G75 T5", 5.0, 6.0, 5.0, 7.5, 5.0, 5.0, 5.0, 5.0, 5.0, 0, 0, 1)]
DESC = {
 "en_unused": ["Preamp only: tight, saturated crunch with a light mid scoop, the starting point.",
        "More gain, deeper scoop and more presence for low-tuned 7-string riffs and palm mutes.",
        "High gain, bass up, mids down, treble up: the classic scooped rhythm wall.",
        "Fuzz only, exactly as captured at noon tone: woolly, thick, long sustain.",
        "Octave doubler into the fuzz and a darker tone: huge, slow, sludgy riffs.",
        "Full distortion and a bright tone: a cutting fuzz lead.",
        "Fuzz feeding a moderate preamp: the fuzz blends into the preamp drive.",
        "Everything on, with the octave: the densest wall the pedal can make.",
        "Low preamp gain with a bit more level: an edgy boost for an amp that is already crunchy.",
        "The original capture (distortion 75 %, tone 5) played back untouched, to compare."],
 "fr": ["Préampli seul : crunch serré et saturé, médiums légèrement creusés, le point de départ.",
        "Plus de gain, médiums plus creusés et plus de présence pour les riffs et palm mutes en 7 cordes accordée bas.",
        "Beaucoup de gain, graves montés, médiums baissés, aigus montés : le mur rythmique creusé classique.",
        "Fuzz seul, exactement comme la capture tone à midi : laineux, épais, long sustain.",
        "Octave doubler dans le fuzz et un tone plus sombre : riffs énormes, lents, sludge.",
        "Distortion à fond et tone brillant : un solo fuzz qui tranche.",
        "Le fuzz attaque un préampli modéré : le fuzz se mélange au drive du préampli.",
        "Tout enclenché, avec l'octave : le mur le plus dense que la pédale sait faire.",
        "Peu de gain de préampli, un peu plus de niveau : un boost mordant devant un ampli déjà crunch.",
        "La capture d'origine (distortion 75 %, tone 5) restituée telle quelle, pour comparer."]}
def pc(v): return f"{round(v * 10)} %"

T = {
"fr": dict(
 lang="FRANÇAIS", sub="Préampli + fuzz", ver="",
 intro_t="1. Présentation",
 intro=["<b>PEACHY</b> est un plugin NINE HANDS | DSP inspiré de la pédale signature KoRn <b>Indigo Ranch</b>, une pédale double qui réunit un "
        "<b>préampli</b> high gain et un <b>fuzz</b> séparé avec une <b>octave</b> grave, au son des guitares des disques du groupe du milieu des années 90 "
        "(crunch serré et saturé pour les riffs en 7 cordes ; fuzz laineux à gros sustain). NINE HANDS | DSP n'a aucun lien avec le groupe ni avec le fabricant de la pédale.",
        "Le <b>fuzz, c'est la vraie pédale</b> : il est joué par 45 captures NAM de la section fuzz (distortion 50 à 100 %, tone 1 à 9). "
        "L'analyse a montré que le TONE agit comme un filtre linéaire après l'écrêtage : Peachy fait tourner les cinq captures TONE 5 en réseaux "
        "de neurones (NeuralAmpModelerCore), passe en fondu entre les deux plus proches quand on tourne DISTORTION, et applique un modèle exact du "
        "filtre TONE mesuré sur les neuf positions capturées. Comparé aux captures, l'écart est du même ordre que l'erreur des captures elles-mêmes.",
        "Le <b>préampli</b> n'a pas été capturé : il est modélisé comme un préampli à lampes high gain (deux étages d'écrêtage à courbe de triode asymétrique, "
        "grave serré avant l'écrêtage, tone stack passif 3 bandes calculé exactement, présence en sortie), avec un sur-échantillonnage x4.",
        "Trajet du signal : entrée &gt; OCTAVE &gt; FUZZ &gt; PREAMP &gt; sortie ; le fuzz attaque le préampli, comme sur la pédale.",
        "Depuis la version 2, l'interface reprend le visuel peint de la pédale (inscriptions manuscrites, silhouette, écran de presets) : potards en métal brossé animés, inverseur et LED rouges en photo, footswitchs hexagonaux noirs."],
 inst_t="2. Installation",
 inst=[("Windows", "Téléchargez l'artefact <b>Peachy-VST3-Windows.zip</b> avec le bouton « Télécharger Windows » de la page GitHub Nine-Hands-Dsp/Peachy (toujours la dernière version), décompressez-le et copiez le dossier <b>Peachy.vst3</b> dans <b>C:\\Program Files\\Common Files\\VST3</b>."),
       ("macOS", "Téléchargez <b>Peachy-VST3-macOS.zip</b> (bouton « Télécharger macOS »), décompressez-le et copiez <b>Peachy.vst3</b> dans <b>~/Bibliothèque/Audio/Plug-Ins/VST3</b>. Si macOS le bloque, tapez <b>xattr -cr ~/Library/Audio/Plug-Ins/VST3/Peachy.vst3</b> dans le Terminal. Le binaire est universel (Apple Silicon et Intel)."),
       ("Reaper", "Options &gt; Préférences &gt; Plug-ins &gt; VST &gt; <b>Re-scan</b>. Le plugin apparaît sous le nom <b>Peachy (NINE HANDS | DSP)</b>. Pour le piloter avec des footswitchs et pédales d'expression MIDI, la piste doit recevoir le MIDI de votre contrôleur (par exemple la M-Vave Chocolate Plus).")],
 ov_t="3. Vue d'ensemble de l'interface",
 ov_rows=[["#", "Commande", "Rôle"],
   ["1", "MASTER", "Volume de sortie du préampli."], ["2", "GAIN", "Gain du préampli."], ["3", "VOLUME", "Volume de sortie du fuzz."],
   ["4", "DISTORTION", "Gain du fuzz."], ["5", "BASS", "Graves du préampli."], ["6", "MID", "Médiums du préampli."], ["7", "TREBLE", "Aigus du préampli."],
   ["8", "TONE", "Tonalité du fuzz (sombre / brillant)."], ["9", "PRESENCE", "Présence du préampli (petit potard)."],
   ["10", "OCTAVE", "Octave doubler de Semitones (levier haut = on), avec ou sans fuzz."],
   ["11", "LED gauche", "Préampli enclenché."], ["12", "LED droite", "Fuzz enclenché."],
   ["13", "Footswitch gauche", "Préampli on / off."], ["14", "Footswitch droit", "Fuzz on / off."],
   ["15", "Écran", "Preset en cours (flèches = précédent / suivant, nom = menu) ; pendant un réglage, la ligne d'état prend sa place."],
   ["16", "IN", "Jack d'entrée (en haut à droite)."], ["17", "OUT", "Jack de sortie (en haut à gauche)."]],
 ctl_t="4. Les commandes en détail",
 ctl=[("GAIN (préampli)", "D'environ 6 dB à 56 dB, répartis sur deux étages façon lampe. En bas de course, un boost mordant et granuleux ; dès midi, le crunch serré et saturé de la pédale ; le haut de la course ajoute du sustain et de la densité. Le grave est resserré avant l'écrêtage pour que les riffs accordés bas restent définis."),
      ("BASS · MID · TREBLE (préampli)", "Tone stack passif après l'écrêtage, comme dans une tête d'ampli britannique (fonction de transfert analogique exacte). Les trois commandes interagissent comme sur un ampli : MID au minimum donne le gros creux de médiums, BASS suit une courbe logarithmique, TREBLE ajoute du mordant. Elles n'agissent que sur le préampli."),
      ("PRESENCE (préampli)", "Plateau d'aigus à 3,2 kHz, environ −10 à +10 dB, même pente des deux côtés de midi : plus d'attaque et d'air, ou un haut du spectre plus doux."),
      ("MASTER (préampli) · VOLUME (fuzz)", "Volume de sortie de chaque section. Midi = niveau de référence (pour le fuzz : le niveau des captures), à fond = environ +10 dB, 0 = coupé. Les deux sections se règlent séparément pour passer de l'une à l'autre sans saut de volume."),
      ("DISTORTION (fuzz)", "De 50 % à 100 %, le son vient directement des captures de la vraie pédale, avec un fondu entre les deux positions capturées les plus proches (50, 65, 75, 90, 100 %). Sous 50 %, la capture 50 % reçoit un niveau d'entrée plus faible : moins de saturation, plus d'attaque du médiator, comme en baissant le vrai potard."),
      ("TONE (fuzz)", "Modèle exact du filtre TONE de la pédale, mesuré sur les neuf positions capturées (erreur rms 0,4 dB) : vers la gauche, les aigus s'adoucissent (sombre, laineux) ; vers la droite, le grave diminue et les aigus montent (fin, brillant, tranchant). La course 0 à 10 couvre les positions capturées 1 à 9 ; midi = 5."),
      ("OCTAVE", "Enclenche exactement le preset Octave doubler (-12) de notre pédale Semitones, placé devant Peachy : le même moteur de transposition descend votre guitare d'une octave et la mélange à 50 / 50 avec le son direct (à puissance égale, le niveau ne change pas). Le signal doublé entre ensuite dans le fuzz et le préampli s'ils sont enclenchés, et va droit en sortie deux footswitchs coupés.")],
 oct_cap="Inverseur OCTAVE coupé (levier en bas) et enclenché (levier en haut).",
 fs_t="5. Footswitchs, LED et noise gate",
 fs=["<b>Footswitchs</b> : footswitchs hexagonaux noirs. Gauche = PREAMP, droit = FUZZ, indépendants. Ils basculent dès l'appui ; tant qu'on garde le bouton de la souris enfoncé, le bouton reste enfoncé (il descend dans sa bague et s'assombrit). Maintenu plus de 0,45 s après avoir enclenché une section, il fonctionne en momentané (la section se coupe au relâchement) ; clic droit &gt; <b>Settings</b> pour désactiver.",
     "<b>LED</b> : rouges, gauche = préampli actif, droite = fuzz actif, allumage et extinction en fondu ; éteintes, la lentille reste visible, rouge sombre. Allumées, elles éclairent la façade autour d'elles : clic droit &gt; <b>Glow (halo of the lights)</b> règle ce halo à 25, 50, 75 ou 100 % (par défaut), réglage commun à toutes les fenêtres de Peachy ; la LED elle-même reste toujours à pleine intensité.",
     "<b>Bypass</b> : chaque section coupée laisse passer le signal sec, aligné sur la latence annoncée au DAW (sans clic, en fondu).",
     "<b>Noise gate</b> (clic droit &gt; Noise gate) : Off, <b>Light</b> (par défaut), Medium ou Strong. Il écoute l'entrée, s'ouvre instantanément à la note suivante et laisse les notes s'éteindre naturellement ; il n'agit que si une section est enclenchée.",
     "Tout est aussi automatisable dans le DAW (tous les potards, Octave, Preamp Footswitch, Fuzz Footswitch)."],
 midi_t="6. MIDI",
 midi_txt=["<b>MIDI Learn sur toutes les commandes</b> : faites un clic droit sur une commande (l'un des 9 potards, l'inverseur OCTAVE ou l'un des footswitchs). Le menu s'ouvre là où vous cliquez ; son en-tête donne le nom de la commande et son assignation (<b>MIDI: CC n</b> ou <b>MIDI: not assigned</b>), suivi de <b>MIDI Learn</b>, <b>Clear MIDI</b> et, tant qu'un apprentissage est en attente, <b>Cancel MIDI learn</b>. Choisissez MIDI Learn puis bougez une pédale, un bouton ou appuyez sur un footswitch de votre contrôleur : l'écran affiche <b>MIDI LEARN · &lt;Nom&gt;</b>, puis <b>&lt;Nom&gt; = CC n</b> pendant 2 secondes.",
           "Chaque menu clic droit (sur une commande ou ailleurs sur la pédale) contient aussi le sous-menu <b>MIDI</b> : <b>MIDI Learn</b> pour chacune des 12 commandes (avec son assignation actuelle), <b>Cancel MIDI learn</b> (tant qu'un apprentissage est en attente) et <b>Clear all MIDI assignments</b>. Choisir de nouveau la commande en attente annule aussi l'apprentissage.",
           "<b>Aucun CC n'est assigné par défaut</b> : Peachy ne réagit à aucun CC tant que vous n'en avez pas appris un. Les anciens projets restés sur l'ancienne table d'usine s'ouvrent sans assignation ; un projet où vous aviez changé au moins une assignation garde ses assignations.",
           "Un numéro de CC ne pilote qu'une seule commande : apprendre un CC déjà utilisé le retire de l'autre commande. L'apprentissage accepte les CC 0 à 119 ; Peachy écoute tous les canaux MIDI. <b>Les assignations sont sauvegardées avec le projet</b> (et avec les presets du DAW)."],
 midi_hdr=["Commande", "Type"],
 midi=[["Master", "Continu"], ["Gain", "Continu"], ["Volume (fuzz)", "Continu"], ["Distortion", "Continu"],
       ["Bass", "Continu"], ["Mid", "Continu"], ["Treble", "Continu"], ["Tone (fuzz)", "Continu"], ["Presence", "Continu"],
       ["Octave", "Bascule : 64 et plus = on, moins de 64 = off"],
       ["Preamp footswitch", "Footswitch : à accrochage (127 = on / 0 = off) ou momentané (bascule à chaque appui)"],
       ["Fuzz footswitch", "Footswitch : à accrochage (127 = on / 0 = off) ou momentané (bascule à chaque appui)"]],
 midi2=["<b>Potards</b> : 0-127 couvre toute la course ; un potard sur un CC de 0 à 31 accepte aussi la partie fine 14 bits sur le CC n+32 (n = le CC appris). Les pédales d'expression sont fluides : rampes entre les messages et apprentissage automatique de la course réelle de la pédale (0 et 100 % toujours atteints).",
        "<b>Footswitchs MIDI</b> : clic droit &gt; <b>Settings</b> &gt; <b>MIDI footswitches latching (127 = on / 0 = off)</b> (par défaut) ou <b>MIDI footswitches momentary (toggle each press)</b>.",
        "<b>Program Change</b> 1 à 10 : presets usine."],
 led_cap="Section préampli coupée, puis enclenchée (LED allumée).",
 win_t="7. Fenêtre",
 win=["Peachy utilise le format pédale double (même hauteur d'ouverture que Ring Think). Les menus clic droit ont le design d'Octopus et s'ouvrent toujours là où vous cliquez. Clic droit &gt; <b>Plugin size</b> : <b>60 %</b>, <b>75 %</b>, <b>100 %</b> redimensionne cette fenêtre ; <b>(default)</b> signale la taille par défaut choisie. En bas de ce sous-menu, <b>Default size (new windows)</b> choisit la taille d'ouverture de toutes les nouvelles fenêtres de Peachy (réglage commun à toutes les instances, enregistré sur l'ordinateur) ; la fenêtre ouverte prend aussi tout de suite cette taille. La taille n'est pas sauvegardée avec le projet : à chaque ouverture, la fenêtre revient à la taille par défaut. Elle ne peut jamais être réduite sous 60 % ; on peut aussi tirer le coin en bas à droite pour l'agrandir (proportions conservées).",
      "L'<b>écran</b> de la pédale affiche le preset en cours. Dès qu'un réglage bouge (souris, molette, automation, MIDI), la <b>ligne d'état</b> prend sa place avec la valeur en direct (potards en %, par ex. <i>Distortion 82 %</i>, <i>Fuzz ON</i>, messages du MIDI Learn), puis s'efface en fondu 2,5 s après le dernier mouvement et le preset revient. Un clic sur l'écran pendant ce temps fait revenir le preset tout de suite."],
 bar_cap="Écran : preset en cours, puis ligne d'état pendant un réglage.",
 pre_t="8. Presets",
 pre=["Utilisez les flèches de l'écran, cliquez sur le nom du preset, faites un clic droit n'importe où, ou passez par le menu de presets du DAW. Clic droit &gt; <b>Save user preset</b> enregistre jusqu'à 9 presets personnels. Les presets incluent l'état des footswitchs et de l'octave."],
 fac_hdr=["PC", "Preset", "Préampli : master / gain · bass / mid / treble · presence", "Fuzz : volume / distortion / tone", "Actif", "Description"],
 tips_t="9. Conseils d'utilisation",
 tips=["Dans Reaper, placez Peachy <b>avant</b> votre simulateur d'ampli (par exemple avant Ampire, suivi d'Impulse pour le baffle) avec un ampli assez clair, comme avec la vraie pédale ; le préampli peut aussi aller directement dans un modèle d'ampli de puissance / baffle.",
       "Pour une 7 cordes accordée en Sol ou plus bas : gardez BASS vers midi, montez un peu PRESENCE, et ajoutez l'OCTAVE pour plus de poids.",
       "Apprenez DISTORTION ou GAIN sur une pédale d'expression pour pousser la saturation au pied pendant un riff.",
       "Fuzz dans le préampli : baissez ensemble le VOLUME du fuzz et le GAIN du préampli ; le fuzz apporte déjà beaucoup de saturation.",
       "Entre deux positions capturées de DISTORTION, Peachy fait tourner deux réseaux à la fois (environ 20 % d'un cœur à 48 kHz) ; sur une position capturée (50, 65, 75, 90 ou 100 %), un seul."],
 tech_t="10. Caractéristiques techniques",
 tech=[["Format", "VST3 (Windows 64 bits, macOS universel)"], ["Canaux", "Mono ou stéréo (traité en mono, comme la pédale)"],
       ["Latence", "32 échantillons à 48 kHz (sur-échantillonnage du préampli), davantage aux autres fréquences (rééchantillonnage vers les 48 kHz des captures) ; annoncée au DAW"],
       ["Fuzz", "5 captures NAM WaveNet (distortion 50 / 65 / 75 / 90 / 100 %), filtre TONE exact"], ["Octave", "Moteur de Semitones (raccords synchronisés sur la période, suivi YIN jusqu'à 31 Hz), -12 demi-tons, mélange 50 / 50 à puissance égale"],
       ["Préampli", "gain 6 à 56 dB, sur-échantillonnage x4, tone stack passif 3 bandes, présence ±10 dB"],
       ["MIDI", "MIDI Learn sur les 12 commandes (sauvegardé avec le projet), aucun CC assigné par défaut, 14 bits sur CC n+32, Program Change 1 à 10, tous canaux"],
       ["Fenêtre", "Plugin size 60 % (minimum), 75 %, 100 %, taille par défaut des nouvelles fenêtres au choix (60 % au départ) ; potards animés avec flou de mouvement ; Glow 25 à 100 % ; anti-gel v2 sous Windows (rendu logiciel, caches d'affichage refaits par un timer, chien de garde de redessin, aucun appel à l'hôte depuis le thread audio)"],
       ["Version", VERSION], ["Processeur", "environ 3 % (préampli), 10 à 20 % (fuzz) d'un cœur à 48 kHz"]]),
}

W = A4[0] - 36 * mm
def section(lang):
    t = T[lang]; f = []
    f.append(NextPageTemplate("p"))
    COVER_TEXT.update(lang=t["lang"], sub=t["sub"])           # couverture dessinee a positions fixes (cover_bg)
    f.append(PageBreak())
    f.append(P(t["intro_t"], "h1")); f += [P(x) for x in t["intro"]]
    f.append(P(t["inst_t"], "h1"))
    for h, x in t["inst"]: f.append(P(h, "h2")); f.append(P(x))
    f.append(PageBreak())
    f.append(P(t["ov_t"], "h1"))
    f.append(img(annotated, W * 0.86))
    f.append(Spacer(1, 3 * mm))
    f.append(table(t["ov_rows"], [10 * mm, 38 * mm, W - 48 * mm]))
    f.append(PageBreak())
    f.append(P(t["ctl_t"], "h1"))
    for h, x in t["ctl"]: f.append(P(h, "h2")); f.append(P(x))
    f.append(KeepTogether([Spacer(1, 3 * mm), img(oct_img, W * 0.42), P(t["oct_cap"], "small")]))
    f.append(P(t["fs_t"], "h1")); f += bullets(t["fs"])
    f.append(KeepTogether([Spacer(1, 2 * mm), img(led_img, W * 0.46), P(t["led_cap"], "small")]))
    f.append(P(t["midi_t"], "h1")); f += [P(x) for x in t["midi_txt"]]
    f.append(Spacer(1, 2 * mm)); f.append(KeepTogether([table([t["midi_hdr"]] + t["midi"], [38 * mm, W - 38 * mm])])); f.append(Spacer(1, 3 * mm))
    f += bullets(t["midi2"])
    f.append(P(t["win_t"], "h1")); f.append(P(t["win"][0]))
    wt = Table([[[P(t["win"][1])], [img(bar_img, 70 * mm), P(t["bar_cap"], "small")]]], colWidths=[W - 74 * mm, 74 * mm])
    wt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (0, 0), 0)]))
    f.append(wt)
    f.append(CondPageBreak(150 * mm))
    f.append(P(t["pre_t"], "h1")); f += [P(x) for x in t["pre"]]
    rows = [t["fac_hdr"]]
    for i, (n, ma, ga, vo, di, ba, mi, tr, to, pr, oc, pon, fon) in enumerate(FACTORY):
        on = " + ".join([x for x, b in (("preamp", pon), ("fuzz", fon), ("octave", oc)) if b])
        rows.append([str(i + 1), "<b>" + n + "</b>", f"{pc(ma)} / {pc(ga)} · {pc(ba)} / {pc(mi)} / {pc(tr)} · {pc(pr)}",
                     f"{pc(vo)} / {pc(di)} / {pc(to)}", on, DESC[lang][i]])
    f.append(table(rows, [9 * mm, 28 * mm, 34 * mm, 24 * mm, 20 * mm, W - 115 * mm]))
    f.append(KeepTogether([P(t["tips_t"], "h1")] + bullets(t["tips"]) + [P(t["tech_t"], "h1"), table(t["tech"], [30 * mm, W - 30 * mm], header=False)]))
    f.append(Spacer(1, 4 * mm))
    f.append(PageBreak())
    return f

def deco(c, doc):
    c.saveState()
    c.setFillColor(DARK); c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - 6.8 * mm, A4[0], 0.8 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, "Peachy (NINE HANDS | DSP) · v" + VERSION)
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()
doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="PEACHY - Notice v" + VERSION, author="NINE HANDS | DSP")
# ---- Couverture « minimale » (modele 6) : gabarit fixe commun a toutes les notices NINE HANDS | DSP ----
COVER_TEXT = {}
COVER_NAME = "PEACHY"
PEDAL_H, PEDAL_MAXW, PEDAL_TOP = 82 * mm, 115 * mm, 84 * mm
LANG_TOP = 18 * mm
NAME_TOP, NAME_PT = 194 * mm, 30
SUB_TOP, SUB_PT = 208 * mm, 10
LOGO_W, LOGO_BOTTOM = 38 * mm, 22 * mm
BAND_H = 3 * mm
def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, 0, A4[0], BAND_H, stroke=0, fill=1)
    def line(text, top, font, size, cs, col):
        w = pdfmetrics.stringWidth(text, font, size) + cs * (len(text) - 1)
        t = c.beginText((A4[0] - w) / 2, A4[1] - top - size * 0.8); t.setFont(font, size); t.setCharSpace(cs)
        t.setFillColor(col); t.textOut(text); c.drawText(t)
    line(COVER_TEXT["lang"], LANG_TOP, "PopM", 8.5, 0, ACC_L)
    ci = Image.open(cover); iw, ih = ci.size
    cw = iw / 1.32; ch = (ih - int(cw * 0.16)) / 1.2; pad = int(cw * 0.16)     # geometrie de peachy_cover_cutout.png
    k = min(PEDAL_H / ch, PEDAL_MAXW / cw)
    dw, dh = iw * k, ih * k
    y0 = A4[1] - (PEDAL_TOP + (PEDAL_H - ch * k) / 2) + pad * k
    c.drawImage(cover, (A4[0] - dw) / 2, y0 - dh, dw, dh)
    line(COVER_NAME, NAME_TOP - NAME_PT * 0.02, "Title", NAME_PT, NAME_PT * 0.5, colors.white)
    line(COVER_TEXT["sub"], SUB_TOP, "Pop", SUB_PT, 1.5, colors.HexColor("#BDC4B8"))
    lw, lh = Image.open(LOGO_PNG).size
    c.drawImage(LOGO_PNG, (A4[0] - LOGO_W) / 2, LOGO_BOTTOM, LOGO_W, LOGO_W * lh / lw, mask="auto")
    c.restoreState()
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
fr = section("fr")              # notice en francais uniquement (couverture noire FRANCAIS)
doc.build(fr[:-1])
print(OUT)
