---
id: "nodes/expression"
kind: "node"
title: "Expression"
category: "color"
summary: "Applies a per-channel C-like expression to pixel values; Foundry ships an Expression-based green and blue despill example."
aliases: ["Expression node", "channel expression", "despill expression"]
tags: ["expression", "despill", "spill", "math"]
requires: ["fundamentals/channels-data", "fundamentals/node-selection"]
related: ["nodes/grade", "nodes/channelmerge", "nodes/copy", "topics/use-spill-map"]
nodes: ["Expression"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1"]
---
# Expression

## Purpose
Source-documented: applies mathematical formulas to channel values with C-like syntax; channels are named (r, g, b, a), 32-bit float maths. Use it for colour maths such as despill. Do not use it to imitate a native node (shapes, checkerboards) (fundamentals/node-selection).

## Inputs
Unnamed image input and optional mask.

## Controls
One expression field per channel (scripting `expr0` to `expr3` for the four channels; Foundry's example script sets `expr1` for green and `expr2` for blue), with `temp_name0..` / `temp_expr0..` for reusable sub-expressions. Confirm names with a live inspect.

## Verify
View each channel on its own and compare with the input where spill is absent: untouched areas must be identical. Runtime verified: false.

## Pitfalls
Foundry states a blank expression is the same as zero; after setting one channel's expression, view every channel and confirm the others still match the input. Never write a spill result into the retained alpha.

## Sources
- Foundry Nuke documentation: https://learn.foundry.com/nuke/17.1/content/reference_guide/color_nodes/expression.html ; despill example: https://learn.foundry.com/nuke/17.1/content/example_scripts/despill_script.html
