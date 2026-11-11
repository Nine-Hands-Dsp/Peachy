# Nine Hands DSP - Peachy pedal GUI pack (design v7)

Everything needed to integrate the Peachy pedal design (distortion, "Wall of Sludge" screen) into a plugin repository of
Nine-Hands-DSP, with the designer's specific rules.

```
README.md                      this file
docs/RULES.md                  BINDING rules (light, knob layering + reflect alpha rule, baked shadows, LED/switch/display rules, values)
docs/CLAUDE_PROMPT.md          prompt to paste into Claude when working inside the plugin repo
docs/knob_check_0_37_90.png    reference validation render of the knob (0 / 37 / 90 deg, dark + light background)
layout/layout.json             every position / size / state (design px, canvas 2350 x 1800)
background/
  pedal_background_widgets_free.png   USE THIS: static shadows baked, NO knobs / switch / LEDs / display text
  pedal_background_complete_no_knobs.png  v7 "sans potards" render (LEDs + display text baked) - alternative / reference
  pedal_reference_complete.png        full v7 render, for visual comparison only
sprites/
  knob_big_filmstrip_128.png          8 main knobs: 128 frames of 271 x 271 px, -135..+135 deg, vertical strip
  knob_presence_filmstrip_128.png     presence knob: 128 frames of 148 x 148 px
  toggle_ON.png / toggle_OFF.png      octave switch (positions in layout.json)
  led_lit_65.png                      LED, lit state only
knob_sources_800px/                   layered 800 px knob sprites (crown, reflect_masked, center, reflect_static, indicator_08)
source_assets/                        4K switch images + LED source (to re-export sprites)
tools/bake_knob_filmstrip.py          re-bake filmstrips (other frame count / range / size / HiDPI)
tools/export_sprites.py               re-export the switch + LED sprites
tools/compose_preview.py              assemble the whole pedal from the pack layers (python tools/compose_preview.py)
fonts/Inter-Medium.otf (+ licence)    font of the screen text (SIL OFL)
juce_reference/PeachyGui.h            reference JUCE code (UNTESTED sketch)
```

## Layer order in the GUI
`background` -> 9 knob filmstrips -> octave switch -> 2 LEDs -> display text (Inter Medium).
Footswitches, jacks, labels and the NINE HANDS | DSP logo are part of the background.

## Quick start
1. `pip install pillow numpy opencv-python`
2. `python tools/compose_preview.py --knob 0.62 --switch ON` -> `preview.png`. This reproduces the full v7 render from the pack layers
   (mean pixel difference against `pedal_reference_complete.png`: 0.1 / 255; the only differences are the tiny crown tabs at the
   rounded frame angle).
3. Copy `background/`, `sprites/`, `fonts/` into the repo's assets, embed them (BinaryData), and follow `juce_reference/PeachyGui.h`
   and `layout/layout.json`.

## What is NOT in the pack (ask the designer)
- An **unlit LED** sprite and a **pressed footswitch** state (only the lit LED / the static footswitch exist).
- Backgrounds for a different parameter set (labels are baked).
- HiDPI: re-bake filmstrips with `--body-diameter` doubled and use a 2x background.

## Honest notes
- The org page of Nine-Hands-DSP lists C++ plugin repositories, but I could not inspect a specific repository's GUI code or build
  system from here: framework, JUCE version and parameter IDs are **assumptions to confirm** in the repo (`docs/CLAUDE_PROMPT.md`).
- `juce_reference/PeachyGui.h` has never been compiled.
- The knob filmstrips carry the designer's x0.80 exposure grade (see RULES.md 2.4).
