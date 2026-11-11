# Prompt to give Claude in the plugin repository

> You are integrating the "Peachy" pedal GUI of Nine Hands DSP into this repository.
> 1. Read `docs/RULES.md` and `layout/layout.json` of the design pack first. They are binding (light direction, knob layering and the
>    reflect-mask alpha rule, baked shadows, no LED glow, exposure grade, display text rules).
> 2. Before writing code, tell me what you find in THIS repo: GUI framework (JUCE? which version?), CMake or Projucer, how assets are
>    embedded (BinaryData / juce_add_binary_data), the parameter IDs, and whether the plugin already has a custom editor / LookAndFeel.
>    Ask me about anything that is not clear (rotation range per knob, number of frames, unlit LED sprite, HiDPI scale).
> 3. Map the repo's parameters to the widgets of the design (master, gain, volume, distortion, bass, mid, treble, tone, presence,
>    octave 2-position switch, two LEDs, two footswitches, preset screen). If the pedal has different parameters, STOP: the labels
>    are baked into the background and a new background has to be produced by the designer.
> 4. Use `background/pedal_background_widgets_free.png` + the filmstrips + switch/LED sprites. Do not rotate anything at runtime,
>    do not add shadows or glows, do not recolour or re-shade sprites in code.
> 5. Validate with the checklist of RULES.md section 2.6 (0, 37 and 90 degrees, dark and light backgrounds) and show me screenshots.

Notes for you (Claude):
- `juce_reference/PeachyGui.h` is a reference sketch, never compiled. Verify every JUCE API against the repo's JUCE version.
- I could not verify the structure of the Nine-Hands-DSP repositories from the design side: confirm everything in step 2.
