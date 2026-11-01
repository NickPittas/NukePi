---
id: "topics/use-ibkcolour-cleanplate"
kind: "topic"
title: "IBKColour as the clean plate"
category: "keying"
summary: "IBKColour used to build the clean-screen RGB for IBKGizmo c: which control removes which defect, the RGB image to judge, good and failed results, and when to ask."
aliases: ["ibk clean plate", "ibkcolour clean plate", "clean screen plate"]
tags: ["purpose:ibkcolour:cleanplate", "review:rgb", "ibk", "clean plate", "keying", "treatment", "control:screen_type", "control:Size", "control:off", "control:mult", "control:erode", "control:multi"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/channels-data"]
related: ["nodes/ibkcolour", "nodes/ibkgizmo", "topics/use-ibkgizmo-matte", "topics/chroma-keying"]
nodes: ["IBKColor", "IBKColour", "IBKGizmo"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# IBKColour as the clean plate

## Applicability
Use when IBKColour (class IBKColourV3) produces the screen-only image that feeds IBKGizmo `c`. Its output is an RGB picture, not a matte: judge the RGB, never its alpha. Full control list and defaults: get_node_reference(node="IBKColourV3", section="controls"); do not reload it unless a value is in doubt.

## Workflow
Each control is chosen by the defect it removes, in the documented top-to-bottom order. A control that does not address a visible defect stays at its default.
1. `screen_type`: tells the node which colour is the screen. Wrong value and every later control chases noise. Set it first.
2. `Size`: how far screen colour expands into the subject area. Raise it when subject-sized remnants still show; too large flattens genuine screen variation.
3. `off` (darks, adds to the grade): lowering the screen channel's darks separates black from the screen colour. Use when dark, black or dirty-coloured areas remain where the subject was. Judge by channel: g for green screens, b for blue.
4. `mult` (lights, multiplies): per channel. Docs examples: a light red artefact is addressed by raising lights.r; a dark green artefact by raising darks.g. Examples only, read the artefact's colour in the image.
5. `erode`: raise while foreground edge traces remain in the output.
6. `multi` (patch black): strength of black patching, applied after darks, lights and erode. It is a strength, not a pass count.
After each change view the IBKColour output (RGB, not alpha) and decide whether that defect improved; a setter readback shows the knob changed, not that the plate improved.

## Verify
View the IBKColour output next to the original plate.
- Good: only screen colour where the subject was, smoothly blended into the real screen; no subject hair, skin or clothing colour; no black holes; outside the subject the screen matches the original.
- Failure: subject colour remains (try Size, erode, then the channel's darks or lights); black holes (patch black, darks); screen outside the subject drifted (studio checkpoint: mask the generated patch into the original RGB with a subject-area matte, then feed that to IBKGizmo `c`).
A real location clean plate is more accurate when one exists.

## Ask the user when
- A named defect persists after trying the documented control for it and you see no step that would plausibly improve the image.
- You cannot tell which channel an artefact belongs to.
- Outside-subject drift needs the masked patch and no subject-area matte exists.
Ask with the available question tool and wait for the answer; a first imperfect adjustment is not a reason to ask.

## Pitfalls
- Pre-render the clean plate to a float format such as .exr; colour-lossy formats can break the key (Foundry).
- Over-raised erode or patch black removes real screen variation.
- Do not connect IBKGizmo `bg` as part of this node's job (studio policy).
- Hidden `filt` and `level` have no UI label; leave them.

## Sources
- IBKColor: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/ibkcolor.html ; installed plugins/IBKColourV3.gizmo (control wiring).
- Studio policy: studio-conventions (outside-subject comparison, masked patch).
