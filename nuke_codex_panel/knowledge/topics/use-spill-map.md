---
id: "topics/use-spill-map"
kind: "topic"
title: "Spill map construction and use"
category: "keying"
summary: "A spill map as the per-pixel screen-colour excess removed by a documented despill expression: how to build it, what it controls, what to view, failures, and when to ask. Desaturation is not a spill map."
aliases: ["spill map", "spill matte", "despill expression", "spill amount", "spill suppression map"]
tags: ["purpose:expression:spill-map", "spill", "despill", "expression", "keying", "treatment", "control:expr0", "control:expr1", "control:expr2", "control:expr3"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/channels-data", "fundamentals/keying-conventions"]
related: ["nodes/expression", "topics/use-saturation-spill-map", "topics/use-saturation-rgb", "topics/use-keylight-despill-output", "topics/chroma-keying", "nodes/copy"]
nodes: ["Expression", "Merge", "Shuffle", "HueCorrect"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "brinkmann-2e", "studio-conventions"]
---
# Spill map construction and use

## Applicability
Use when the work needs to know where and how much screen colour was removed from the foreground: to confirm a despill, to limit it to the edge zone, or to feed a replacement. Foundry documents despill expressions and HueCorrect; it does not define a "spill map" node or recipe. The construction below is derived from the documented expression and is a method to verify on the shot, not a Foundry procedure. Prefer a native despill (a keyer's despill, HueCorrect) when it already gives the despilled copy; the Expression is Foundry's documented fallback. If the user asks for a Saturation-based map, that is a different purpose: `saturation:spill-map` (topics/use-saturation-spill-map). Desaturating the image is not a spill map.

## Workflow
1. Despilled copy of the foreground (a branch; the retained RGB and alpha stay intact). Foundry's documented Expression for green screen: `g>(r+b)/2?(r+b)/2:g` on the green channel; for blue screen `b>(r+g)/2?(r+g)/2:b` on the blue channel. Brinkmann's simplest form replaces the screen channel with the smaller of it and another channel where it exceeds it. HueCorrect (suppression curves) is Foundry's hue-limited alternative.
2. Spill map = the screen channel before despill minus after despill (zero where nothing was removed), kept as a single channel in its own layer or as a grey image via Shuffle, never in the retained alpha.
3. Uses, each chosen by the problem:
- Verify: view the map; bright regions are where the despill acted. Spill outside the subject, or on legitimately coloured parts, shows up as unexpected brightness.
- Limit: use the map or a core/edge mask as the mask of the despill branch so edge zones get stronger treatment than the core (studio: keep despill minimal and edge-masked).
- Replace: add colour back where spill was removed, if the despilled area looks dark or grey; Brinkmann notes that despill darkens and may need a compensating brightness lift, and Primatte documents complement, solid colour and defocused-background replacement as options.
Build it after the final alpha is Copied onto the retained RGB, and match premultiplication (unpremult, adjust, premult).

## Verify
View the map as an image, plus before and after of the RGB over bright and dark backgrounds, and on the screen channel alone.
- Good: the map is bright only in real spill zones (edges, hair, reflective areas), near zero in the core and in legitimately coloured clothing; despilled RGB has no coloured halo and no grey rim.
- Failure: map active inside blue or green clothing (despill is not region-selective), a grey or dark rim (brightness not compensated, or premultiplication mismatch), grain increased in the replaced channel (Brinkmann, especially greenscreen).

## Ask the user when
- The map's purpose is unclear (verify, limit or replace).
- The spill problem is on elements the user may want to keep coloured.
- A map built this way does not match what you see and no documented alternative (HueCorrect, keyer despill bias) clearly fits.
Ask with the available question tool and wait.

## Pitfalls
- No node or number is the spill map by default; do not label saturation or hue shifts as one.
- Keep the map and the despill out of the retained alpha and original RGB.
- Foundry's expression ignores brightness; judge the result by eye.

## Sources
- Expression: https://learn.foundry.com/nuke/17.1/content/reference_guide/color_nodes/expression.html ; despill example script: https://learn.foundry.com/nuke/17.1/content/example_scripts/despill_script.html ; Primatte spill_removal_method1 (documented despill expressions) and replacing_spill pages under comp_environment/keying_with_primatte/ ; HueCorrect reference.
- Brinkmann 2e ch.6 (color difference method), ch.13 "Spill Suppression", ch.15.
- Studio policy: studio-conventions (minimal edge-masked despill).
