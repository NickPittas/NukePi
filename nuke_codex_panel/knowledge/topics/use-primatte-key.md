---
id: "topics/use-primatte-key"
kind: "topic"
title: "Primatte as a sampled key"
category: "keying"
summary: "Primatte built by sampling: Auto-Compute, what each operation does to the matte and spill, output modes, the colour-space caveat, what to view, failures, and when to ask."
aliases: ["primatte key", "primatte sampling", "primatte auto compute"]
tags: ["purpose:primatte:key", "review:alpha", "review:rgb", "primatte", "keying", "sampling", "treatment", "control:algorithm", "control:mode", "control:graintype", "control:graintolerance"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/color-spaces"]
related: ["nodes/primatte", "topics/picker-keyers", "topics/chroma-keying", "topics/use-spill-map"]
nodes: ["Primatte", "Colorspace"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# Primatte as a sampled key

## Applicability
Use when Primatte is chosen for the screen. Every sample moves a colour-space polyhedron, so the result depends on which colours you sample and in what order. Scripted sampling: topics/picker-keyers; confirm the installed controls first.

## Workflow
1. Connect `fg` (the screen plate); `bg` is optional (needed for composite output and defocused-background spill replacement).
2. `Auto-Compute` first: it senses the screen colour, removes it and cleans some foreground and background noise. On an even, well-saturated screen it may only leave spill work. `algorithm`: Primatte (best, slowest), RT, RT+ (faster, weaker on less saturated screens, no complement spill).
3. `operation` (the sample mode) is chosen by the defect:
- Clean BG Noise: sampled pixels are 100% background (noisy white in the background goes black).
- Clean FG Noise: sampled pixels are 100% foreground (dark grey in the body goes white).
- Matte Sponge: stray transparent pixels. Restore Detail: lost hair or wisps. Make FG Trans.: deliberate foreground translucency.
- Spill Sponge: removes the screen colour component for the sampled colour region; Spill(-)/Spill(+): one increment of spill removed or returned for the colour region. One sample per colour region (skin, hair) affects all similar colours.
- Matte(-)/(+), Detail(-)/(+): thin or thicken matte and detail per colour region, one increment per click.
4. `degrain` type/tolerance average colours around a sample for grainy plates; keep tolerance low.
5. `Spill Process` replace with: no suppression, complement, solid colour, or defocused background.
6. `output mode`: composite; premultiplied (use with a Merge over); unpremultiplied (use with Merge matte); not premultiplied (original foreground plus the calculated matte); adjust lighting FG.

## Verify
View alpha first (no grey in the body, no noise in the screen), then RGB and composite.
- Good: solid white body, clean black screen, preserved hair or edge transitions, spill gone from colour regions without neutralising legitimate colours.
- Failure: grey in the body (Clean FG Noise or Matte Sponge on the grey), noise or tint left in the screen (Clean BG Noise), hair lost (Restore Detail / Detail(-)), wrong-coloured clothing after Spill Sponge (undo that sample with Spill(+)).
- Colour space: Primatte works in sRGB while Nuke is linear; Foundry says to add Colorspace conversions around Primatte before using its premultiplied or unpremultiplied outputs in a Merge pipeline.

## Ask the user when
- Samples disagree (a sample cleans one area and damages another) and you cannot see an operation that would reconcile them.
- Auto-Compute misidentifies the screen colour.
- Whether to take its alpha only or its RGB is not decided (studio default: alpha only).
Ask with the available question tool and wait.

## Pitfalls
- Primatte is a trademark with patent notes in the docs; no licence assumptions.
- Foundry documents unlimited undo while sampling in the UI; plan a way back for a bad scripted sample (for example Spill(+) after Spill(-)).
- Studio policy: take its alpha as one regional matte, assemble with ChannelMerge, Copy onto the retained RGB (fundamentals/keying-conventions).

## Sources
- Primatte: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/primatte.html ; comp_environment/keying_with_primatte/ (primatte_basic_operation, output_section, spill_process_section, spill_removal_method1).
- Studio policy: studio-conventions.
