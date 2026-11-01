---
id: "topics/use-ibkgizmo-matte"
kind: "topic"
title: "IBKGizmo as the detailed-edge matte"
category: "keying"
summary: "IBKGizmo used for the edge alpha with a clean plate on c: what each control changes, the alpha to judge, good and failed results, and when to ask."
aliases: ["ibk edge matte", "ibkgizmo alpha", "ibk detail edge"]
tags: ["purpose:ibkgizmo:matte", "review:alpha", "ibk", "matte", "edge", "keying", "treatment", "control:st", "control:colour", "control:red_weight", "control:blue_green_weight", "control:level", "control:lm_enable", "control:luma", "control:ll_enable", "control:ss", "control:ublu", "control:ubcr"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/channels-data"]
related: ["nodes/ibkgizmo", "nodes/ibkcolour", "topics/use-ibkcolour-cleanplate", "topics/combine-keys", "topics/use-grade-alpha"]
nodes: ["IBKGizmo", "IBKColour", "Grade", "ChannelMerge"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# IBKGizmo as the detailed-edge matte

## Applicability
Use when IBKGizmo (class IBKGizmoV3) keys with a clean plate on `c` and its alpha supplies edge detail (hair, motion blur). Studio policy takes only that alpha; the output RGB is premultiplied and is not the finished foreground. Full controls: get_node_reference(node="IBKGizmoV3", section="controls").

## Workflow
Connect fg and `c` (IBKColour output or a real clean plate); leave `bg` empty. Then change only what the viewed alpha asks for:
- `st` (screen type) must match the screen; `pick` needs `colour` and no `c`.
- `red_weight`, `blue_green_weight` (0.5 each): matte hardness in red and in blue-green regions. Lower the one that governs a discoloured or too-strong edge. If one weight fixes one edge but breaks another, Foundry documents splitting several IBKGizmos combined with Keymix.
- `level` (screen range): lowering it reduces noise in the screen area, too far eats foreground blacks.
- `lm_enable` luminance match captures transparent foreground brighter than the screen. `luma` has no effect until `ll_enable` is checked, and Foundry says it is rarely needed.
- `ss` screen subtraction and `ublu`/`ubcr` change RGB, not the studio alpha-only path.
The body of this alpha may be soft or grey; keep the area outside the subject black. If background noise reaches the edge, a slight alpha-only Grade black crush before combining is the studio method (topics/use-grade-alpha).

## Verify
View the alpha channel of the IBKGizmo output with `c` connected, then over the real background.
- Good: hair and motion-blur detail intact, outside the subject near black, no screen-coloured halo at the edge. Body holes are acceptable here; they are not in the final combined matte.
- Failure: noisy or grey background (clean plate quality, `level`, or the alpha crush); edges too hard or discoloured (weights); detail missing (weights, luminance match).

## Ask the user when
- The key needs different weights in different regions (splitting gizmos is a structural choice).
- The clean plate itself looks wrong: fix that first, not the gizmo.
- No documented control plausibly improves a viewed defect.
Ask with the available question tool and wait. Tuning a weight a first time and judging it is normal, not a reason to ask.

## Pitfalls
- Never Merge the premultiplied output over a background as if finished.
- Combine core and edge alphas by ChannelMerge union/max, not multiply (topics/combine-keys).
- The weights are starting points (0.5); no value is correct without the picture.

## Sources
- IBKGizmo: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/ibkgizmo.html ; installed plugins/IBKGizmoV3.gizmo.
- Studio policy: studio-conventions (alpha-only edge, outside-subject black).
