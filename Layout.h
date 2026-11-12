#pragma once
#include <juce_graphics/juce_graphics.h>

// Peachy v2 : reperes generes par tools/v7/make_v2_art.py a partir du pack design v7 (layout.json, 2350 x 1800 px)
// unites du plugin = pixels du design / 2 (repere 1175 x 900)
namespace layout
{
    constexpr float baseW = 1175.0f, baseH = 900.0f;
    const juce::Point<float> knobPos[9] = { { 234.00f, 171.75f }, { 466.50f, 171.75f }, { 699.50f, 171.75f }, { 989.00f, 171.75f }, { 120.50f, 381.50f }, { 353.00f, 381.50f }, { 586.00f, 381.50f }, { 875.25f, 381.50f }, { 471.25f, 547.25f } };
    const float knobFrame[9] = { 135.50f, 135.50f, 135.50f, 135.50f, 135.50f, 135.50f, 135.50f, 135.50f, 74.00f };   // cote du calque 800 px (271 / 148 px)
    const float knobHit[9] = { 66.00f, 66.00f, 66.00f, 66.00f, 66.00f, 66.00f, 66.00f, 66.00f, 36.00f };
    const juce::Point<float> togglePos { 1021.25f, 382.50f };
    constexpr float toggleS = 84.00f;
    const juce::Rectangle<float> ledL { 243.00f, 531.00f, 32.50f, 32.50f };
    const juce::Rectangle<float> glowL { 139.00f, 427.00f, 240.00f, 240.00f };
    const juce::Rectangle<float> ledR { 897.00f, 531.00f, 32.50f, 32.50f };
    const juce::Rectangle<float> glowR { 793.50f, 427.00f, 240.00f, 240.00f };
    const juce::Point<float> fsL { 200.00f, 761.25f };
    const juce::Rectangle<float> fsDownL { 144.00f, 705.00f, 112.00f, 112.00f };
    const juce::Point<float> fsR { 975.50f, 761.25f };
    const juce::Rectangle<float> fsDownR { 919.50f, 705.00f, 112.00f, 112.00f };
    constexpr float footR = 54.50f;           // zone d'appui (bouton + bague)
    const juce::Rectangle<float> display { 389.00f, 739.00f, 396.00f, 48.50f };
    const juce::Point<float> displayCentre { 587.00f, 763.25f };
    constexpr float displayFont = 25.00f;   // Inter Medium 50 px du design
    const juce::Point<float> arrowL { 415.00f, 763.25f }, arrowR { 759.00f, 763.25f };
}
