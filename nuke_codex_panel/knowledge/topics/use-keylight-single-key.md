---
id: "topics/use-keylight-single-key"
kind: "topic"
title: "Keylight as a single key"
category: "keying"
summary: "One Keylight pulling the whole key: how Screen Color, Gain, Balance, Biases and clip controls change the matte, the View modes to judge with, good and failed results, and when to ask."
aliases: ["keylight single key", "one keylight", "basic keylight"]
tags: ["purpose:keylight:single-key", "review:alpha", "review:rgb", "keylight", "keying", "chroma", "treatment", "control:show", "control:unPreMultiply", "control:screenColor", "control:screenGain", "control:screenBalance", "control:alphaBias", "control:despillBias", "control:gangBiases", "control:screenClipMin", "control:screenClipMax", "control:screenClipRollback", "control:screenGrowShrink", "control:insideComponent", "control:outsideComponent"]
requires: ["fundamentals/alpha-premultiplication", "fundamentals/color-spaces"]
related: ["nodes/keylight", "topics/use-keylight-core-key", "topics/use-keylight-edge-key", "topics/use-keylight-despill-output", "topics/chroma-keying"]
nodes: ["Keylight"]
version: "Nuke 17.1 documentation; static reference, not runtime verified. Check installed node generation and licence."
source_ids: ["foundry-17.1", "studio-conventions"]
---
# Keylight as a single key

## Applicability
Use when one Keylight is expected to give the whole usable matte (even screen, simple subject). If the body and edge need different treatment, or regions need different keys, use the core and edge purposes instead. Keylight's script class may be an OFX name; confirm with node.Class(). Knob list: get_node_reference(node="Keylight", section="controls").

## Workflow
1. `screenColor` first: sample the average of a screen area from the Source (Alt samples the source while you view something else). It creates the screen matte, sets `screenBalance` if still unset, and despills. It is one colour, not an accumulating set; different shades give different keys.
2. Read the result in View = Screen Matte (alpha without inside/outside masks), then Status, then Final Result or Composite.
3. Change a control only for the defect you see:
- Screen background still showing or key too weak: `screenGain` up keys more; try `screenBalance` near 0.95 (blue), 0.5 (green), or 0.05/0.5/0.95 (Foundry hints, not rules).
- Subject partly transparent because the screen is not pure: sample `alphaBias` on the affected foreground area.
- Leftover transparency inside the subject or background grey: `screenClipMax` (Clip White) firms the body, `screenClipMin` (Clip Black) clears the background; too far gives hard edges, `screenClipRollback` restores edge detail.
- Remaining spill: `despillBias` on skin or hair (it is disabled while `gangBiases` is on).
- Known garbage or holdout areas: OutM and InM masks with `outsideComponent` / `insideComponent`, instead of over-processing the matte.

## Verify
- Good: Status is black background, white body, gray only where fg and bg blend (gray does not mean a bad key); no green or blue Status pixels you did not expect.
- Green Status pixels mean alpha was processed after despill; fix with the Screen Replace controls. Blue pixels mean the inside mask altered despill.
- Failure: holes in the subject, transparent hair, hard cut edges, matte noise in the screen, residual spill colour; check over a bright and a dark background.

## Ask the user when
- Screen Color samples from different areas give materially different keys and the image does not say which is right.
- The screen is too uneven or the subject too similar to the screen for any documented control to help (consider multipass or IBK; that is a structural choice).
- You cannot name a documented control that would plausibly improve the defect you see.
Ask with the available question tool and wait. A first imperfect adjustment is not a reason to ask.

## Pitfalls
- Result colour of Final Result is premultiplied unless `unPreMultiply` is enabled; match the next node.
- `screenGrowShrink` (Dilate) erosion usually makes a poor key (Foundry).
- Despill from Keylight is applied to its own RGB; studio policy extracts alpha and despills the retained RGB after Copy (topics/use-keylight-despill-output).

## Sources
- Keylight: https://learn.foundry.com/nuke/17.1/content/reference_guide/keyer_nodes/keylight.html ; guide pages basic_keying, screen_color, view, advanced_keying, screen_processing under comp_environment/keying_with_keylight/.
- Studio policy: studio-conventions.
