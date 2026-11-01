---
id: "topics/use-saturation-spill-map"
kind: "topic"
title: "Saturation inside a spill-map build"
category: "keying"
summary: "What the Saturation node can contribute to a spill map (a colour-intensity comparison, not hue-selective), what its output means and does not mean, and which definition the user must supply before building one."
aliases: ["saturation spill map", "desaturate to find spill", "spill map with saturation"]
tags: ["purpose:saturation:spill-map", "saturation", "spill", "despill", "keying", "treatment", "control:channels", "control:saturation", "control:mix", "control:maskChannelInput", "control:invert_mask", "control:fringe", "control:unpremult"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/channels-data", "fundamentals/keying-conventions"]
related: ["nodes/saturation", "topics/use-saturation-rgb", "topics/use-spill-map", "topics/use-keylight-despill-output", "nodes/copy"]
nodes: ["Saturation", "HueCorrect", "Merge", "Shuffle"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "brinkmann-2e", "studio-conventions"]
---
# Saturation inside a spill-map build

## Applicability
Use when the request is to build or use a spill map with the native Saturation node rather than an Expression. Foundry documents no spill-map recipe. It documents Saturation as a control that scales colour intensity of every hue together (1 unchanged, 0 grayscale) and points to HueCorrect when a range of hues, such as screen spill, is the target. So a Saturation-based map is a derived technique that depends on the plate and on what is being compared; it is not a universal recipe and desaturating an image is not itself a spill map.

## Workflow
What the node offers for such a build, from its reference:
- `saturation` (1 = no change, 0 = grayscale): a copy at 0 keeps luminance and removes colour, so original minus desaturated copy isolates how much colour each pixel carries (all hues, not only spill).
- `channels` (default all): set rgb so alpha stays untouched; keep the retained RGB and alpha unchanged by building on a branch.
- `mix`: dissolve between input and the full change; a partial amount is a partial comparison.
- Mask (`maskChannelInput`, `invert_mask`) and `fringe` (only the mask edge) restrict where the change applies; a core or edge matte can confine the comparison to the edge zone.
- `unpremult` by the alpha for premultiplied input.
What the output means: a colour-intensity difference. In a screen-spill zone it will be high, but so is any saturated legitimate colour (clothing, lips, lights). To make it spill-specific it must be limited by hue or by a spill-free comparison (for example an original versus a despilled version, topics/use-spill-map), or by a region matte the user agrees to.

## Verify
View the resulting map as a single-channel image next to the plate.
- Good: the map is bright where you can see spill on the plate (edges, hair, reflective surfaces) and close to zero on the spill-free core.
- Failure: bright on legitimately coloured parts (map is measuring saturation, not spill); bright on the whole screen area; changes where alpha is retained.
A map that does not isolate spill needs a hue or region limit, not a different Saturation value.

## Ask the user when
Always before committing a Saturation-based map, unless the user already defined it:
- Which comparison defines the map: original versus desaturated, original versus a despilled version, or something else.
- Whether legitimately saturated areas must be excluded, and how (hue limit with HueCorrect, matte, or roto).
- Which plate or element it is for, and what the map will drive (verify, limit a despill, replace colour).
Ask with the available question tool and wait; do not invent a definition.

## Pitfalls
- Saturation is not hue-selective; do not present its output as a spill map unless the comparison above makes it one.
- Do not write the map into the retained alpha or original RGB.
- No Saturation value is correct in advance; 0 and 1 are the documented endpoints, not a recipe.

## Sources
- Saturation: https://learn.foundry.com/nuke/17.1/content/reference_guide/color_nodes/saturation.html ; HueCorrect: https://learn.foundry.com/nuke/17.1/content/reference_guide/color_nodes/huecorrect.html
- Brinkmann 2e ch.13 "Spill Suppression" (spill suppression cannot tell spill from real colour).
- Derived construction: stated as such; verify on the shot.
