#include "PluginEditor.h"
#include "BinaryData.h"
#include "Layout.h"
#include "WigaWindowSize.h"
#include "NineHandsGlow.h"

using namespace juce;

namespace
{
    // valeurs suivies pour la ligne d'etat : 9 potards, octave, preampOn, fuzzOn, gate
    const char* const valueIds[] = { "master", "gain", "volume", "distortion", "bass", "mid", "treble", "tone", "presence",
                                     "octave", "preampOn", "fuzzOn", "gate" };
    const Colour screenText (251, 251, 251);           // couleur du texte de l'ecran (layout.json du pack)

    Image png (const void* d, int n) { return ImageCache::getFromMemory (d, n); }

    Rectangle<float> square (Point<float> c, float side) { return { c.x - side * 0.5f, c.y - side * 0.5f, side, side }; }
}

//==============================================================================
// INVERSEUR
//==============================================================================
LeverSwitch::LeverSwitch (RangedAudioParameter& p)
    : attachment (p, [this] (float v)
                  {
                      const bool nv = v > 0.5f;
                      if (nv != on)
                      {
                          on = nv;
                          targetFrame = on ? 0 : 2;
                          shownFrame = 1;                                    // position intermediaire ~55 ms
                          transitionUntil = Time::getMillisecondCounterHiRes() + 55.0;
                          repaint();
                      }
                  })
{
    attachment.sendInitialUpdate();
    shownFrame = targetFrame = on ? 0 : 2;
    setMouseCursor (MouseCursor::PointingHandCursor);
}

bool LeverSwitch::hitTest (int x, int y)
{
    const auto c = getLocalBounds().toFloat().getCentre();
    return std::abs ((float) x - c.x) < (float) getWidth() * 0.32f && std::abs ((float) y - c.y) < (float) getHeight() * 0.48f;
}

void LeverSwitch::tick (double now)
{
    if (shownFrame != targetFrame && now >= transitionUntil) { shownFrame = targetFrame; repaint(); }
}

void LeverSwitch::paint (Graphics& g)
{
    if (! strip.isValid()) return;
    const int fs = strip.getWidth();
    g.setImageResamplingQuality (Graphics::highResamplingQuality);
    g.drawImage (strip, 0, 0, getWidth(), getHeight(), 0, shownFrame * fs, fs, fs);
}

void LeverSwitch::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { if (onRightClick) onRightClick (e); return; }
    // moitie haute = levier en haut (ON), moitie basse = levier en bas (OFF)
    const bool want = e.position.y < (float) getHeight() * 0.5f;
    if (want == on) return;
    attachment.setValueAsCompleteGesture (want ? 1.0f : 0.0f);
    if (onUserChange) onUserChange();
}

void LeverSwitch::mouseWheelMove (const MouseEvent&, const MouseWheelDetails& w)
{
    if (std::abs (w.deltaY) <= 0.0f) return;
    const bool want = w.deltaY > 0;                       // molette vers le haut = levier en haut = ON
    if (want != on) { attachment.setValueAsCompleteGesture (want ? 1.0f : 0.0f); if (onUserChange) onUserChange(); }
}

//==============================================================================
// FOOTSWITCH (fonctionnement d'Echoflex sur le footswitch du pack)
//==============================================================================
FootSwitchArea::FootSwitchArea (RangedAudioParameter& p, std::atomic<float>* holdMomentary)
    : hold (holdMomentary), attachment (p, [this] (float v) { value = v > 0.5f; })
{
    attachment.sendInitialUpdate();
    setMouseCursor (MouseCursor::PointingHandCursor);
}

bool FootSwitchArea::hitTest (int x, int y)
{
    const auto c = getLocalBounds().toFloat().getCentre();
    return c.getDistanceFrom ({ (float) x, (float) y }) <= (float) getWidth() * 0.5f * hitRadiusRatio;
}

void FootSwitchArea::paint (Graphics& g)
{
    // au repos : rien (footswitch cuit dans le fond) ; appuye : bouton enfonce (plus petit, plus sombre, gorge ombree)
    if (pressed && imgDown.isValid())
    {
        g.setImageResamplingQuality (Graphics::highResamplingQuality);
        g.drawImage (imgDown, getLocalBounds().toFloat());
    }
}

void FootSwitchArea::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { if (onRightClick) onRightClick (e); return; }
    pressed = true;
    downTime = Time::getMillisecondCounterHiRes();
    turnedOnByPress = ! value;
    repaint();
    attachment.setValueAsCompleteGesture (value ? 0.0f : 1.0f);
    if (onUserChange) onUserChange();
}

void FootSwitchArea::mouseUp (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) return;
    const bool momentary = hold != nullptr && hold->load() > 0.5f;
    if (pressed && momentary && turnedOnByPress && Time::getMillisecondCounterHiRes() - downTime > 450.0 && value)
    {
        attachment.setValueAsCompleteGesture (0.0f);
        if (onUserChange) onUserChange();
    }
    pressed = false;
    repaint();
}

//==============================================================================
// EDITEUR
//==============================================================================
PeachyAudioProcessorEditor::PeachyAudioProcessorEditor (PeachyAudioProcessor& p)
    : AudioProcessorEditor (&p), proc (p),
      octSwitch (*p.apvts.getParameter ("octave")),
      preFs  (*p.apvts.getParameter ("preampOn"), p.apvts.getRawParameterValue ("holdMomentary")),
      fuzzFs (*p.apvts.getParameter ("fuzzOn"),   p.apvts.getRawParameterValue ("holdMomentary"))
{
    background = png (BinaryData::background_png, BinaryData::background_pngSize);
    ledOn      = png (BinaryData::led_on_png, BinaryData::led_on_pngSize);
    ledOff     = png (BinaryData::led_off_png, BinaryData::led_off_pngSize);
    glowImg[0] = png (BinaryData::glow_led_l_png, BinaryData::glow_led_l_pngSize);
    glowImg[1] = png (BinaryData::glow_led_r_png, BinaryData::glow_led_r_pngSize);
    preFs.imgDown  = png (BinaryData::fs_down_l_png, BinaryData::fs_down_l_pngSize);
    fuzzFs.imgDown = png (BinaryData::fs_down_r_png, BinaryData::fs_down_r_pngSize);
    octSwitch.strip = png (BinaryData::toggle_strip_png, BinaryData::toggle_strip_pngSize);

    interFace   = Typeface::createSystemTypefaceFor (BinaryData::InterMedium_otf, BinaryData::InterMedium_otfSize);
    regularFace = Typeface::createSystemTypefaceFor (BinaryData::PoppinsRegular_ttf, BinaryData::PoppinsRegular_ttfSize);
    mediumFace  = Typeface::createSystemTypefaceFor (BinaryData::PoppinsMedium_ttf, BinaryData::PoppinsMedium_ttfSize);
    boldFace    = Typeface::createSystemTypefaceFor (BinaryData::PoppinsBold_ttf, BinaryData::PoppinsBold_ttfSize);
    menuLnf.f = { regularFace, mediumFace, boldFace };
    glow = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;

    // potards du pack : couronne + reflet masque + centre fixe + index (nh::Knob, flou de mouvement)
    nh::Knob::Layers L;
    L.crown   = png (BinaryData::knob_crown_png, BinaryData::knob_crown_pngSize);
    L.reflect = png (BinaryData::knob_reflect_png, BinaryData::knob_reflect_pngSize);
    L.center  = png (BinaryData::knob_center_png, BinaryData::knob_center_pngSize);
    L.marker  = png (BinaryData::knob_indicator_png, BinaryData::knob_indicator_pngSize);
    for (int i = 0; i < PeachyAudioProcessor::numKnobs; ++i)
    {
        auto& k = knobs[i];
        k = std::make_unique<nh::Knob> (*proc.apvts.getParameter (PeachyAudioProcessor::knobId (i)), L);
        k->onRightClick = [this, i] (const MouseEvent& e) { showContextMenu (&e, i); };
        k->onUserChange = [this, i] { proc.currentPreset = -1; lastChanged = i; statusUntil = Time::getMillisecondCounterHiRes() + 2500.0; };
        addAndMakeVisible (*k);
    }

    octSwitch.onRightClick = [this] (const MouseEvent& e) { showContextMenu (&e, 9); };
    octSwitch.onUserChange = [this] { proc.currentPreset = -1; };
    addAndMakeVisible (octSwitch);
    preFs.onRightClick  = [this] (const MouseEvent& e) { showContextMenu (&e, 10); };
    fuzzFs.onRightClick = [this] (const MouseEvent& e) { showContextMenu (&e, 11); };
    for (auto* f : { &preFs, &fuzzFs })
    {
        f->hitRadiusRatio = layout::footR / (layout::fsDownL.getWidth() * 0.5f);
        f->onUserChange = [this] { proc.currentPreset = -1; };
        addAndMakeVisible (*f);
    }

    for (int i = 0; i < numValueIds; ++i) lastValues[i] = proc.raw (valueIds[i]);
    lastPresetCounter = proc.presetCounter.load();
    lastMidiCount = proc.midiCounter.load();
    ledLevel[0] = proc.raw ("preampOn") > 0.5f ? 1.0f : 0.0f;
    ledLevel[1] = proc.raw ("fuzzOn") > 0.5f ? 1.0f : 0.0f;
    linePreset = buildPresetLine();

    // taille par defaut = taille minimale (hauteur de Ring Think), proportions bloquees
    const int defaultW = roundToInt (defaultH * baseW / baseH);
    setResizable (true, true);
    setResizeLimits (defaultW, (int) defaultH, roundToInt (maxH * baseW / baseH), (int) maxH);
    if (auto* cons = getConstrainer()) cons->setFixedAspectRatio ((double) baseW / (double) baseH);
    setOpaque (true);
    setSize (defaultW, (int) defaultH);
    setScaledHeight (sizeHeight (WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes)));
    rebuildCaches();
    startTimerHz (30);
}

PeachyAudioProcessorEditor::~PeachyAudioProcessorEditor()
{
    stopTimer();
    PopupMenu::dismissAllActiveMenus();
}

//==============================================================================
int PeachyAudioProcessorEditor::sizeHeight (int idx)
{
    const int h[numSizes] = { (int) defaultH, roundToInt (refH * 0.75f), (int) refH };
    return h[jlimit (0, numSizes - 1, idx)];
}

void PeachyAudioProcessorEditor::setScaledHeight (int h)
{
    h = jlimit ((int) defaultH, (int) maxH, h);
    setSize (roundToInt ((float) h * baseW / baseH), h);
}

void PeachyAudioProcessorEditor::setGlowPercent (int pc)
{
    NineHandsGlow::setPercent (JucePlugin_Name, pc);
    glow = (float) jlimit (25, 100, pc) / 100.0f;
    repaint();
}

Rectangle<int> PeachyAudioProcessorEditor::scaled (Rectangle<float> r) const
{
    const float s = (float) getHeight() / baseH;
    return r.transformedBy (AffineTransform::scale (s)).getSmallestIntegerContainer();
}

float PeachyAudioProcessorEditor::physicalScale() const
{
    return jlimit (1.0f, 4.0f, (float) Component::getApproximateScaleFactorForComponent (this));
}

void PeachyAudioProcessorEditor::flash (const String& s)
{
    flashLine = s;
    flashUntil = Time::getMillisecondCounterHiRes() + 1800.0;
    statusUntil = jmax (statusUntil, flashUntil);
}

// cache du fond a la resolution physique de l'ecran (reconstruit par le timer seulement)
void PeachyAudioProcessorEditor::rebuildCaches (float sc)
{
    if (sc <= 0.0f) sc = cacheScale > 0.0f ? cacheScale : physicalScale();
    const int w = getWidth(), h = getHeight();
    if (w <= 0 || h <= 0) return;
    if (w == cacheW && h == cacheH && std::abs (sc - cacheScale) < 0.01f && bgScaled.isValid()) return;
    cacheW = w; cacheH = h; cacheScale = sc;
    const int pw = roundToInt ((float) w * sc), ph = roundToInt ((float) h * sc);
    if (pw >= background.getWidth()) bgScaled = background;
    else
    {
        Image s = background;
        while (s.getWidth() > pw * 2) s = s.rescaled (s.getWidth() / 2, s.getHeight() / 2, Graphics::highResamplingQuality);
        bgScaled = s.rescaled (pw, ph, Graphics::highResamplingQuality);
    }
    repaint();
}

void PeachyAudioProcessorEditor::resized()
{
    // anti-gel : jamais de setSize ici ; les limites du constrainer suffisent
    for (int i = 0; i < PeachyAudioProcessor::numKnobs; ++i)
        knobs[i]->setBounds (scaled (square (layout::knobPos[i], layout::knobFrame[i])));
    octSwitch.setBounds (scaled (square (layout::togglePos, layout::toggleS)));
    preFs.setBounds  (scaled (layout::fsDownL));
    fuzzFs.setBounds (scaled (layout::fsDownR));
    resizeSettle = 4;
}

//==============================================================================
// Anti-gel v2 : rendu logiciel force sous Windows, aucun calcul lourd dans paint(), caches reconstruits par le timer,
// chien de garde de redessin ; cote audio, aucun appel a l'hote.
//==============================================================================
void PeachyAudioProcessorEditor::useSoftwareRenderer()
{
    auto* peer = getPeer();
    if (peer != lastPeer) { lastPeer = peer; repaint(); }
   #if JUCE_WINDOWS
    if (peer != nullptr)
    {
        int sw = peer->getAvailableRenderingEngines().indexOf ("Software Renderer");
        if (sw < 0) sw = 0;
        if (peer->getCurrentRenderingEngine() != sw) peer->setCurrentRenderingEngine (sw);
    }
   #endif
}

void PeachyAudioProcessorEditor::parentHierarchyChanged() { useSoftwareRenderer(); }
void PeachyAudioProcessorEditor::visibilityChanged()      { useSoftwareRenderer(); if (isShowing()) repaint(); }

void PeachyAudioProcessorEditor::askRepaint (Rectangle<int> r)
{
    if (repaintAskedMs <= 0.0) repaintAskedMs = Time::getMillisecondCounterHiRes();
    repaint (r);
}

//==============================================================================
String PeachyAudioProcessorEditor::buildStatusLine() const
{
    const int i = lastChanged;
    if (i < 0) return {};
    const float v = proc.raw (valueIds[i]);
    static const char* names[] = { "Master", "Gain", "Volume", "Distortion", "Bass", "Mid", "Treble", "Tone", "Presence" };
    if (i < 9) return String (names[i]) + "  " + String (roundToInt (v * 10.0f)) + " %";
    if (i == 9)  return v > 0.5f ? "Octave  ON" : "Octave  OFF";
    if (i == 10) return v > 0.5f ? "Preamp  ON" : "Preamp  OFF";
    if (i == 11) return v > 0.5f ? "Fuzz  ON" : "Fuzz  OFF";
    return "Noise gate  " + PeachyAudioProcessor::gateNames()[jlimit (0, 3, roundToInt (v))];
}

String PeachyAudioProcessorEditor::buildPresetLine() const
{
    const int cp = proc.currentPreset.load();
    String s;
    if (cp >= 0 && cp < PeachyAudioProcessor::getNumFactoryPresets())
        s << "P" << (cp + 1) << "  " << PeachyAudioProcessor::getFactoryPreset (cp).name;
    else if (cp > 100) s << "User " << (cp - 100);
    else               s << "Edited";
    if (! proc.modelsLoaded()) s << "  -  fuzz captures not loaded";
    return s;
}

//==============================================================================
void PeachyAudioProcessorEditor::timerCallback()
{
    const double now = Time::getMillisecondCounterHiRes();
    if (getPeer() != lastPeer || now - lastRendererCheckMs > 1000.0) { lastRendererCheckMs = now; useSoftwareRenderer(); }

    if (resizeSettle > 0 && --resizeSettle == 0) rebuildCaches();
    else if (resizeSettle == 0 && now - lastScaleCheckMs > 250.0)
    {
        lastScaleCheckMs = now;
        const float sc = physicalScale();
        if (std::abs (sc - cacheScale) > 0.01f) rebuildCaches (sc);
    }
    if (now - lastGlowCheckMs > 3000.0)                 // reglage Glow commun a toutes les fenetres du plugin
    {
        lastGlowCheckMs = now;
        const float g = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;
        if (std::abs (g - glow) > 0.001f) { glow = g; repaint(); }
    }

    if (repaintAskedMs > 0.0 && isShowing() && now - repaintAskedMs > 1500.0 && lastPaintMs < repaintAskedMs)
    {
        repaintAskedMs = 0.0; lastPeer = nullptr;
        useSoftwareRenderer(); repaint();
    }

    octSwitch.tick (now);

    int changed = -1, numChanged = 0;
    for (int i = 0; i < numValueIds; ++i)
    {
        const float v = proc.raw (valueIds[i]);
        if (std::abs (v - lastValues[i]) > 1.0e-4f) { lastValues[i] = v; changed = i; ++numChanged; }
    }
    const int pcount = proc.presetCounter.load();
    if (pcount != lastPresetCounter) { lastPresetCounter = pcount; numChanged = 0; statusUntil = 0.0; }
    if (numChanged == 1) { lastChanged = changed; statusUntil = now + 2500.0; learnLineUntil = 0.0; flashUntil = 0.0; }
    for (int i = 0; i < PeachyAudioProcessor::numKnobs; ++i)
        if (knobs[i]->isDragging()) { lastChanged = i; statusUntil = now + 2500.0; }

    // MIDI Learn : attente puis confirmation 2 s sur l'ecran
    const int lt = proc.learnTarget.load();
    const int learned = proc.lastLearned.exchange (-1);
    if (learned >= 0)
    {
        learnLine = String (PeachyAudioProcessor::learnDef (learned).name) + " = CC " + String (proc.ccMap[learned].load());
        learnLineUntil = now + 2000.0;
        statusUntil = jmax (statusUntil, learnLineUntil);
    }
    else if (lt >= 0)
    {
        learnLine = "MIDI LEARN \xc2\xb7 " + String (PeachyAudioProcessor::learnDef (lt).name);
        learnLineUntil = now + 200.0;
        statusUntil = jmax (statusUntil, now + 200.0);
    }
    const int mc = proc.midiCounter.load();
    if (mc != lastMidiCount) { lastMidiCount = mc; midiFlash = 8; }
    if (midiFlash > 0) --midiFlash;

    // fondu croise : ~120 ms a l'apparition, ~300 ms au retour de la barre de presets
    const float target = now < statusUntil ? 1.0f : 0.0f;
    statusAlpha += (target - statusAlpha) * (target > statusAlpha ? 0.55f : 0.20f);
    if (statusAlpha < 0.005f) statusAlpha = 0.0f;
    if (statusAlpha > 0.995f) statusAlpha = 1.0f;

    // LED : PREAMP (gauche), FUZZ (droite) ; fondu 0,45 a l'allumage / 0,28 a l'extinction
    const bool on[2] = { proc.raw ("preampOn") > 0.5f, proc.raw ("fuzzOn") > 0.5f };
    const Rectangle<float> gr[2] = { layout::glowL, layout::glowR };
    for (int i = 0; i < 2; ++i)
    {
        auto& l = ledLevel[i];
        l += ((on[i] ? 1.0f : 0.0f) - l) * (on[i] ? 0.45f : 0.28f);
        if (l < 0.003f) l = 0.0f;
        if (l > 0.997f) l = 1.0f;
        if (std::abs (l - drawnLed[i]) > 0.004f) { drawnLed[i] = l; askRepaint (scaled (gr[i])); }
    }

    String st;
    if (flashUntil > now) st = flashLine;
    else if (learnLineUntil > 0.0 && now < learnLineUntil + 800.0) st = learnLine;
    else st = buildStatusLine();
    const auto pl = buildPresetLine();
    if (std::abs (statusAlpha - drawnStatus) > 0.003f || (statusAlpha > 0.0f && st != lineStatus) || pl != linePreset
        || hoverZone != drawnHover || midiFlash > 0)
    {
        drawnStatus = statusAlpha; lineStatus = st; linePreset = pl; drawnHover = hoverZone;
        askRepaint (scaled (layout::display.expanded (4.0f)));
    }
}

//==============================================================================
void PeachyAudioProcessorEditor::drawLeds (Graphics& g)
{
    const Rectangle<float> led[2] = { layout::ledL, layout::ledR }, gr[2] = { layout::glowL, layout::glowR };
    g.setImageResamplingQuality (Graphics::highResamplingQuality);
    for (int i = 0; i < 2; ++i)
    {
        const float level = ledLevel[i];
        if (level > 0.003f && glowImg[i].isValid()) { g.setOpacity (jmin (1.0f, level * glow)); g.drawImage (glowImg[i], gr[i]); }   // halo dose par Glow
        g.setOpacity (1.0f);
        if (ledOff.isValid()) g.drawImage (ledOff, led[i]);
        if (level > 0.003f && ledOn.isValid()) { g.setOpacity (level); g.drawImage (ledOn, led[i]); }   // la LED elle-meme : jamais dosee
        g.setOpacity (1.0f);
    }
}

void PeachyAudioProcessorEditor::drawDisplay (Graphics& g)
{
    // ecran du pack (creux, fleches cuits) : texte Inter Medium, centre ; barre de presets et ligne d'etat au meme endroit
    const auto r = layout::display;
    const float a = statusAlpha;
    const Font f (FontOptions (interFace).withHeight (layout::displayFont));
    const auto textArea = Rectangle<float> (layout::arrowL.x + 14.0f, r.getY(), layout::arrowR.x - layout::arrowL.x - 28.0f, r.getHeight());
    auto drawLine = [&] (const String& s, float alpha, Colour c)
    {
        if (alpha <= 0.0f || s.isEmpty()) return;
        g.setFont (f);
        g.setColour (c.withAlpha (alpha));
        // bande des capitales centree sur y = displayCentre.y (regle du pack)
        const float capH = f.getAscent() * 0.727f;
        const float base = layout::displayCentre.y + capH * 0.5f;
        g.drawFittedText (s, textArea.withY (base - f.getAscent()).withHeight (f.getHeight()).toNearestInt(), Justification::centredTop, 1, 0.6f);
    };
    drawLine (linePreset, 1.0f - a, midiFlash > 0 ? Colour (0xffff9a80) : screenText.withAlpha (hoverZone == 2 ? 1.0f : 0.94f));
    drawLine (lineStatus, a, screenText);
    // fleches cuites dans le fond : on les eclaire au survol
    if (a < 0.5f && (hoverZone == 1 || hoverZone == 3))
    {
        const auto c = hoverZone == 1 ? layout::arrowL : layout::arrowR;
        ColourGradient halo (screenText.withAlpha (0.22f), c.x, c.y, screenText.withAlpha (0.0f), c.x + 11.0f, c.y, true);
        g.setGradientFill (halo);
        g.fillEllipse (c.x - 11.0f, c.y - 11.0f, 22.0f, 22.0f);
    }
}

void PeachyAudioProcessorEditor::paint (Graphics& g)
{
    lastPaintMs = Time::getMillisecondCounterHiRes();
    repaintAskedMs = 0.0;
    g.fillAll (Colour (0xff121212));                 // gris tres sombre derriere les zones transparentes (jacks, coins)
    const Image& bg = bgScaled.isValid() ? bgScaled : background;
    g.setImageResamplingQuality (&bg == &background ? Graphics::highResamplingQuality : Graphics::lowResamplingQuality);
    if (bg.isValid()) g.drawImage (bg, getLocalBounds().toFloat());

    const float s = (float) getHeight() / baseH;
    g.addTransform (AffineTransform::scale (s));
    drawLeds (g);
    drawDisplay (g);
}

//==============================================================================
int PeachyAudioProcessorEditor::presetZoneAt (Point<float> p) const
{
    const auto r = layout::display;
    if (! r.contains (p)) return 0;
    if (p.x < r.getX() + 52.0f) return 1;
    if (p.x > r.getRight() - 52.0f) return 3;
    return 2;
}

void PeachyAudioProcessorEditor::mouseMove (const MouseEvent& e)
{
    hoverZone = presetZoneAt (e.position / ((float) getHeight() / baseH));
    setMouseCursor (hoverZone != 0 ? MouseCursor::PointingHandCursor : MouseCursor::NormalCursor);
}

void PeachyAudioProcessorEditor::mouseExit (const MouseEvent&) { hoverZone = 0; }

void PeachyAudioProcessorEditor::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { showContextMenu (&e); return; }
    const int z = presetZoneAt (e.position / ((float) getHeight() / baseH));
    if (z != 0 && statusAlpha > 0.0f) { statusUntil = 0.0; flashUntil = 0.0; learnLineUntil = 0.0; return; }   // un clic fait revenir la barre
    switch (z)
    {
        case 1: stepPreset (-1); break;
        case 2: showPresetMenu(); break;
        case 3: stepPreset (1); break;
        default: break;
    }
}

void PeachyAudioProcessorEditor::stepPreset (int delta)
{
    const int n = PeachyAudioProcessor::getNumFactoryPresets();
    int cp = proc.currentPreset.load();
    if (cp < 0 || cp >= n) cp = delta > 0 ? -1 : 0;
    proc.applyFactoryPreset ((cp + delta + n) % n);
}

void PeachyAudioProcessorEditor::buildPresetMenu (PopupMenu& m)
{
    m.setLookAndFeel (&menuLnf);
    NineHandsMenu::addHeader (m, menuLnf.f, NineHandsMenu::icoPreset, menuAccent, "Presets", buildPresetLine());
    m.addSectionHeader ("Factory presets");
    for (int i = 0; i < PeachyAudioProcessor::getNumFactoryPresets(); ++i)
        m.addItem (100 + i, "Preset " + String (i + 1) + "  " + PeachyAudioProcessor::getFactoryPreset (i).name, true, proc.currentPreset.load() == i);
    m.addSeparator();
    PopupMenu load, save;
    for (int slot = 1; slot <= 9; ++slot)
    {
        const bool exists = proc.hasUserPreset (slot);
        load.addItem (200 + slot, "User preset " + String (slot) + (exists ? "" : "  (empty)"), exists, proc.currentPreset.load() == 100 + slot);
        save.addItem (300 + slot, "Save user preset " + String (slot) + (exists ? "  (overwrite)" : ""));
    }
    m.addSubMenu ("Load user preset", load);
    m.addSubMenu ("Save user preset", save);
}

void PeachyAudioProcessorEditor::showPresetMenu()
{
    PopupMenu m;
    buildPresetMenu (m);
    m.showMenuAsync (PopupMenu::Options().withTargetScreenArea (localAreaToGlobal (scaled (layout::display))),
        [safe = Component::SafePointer<PeachyAudioProcessorEditor> (this)] (int r) { if (safe != nullptr && r != 0) safe->handleMenu (r); });
}

void PeachyAudioProcessorEditor::buildContextMenu (PopupMenu& menu, int learnIdx)
{
    using namespace NineHandsMenu;
    menu.setLookAndFeel (&menuLnf);
    if (learnIdx >= 0 && learnIdx < PeachyAudioProcessor::numLearn)
    {
        // clic droit sur une commande : en-tete de la commande + MIDI Learn en tete du menu
        const int cc = proc.ccMap[learnIdx].load();
        const int lt = proc.learnTarget.load();
        const String name = PeachyAudioProcessor::learnDef (learnIdx).name;
        const int ico = learnIdx < 9 ? icoKnob : icoSwitch;
        addHeader (menu, menuLnf.f, ico, menuAccent, name, "MIDI: " + (cc >= 0 ? "CC " + String (cc) : String ("not assigned")));
        menu.addItem (1000 + learnIdx, "MIDI Learn", true, lt == learnIdx);
        menu.addItem (1100 + learnIdx, "Clear MIDI", cc >= 0);
        if (lt >= 0) menu.addItem (1200, "Cancel MIDI learn");
        menu.addSeparator();
    }
    else
        addHeader (menu, menuLnf.f, icoPedal, menuAccent, "Peachy", "Preamp + fuzz  v" + String (JucePlugin_VersionString));

    {
        // Plugin size : taille de cette fenetre + taille par defaut des nouvelles fenetres (comme Octopus)
        const char* names[numSizes] = { "60 %", "75 %", "100 %" };
        const int def = WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes);
        PopupMenu sizes, defSizes;
        for (int i = 0; i < numSizes; ++i)
        {
            sizes.addItem (1 + i, String (names[i]) + (i == 0 ? "  (default)" : ""), true, std::abs (getHeight() - sizeHeight (i)) <= 2);
            defSizes.addItem (20 + i, String ("Size ") + names[i], true, i == def);
        }
        sizes.addSeparator();
        sizes.addSubMenu ("Default size (new windows)", defSizes);
        menu.addSubMenu ("Plugin size", sizes);
    }
    {
        PopupMenu glowM;                   // reglage du halo des lumieres (regle des skills, nov. 2026)
        const int now = roundToInt (glow * 100.0f);
        for (int i = 0; i < NineHandsGlow::numSteps; ++i)
        {
            const int pc = NineHandsGlow::steps[i];
            glowM.addItem (60 + i, "Glow " + String (pc) + " %" + (pc == 100 ? "  (default)" : ""), true, now == pc);
        }
        menu.addSubMenu ("Glow (halo of the lights)", glowM);
    }
    menu.addSeparator();

    PopupMenu factory;
    for (int i = 0; i < PeachyAudioProcessor::getNumFactoryPresets(); ++i)
        factory.addItem (100 + i, "Preset " + String (i + 1) + "  " + PeachyAudioProcessor::getFactoryPreset (i).name, true, proc.currentPreset.load() == i);
    menu.addSubMenu ("Factory presets", factory);
    PopupMenu load, save;
    for (int slot = 1; slot <= 9; ++slot)
    {
        const bool exists = proc.hasUserPreset (slot);
        load.addItem (200 + slot, "User preset " + String (slot) + (exists ? "" : "  (empty)"), exists, proc.currentPreset.load() == 100 + slot);
        save.addItem (300 + slot, "Save user preset " + String (slot) + (exists ? "  (overwrite)" : ""));
    }
    menu.addSubMenu ("Load user preset", load);
    menu.addSubMenu ("Save user preset", save);
    menu.addSeparator();

    PopupMenu gate;
    const int gNow = jlimit (0, 3, roundToInt (proc.raw ("gate")));
    const char* gateHelp[4] = { "Gate off", "Gate light (default)", "Gate medium", "Gate strong (noisy pickups / hum)" };
    for (int i = 0; i < 4; ++i) gate.addItem (50 + i, gateHelp[i], true, gNow == i);
    menu.addSubMenu ("Noise gate", gate);

    PopupMenu settings;
    settings.addItem (40, "Hold footswitch = momentary", true, proc.raw ("holdMomentary") > 0.5f);
    settings.addSeparator();
    settings.addItem (41, "MIDI footswitches latching (127 = on / 0 = off)", true, proc.raw ("midiFsMode") < 0.5f);
    settings.addItem (42, "MIDI footswitches momentary (toggle each press)", true, proc.raw ("midiFsMode") > 0.5f);
    menu.addSubMenu ("Settings", settings);

    PopupMenu midi;
    for (int i = 0; i < PeachyAudioProcessor::numLearn; ++i)
    {
        const int cc = proc.ccMap[i].load();
        midi.addItem (1000 + i, "MIDI Learn " + String (PeachyAudioProcessor::learnDef (i).name)
                                 + "  (" + (cc >= 0 ? "CC " + String (cc) : String ("none")) + ")",
                      true, proc.learnTarget.load() == i);
    }
    midi.addSeparator();
    if (proc.learnTarget.load() >= 0) midi.addItem (1200, "Cancel MIDI learn");
    midi.addItem (1201, "Clear all MIDI assignments");
    midi.addSeparator();
    midi.addItem (914, "MIDI Program Change 1-10 = factory presets", false);
    menu.addSubMenu ("MIDI", midi);
    menu.addSeparator();
    menu.addItem (999, "Info  Peachy v" + String (JucePlugin_VersionString) + "  NINE HANDS | DSP", false);
}

void PeachyAudioProcessorEditor::showContextMenu (const MouseEvent*, int learnIdx)
{
    PopupMenu menu;
    buildContextMenu (menu, learnIdx);
    menu.showMenuAsync (PopupMenu::Options().withMousePosition(),       // toujours la ou l'on clique
        [safe = Component::SafePointer<PeachyAudioProcessorEditor> (this)] (int r) { if (safe != nullptr && r != 0) safe->handleMenu (r); });
}

void PeachyAudioProcessorEditor::handleMenu (int r)
{
    auto& pr = proc;
    if      (r >= 1 && r < 1 + numSizes) setScaledHeight (sizeHeight (r - 1));
    else if (r >= 20 && r < 20 + numSizes)
    {
        WigaWindowSize::setDefaultIndex (JucePlugin_Name, r - 20);   // toutes les nouvelles fenetres de ce plugin
        setScaledHeight (sizeHeight (r - 20));                        // et cette fenetre tout de suite
    }
    else if (r == 40) pr.setParamValue ("holdMomentary", pr.raw ("holdMomentary") > 0.5f ? 0.0f : 1.0f);
    else if (r == 41) pr.setParamValue ("midiFsMode", 0.0f);
    else if (r == 42) pr.setParamValue ("midiFsMode", 1.0f);
    else if (r >= 50 && r <= 53) pr.setParamValue ("gate", (float) (r - 50));
    else if (r >= 60 && r < 60 + NineHandsGlow::numSteps)
    {
        setGlowPercent (NineHandsGlow::steps[r - 60]);
        flash ("Glow  " + String (NineHandsGlow::steps[r - 60]) + " %");
    }
    else if (r >= 100 && r < 200) pr.applyFactoryPreset (r - 100);
    else if (r > 200 && r < 300)  pr.loadUserPreset (r - 200);
    else if (r > 300 && r < 400)  pr.saveUserPreset (r - 300);
    else if (r >= 1000 && r < 1000 + PeachyAudioProcessor::numLearn)
        pr.learnTarget.store (pr.learnTarget.load() == r - 1000 ? -1 : r - 1000);     // re-cliquer annule
    else if (r >= 1100 && r < 1100 + PeachyAudioProcessor::numLearn) pr.ccMap[r - 1100].store (-1);
    else if (r == 1200) pr.learnTarget.store (-1);
    else if (r == 1201) { pr.learnTarget.store (-1); pr.resetMidiMap(); }
}
