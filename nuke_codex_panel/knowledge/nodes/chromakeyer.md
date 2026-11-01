---
id: "nodes/chromakeyer"
kind: "node"
title: "ChromaKeyer"
category: "keying"
summary: "GPU-capable colour-difference keyer with screen colour, matte controls, despill and replace modes; one Source input."
aliases: ["ChromaKeyer node", "chroma keyer"]
tags: ["key", "chroma", "despill", "matte"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/channels-data"]
related: ["nodes/keylight", "topics/chroma-keying", "topics/combine-keys"]
nodes: ["ChromaKeyer"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1"]
---
# ChromaKeyer

## Purpose
Source-documented: keys a blue or green screen from a single Source input. Picking `screen color` creates the initial matte and also despills; matte and despill controls refine each. Use purpose guidance (`topics/use-chromakeyer-key`) for how to run it.

## Inputs
Source only (the foreground to key). There is no bg, inside or outside mask input.

## Controls
Documented knobs (scripting names): `view` (default final result; intermediate result for multipass), `_screenColor`, `_screenGain` (1), `_screenBalance` (0.5), `_chromaGain` (0), `_whitePoint` (1), `_blackPoint` (0), `_alphaBias`, `_insideMask` (ignore; source alpha for multipass), `_overrideDespillBias` and `despillBias`, `_replace` (ignore), `_replaceColor`, `_replaceAmount` (1), `_replaceAlphaDiff`, `_preMultiply` (enabled), plus GPU controls. Several scripting names start with an underscore; confirm with a live inspect before setting.

## Verify
View the alpha channel (R or Luminance display) for the matte and the RGB for despill. Runtime verified: false; availability, knobs and defaults may differ in the installed build.

## Pitfalls
`premultiply` can be too aggressive on hair (Foundry). Picking more colours does not accumulate; use extra ChromaKeyer nodes with `inside mask` = source alpha.

## Sources
- Foundry Nuke documentation: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/chromakeyer.html
