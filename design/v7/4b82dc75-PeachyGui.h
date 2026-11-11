// ---------------------------------------------------------------------------------------------------------------------
// PeachyGui.h - REFERENCE implementation of the Peachy pedal GUI layers for JUCE.
// STATUS: written from the design rules, NOT compiled / NOT tested against the Nine-Hands-DSP repos.
//         Verify every JUCE API against the JUCE version used by the target repo (Font/FontOptions changed in JUCE 8).
// Design canvas = 2350 x 1800. Every layout number comes from layout/layout.json (copy the values or parse the JSON).
// Rules: docs/RULES.md  (knobs: filmstrip frames, nothing rotates at runtime; shadows are baked; no glow on LEDs).
// ---------------------------------------------------------------------------------------------------------------------
#pragma once
#include <JuceHeader.h>

namespace nh
{
    constexpr int kDesignW = 2350, kDesignH = 1800, kFrames = 128;

    // design-pixel rectangle -> component rectangle (uniform scale from the 2350 px wide design)
    inline juce::Rectangle<int> fromDesign (float x, float y, float w, float h, float scale)
    {
        return juce::Rectangle<float> (x, y, w, h).transformedBy (juce::AffineTransform::scale (scale)).getSmallestIntegerContainer();
    }

    // ---- knobs: one vertical filmstrip per knob size, frame i = round(value * (N-1)) -------------------------------------
    class FilmstripLookAndFeel : public juce::LookAndFeel_V4
    {
    public:
        FilmstripLookAndFeel (juce::Image bigStrip, juce::Image presenceStrip, int numFrames = kFrames)
            : big (std::move (bigStrip)), presence (std::move (presenceStrip)), frames (numFrames) {}

        void drawRotarySlider (juce::Graphics& g, int x, int y, int w, int h, float sliderPosProportional,
                               float, float, juce::Slider& s) override
        {
            const auto& strip = (s.getComponentID() == "presence") ? presence : big;   // set slider.setComponentID("presence")
            const int fs    = strip.getWidth();                                          // frames are square, stacked vertically
            const int frame = juce::jlimit (0, frames - 1, juce::roundToInt (sliderPosProportional * (float) (frames - 1)));
            g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
            g.drawImage (strip, x, y, w, h, 0, frame * fs, fs, fs);                      // never rotate at runtime
        }
    private:
        juce::Image big, presence; int frames;
    };

    // ---- octave switch: two pre-rendered states (design shows ON) ---------------------------------------------------------
    class OctaveSwitch : public juce::Button
    {
    public:
        OctaveSwitch (juce::Image onImg, juce::Image offImg) : juce::Button ("octave"), on (std::move (onImg)), off (std::move (offImg))
        { setClickingTogglesState (true); }
        void paintButton (juce::Graphics& g, bool, bool) override
        {
            g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
            g.drawImage (getToggleState() ? on : off, getLocalBounds().toFloat());
        }
    private:
        juce::Image on, off;
    };

    // ---- LED: only the LIT sprite exists. Request an UNLIT sprite from the designer (do not darken the lit one in code) -------
    class Led : public juce::Component
    {
    public:
        explicit Led (juce::Image lit) : litImg (std::move (lit)) { setInterceptsMouseClicks (false, false); }
        void setLit (bool b) { if (lit != b) { lit = b; repaint(); } }
        void paint (juce::Graphics& g) override
        {
            g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
            if (lit) g.drawImage (litImg, getLocalBounds().toFloat());
            // else: TODO draw the unlit sprite once the designer provides it
        }
    private:
        juce::Image litImg; bool lit = true;
    };

    // ---- editor skeleton ------------------------------------------------------------------------------------------------------
    // background: background/pedal_background_widgets_free.png (shadows of knobs / switch / LEDs already baked in)
    // draw order: background -> knobs -> octave switch -> LEDs -> display text
    class PeachyEditorBase : public juce::AudioProcessorEditor
    {
    public:
        PeachyEditorBase (juce::AudioProcessor& p, juce::Image bg, juce::Typeface::Ptr displayTypeface)
            : juce::AudioProcessorEditor (p), background (std::move (bg)), inter (displayTypeface)
        {
            setResizable (false, false);
            setSize (1175, 900);                       // half of the design; any uniform scale of 2350 x 1800 works
        }
        float scale() const { return (float) getWidth() / (float) kDesignW; }

        void paint (juce::Graphics& g) override
        {
            g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
            g.drawImage (background, getLocalBounds().toFloat());
        }
        void paintOverChildren (juce::Graphics& g) override
        {
            // display text: Inter Medium, 50 px at design scale, colour (251,251,251),
            // ink box centred on x = 1174, cap-height band centred on y = 1526.5
            g.setColour (juce::Colour::fromRGB (251, 251, 251));
            g.setFont (juce::Font (inter).withHeight (50.0f * scale()));      // JUCE 8: juce::Font (juce::FontOptions (inter).withHeight (...))
            g.drawText (displayText, fromDesign (778, 1478, 792, 97, scale()), juce::Justification::centred, false);
        }
        juce::String displayText { "P8  Wall of Sludge" };
    private:
        juce::Image background; juce::Typeface::Ptr inter;
    };
}

// ---- usage sketch (positions from layout.json; sizes are the frame sizes, e.g. 271 x 271 for the 8 main knobs) -------------
//   juce::Slider master;  master.setSliderStyle (juce::Slider::RotaryVerticalDrag);
//   master.setTextBoxStyle (juce::Slider::NoTextBox, false, 0, 0);  master.setLookAndFeel (&filmstripLnf);
//   master.setBounds (nh::fromDesign (332, 208, 271, 271, scale()));
//   attachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (apvts, "master", master);
//   presence.setComponentID ("presence");  presence.setBounds (nh::fromDesign (868, 1020, 148, 148, scale()));
//   octave.setBounds (nh::fromDesign (2001, 696, 84, 111, scale()));         // ON sprite offset; OFF sprite: y = 723, h = 102
//   ledLeft.setBounds (nh::fromDesign (486, 1062, 65, 65, scale()));  ledRight.setBounds (nh::fromDesign (1794, 1062, 65, 65, scale()));
// CMake: juce_add_binary_data (NH_Assets SOURCES background/*.png sprites/*.png fonts/Inter-Medium.otf)
