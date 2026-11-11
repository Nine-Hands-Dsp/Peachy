#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_audio_processors/juce_audio_processors.h>

//==============================================================================
// nh::Knob (NINE HANDS | DSP, skill potards-nine-hands-dsp) adapte aux calques du pack Peachy (design v7) :
//   couronne      (tourne, flou de mouvement)
//   reflet        (FIXE, monde : alpha multiplie par l'alpha de la couronne tournee -> rien ne flotte dans les creux)
//   centre        (FIXE : disque brosse + biseau metal, la lumiere ne bouge pas)
//   index         (tourne, meme angle, flou de mouvement)
// L'ombre portee est cuite dans le fond du pack (lumiere en haut a gauche a 45 deg).
// Flou : longueur = angle parcouru pendant l'image, montee immediate, retombee x0,6 par image, pas de 3 deg max.
// Anti-gel v2 : timer 30 Hz, paint() ne fait que dessiner l'image prete, caches reconstruits par le timer seulement.
//==============================================================================
namespace nh
{
struct KnobStyle
{
    float startAngle = juce::degreesToRadians (-135.0f);
    float endAngle   = juce::degreesToRadians ( 135.0f);
    float blurMax    = juce::degreesToRadians (40.0f);
    float blurStep   = juce::degreesToRadians (3.0f);
    float blurDecay  = 0.6f;
    float dragPixels = 250.0f;
    float hitRatio   = 0.975f;     // disque cliquable / demi-cote du calque
};

class Knob : public juce::Component, private juce::Timer
{
public:
    struct Layers { juce::Image crown, reflect, center, marker; };

    using Style = KnobStyle;

    Knob (juce::RangedAudioParameter& p, Layers l, Style s = {})
        : param (p), layers (std::move (l)), style (s),
          attachment (p, [this] (float v) { target = param.convertTo0to1 (v); }, nullptr)
    {
        attachment.sendInitialUpdate();
        lastAngle = angleFor (target);
        setMouseCursor (juce::MouseCursor::PointingHandCursor);
        startTimerHz (30);
    }

    std::function<void (const juce::MouseEvent&)> onRightClick;
    std::function<void()> onUserChange;
    bool isDragging() const { return dragging; }

    bool hitTest (int x, int y) override
    {
        const auto c = getLocalBounds().toFloat().getCentre();
        return c.getDistanceFrom ({ (float) x, (float) y }) <= (float) getWidth() * 0.5f * style.hitRatio;
    }

    void resized() override { resizeSettle = frame.isValid() ? 3 : 1; }

    void paint (juce::Graphics& g) override
    {
        if (frame.isValid())
        {
            g.setImageResamplingQuality (juce::Graphics::mediumResamplingQuality);
            g.drawImage (frame, getLocalBounds().toFloat());
        }
    }

    void mouseDown (const juce::MouseEvent& e) override
    {
        if (e.mods.isPopupMenu()) { if (onRightClick) onRightClick (e); return; }
        dragging = true; lastY = e.position.y; attachment.beginGesture();
        if (onUserChange) onUserChange();
    }
    void mouseDrag (const juce::MouseEvent& e) override
    {
        if (! dragging) return;
        const auto range = style.dragPixels * (e.mods.isShiftDown() ? 5.0f : 1.0f);
        const auto dy = e.position.y - lastY; lastY = e.position.y;
        setNormalised (target - dy / range, true);
    }
    void mouseUp (const juce::MouseEvent&) override { if (dragging) attachment.endGesture(); dragging = false; }
    void mouseDoubleClick (const juce::MouseEvent& e) override
    {
        if (e.mods.isPopupMenu()) return;
        setNormalised (param.getDefaultValue(), false);
        if (onUserChange) onUserChange();
    }
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails& w) override
    {
        setNormalised (target + w.deltaY * 0.05f, false);
        if (onUserChange) onUserChange();
    }

private:
    float angleFor (float v) const { return style.startAngle + v * (style.endAngle - style.startAngle); }

    void setNormalised (float v, bool inGesture)
    {
        target = juce::jlimit (0.0f, 1.0f, v);
        const auto plain = param.convertFrom0to1 (target);
        if (inGesture) attachment.setValueAsPartOfGesture (plain);
        else           attachment.setValueAsCompleteGesture (plain);
    }

    void timerCallback() override
    {
        if (++scaleTick >= 8)
        {
            scaleTick = 0;
            const auto s = juce::jmax (1.0f, juce::Component::getApproximateScaleFactorForComponent (this));
            if (std::abs (s - scale) > 0.01f && resizeSettle == 0) resizeSettle = 1;
        }
        if (resizeSettle > 0 && --resizeSettle == 0) { rebuildCache(); dirty = true; }

        const auto a = angleFor (target);
        const auto v = a - lastAngle;
        lastAngle = a;
        if (std::abs (v) > 1.0e-5f) blurDir = v > 0.0f ? 1.0f : -1.0f;
        blurSpan = juce::jmax (juce::jmin (std::abs (v), style.blurMax), blurSpan * style.blurDecay);
        if (blurSpan < 0.002f) blurSpan = 0.0f;

        const bool changed = dirty || std::abs (a - drawnAngle) > 1.0e-4f || blurSpan != drawnSpan;
        if (changed && crownC.isValid())
        {
            renderFrame (a);
            drawnAngle = a; drawnSpan = blurSpan; dirty = false;
            repaint();
        }
    }

    // calque tourne (moyenne de positions pendant le flou), dans une image de px x px
    void drawRotated (juce::Image& dst, const juce::Image& src, float a)
    {
        dst.clear (dst.getBounds());
        juce::Graphics g (dst);
        g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
        const float c = (float) px * 0.5f;
        if (blurSpan <= 0.0f) { g.drawImageTransformed (src, juce::AffineTransform::rotation (a, c, c), false); return; }
        const int n = juce::jlimit (4, 16, (int) std::ceil (blurSpan / style.blurStep) + 1);
        for (int k = 0; k < n; ++k)
        {
            const auto t = (float) k / (float) (n - 1);
            g.setOpacity (1.0f / (float) (k + 1));                         // moyenne progressive
            g.drawImageTransformed (src, juce::AffineTransform::rotation (a - blurDir * blurSpan * t, c, c), false);
        }
    }

    void renderFrame (float a)
    {
        if (px <= 0) return;
        drawRotated (crownBuf, crownC, a);
        drawRotated (markBuf, markC, a);
        // reflet du monde masque par l'alpha de la couronne tournee (regle 2.3 du pack) : A = A_reflet x A_couronne
        reflBuf.clear (reflBuf.getBounds());
        { juce::Graphics g (reflBuf); g.drawImageAt (reflC, 0, 0); }
        {
            juce::Image::BitmapData rb (reflBuf, juce::Image::BitmapData::readWrite);
            juce::Image::BitmapData cb (crownBuf, juce::Image::BitmapData::readOnly);
            for (int y = 0; y < px; ++y)
            {
                auto* r = rb.getLinePointer (y);
                const auto* c = cb.getLinePointer (y);
                for (int x = 0; x < px; ++x)
                {
                    auto* rp = reinterpret_cast<juce::PixelARGB*> (r + x * rb.pixelStride);
                    const auto* cp = reinterpret_cast<const juce::PixelARGB*> (c + x * cb.pixelStride);
                    rp->multiplyAlpha ((int) cp->getAlpha());
                }
            }
        }
        frame.clear (frame.getBounds());
        juce::Graphics g (frame);
        g.drawImageAt (crownBuf, 0, 0);
        g.drawImageAt (reflBuf, 0, 0);
        g.drawImageAt (centerC, 0, 0);
        g.drawImageAt (markBuf, 0, 0);
    }

    void rebuildCache()
    {
        scale = juce::jmax (1.0f, juce::Component::getApproximateScaleFactorForComponent (this));
        px = juce::roundToInt ((float) juce::jmin (getWidth(), getHeight()) * scale);
        if (px <= 0) return;
        auto fit = [this] (const juce::Image& src)
        {
            juce::Image out (juce::Image::ARGB, px, px, true, juce::SoftwareImageType());
            if (src.isNull()) return out;
            juce::Graphics g (out);
            g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
            // reduction en une fois depuis les 800 px (deux passes si la reduction est forte : pas de crenelage)
            juce::Image s = src;
            while (s.getWidth() > px * 2) s = s.rescaled (s.getWidth() / 2, s.getHeight() / 2, juce::Graphics::highResamplingQuality);
            g.drawImage (s, juce::Rectangle<float> (0.0f, 0.0f, (float) px, (float) px), juce::RectanglePlacement::stretchToFit);
            return out;
        };
        crownC = fit (layers.crown); reflC = fit (layers.reflect); centerC = fit (layers.center); markC = fit (layers.marker);
        for (auto* im : { &frame, &crownBuf, &markBuf, &reflBuf })
            *im = juce::Image (juce::Image::ARGB, px, px, true, juce::SoftwareImageType());
    }

    juce::RangedAudioParameter& param;
    Layers layers;
    Style style;
    juce::ParameterAttachment attachment;
    juce::Image crownC, reflC, centerC, markC, frame, crownBuf, markBuf, reflBuf;
    float scale = 1.0f, target = 0.0f, lastAngle = 0.0f;
    float blurSpan = 0.0f, blurDir = 1.0f, lastY = 0.0f;
    float drawnAngle = 1.0e9f, drawnSpan = -1.0f;
    int px = 0, resizeSettle = 0, scaleTick = 0;
    bool dragging = false, dirty = true;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (Knob)
};
} // namespace nh
