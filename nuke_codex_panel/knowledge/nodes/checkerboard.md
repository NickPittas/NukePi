---
id: "nodes/checkerboard"
kind: "node"
title: "CheckerBoard2"
category: "image-io"
summary: "Native generator for checkerboard test images or placeholder textures with controllable box size, four colours and guide lines."
aliases: ["CheckerBoard", "checker", "test pattern", "checkerboard texture"]
tags: ["generator", "pattern", "texture", "placeholder"]
requires: ["fundamentals/coordinates", "fundamentals/channels-data"]
related: ["nodes/constant", "nodes/reformat"]
nodes: ["CheckerBoard2", "CheckerBoard"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1"]
---
# CheckerBoard2

## Purpose
Source-documented: a checkerboard image usable as a placeholder texture or background. Use this node (class CheckerBoard2 in 17.1 where installed) rather than rebuilding a checker pattern with an Expression-based stand-in.

## Inputs
No image input is documented; it has its own format control.

## Controls
Documented knobs: format -> `format`; size -> `boxsize` (default 64); `color0`-`color3` (four box colours, color 0 starts at 0,0 then alternates); line color -> `linecolor`; line width -> `linewidth`; centerline color -> `centerlinecolor`; centerline width -> `centerlinewidth`. The doc notes proxy mode may round boxes to the nearest pixel. Keep an existing legacy CheckerBoard node unless an upgrade is requested; if the required knobs are uncertain, inspect the node at runtime.

## Verify
View at full resolution, confirm box size, colours, format and bounding box; test stretching or projection with the pattern to see distortion. Runtime verified: false; availability, knobs and defaults may differ in the installed build.

## Pitfalls
Conditional practice: because of proxy rounding, evaluate pixel-accuracy at full resolution. If the pattern is only needed as a flat tone, use Constant. Static evidence for CheckerBoard2 being the 17.1 generation: the installed official reference page documents format, boxsize and color0-color3, and three Foundry toolsets shipped with 17.1 (paths relative to the install root: `plugins/caravr/ToolSets/CaraVR/Facebook_Surround_Depth_To_Points2_1.nk`, `Google_Jump_Depth_To_Points2_1.nk`, `Nokia_OZO_Depth_To_Points2_1.nk`) contain a `CheckerBoard2` node. This is installed-distribution evidence, not runtime observation; confirm with node.Class() in the running Nuke.

## Sources
- Foundry Nuke documentation: https://learn.foundry.com/nuke/17.1/content/reference_guide/image_nodes/checkerboard.html
- Installed Nuke 17.1 distribution, relative to the install root: `Documentation/html/content/reference_guide/image_nodes/checkerboard.html` and the CaraVR ToolSets above (static evidence).
