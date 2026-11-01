---
id: "nodes/ibkcolour"
kind: "node"
title: "IBKColor"
category: "keying"
summary: "Creates the clean-plate image for IBKGizmo from a blue or green screen."
aliases: ["IBKColour", "IBKColor", "IBKColourV3", "ibk clean plate"]
tags: ["key", "ibk", "clean plate", "chroma"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/channels-data"]
related: ["nodes/ibkgizmo", "nodes/keylight"]
nodes: ["IBKColor", "IBKColour"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# IBKColor

## Purpose
Source-documented: IBKColor builds the clean-screen image that IBKGizmo reads on its c input. The Keyer-menu entry "IBKColour" creates script class `IBKColourV3` (gizmo `IBKColourV3.gizmo`); the docs page is titled IBKColor. Do not use the legacy toolbar commands `IBKColour`/`IBK2Gizmo` unless asked. Create with class `IBKColourV3` and confirm with node.Class().

## Inputs
Input 1: the blue- or green-screen plate. Its output feeds IBKGizmo `c` (the required clean-screen reference in reference-based mode). A real location clean plate may replace it.

## Controls
Source-verified from the gizmo script and the official page; work top to bottom, since the gizmo help calls that the only real workflow.
- `screen_type` (default blue): green or blue.
- `Size` (default 10, 0-100): size of the colour expansion.
- `off` (label darks, RGB, default 0, -1..1): wired as Grade add. Lowering the screen-channel darks separates black from the screen colour (g for green screen, b for blue).
- `mult` (label lights, RGB, default 1, 0..2): wired as Grade multiply. Docs examples: light red artefact -> raise lights.r; dark green artefact -> raise darks.g. Examples, not fixed recipes; judge each channel from the image.
- `erode` (default 0, 0-5): raise while foreground edge colour traces remain in the output; positive values expand screen colour over the foreground remnants.
- `multi` (label patch black, default 0, 0-5): patches remaining black; use once darks/lights are set. Strength scales with Size and multi.
- Hidden `filt` and `level` have no UI label; leave them untouched.
Leave other controls at their defaults. No doc or gizmo statement describes repeated patch passes or automatic preservation of the screen outside the subject.

## Workflow
1. Connect the plate to input 1; set screen_type and Size.
2. Clean the fringe top to bottom: darks, then lights, then erode, then patch black. Judge after each change by viewing the output.
3. Goal (teacher policy): the clean screen shows only screen colour where the subject was, and the area outside the subject stays like the original screen.
4. Check by comparing IBKColour output against the original plate before and after, especially outside the subject patch. If the outside drifted, mask the generated patch into the original RGB (Keymix on RGB, with a roto/alpha limited to the subject area), then feed that result to IBKGizmo c.
5. Connect to IBKGizmo c; judge the key edges there (nodes/ibkgizmo). Iterate visually; quality may take several rounds.

## Verify
View original and IBKColour output side by side: no foreground detail remains, no black holes, outside-subject screen matches the original. Then judge the alpha downstream. Runtime verified: false; availability and defaults may differ in the installed build.

## Pitfalls
- Pre-render the clean plate to .exr (float); formats that lose colour information can break the key, per the docs.
- A real clean plate is more accurate when one exists.
- Raising erode or multi too far removes real screen variation; compare against the original.
- Do not connect the optional IBKGizmo bg input as part of this node's job (studio policy).

## Sources
- Foundry Nuke documentation: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/ibkcolor.html (installed copy: Documentation/html/content/reference_guide/keyer_nodes/ibkcolor.html; plugins/IBKColourV3.gizmo)
- Studio policy: studio-conventions (teacher-supplied clean-plate procedure and outside-subject comparison; project preferences, not Foundry rules).
