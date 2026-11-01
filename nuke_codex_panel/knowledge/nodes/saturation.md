---
id: "nodes/saturation"
kind: "node"
title: "Saturation"
category: "color"
summary: "Scales colour intensity of all hues together; 1 is unchanged, 0 is grayscale. Not hue-selective."
aliases: ["Saturation node", "desaturate", "colour intensity"]
tags: ["saturation", "color", "grade"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/color-spaces"]
related: ["nodes/grade", "nodes/colorcorrect", "topics/use-saturation-rgb", "topics/use-saturation-spill-map"]
nodes: ["Saturation"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1"]
---
# Saturation

## Purpose
Source-documented: corrects an image's saturation without limiting the change to any range of hues. For a range of hues (for example screen spill) Foundry points to HueCorrect instead.

## Inputs
Unnamed image input and optional mask (the change is limited to non-black mask areas).

## Controls
Documented knobs: `channels` (default all); `saturation` (1 = no change, 0 = grayscale); mask controls with `invert` and `fringe`; (un)premult by (`unpremult`, default none); `mix` (1). Use purpose guidance (`topics/use-saturation-rgb`) before grading colour.

## Verify
Compare against the input in the Viewer and on a vectorscope or pixel sample. Runtime verified: false; availability, knobs and defaults may differ in the installed build.

## Pitfalls
Default `channels` is all, so restrict it to rgb when alpha must stay untouched. Premultiplied input: use unpremult by the alpha or an Unpremult/Premult pair.

## Sources
- Foundry Nuke documentation: https://learn.foundry.com/nuke/17.1/content/reference_guide/color_nodes/saturation.html
