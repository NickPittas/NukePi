---
id: "topics/use-keylight-core-key"
kind: "topic"
title: "Keylight as the core (body) key"
category: "keying"
summary: "A Keylight pulled hard for a solid opaque body: which controls firm and shrink the matte, the Screen Matte to judge, good and failed results, and when to ask."
aliases: ["keylight core", "keylight body key", "hard core matte"]
tags: ["purpose:keylight:core-key", "review:alpha", "keylight", "core", "matte", "keying", "treatment", "control:show", "control:screenColor", "control:screenClipMin", "control:screenClipMax", "control:screenGrowShrink", "control:screenSoftness", "control:screenDespotBlack", "control:screenDespotWhite", "control:sourceAlphaHandling"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/keying-conventions"]
related: ["nodes/keylight", "topics/use-keylight-edge-key", "topics/use-keylight-single-key", "topics/combine-keys", "nodes/channelmerge"]
nodes: ["Keylight", "ChannelMerge", "FilterErode", "Blur"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# Keylight as the core (body) key

## Applicability
Use when Keylight supplies the solid inside of the subject that a softer edge key (IBK or an edge Keylight) will be combined with. Only the final combined matte must be opaque; this core matte is allowed to be hard and to lose hair. Core versus edge assembly and erode/blur numbers: topics/combine-keys. Studio policy: the core is a hard black-and-white matte (studio-conventions).

## Workflow
1. Pick `screenColor` as usual (topics/use-keylight-single-key), then process the Screen Matte:
- `screenClipMax` (Clip White) down and `screenClipMin` (Clip Black) up make the matte harsher; Foundry's two-stage description is a harsh clipped matte, then soften and erode it.
- `screenGrowShrink` (Dilate) less than zero shrinks the alpha at sub-pixel level; use it to pull the core away from the edge, not to key more.
- `screenSoftness` blurs a harsh matte meant for an inside matte.
- `screenDespotBlack` removes isolated black specks in the white body; `screenDespotWhite` removes isolated white specks in the background.
2. Output choice: View = Screen Matte to judge the alpha. To feed another keyer, View = Intermediate Result (original source image plus this node's screen matte) and set the next Keylight's `sourceAlphaHandling` to Add To Inside Mask. To use the matte as an alpha extractor, take only its alpha and keep the retained RGB (studio policy).
3. If the core is combined with an edge key, shrink further with FilterErode then Blur or soften as topics/combine-keys describes; sizes follow the picture, not a fixed number.

## Verify
View the alpha only (View = Screen Matte, then the alpha channel).
- Good: body solid white with no holes, background solid black, edge transition well inside the real silhouette.
- Failure: grey or holes inside the subject (firm with Clip White, InM, or Despot Black); core touching the edge or background clinging to it (shrink or soften more); ringed or stair-stepped edge (reduce clipping, apply Clip Rollback only where an edge key is not covering).

## Ask the user when
- Parts of the subject share the screen's hue (so firming the body eats real colour) and a holdout or roto choice is needed.
- The body needs per-region treatment and the regions are not obvious.
- You cannot name a documented control that would improve the viewed defect.
Ask with the available question tool and wait.

## Pitfalls
- Aggressive Clip Black/White creates hard edges (Foundry), acceptable here only because an edge key will cover them; do not ship this matte alone.
- Dilate/erode on the key itself produces poor results (Foundry); shrink with the combine step when possible.
- Never blur the final edge matte (Brinkmann 2e ch.15); softening belongs to the core component.

## Sources
- Keylight: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/keylight.html ; guide pages screen_processing, view, inside_outside_masks under comp_environment/keying_with_keylight/.
- Studio policy: studio-conventions. Brinkmann 2e ch.15 (final matte edge).
