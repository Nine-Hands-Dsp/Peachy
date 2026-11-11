#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "PluginProcessor.h"
#include "NHKnob.h"
#include "NineHandsMenu.h"

//==============================================================================
// Peachy v2 (NINE HANDS | DSP) : pack design v7. Fond 2350 x 1800 (ombres cuites), repere 1175 x 900 unites.
//==============================================================================

// inverseur OCTAVE : kit photo (haut / milieu / bas), image du milieu ~55 ms pendant la bascule
class LeverSwitch : public juce::Component
{
public:
    explicit LeverSwitch (juce::RangedAudioParameter&);
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails&) override;
    bool hitTest (int x, int y) override;
    void tick (double nowMs);
    juce::Image strip;
    std::function<void (const juce::MouseEvent&)> onRightClick;
    std::function<void()> onUserChange;
private:
    juce::ParameterAttachment attachment;
    bool on = false;
    int shownFrame = 0, targetFrame = 0;
    double transitionUntil = 0.0;
};

// footswitch du pack (cuit dans le fond) : zone d'appui circulaire, bascule a l'appui, bouton enfonce tant qu'on appuie
class FootSwitchArea : public juce::Component
{
public:
    FootSwitchArea (juce::RangedAudioParameter&, std::atomic<float>* holdMomentary);
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    bool hitTest (int x, int y) override;
    juce::Image imgDown;
    float hitRadiusRatio = 0.97f;               // rayon cliquable / demi-cote du composant
    std::function<void (const juce::MouseEvent&)> onRightClick;
    std::function<void()> onUserChange;
private:
    std::atomic<float>* hold;
    juce::ParameterAttachment attachment;
    bool value = false, pressed = false, turnedOnByPress = false;
    double downTime = 0.0;
};

class PeachyAudioProcessorEditor : public juce::AudioProcessorEditor,
                                   private juce::Timer
{
public:
    explicit PeachyAudioProcessorEditor (PeachyAudioProcessor&);
    ~PeachyAudioProcessorEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;
    void parentHierarchyChanged() override;
    void visibilityChanged() override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseMove (const juce::MouseEvent&) override;
    void mouseExit (const juce::MouseEvent&) override;

    // taille : defaut « 60 % » (hauteur de Ring Think), 75 %, 100 % ; jamais plus petit que le defaut
    static constexpr float baseW = 1175.0f, baseH = 900.0f;
    static constexpr float defaultH = 495.0f, refH = 743.0f, maxH = 1114.0f;
    static constexpr int numSizes = 3;
    static int sizeHeight (int idx);
    void setScaledHeight (int h);
    void setGlowPercent (int pc);
    void showMenuForTest (int learnIdx, juce::PopupMenu& out) { buildContextMenu (out, learnIdx); }   // tools/render
    void buildPresetMenu (juce::PopupMenu&);
    NineHandsMenu::MenuLnf menuLnf;
    float glow = 1.0f;

private:
    void timerCallback() override;
    void useSoftwareRenderer();
    void askRepaint (juce::Rectangle<int> r);
    void rebuildCaches (float scale = 0.0f);
    float physicalScale() const;
    juce::Rectangle<int> scaled (juce::Rectangle<float> r) const;
    void showContextMenu (const juce::MouseEvent* e, int learnIdx = -1);
    void buildContextMenu (juce::PopupMenu& menu, int learnIdx);
    void handleMenu (int r);
    void showPresetMenu();
    void stepPreset (int delta);
    void flash (const juce::String& s);
    juce::String buildStatusLine() const;
    juce::String buildPresetLine() const;
    void drawLeds (juce::Graphics&);
    void drawDisplay (juce::Graphics&);
    int presetZoneAt (juce::Point<float> p) const;

    PeachyAudioProcessor& proc;
    std::unique_ptr<nh::Knob> knobs[PeachyAudioProcessor::numKnobs];
    LeverSwitch octSwitch;
    FootSwitchArea preFs, fuzzFs;

    juce::Image background, bgScaled, ledOn, ledOff, glowImg[2];
    juce::Typeface::Ptr interFace, regularFace, mediumFace, boldFace;
    const juce::Colour menuAccent { 0xffe0251c };

    // anti-gel v2
    void* lastPeer = nullptr;
    double lastRendererCheckMs = 0.0, lastScaleCheckMs = 0.0, repaintAskedMs = 0.0, lastPaintMs = 0.0, lastGlowCheckMs = 0.0;
    int resizeSettle = 0, cacheW = 0, cacheH = 0;
    float cacheScale = 0.0f;

    // ecran : barre de presets et ligne d'etat au meme endroit
    static constexpr int numValueIds = 13;
    float lastValues[numValueIds] {};
    int lastChanged = -1, lastPresetCounter = 0, lastMidiCount = 0, hoverZone = 0, drawnHover = -1, midiFlash = 0;
    double statusUntil = 0.0, learnLineUntil = 0.0, flashUntil = 0.0;
    float statusAlpha = 0.0f, drawnStatus = -1.0f;
    juce::String learnLine, flashLine, lineStatus, linePreset;

    float ledLevel[2] {}, drawnLed[2] { -1.0f, -1.0f };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (PeachyAudioProcessorEditor)
};
