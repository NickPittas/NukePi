"""Ask-before-further-changes gate: which bridge requests change the scene, and what the model is told.

The state lives in :class:`bridge.control.BridgeControl` (armed by the bridge when a complete composite has
been delivered to the model, lifted by the person's answer or message). This module is only the policy:
no state, no clock, no counter.
"""

from __future__ import annotations

# The answer that ends the person's wish for more work, matched case-insensitively on the start of the
# answer text. The model is told to offer exactly this option.
STOP_ANSWER = "stop here"
ERROR_CODE = "ask_before_further_changes"

# nuke_action actions that only read, or only steer the Viewer used to look at the result.
READ_ACTIONS = frozenset({"inspect", "sample", "render", "view", "select"})
# Actions that change the scene unless they target the Viewer node itself (channel/display knobs).
VIEWER_CLASS = "Viewer"
VIEWER_STEERING = frozenset({"set", "connect"})

_READ_ONLY = (
    "Still allowed: inspect, sample, render and view actions, nuke_workflow, get_nuke_context, screenshots, "
    "documentation and knowledge lookups, and ask_user"
)


def is_scene_change(method: str, params: dict, node_class) -> bool:
    """True when this bridge request could change the scene.

    ``node_class(name)`` returns the class of a node or None. ``execute_python`` can always change it. A
    ``nuke_action`` changes it unless its action only reads (``READ_ACTIONS``) or only sets knobs/inputs on
    the Viewer node. Every other bridge method is read-only, and an unknown action name is left to the
    action's own error (it changes nothing).
    """
    if method == "execute_python":
        return True
    if method != "execute_action":
        return False
    from ..tools.guided_actions import NativeActions

    action = params.get("action")
    if not isinstance(action, str) or action not in NativeActions.ALLOWED or action in READ_ACTIONS:
        return False
    if action in VIEWER_STEERING:
        node = params.get("node")
        if isinstance(node, str) and node_class(node) == VIEWER_CLASS:
            return False
    return True


def armed_notice(composite: dict) -> str:
    """Appended to the tool result whose image just armed the gate."""
    return (
        "[ask_before_further_changes] The complete composite (%s, a foreground over a background through %s) has now "
        "been delivered to you. Before you change the scene again, call ask_user: offer each specific remaining "
        "issue you actually see as its own option (what and where: frame and region) plus the option \"Stop here\". "
        "If you see no remaining issue, offer only \"Stop here\" with a one-line summary of the result. Until the "
        "person answers, every request that could change the scene (nuke_action create/set/connect/swap/layout/"
        "project/animate/shape*/delete/internal_python, and execute_python) is refused with nothing executed. %s. "
        "Use them to collect the issues. Work only on what the person picks; looking again before you change anything "
        "does not re-ask, but after your next scene change and a delivered review of the complete composite you must "
        "ask again. If they pick \"Stop here\", end your turn with a short summary."
        % (composite.get("node"), composite.get("merge"), _READ_ONLY)
    )


def review_notice(network: dict) -> str:
    """Appended to the tool result whose review first found the complete composite network (stage "review")."""
    return (
        "[ask_before_further_changes] A complete composite exists (%s, a foreground over a background through %s): "
        "every node you built feeds it. Before you change the scene again, render %s in RGB (nuke_action render, "
        "Viewer channels rgba) and review it, then call ask_user with your specific remaining issues as options "
        "plus the option \"Stop here\". Until then every request that could change the scene (nuke_action create/set/"
        "connect/swap/layout/project/animate/shape*/delete/internal_python, and execute_python) is refused with "
        "nothing executed. %s."
        % (network.get("node"), network.get("merge"), network.get("node"), _READ_ONLY)
    )


def refusal(gate: dict) -> dict:
    """The bridge response for a scene change refused while the gate is armed."""
    composite = gate["composite"]
    if gate["stopped"]:
        error = (
            "%s: nothing was executed. The person chose \"Stop here\". Do not change the scene. End your turn now "
            "with a short summary of the composite and what you consider unfinished; a new message from the person "
            "lifts this." % ERROR_CODE
        )
    elif gate["stage"] == "review":
        error = (
            "%s: nothing was executed. A complete composite exists (%s). Render %s in RGB and review it, then ask "
            "the user with your remaining issues (one option per specific issue, what and where) plus \"Stop "
            "here\". %s." % (ERROR_CODE, composite.get("node"), composite.get("node"), _READ_ONLY)
        )
    else:
        error = (
            "%s: nothing was executed. The complete composite (%s) was already delivered to you and the person has "
            "not yet been asked whether to go on. Call ask_user now: one option per specific remaining issue you see "
            "(what and where) plus the option \"Stop here\"; then act only on the answer. %s."
            % (ERROR_CODE, composite.get("node"), _READ_ONLY)
        )
    return {
        "success": False,
        "graph_changed": False,
        "error_code": ERROR_CODE,
        "error": error,
        "question_gate": {"composite": composite.get("node"), "stage": gate["stage"], "stopped": gate["stopped"]},
    }
