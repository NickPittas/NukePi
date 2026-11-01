---
id: "topics/use-grade-alpha"
kind: "topic"
title: "Grade on alpha (matte shaping)"
category: "keying"
summary: "Grade restricted to the alpha channel to crush background noise or firm a matte: which controls change which alpha values, the alpha to view, failures, and when to ask."
aliases: ["grade alpha", "crush alpha", "matte grade", "alpha black crush"]
tags: ["purpose:grade:alpha", "review:alpha", "grade", "alpha", "matte", "treatment", "control:channels", "control:blackpoint", "control:whitepoint", "control:multiply", "control:add", "control:gamma", "control:black_clamp", "control:white_clamp"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/channels-data"]
related: ["nodes/grade", "topics/use-grade-rgb", "topics/use-ibkgizmo-matte", "topics/combine-keys", "fundamentals/keying-conventions"]
nodes: ["Grade", "ChannelMerge", "Copy"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions", "brinkmann-2e"]
---
# Grade on alpha (matte shaping)

## Applicability
Use when Grade's `channels` is set to the alpha channel only, to shape a matte before it is combined: typically a slight black crush on an IBK edge alpha so background noise does not propagate through the union (studio policy). The RGB is not touched; premultiplied RGB tied to the old alpha is no longer consistent after this, so keep the retained RGB separate and Copy the final alpha onto it later (fundamentals/keying-conventions).

## Workflow
Change the alpha only as far as the viewed alpha asks:
- `blackpoint` raised a little: alpha at or below it becomes 0, clearing low-level background noise; this removes edge detail if pushed.
- `whitepoint` lowered: alpha at or above it becomes 1, firming a body; hardens edges.
- `gamma`: reshapes mid alpha (hair) without moving 0 and 1.
- `multiply`, `offset` (`add`): scale or shift the whole alpha; offset also lifts 0 away from black.
- `black_clamp` (on) stops negatives; `white_clamp` (off) leaves values above 1: clamp when a union or Copy needs a 0..1 matte.
A mask can limit the grade to a region.

## Verify
View the alpha channel of the graded node, then compare with the ungraded alpha at hair and motion blur at 1:1, and over the real background.
- Good: outside the subject black (sample it), edge gradation and hair still present, no stepping.
- Failure: hair or motion blur vanishes or turns binary (blackpoint too high or a broad clip: back off; Brinkmann warns against hard-clipping the final edge), background noise remains (clean plate or key issue, not only Grade), alpha above 1 reaching a union.
The only valid check is the image of the alpha; the readback of a setter proves nothing about quality.

## Ask the user when
- Noise removal and edge detail trade directly and the preference is artistic.
- Only an aggressive crush clears the background, which suggests the upstream key needs a different treatment.
Ask with the available question tool and wait.

## Pitfalls
- Never touch RGB in this grade, and do not require an opaque body from the edge component.
- A broad hard clip eats hair and soft edges; keep it slight and alpha only.
- No number is portable between shots.

## Sources
- Grade: https://learn.foundry.com/nuke/17.1/content/reference_guide/color_nodes/grade.html
- Studio policy: studio-conventions (IBK edge alpha crush). Brinkmann 2e ch.15 (no blurred or crushed final edge).
