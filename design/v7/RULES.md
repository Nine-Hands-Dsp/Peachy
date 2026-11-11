# Nine Hands DSP - "Peachy" pedal GUI: design rules (v7)

These rules are binding for every integration of this design. They come from the designer's own instructions
and from the decisions taken while building the artwork. Do not "improve" the assets in code: ask the designer.

## 0. Canvas
- Design canvas: **2350 x 1800 px**, RGBA, transparent outside the rounded enclosure. All coordinates in
  `layout/layout.json` are pixels of this canvas (origin top-left, y down).
- Scale the whole GUI uniformly from this canvas (see juce_reference/PeachyGui.h). For HiDPI, re-bake the knob
  filmstrips with `--body-diameter` x2 and use a 2x background; never upscale the 1x sprites.

## 1. Global light rule (applies to everything)
- Light comes from the **top-left, azimuth 45 deg, elevation 45 deg**. Light vector (x right, y down, z toward viewer):
  `L = (-0.5, -0.5, 0.7071)`.
- Cast shadows therefore fall **down and to the right**. Brightest highlights: top-left; weaker highlight bottom-right.
- Never add drop shadows or glows that contradict this. **No glow / halo around the LEDs** (removed on purpose).
- The static shadows of the knobs, the octave switch and the LEDs are **baked into `pedal_background_widgets_free.png`**.
  Do not add shadows in code.

## 2. KNOBS (sprite integration rules)

### 2.1 Sprite format (all knobs)
- PNG, RGBA (straight, non-premultiplied alpha), 800 x 800 px, transparent background.
- Knob is full frame: pivot = exact centre = (400, 400) in continuous coordinates. Outer radius <= 400 px.
- Rotation is clockwise-positive. Angle 0 = 12 o'clock (indicator pointing up).
- Do not resample static layers. Only the crown and the indicator are rotated.

### 2.2 Layer stack (bottom to top) - one knob = 4 layers
1. crown      `knob_12_peachy02_metal_bevel_lip_crown_rotating.png`   ROTATES
2. reflect    `knob_12_peachy02_metal_bevel_lip_reflect_masked.png`   STATIC (world-space lighting overlay)
3. center     `knob_12_peachy02_metal_bevel_lip_center_fixed.png`     STATIC (disc + metal bevel/ring)
4. indicator  `indicator_08_dash_white_half_radius.png`               ROTATES (same angle as the crown)
- Crown and indicator always use the same angle and the same pivot.
- Indicator shading is baked (45 deg relief) and rotates with it. Accepted; do not relight it.

### 2.3 The reflect layer and the alpha rule (the important part)
The reflect is a lighting overlay painted in WORLD space. It must NEVER rotate. Pixels are pure white (highlight) or pure
black (shadow); alpha is the strength; blend with normal source-over.
- The crown has gaps (8 tabs), so a static reflect would leak into the gaps (floating halo) unless masked:
  `A_reflect_final(x, y) = A_reflect(x, y) * A_crown_rotated(x, y)`
  then composite in this order: crown_rotated, reflect_final, center, indicator_rotated.
- Use `reflect_masked` + this multiplication by default. `reflect_static` (safe variant, clipped to r <= 389) is provided only
  for engines that cannot mask. **Never** use the masked variant without the multiplication.
- Keep RGB valid under alpha = 0 (they are) or premultiply consistently - do not premultiply twice. PNGs are straight alpha;
  JUCE images are premultiplied ARGB internally: do the mask multiplication in one domain.

### 2.4 Implementation
- **Filmstrip bake (preferred, exact, cheap):** `tools/bake_knob_filmstrip.py` renders N frames over the rotation range at 800 px,
  then downscales each finished frame ONCE (area filter). Defaults used by the design: **128 frames, -135..+135 deg**
  around 12 o'clock (ask the designer if a different range / count is needed for a given plugin).
  At runtime draw frame `round(normalizedValue * (N - 1))`. Nothing rotates live.
- **Design-level exposure:** the pedal artwork grades the knobs to **x0.80** (the designer's explicit request). The pre-baked
  filmstrips already include it (`--exposure 0.80`). This is an offline grade, not a runtime recolour. For other knobs of the
  same pedal keep `--exposure 0.80`.
- **Live rendering (only if a filmstrip is impossible):** cache pre-scaled images, high-quality resampling for rotated layers,
  rotate crown + indicator about the scaled centre, draw center + reflect unrotated, mask the reflect by the rotated crown
  alpha (clip-to-image-alpha or an offscreen composite per angle step). VERIFY JUCE APIs against the repo's JUCE version.
  Never nearest-neighbour.

### 2.5 Sizes used in this design
- 8 main knobs: continuous body (lip, r = 390 of 400) = **264 px** diameter -> frame **271 x 271 px**; the 8 outer tabs
  (r 390-400) protrude about 3 px.
- Presence knob: body **144 px** -> frame **148 x 148 px**.
- Frame top-left positions are in `layout.json` (`x`, `y`). The design shows all pointers at 33 deg: that is only a static
  mock-up value; in the plugin the angle comes from the parameter value.
- Knob geometry (800 px sprite): black brushed disc r < 325, flat metal bevel 325-375 (center layer), crown = continuous lip
  r 375-390 + 8 tabs up to r 400 (tab width 181 px). Safe reflect valid up to r 389. Indicator_08: white dash r 105-305, 24 px wide.
- Mixing with older knob batches (different light direction) in one GUI: warn the designer, offer to regenerate.

### 2.6 Validation checklist
- Render at 0, 37 and 90 deg on a dark AND a light background (`docs/knob_check_0_37_90.png` is the reference result):
  no floating arcs in the crown gaps, no dark fringes on the crown edges.
- Highlights stay top-left (weaker bottom-right) at every angle: the lit zone on the bevel does not move when the knob turns.
- Indicator pivots exactly around the image centre; at 0 deg it points at 12 o'clock.
- Silhouette matches the sprite (full frame, no cropping); crisp at the final GUI size.

### 2.7 Do not
- Do not rotate the reflect or the center layer. Do not apply the masked reflect without the alpha multiplication.
- Do not mix light directions without telling the designer. Do not recolour or re-shade the sprites in code.

## 3. Other widgets
- **Octave switch (2 positions):** `sprites/toggle_ON.png` / `toggle_OFF.png`, positions in layout.json. The design artwork shows
  **ON** (lever up). The cast shadow is baked and comes from the washer only: the part of the lever that sticks out casts no shadow.
- **LEDs:** `sprites/led_lit_65.png`, 65 px, fixed size and fixed positions, centred on y = 1094.5 (same line as the presence knob).
  Only the LIT state exists. An unlit sprite must be requested from the designer (do not darken the lit one in code).
- **Footswitches:** static, baked in the background (hex 322 x 279 at the two positions). No pressed state exists.
- **Jacks (in / out):** baked. `in` is on the left jack, `out` on the right jack.
- **Display (preset screen):** recessed look is baked (housing lip + 3.25 px black gap + darker screen with its own edge highlight).
  The text is drawn by the plugin: **Inter Medium, 50 px at design scale**, colour from `layout.json`, ink box centred horizontally on x = 1174,
  cap-height band centred vertically on y = 1526.5. The two arrows are baked. Keep the screen shape, text and arrows unchanged.
- **Labels** (master, gain, volume, distortion, bass, mid, treble, tone, octave, presence, in, out) and the NINE HANDS | DSP logo are
  baked into the backgrounds. KORN.TTF was used for the labels (its lower-case 'r' is mirrored by design). If a pedal has different
  parameters, a new background must be produced by the designer - do not paint labels over this one.

## 4. Colour / texture values to respect when anything is drawn on top
- Enclosure / graphic black ~ 0x0b-0x0c (never pure black), fine sand grain, deep black ink for graphics and text.
- Screen gap black ~ 0x0d-0x12. Footswitch metal ~ 29/255 mean luminance (dark, neutral grey).
- Red paint ~ (176, 33, 27) base, textured. LED lens red with orange core.
