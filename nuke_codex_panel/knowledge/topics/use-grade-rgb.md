---
id: "topics/use-grade-rgb"
kind: "topic"
title: "Grade on RGB (colour and tonal match)"
category: "color"
summary: "Grade applied to colour channels: what blackpoint, whitepoint, lift, gain, multiply, offset and gamma each change, the premultiplication rule, what to view, failures, and when to ask."
aliases: ["grade rgb", "grade colour", "match plates grade", "grade foreground to background"]
tags: ["purpose:grade:rgb", "review:rgb", "grade", "color", "levels", "treatment", "control:channels", "control:blackpoint", "control:whitepoint", "control:black", "control:white", "control:multiply", "control:add", "control:gamma", "control:black_clamp", "control:white_clamp"]
requires: ["fundamentals/color-spaces", "fundamentals/alpha-premultiplication"]
related: ["nodes/grade", "topics/use-grade-alpha", "topics/use-saturation-rgb", "nodes/colorcorrect"]
nodes: ["Grade", "Unpremult", "Premult"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# Grade on RGB (colour and tonal match)

## Applicability
Use when Grade changes colour (`channels` = rgb, the default): tonal range, black and white levels, or matching a foreground to a background plate. For a matte, use topics/use-grade-alpha; Grade does not need to touch alpha for a colour correction.

## Workflow
Pick the control by what is wrong in the viewed colour:
- `blackpoint` / `whitepoint`: the input values that become 0 and 1. Sample the darkest or lightest pixels (sample the input with Alt while viewing the output).
- `lift` (`black`) / `gain` (`white`): the output values the black and white points map to; matching one clip's range to another is blackpoint/whitepoint from the first, lift/gain from the second.
- `multiply`: scales the result and keeps the black point. `offset` (`add`): adds a constant, lifting everything including black.
- `gamma`: midtones lighter or darker.
- `black_clamp` (on) / `white_clamp` (off): clipping of the output; leave unless a value outside 0 to 1 is a problem.
Change one control for one defect, then compare. Linear versus display-referred input changes how gamma and offset look (fundamentals/color-spaces). Premultiplied input: unpremult before, premult after (or use `unpremult` by the alpha if the live node has it); unpremultiplied input needs neither.

## Verify
View the RGB and a scope or pixel samples of reference areas (neutral grey, skin, black and white references), against the reference plate.
- Good: the compared areas land where the reference sits; no crushed blacks or clipped highlights you did not intend; edges of a keyed element keep no dark or bright fringe.
- Failure: fringe on keyed edges after a grade (the RGB was premultiplied and not unpremulted), clipped negative values (black clamp), mismatch that one control cannot fix (different colour cast: ask before stacking).

## Ask the user when
- Which reference or white point is correct is a creative judgement.
- The mismatch is colour cast versus saturation versus contrast and you cannot tell which control is responsible from the image.
- No documented control plausibly improves the viewed defect.
Ask with the available question tool and wait.

## Pitfalls
- UI labels and script names differ: lift is `black`, gain is `white`, offset is `add`.
- Do not grade RGB to fix an alpha problem or the reverse.
- No numeric value here is correct in advance; the picture decides.

## Sources
- Grade: https://learn.foundry.com/nuke/17.1/content/reference_guide/color_nodes/grade.html
- Premultiplication: fundamentals/alpha-premultiplication.
