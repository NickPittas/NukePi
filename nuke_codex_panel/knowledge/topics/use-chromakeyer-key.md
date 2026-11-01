---
id: "topics/use-chromakeyer-key"
kind: "topic"
title: "ChromaKeyer as a key"
category: "keying"
summary: "ChromaKeyer matte and despill controls: what gain, white/black point and replace modes change, what to view, good and failed results, and when to ask."
aliases: ["chromakeyer key", "chromakeyer despill", "chroma keyer multipass"]
tags: ["purpose:chromakeyer:key", "review:alpha", "review:rgb", "chromakeyer", "keying", "chroma", "treatment", "control:_view", "control:_screenColor", "control:_screenGain", "control:_screenBalance", "control:_chromaGain", "control:_whitePoint", "control:_blackPoint", "control:_alphaBias", "control:_insideMask", "control:_overrideDespillBias", "control:despillBias", "control:_replace", "control:_replaceColor", "control:_replaceAmount", "control:_replaceAlphaDiff", "control:_preMultiply"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/channels-data"]
related: ["nodes/chromakeyer", "nodes/keylight", "topics/chroma-keying", "topics/combine-keys"]
nodes: ["ChromaKeyer"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# ChromaKeyer as a key

## Applicability
Use when ChromaKeyer is the chosen screen keyer (GPU-capable, single Source input, no inside or outside mask). Studio policy may use it as a core key alongside an IBK edge. Knob names, several with a leading underscore, come from get_node_reference(node="ChromaKeyer", section="controls"); inspect the live node before setting.

## Workflow
1. `screen color`: average of a rectangle on the screen. Picking creates the initial matte and despills; repeated picks do not accumulate. To key more, pick other shades in additional ChromaKeyer nodes, each set to `inside mask` = source alpha except the first (view = intermediate result upstream).
2. `screen gain` (1): more screen colour removed, so it keys more; too high erodes the subject and tints edges. `screen balance` (0.5): try 0.05, 0.5, 0.95 if the key is poor.
3. Matte, judged on the alpha channel:
- `chroma gain` (0): fills transparent areas in the foreground but hardens edges.
- `white point` (1): alpha above it becomes 1 (firms the body). `black point` (0): alpha below it becomes 0 (cleans background). These two trade foreground loss against background retention.
- `alpha bias`: sample the part of the foreground that is wrongly transparent.
4. Despill: `despill bias` (enable `Use custom despill bias`, sample skin or hair); `replace mode` ignore (default), edge hard/linear/soft color restore colour where alpha changed, with `replace color`, `replace amount`, and `add-in matte fix` for areas changed by the points.
5. `premultiply` (on): output is the matte multiplied into the foreground; Foundry warns it can be too aggressive on hair.

## Verify
View the alpha channel in R or Luminance display.
- Good: solid body, clean background, soft edge where hair is, despilled RGB without tinted rim.
- Failure: hair eaten (premultiply, high white point, high chroma gain), grey body (chroma gain, white point), tinted edges after matte changes (replace mode), noisy screen (black point, extra pass).

## Ask the user when
- A single pass cannot cover an uneven screen and you would need several passes whose regions are unclear.
- Hair loss comes from `premultiply` versus background noise and the trade-off is the user's.
- No documented control plausibly helps the viewed defect.
Ask with the available question tool and wait.

## Pitfalls
- Take its alpha only when assembling with other keys (fundamentals/keying-conventions); do not assume its RGB is the final foreground.
- Untouched `inside mask` ignore means upstream passes are ignored.

## Sources
- ChromaKeyer: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/chromakeyer.html ; comp_environment/keying_with_chromakeyer/ (picking_screencolor, improving_mattes, despill_controls, multipass_keying).
- Studio policy: studio-conventions.
