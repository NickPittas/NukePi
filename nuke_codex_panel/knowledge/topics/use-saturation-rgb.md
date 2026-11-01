---
id: "topics/use-saturation-rgb"
kind: "topic"
title: "Saturation on RGB"
category: "color"
summary: "Saturation changes colour intensity of all hues equally; it is not a spill map and not hue-selective. What it does, what to view, failures, and when to ask."
aliases: ["saturation rgb", "desaturate", "saturation not spill"]
tags: ["purpose:saturation:rgb", "review:rgb", "saturation", "color", "treatment", "control:channels", "control:saturation", "control:mix", "control:unpremult"]
requires: ["fundamentals/color-spaces", "fundamentals/alpha-premultiplication"]
related: ["nodes/saturation", "topics/use-grade-rgb", "topics/use-spill-map", "topics/use-saturation-spill-map", "topics/use-keylight-despill-output"]
nodes: ["Saturation", "HueCorrect"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "brinkmann-2e"]
---
# Saturation on RGB

## Applicability
Use when the whole image or a masked region needs more or less colour intensity. Foundry: use Saturation when no hue range needs limiting; for a range of hues, for example screen spill, use HueCorrect. Saturation is not a despill and it does not build a spill map.

## Workflow
- `saturation` (default 1): 1 leaves the image, 0 gives grayscale, above 1 intensifies. It scales every hue together.
- `channels` defaults to all; set rgb so alpha is not altered.
- `mix` blends back to the input; a mask limits the region; `fringe` limits the effect to the mask edge.
- Premultiplied input: set `unpremult` by the alpha, or Unpremult before and Premult after, so the result simulates grading before premultiplication.
Change saturation for an observed colour-intensity difference only. Viewing at the node output against the input shows the effect; saturation is a creative colour decision in a match, so judge it against the reference plate.

## Verify
- Good: the colour intensity matches the reference; skin and key colours stay plausible; edges show no new fringe.
- Failure: desaturating a spill region also greys legitimate colours and the subject's real colour (Brinkmann 2e ch.13 warns spill suppression cannot tell spill from real colour); alpha changed because `channels` was all; premultiplied edges darkened.

## Ask the user when
- The reference for the target look is unknown.
- A hue-specific problem such as green or blue spill is the real defect: ask whether a spill treatment is wanted instead (topics/use-spill-map) rather than inventing one from saturation.
Ask with the available question tool and wait.

## Pitfalls
- Desaturating a spill area is not a spill map and is not an accepted despill substitute.
- The default `channels` is all.

## Sources
- Saturation: https://learn.foundry.com/nuke/17.1/content/reference_guide/color_nodes/saturation.html ; HueCorrect: https://learn.foundry.com/nuke/17.1/content/reference_guide/color_nodes/huecorrect.html
- Brinkmann 2e ch.13 "Spill Suppression".
