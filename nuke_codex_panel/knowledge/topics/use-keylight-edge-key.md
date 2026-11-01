---
id: "topics/use-keylight-edge-key"
kind: "topic"
title: "Keylight as the edge key"
category: "keying"
summary: "A Keylight kept soft for hair and motion-blur edges: which controls preserve gradation, the Screen Matte zone to judge, good and failed results, and when to ask."
aliases: ["keylight edge", "keylight hair key", "soft edge matte"]
tags: ["purpose:keylight:edge-key", "review:alpha", "keylight", "edge", "matte", "keying", "treatment", "control:show", "control:screenColor", "control:screenClipMin", "control:screenClipMax", "control:screenClipRollback", "control:preBlur", "control:alphaBias", "control:screenBalance", "control:screenReplaceMethod", "control:screenReplaceColour"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/keying-conventions"]
related: ["nodes/keylight", "topics/use-keylight-core-key", "topics/use-keylight-single-key", "topics/combine-keys", "topics/use-ibkgizmo-matte"]
nodes: ["Keylight", "ChannelMerge"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# Keylight as the edge key

## Applicability
Use when a Keylight supplies the fine gradation at hair, fuzzy cloth and motion blur, to be unioned with an opaque core key (topics/combine-keys). Its body may be partly transparent; the core covers it. Pull it from the same original or cleaned RGB as the core.

## Workflow
1. `screenColor` sampled near the edge zone, comparing shades; Foundry notes different samples can give quite different edges.
2. Keep the matte gradation: leave `screenClipMin`/`screenClipMax` near their defaults; if you did clip, `screenClipRollback` restores lost edge detail.
3. Grainy or video footage: a slight `preBlur` softens the image the key is generated from; keep it small. Key a denoised copy only if the shot requires it (topics/chroma-keying), then Copy the alpha to the retained RGB.
4. Fringe of the wrong colour or the subject going transparent where it is close to the screen hue: `alphaBias` sampled on that foreground area, `screenBalance` changes.
5. `screenReplaceMethod` and `screenReplaceColour` only matter if you also use this node's RGB; with alpha-only use they do not affect the matte.
Output: take the alpha; View = Screen Matte to judge.

## Verify
Zoom into hair and motion-blurred edges at 1:1 and look at the alpha, then over the real background.
- Good: continuous soft gradation, hair strands present, motion blur transitions smooth, no screen-coloured halo after despill, background clean.
- Failure: hard stair-stepped edge or lost hair (reduce clip, increase rollback, check preBlur); edge transparency creeping into the body is fine if the core covers it; a noisy background fringe (small alpha-only Grade crush before combining, topics/use-grade-alpha).

## Ask the user when
- Hair detail appears missing from the plate itself (grain or compression) and the only options trade quality (denoise, different keyer).
- Different edge regions need conflicting settings.
- No documented control plausibly improves the edge defect you see.
Ask with the available question tool and wait; first adjustments and judging them are normal work.

## Pitfalls
- Never blur the edge matte to hide a bad extraction (Brinkmann 2e ch.15); redo the extraction instead.
- Combine with the core by ChannelMerge union/max, not multiply.
- Dilate (shrink/grow) on this key damages edges (Foundry).

## Sources
- Keylight: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/keylight.html ; guide pages screen_processing, preblur, screen_color under comp_environment/keying_with_keylight/.
- Studio policy: studio-conventions; Brinkmann 2e ch.15.
