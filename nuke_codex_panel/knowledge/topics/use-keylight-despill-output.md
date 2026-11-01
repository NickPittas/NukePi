---
id: "topics/use-keylight-despill-output"
kind: "topic"
title: "Keylight as a separate despill / corrected-colour output"
category: "keying"
summary: "Keylight used for corrected RGB rather than for the alpha: which View output carries despilled colour, how premultiplication follows, what to view, failures, and when to ask."
aliases: ["keylight despill", "keylight final result", "keylight intermediate result", "keylight output mode"]
tags: ["purpose:keylight:despill-output", "review:rgb", "keylight", "despill", "view", "color", "treatment", "control:show", "control:unPreMultiply", "control:screenColor", "control:despillBias", "control:gangBiases", "control:alphaBias", "control:screenReplaceMethod", "control:screenReplaceColour"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/keying-conventions"]
related: ["nodes/keylight", "topics/use-keylight-single-key", "topics/use-spill-map", "topics/use-saturation-rgb", "nodes/copy"]
nodes: ["Keylight", "Copy", "Premult", "Unpremult"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "brinkmann-2e", "studio-conventions"]
---
# Keylight as a separate despill / corrected-colour output

## Applicability
Use when Keylight's colour, not its alpha, is wanted as its own branch. Studio default (studio-conventions, a preference): keyers are alpha extractors; the final alpha is Copied onto the retained RGB, and despill, edge treatment and premultiplication follow. Which `show` (View) mode gives the colour to use for this branch is not stated by Foundry; it must be observed on the plate (below).

## Workflow
Documented facts (Foundry, keylight.html and keying_with_keylight/view.html, basic_keying.html, screen_color.html):
- Picking `screenColor` "creates the screen matte... It also sets the Screen Balance and despills the foreground." `screenBalance` sets the balance point for the key; `despillBias` "adjusts... to remove any remaining spill", best picked from hair and skin tones, and is disabled while `gangBiases` is on (then the Alpha Bias colour is used).
- `show` (View, default Final Result) options: Intermediate Result "renders the original source image with the Screen Matte generated in this Keylight node"; Final Result "creates a premultiplied RGBA foreground that can be composited later", with `unPreMultiply` (default on) as an "Unpremultiply Result" checkbox; Composite "renders the foreground composited over the background using all mattes, spill and color corrections". Screen Matte and Status are for judging.
- `screenReplaceMethod` / `screenReplaceColour` describe how colour is restored where alpha was processed after despill.
Not documented: whether Intermediate Result's colour carries any despill, whether Final Result's colour is the despilled colour you want, and which mode suits a separate despill branch. Do not assume either. Do not force Final Result.
To build the branch: view the candidate `show` modes on the actual plate (RGB only, edge and hair zoomed, single channels), pick the one whose colour is despilled the way the shot needs, and note the `unPreMultiply` state it gives. Handle the retained alpha separately: Copy the final assembled alpha onto the chosen colour or onto the retained RGB, then match premultiplication.

## Verify
View the RGB only, at edges and in hair, over bright and dark backgrounds and on the screen channel alone.
- Good: no screen-coloured fringe, skin and hair keep their colour, legitimately coloured clothing is not neutralised.
- Failure: grey or dark rims (premultiplication mismatch; or alpha processed after despill, shown as green Status pixels, use Screen Replace), hollow or desaturated hair, green or blue clothing neutralised (despill is not region-selective).
Compare with the input where no spill exists: unaffected areas should be unchanged.

## Ask the user when
- You cannot tell from the views which `show` mode gives the colour the user wants, or they named a specific mode.
- Despilled colour trades against legitimate colour in the subject and the choice is artistic.
- It is unclear whether the downstream expects premultiplied or straight colour.
Ask with the available question tool and wait; do not invent the mode.

## Pitfalls
- Premultiplying twice or despilling before the alpha is final causes dark or bright edges (fundamentals/keying-conventions).
- Simple despill removes screen colour everywhere and darkens spill areas; a brightness compensation may be needed (Brinkmann 2e ch.13).

## Sources
- Keylight: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/keylight.html ; comp_environment/keying_with_keylight/view.html, color_replacement.html, screen_color.html.
- Brinkmann 2e ch.13 "Spill Suppression". Studio policy: studio-conventions.
