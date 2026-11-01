---
id: "nodes/ibkgizmo"
kind: "node"
title: "IBKGizmo"
category: "keying"
summary: "Pulls a key using a clean plate input rather than a single colour picker; output is premultiplied with alpha."
aliases: ["IBKGizmoV3", "IBK", "image based keyer", "ibk key"]
tags: ["key", "ibk", "clean plate", "premultiplied"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/channels-data"]
related: ["nodes/ibkcolour", "nodes/merge", "nodes/keylight", "nodes/channelmerge", "nodes/copy"]
nodes: ["IBKGizmo"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# IBKGizmo

## Purpose
Source-documented: IBKGizmo keys using a clean-screen reference, helpful on uneven screens, and its output is premultiplied with alpha (not a finished comp). Menu entry "IBKGizmo" creates script class `IBKGizmoV3` (gizmo `IBKGizmoV3.gizmo`, two internal IBK ops plus a Switch). Studio policy: use it mainly for detailed edge alpha.

## Inputs
- `fg` (input 0): the screen plate.
- `c` (input 1): IBKColour output or a location clean plate. Keep it connected in reference-based mode; not needed when screen type is pick.
- `bg` (input 2): optional replacement background used for fine edge detail. Studio policy: leave it unconnected.

## Controls
Source-verified; defaults are starting points, not blind changes.
- `st` (screen type): C-blue (default), C-green, pick. `colour` (default 0,0,1) is used only with pick.
- `red_weight`, `blue_green_weight` (default 0.5 each): matte hardness in red / blue-green areas. Lower a weight when the edge looks discoloured because the matte is too strong. If one weight fixes one edge but breaks another, split several IBKGizmos with Keymix (docs).
- `lm_enable` (luminance match), `level` (screen range, default 1), `luma` (luminance level, default 0), `ll_enable` (UI label "enable", default disabled): luminance match captures transparent foreground brighter than the screen. Lowering screen range reduces screen-area noise but too far eats foreground blacks. `ll_enable` activates the luminance level control: `luma` adjustments have no effect until `ll_enable` is checked. Docs: luma is usually effective only in a small number of cases and generally needs no adjustment, so enable it only if the shot calls for it. Change one at a time and compare.
- `autolevels` with `yellow`, `cyan`, `magenta` keep boxes: pre-key correction for hard edges on saturated foreground. Best as a separate node; weights then behave unexpectedly.
- `ss` (screen subtraction): removes backing from the RGB; off premultiplies the original fg by the matte.
- `ublu`, `ubcr` (use bkg luminance / chroma): bg-driven edge brightness/colour on the RGB output; they require bg. They act on RGB, not the studio alpha-only path.
Leave unspecified controls at defaults. There are no RGB despill controls here.

## Workflow
Studio policy:
1. Run IBKColour (or a real clean plate) into `c`; connect fg; leave bg empty.
2. Take only the alpha: this alpha is the detail-edge component. Its body may be soft, grey or have holes; that is acceptable at this stage. Keep the area outside the subject as black as possible without losing detailed edges, or background noise propagates through ChannelMerge: Grade this alpha only, before combining, with slight black crush if needed; never touch RGB or require an opaque core here.
3. Build a separate opaque core alpha (see fundamentals/keying-conventions and topics/combine-keys): contract it with FilterErode positive then Blur of similar size; 5-10 px is an HD example/artist preference, not a limit, and higher resolution may need more, set by edge quality and how far the core must contract. Combine core and edge by union/max with nodes/channelmerge, Copy the final alpha to the retained RGB, then despill and premultiply as the next Merge expects.
4. Judge the result visually, tune weights and, only if the shot needs it, `ll_enable` plus `luma`; repeat. Screenshots and back-and-forth refinement are normal.

## Verify
Final combined alpha must have a solid core with no holes and intact hair/motion-blur edges, checked over the actual background and against the original screen. Component IBK edges with body holes are acceptable; the final matte is not. Verify the clean plate against the original outside the subject. Runtime verified: false.

## Pitfalls
- Premultiplied output is not a finished comp; do not Merge it as-is over a background without checking.
- Clean plate quality limits the key.
- Crushing alpha with Grade black is for suppressing background noise on the edge matte: slight, alpha only, never a broad hard clip that eats hair, motion blur or soft edges.
- Use `ChannelMerge` union/max for core + edge, not multiply (multiply only for regional-mask intersection).
- Keymix splits remain an explicit option (Foundry page); default studio route takes only alpha.

## Sources
- Foundry Nuke documentation: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/ibkgizmo.html (installed copy: Documentation/html/content/reference_guide/keyer_nodes/ibkgizmo.html; plugins/IBKGizmoV3.gizmo)
- Studio policy: studio-conventions (teacher-supplied production conventions; project preferences, not universal Nuke facts).
