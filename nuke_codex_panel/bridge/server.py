"""Authenticated localhost JSONL bridge running on Nuke's Qt main thread."""

from __future__ import annotations

from collections import OrderedDict
import hmac
import json
import os
from pathlib import Path
import secrets
import traceback

from PySide6 import QtCore, QtNetwork

from ..capture import capture_metadata, capture_target
from ..capture.widgets import normalize_viewer_navigation
from ..process_ownership import pid_running
from ..runtime_paths import RuntimePathError, private_runtime_directory
from ..tools import PythonExecutor, diff_snapshots, get_context, graph_snapshot
from ..tools.guided import GuidedNuke
from . import api_recovery
from . import question_gate
from . import control as control_module
from .control import ControlRefused
from .inspection import InspectionGate, normalize_client_id

# Evidence kind for a captured image delivered to the workflow.
RENDER = "render"
ROOT_KEY = "<root>"
MAX_PENDING_EVIDENCE = 256
# python_executor reports at most this many modified nodes; a full list cannot prove the rest.
MODIFIED_NODES_CAP = 50
READ_ONLY_ACTIONS = frozenset({"render", "view", "sample", "inspect"})


class NukeBridgeServer(QtCore.QObject):
    """Serve Nuke operations without letting worker threads touch Nuke."""

    status_changed = QtCore.Signal(str)
    # Every control/operation event of this bridge (see bridge.control): operation_started,
    # operation_finished, operation_refused, paused, resumed, revoked.
    operation_event = QtCore.Signal(object)
    # One dict per image the MCP sidecar really attached to a tool result: delivery_id, path, sha256,
    # bytes, tool, client_id, control_id, control_epoch, received_ns, metadata (see _images_delivered).
    image_delivered = QtCore.Signal(object)

    def __init__(self, approval_callback, parent=None, documentation_info=None):
        super().__init__(parent)
        self.approval_callback = approval_callback
        self.server = QtNetwork.QTcpServer(self)
        self.server.newConnection.connect(self._accept_connections)
        self.token = secrets.token_urlsafe(32)
        self.executor = PythonExecutor()
        self.gate = InspectionGate(graph_snapshot)
        self.guided = GuidedNuke()
        # Execution control; published under the discovery path by start() (get_control).
        self.control = control_module.BridgeControl()
        self.control.add_listener(self._on_control_event)
        # token -> (client_id, evidence) for captured images awaiting delivery confirmation.
        self._evidence_tokens: OrderedDict = OrderedDict()
        self.documentation_info = documentation_info or api_recovery.installed_documentation
        self.buffers = {}
        self._serving = False
        self.discovery_path = None

    def start(self) -> bool:
        if self.server.isListening():
            return True
        if not self.server.listen(QtNetwork.QHostAddress.SpecialAddress.LocalHost, 0):
            self.status_changed.emit("Nuke bridge failed: %s" % self.server.errorString())
            return False
        try:
            directory = private_runtime_directory()
        except (RuntimePathError, OSError) as exc:
            self.server.close()
            self.status_changed.emit("Nuke bridge failed: the runtime directory is unusable: %s" % exc)
            return False
        # Unique per instance: two panels in the same Nuke process share the
        # pid, and a shared filename made one panel's stop() delete the other's
        # discovery record, bricking the MCP sidecar for the surviving panel.
        self._prune_stale_sessions(directory)
        self.discovery_path = directory / (
            "session-%s-%s.json" % (os.getpid(), secrets.token_hex(4))
        )
        control_module.register(self.discovery_path, self.control)
        record = {
            "pid": os.getpid(),
            "host": "127.0.0.1",
            "port": self.server.serverPort(),
            "token": self.token,
        }
        temporary = self.discovery_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(record), encoding="utf-8")
        os.chmod(temporary, 0o600)
        temporary.replace(self.discovery_path)
        self.status_changed.emit("Nuke bridge ready on localhost")
        return True

    def _prune_stale_sessions(self, directory: Path):
        """Drop discovery records whose Nuke process is gone; keep ours alive."""
        for path in directory.glob("session-*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if pid_running(int(record.get("pid", 0))):
                    continue
            except Exception:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def stop(self):
        self.server.close()
        for socket in list(self.buffers):
            socket.disconnectFromHost()
        self.buffers.clear()
        self._evidence_tokens.clear()
        if self.discovery_path:
            control_module.unregister(self.discovery_path)
            try:
                self.discovery_path.unlink(missing_ok=True)
            except Exception:
                pass

    @staticmethod
    def _guided_key(client_id: str) -> str:
        """Guided workflow state belongs to the control (the chat session), not to one sidecar process.

        A sidecar retired by a manual intervention is replaced by one with a fresh client id; the
        workflow, its bindings and evidence digests carry over because they are keyed by control id.
        Unscoped clients (no control) are keyed by their own client id.
        """
        operation = control_module.current_operation()
        return operation.control_id if operation is not None and operation.control_id else client_id

    def _on_control_event(self, event: dict) -> None:
        """Control transitions: retired/revoked clients lose their pending deliveries and workflow state."""
        kind = event.get("event")
        if kind in ("retired", "revoked"):
            for client_id in event.get("clients") or ():
                self.gate.forget(client_id)
                for token in [key for key, entry in self._evidence_tokens.items() if entry[0] == client_id]:
                    del self._evidence_tokens[token]
        if kind == "revoked":
            # The session ended: its workflow state goes too. A mere intervention keeps it.
            self.guided.forget_client(event["control_id"])
        elif kind == "conversation_reset":
            # New chat on the same control: the old conversation's workflow, scope and evidence are not this one's.
            self.guided.forget_client(event["control_id"])
        self.operation_event.emit(event)

    def _accept_connections(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            self.buffers[socket] = b""
            socket.readyRead.connect(lambda current=socket: self._read_socket(current))
            socket.disconnected.connect(lambda current=socket: self._drop_socket(current))

    def _drop_socket(self, socket):
        self.buffers.pop(socket, None)
        socket.disconnectFromHost()
        socket.deleteLater()

    def _read_socket(self, socket):
        if socket not in self.buffers:
            # Dropped between queueing and delivery: the C++ object may
            # already be gone. Touching it raises RuntimeError and, inside
            # this slot, kills the bridge for every later request.
            return
        self.buffers[socket] += bytes(socket.readAll())
        self._pump()

    def _pump(self):
        """Serve complete requests strictly one at a time, in arrival order.

        Serving can run a nested Qt event loop (the approval dialog, a Viewer render's
        progress handling, user code). Without this guard a request from another
        connection would be handled mid-operation, so one client could mutate the
        graph while another is waiting on an approval or a render. A reentrant call
        only buffers; the outer loop serves the queued request afterwards.
        """
        if self._serving:
            return
        self._serving = True
        try:
            while True:
                queued = self._next_request()
                if queued is None:
                    return
                self._serve(*queued)
        finally:
            self._serving = False

    def _next_request(self):
        for socket in list(self.buffers):
            buffer = self.buffers[socket]
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if line.strip():
                    self.buffers[socket] = buffer
                    return socket, line
            self.buffers[socket] = buffer
        return None

    def _serve(self, socket, line):
        try:
            payload = json.dumps(self._handle_request(json.loads(line.decode("utf-8"))))
        except Exception as exc:
            payload = json.dumps({"success": False, "error": "%s: %s" % (type(exc).__name__, exc)})
        if socket not in self.buffers:
            return  # the client disconnected while its request was being served
        try:
            socket.write((payload + "\n").encode("utf-8"))
            socket.flush()
        except RuntimeError:
            self._drop_socket(socket)

    def request_local(self, request: dict) -> dict:
        """Serve one request from inside the Nuke process (same token, admission and control path as the socket)."""
        return self._handle_request(request)

    def _handle_request(self, request: dict) -> dict:
        if not hmac.compare_digest(str(request.get("token", "")), self.token):
            return {"success": False, "error": "Unauthorized Nuke bridge request"}
        method = request.get("method")
        params = request.get("params")
        if not isinstance(params, dict):
            params = {}
        client_id = normalize_client_id(request.get("client_id"))
        handlers = {
            "execute_python": lambda: self._execute_python(client_id, params),
            "execute_action": lambda: self._execute_action(client_id, params),
            "workflow": lambda: self._workflow(client_id, params),
            "get_context": lambda: self._get_context(client_id, params),
            "capture_screenshot": lambda: self._capture_screenshot_request(client_id, params),
            "confirm_delivery": lambda: self._confirm_delivery(client_id, params),
            "api_docs_begin": lambda: self._api_docs_begin(client_id, params),
            "images_delivered": lambda: self._images_delivered(
                client_id, params, request.get("control_epoch"), request.get("received_ns")
            ),
        }
        handler = handlers.get(method)
        if handler is None:
            return {"success": False, "error": "Unknown bridge method: %s" % method}
        detail = ""
        for key in ("action", "command", "op", "step", "type"):
            if isinstance(params.get(key), str):
                detail = params[key][:48]
                break
        # Nothing below runs, asks for approval, or touches the graph unless the control admits it:
        # this is where queued and batched requests of an interrupted run are turned away.
        try:
            operation = self.control.admit(
                request.get("control_id"),
                client_id,
                str(method),
                request.get("received_ns"),
                detail,
                request.get("control_epoch"),
            )
        except ControlRefused as refusal:
            return refusal.response()
        with operation:
            try:
                gated = self._question_gate_refusal(operation, str(method), params)
                changes = gated is None and question_gate.is_scene_change(str(method), params, self._node_class)
                response = gated if gated is not None else handler()
                if changes and response.get("graph_changed") is not False:
                    self.control.note_scene_change(operation.control_id)
            except ControlRefused as refusal:
                response = refusal.response()
            operation.finish(bool(response.get("success")), response.get("error_code"))
        return response

    def _question_gate_refusal(self, operation, method: str, params: dict) -> dict | None:
        """The refusal for a scene change while the ask-before-further-changes gate is armed, else None.

        Runs after control admission and before any approval dialog, graph access or code, so a refused
        request costs the person nothing and leaves the graph untouched.
        """
        gate = self.control.question_gate(operation.control_id)
        if gate is None:
            return None
        if not question_gate.is_scene_change(method, params, self._node_class):
            return None
        return question_gate.refusal(gate)

    def _node_class(self, name: str):
        """The class of a live node by name, or None."""
        return (self.guided.facts.node(name) or {}).get("class")

    @staticmethod
    def _attach_inspection(response: dict, note: str | None = None, changed=()) -> None:
        """Add ``inspection`` only when it carries real information: a note, or changes made by others."""
        status = {}
        if note:
            status["note"] = note
        if changed:
            status["changed_since_last_seen"] = list(changed)
        if status:
            response["inspection"] = status

    @staticmethod
    def _recheck() -> None:
        """Raise ControlRefused if the operation being served was paused/revoked while it waited (approval dialog, render)."""
        operation = control_module.current_operation()
        if operation is not None:
            operation.recheck()

    def _execute_python(self, client_id: str, params: dict) -> dict:
        code = str(params.get("code", ""))
        if not code.strip():
            return {"success": False, "error": "Python code is empty", "graph_changed": False}
        # Fingerprint first so edits made by the user or another client since the last
        # call advance the revision before the run is compared against it.
        observation = self.gate.observe()
        approved = self.approval_callback(code)
        # The dialog ran a nested event loop: a manual pause during it must win over the approval.
        self._recheck()
        if not approved:
            return {"success": False, "error": "Python execution denied by the user", "graph_changed": False}
        # Anything but a known-unchanged graph (changed, unknown, or the executor itself
        # failing) invalidates every client's evidence, the executing client's included.
        finished = False
        try:
            result = self.executor.execute(
                code,
                undo=bool(params.get("undo", True)),
                label=str(params.get("label", "Codex Python")),
                before=observation.snapshot,
            )
            finished = True
        finally:
            if not finished:
                self.gate.graph_may_have_changed()
                self.guided.invalidate(None, "python")
        if result.get("graph_changed") is not False:
            self.gate.graph_may_have_changed()
            self.guided.invalidate(None, "python")
        if result.get("graph_changed") is True:
            # Diagnostics only: raw Python's actual delta is not ownership of those nodes.
            self.guided.engine.record_python_delta(
                self._guided_key(client_id),
                result.get("added_nodes"),
                result.get("removed_nodes"),
                result.get("modified_nodes"),
            )
        result["graph_revision"] = self.gate.revision
        return result

    def _capture_for_action(self, client_id: str, captures: list, side_effects: set):
        """The ``capture_callback`` handed to GuidedNuke.action: synchronous, evidence-tracked, control-aware."""

        def capture(target: str, **options) -> dict:
            try:
                self._recheck()
            except ControlRefused as refusal:
                return refusal.response()
            try:
                response = self._capture_screenshot(client_id, {"target": target, **options})
            except Exception as exc:
                return {"success": False, "error": "%s: %s" % (type(exc).__name__, exc)}
            if not response.get("success"):
                return response
            # Rendering can touch the graph (Viewer state). Whatever it changed is a capture side
            # effect, reported as such, and the evidence belongs to the graph as it is afterwards.
            after = self.gate.observe()
            if after.revision != response.get("graph_revision"):
                side_effects.update(after.changed)
                response["graph_revision"] = after.revision
                response["capture_side_effects"] = list(after.changed)
                token = None
            else:
                token = response.pop("delivery_token", None)
            response.pop("delivery_token", None)
            if token is None:
                token = self.gate.issue_delivery(client_id, RENDER, after.revision)
            evidence_id = secrets.token_hex(8)
            response["evidence_id"] = evidence_id
            evidence = dict(response)
            self._evidence_tokens[token] = (client_id, evidence)
            while len(self._evidence_tokens) > MAX_PENDING_EVIDENCE:
                self._evidence_tokens.popitem(last=False)
            captures.append({"token": token, "path": response.get("path"), "evidence_id": evidence_id, "target": target})
            return dict(response)

        return capture

    @staticmethod
    def _node_names(values) -> set:
        if not isinstance(values, (list, tuple, set)):
            return set()
        return {ROOT_KEY if str(name) in ("root", ROOT_KEY) else str(name) for name in values}

    @staticmethod
    def _in_scope(name: str, declared: set) -> bool:
        """True for a declared node or a node inside one: the full name or one of its dot-separated
        ancestors (a group/gizmo containing it) is declared. A shared name prefix is not ancestry."""
        while True:
            if name in declared:
                return True
            name, dot, _ = name.rpartition(".")
            if not dot:
                return False

    def _execute_action(self, client_id: str, params: dict) -> dict:
        """One bounded nuke_action: GuidedNuke does the native work, this adds the bridge conventions."""
        description = self.guided.approval_text(params)
        if description is not None:
            approved = self.approval_callback(description)
            self._recheck()
            if not approved:
                return {"success": False, "error": "Action denied by the user", "graph_changed": False}
        # Fingerprint first so edits made since the last call advance the revision before the action sees it.
        before = self.gate.observe()
        captures: list = []
        side_effects: set = set()
        failure = None
        try:
            outcome = self.guided.action(
                self._guided_key(client_id),
                params,
                before.revision,
                self._capture_for_action(client_id, captures, side_effects),
            )
            if not isinstance(outcome, dict):
                raise TypeError("nuke_action produced %s, not a result object" % type(outcome).__name__)
        except Exception as exc:
            # Whatever the failed action already changed is real and is reported by the diff below.
            failure = "%s: %s" % (type(exc).__name__, exc)
            outcome = {"success": False, "error": failure, "traceback": traceback.format_exc()}
        after = self.gate.observe()
        meta = diff_snapshots(before.snapshot, after.snapshot)
        changed = list(meta["added_nodes"]) + list(meta["removed_nodes"]) + list(meta["modified_nodes"])
        declared = self._node_names(outcome.get("touched_nodes")) | side_effects
        verified = meta["graph_changed"] is not None and len(meta["modified_nodes"]) < MODIFIED_NODES_CAP
        outside = (
            sorted(name for name in changed if not self._in_scope(name, declared))
            if meta["graph_changed"] is not None
            else []
        )
        # A read-only action cannot edit nodes; existing nodes whose fingerprint moved while it evaluated the
        # graph (first evaluation of an OFX/Read node updates derived knobs) are reported as such. Added or
        # removed nodes are never excused, and every other action keeps full out-of-scope detection.
        action_name = params.get("action")
        evaluation = []
        if action_name in READ_ONLY_ACTIONS:
            evaluation = [name for name in outside if name in meta["modified_nodes"]]
            outside = [name for name in outside if name not in evaluation]
        response = {key: value for key, value in outcome.items() if key != "delivery_token"}
        success = bool(outcome.get("success")) and failure is None
        response["graph_changed"] = meta["graph_changed"]
        response["changes"] = {
            "added_nodes": meta["added_nodes"],
            "removed_nodes": meta["removed_nodes"],
            "modified_nodes": meta["modified_nodes"],
        }
        response["change_detection"] = meta["graph_change_detection"]
        response["node_errors"] = meta["node_errors"]
        if evaluation:
            response["evaluation_derived_updates"] = {
                "nodes": evaluation,
                "note": (
                    "%s only reads/evaluates; these existing nodes' knob values changed while it evaluated them "
                    "(e.g. first evaluation of an OFX or Read node). Reported, not an out-of-scope edit." % action_name
                ),
            }
        # The action may provisionally claim it changed the graph; only the before/after fingerprint decides.
        attempted = outcome.get("partial") is not None and not outcome.get("rolled_back")
        if not success and not outcome.get("rolled_back"):
            if meta["graph_changed"] is True:
                response["partial"] = (
                    "the action changed the graph before it failed; nothing was rolled back or replayed. "
                    "`changes` and the readback in this result (applied, knobs, inputs, connected) are the state "
                    "that exists now; touched_nodes names the node(s) it was working on"
                )
            elif attempted and meta["graph_changed"] is None:
                response["partial"] = (
                    "the action attempted a change before it failed, but the graph fingerprint failed, so whether "
                    "anything changed is UNKNOWN; nothing was rolled back or replayed. Treat only the readback in "
                    "this result (applied, knobs, inputs, connected) as observed; touched_nodes names the node(s) "
                    "it was working on"
                )
            elif attempted:
                response.pop("partial", None)  # fingerprint: nothing changed
        if outside:
            success = False
            response["outside_scope_changes"] = outside
            response["rolled_back"] = False
            message = (
                "outside_scope: this action also changed nodes it did not declare: %s. Those changes happened "
                "and were NOT rolled back; they are listed in outside_scope_changes and changes."
                % ", ".join(outside[:10])
            )
            if outcome.get("error"):
                message += " The action itself also reported: %s" % outcome["error"]
            response["error"] = message
            self.guided.invalidate(self._guided_key(client_id), "outside_scope")
        elif success and meta["node_errors"]:
            # The requested operation completed and is verified; the error state is a diagnostic of the
            # resulting image/channels (a missing input or channel, for example), not a failed operation.
            response["node_errors_note"] = (
                "the operation completed and its changes are recorded; these nodes report an error state "
                "(for example a missing input or channel) that affects their image: "
                + ", ".join(entry["node"] for entry in meta["node_errors"])
            )
        if not verified and meta["graph_changed"] is not None:
            response["scope_verified"] = False
        response["success"] = success
        response["graph_revision"] = after.revision
        if before.changed:
            response["changed_since_last_seen"] = list(before.changed)
        if captures:
            response["images"] = [
                {"path": entry["path"], "evidence_id": entry["evidence_id"], "target": entry["target"]}
                for entry in captures
            ]
            response["delivery_tokens"] = [entry["token"] for entry in captures]
        return response

    def _workflow(self, client_id: str, params: dict) -> dict:
        """One nuke_workflow call: read-only workflow state."""
        observation = self.gate.observe()
        try:
            outcome = self.guided.workflow(self._guided_key(client_id), params, observation.revision)
            if not isinstance(outcome, dict):
                raise TypeError("nuke_workflow produced %s, not a result object" % type(outcome).__name__)
        except Exception as exc:
            outcome = {
                "success": False,
                "error": "%s: %s" % (type(exc).__name__, exc),
                "traceback": traceback.format_exc(),
            }
        response = {key: value for key, value in outcome.items() if key != "delivery_token"}
        response["graph_changed"] = False
        response["graph_revision"] = observation.revision
        self._attach_inspection(response, None, observation.changed)
        return response

    def _get_context(self, client_id: str, params: dict) -> dict:
        include_nodes = bool(params.get("include_nodes", True))
        # Read first, fingerprint second, so the revision describes the graph state the
        # reader actually holds even if reading touches node state.
        context = get_context(include_nodes)
        observation = self.gate.observe()
        response = {"success": True, "context": context, "graph_revision": observation.revision}
        # Read-only, factual, fetched on demand: nothing here prompts the model or triggers a check.
        try:
            report = self.guided.engine.completion_report(self._guided_key(client_id))
        except Exception as exc:
            response["operation_report_error"] = "%s: %s" % (type(exc).__name__, exc)
        else:
            if report.get("nodes"):
                response["operation_report"] = report
        note = None
        if not include_nodes:
            note = "include_nodes=false: the node list was not read"
        elif not observation.certified:
            note = "the graph could not be fingerprinted; graph_revision cannot be compared with others"
        self._attach_inspection(response, note, observation.changed)
        return response

    @staticmethod
    def _capture_options(target: str, params: dict) -> dict:
        """Keyword options for capture_target, rejecting arguments the target cannot honor."""
        options = {}
        frame = params.get("frame")
        if frame is not None:
            if target != "viewer":
                raise ValueError("frame is only valid with target='viewer'")
            if isinstance(frame, bool) or not isinstance(frame, (int, float)) or int(frame) != frame:
                raise ValueError("frame must be an integer frame number, got %r" % (frame,))
            options["frame"] = int(frame)
        scope = params.get("scope")
        if scope is not None:
            if scope not in ("all", "visible"):
                raise ValueError("scope must be 'all' or 'visible', got %r" % (scope,))
            if target == "nodegraph":
                options["scope"] = scope
            elif scope != "all":
                raise ValueError("scope='visible' is only valid with target='nodegraph'")
        navigation = normalize_viewer_navigation(params.get("zoom"), params.get("center"), params.get("region"))
        if navigation is not None:
            if target != "viewer":
                raise ValueError("zoom, center and region are only valid with target='viewer'")
            options.update({key: params[key] for key in ("zoom", "center", "region") if params.get(key) is not None})
        return options

    def _capture_screenshot(self, client_id: str, params: dict) -> dict:
        target = str(params.get("target", "viewer"))
        try:
            options = self._capture_options(target, params)
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        before = self.gate.observe()
        path = capture_target(target, **options)
        metadata = capture_metadata(path)
        response = {"success": True, **metadata, "path": str(path), "graph_revision": before.revision}
        note = None
        changed = before.changed
        if target == "nodegraph":
            complete = (
                metadata.get("scope") == "all"
                and metadata.get("complete") is True
                and metadata.get("graph_group") == "root"
            )
            if not complete:
                note = "this nodegraph capture is not a complete all-scope root view"
            elif not before.certified:
                note = "the graph could not be fingerprinted; graph_revision cannot be compared with others"
            else:
                # Rendering the view can pump events; report it if the graph moved meanwhile.
                after = self.gate.observe()
                response["graph_revision"] = after.revision
                if not after.certified or after.revision != before.revision:
                    note = "the graph changed while the view was captured; capture it again"
                    changed += after.changed
        self._attach_inspection(response, note, changed)
        return response

    def _capture_screenshot_request(self, client_id: str, params: dict) -> dict:
        """A capture_nuke_screenshot call. A Viewer render joins the same evidence/delivery lifecycle as a
        nuke_action render: provisional until the sidecar confirms the image really reached the model.

        (nuke_action renders call ``_capture_screenshot`` through ``_capture_for_action``, which registers its
        own evidence; they never come through here, so nothing is registered twice.)
        """
        response = self._capture_screenshot(client_id, params)
        if not response.get("success") or str(params.get("target", "viewer")) != "viewer":
            return response
        # Rendering can touch the graph (Viewer state): the evidence belongs to the graph as it is afterwards.
        after = self.gate.observe()
        response["graph_revision"] = after.revision
        token = self.gate.issue_delivery(client_id, RENDER, after.revision)
        response["evidence_id"] = secrets.token_hex(8)
        self._evidence_tokens[token] = (client_id, dict(response))
        while len(self._evidence_tokens) > MAX_PENDING_EVIDENCE:
            self._evidence_tokens.popitem(last=False)
        response["delivery_token"] = token
        return response

    def _confirm_delivery(self, client_id: str, params: dict) -> dict:
        """The sidecar read every result (and image) behind these tokens and is handing them on."""
        tokens = params.get("tokens")
        if not isinstance(tokens, list) or not all(isinstance(token, str) for token in tokens):
            return {"success": False, "error": "confirm_delivery needs a list of delivery tokens"}
        recorded = []
        delivered = []
        failure = None
        notice = None
        composite = network = None
        for token in tokens:
            try:
                recorded.append(self.gate.confirm_delivery(client_id, token))
            except KeyError:
                failure = {
                    "success": False,
                    "error": "Unknown, repeated, or foreign delivery token; it was not recorded",
                    "recorded": recorded,
                }
                break
            entry = self._evidence_tokens.pop(token, None)
            if entry is not None and entry[0] == client_id:
                delivered.append(entry[1])
        if delivered:
            # The image reached the model; whether it still counts is the workflow's call, made
            # against the graph as it is now (an edit while the image was in flight stales it).
            current = self.gate.observe()
            for evidence in delivered:
                try:
                    record = self.guided.evidence_delivered(self._guided_key(client_id), evidence, current.revision)
                except Exception as exc:
                    failure = failure or {
                        "success": False,
                        "error": "Delivered image evidence could not be recorded by the workflow: %s: %s"
                        % (type(exc).__name__, exc),
                        "recorded": recorded,
                    }
                    continue
                if not isinstance(record, dict):
                    continue
                composite = composite or record.get("complete_composite")
                network = network or record.get("complete_network")
            # An RGB render of the complete composite asks; otherwise a review of any node of the complete network
            # first requires that composite render (the gate's "review" stage).
            if composite:
                notice = self._arm_question_gate(composite, "ask")
            elif network:
                notice = self._arm_question_gate(network, "review")
        if failure is not None:
            return failure
        response = {"success": True, "recorded": recorded, "graph_revision": self.gate.revision}
        if notice is not None:
            response["question_gate_notice"] = notice
        return response

    def _arm_question_gate(self, composite: dict, stage: str) -> str | None:
        """Arm or advance the gate for this control; the notice to show the model, or None.

        None when the control's harness cannot ask the person a question, or the gate is already at that stage.
        """
        operation = control_module.current_operation()
        if operation is None or not self.control.arm_question_gate(operation.control_id, composite, stage):
            return None
        return question_gate.armed_notice(composite) if stage == "ask" else question_gate.review_notice(composite)

    def _api_docs_begin(self, client_id: str, params: dict) -> dict:
        """Where the installed Nuke documentation lives; the sidecar reads it, never Nuke's GUI thread."""
        try:
            info = dict(self.documentation_info())
        except Exception as exc:
            return {
                "success": False,
                "error": "The installed Nuke documentation location is unavailable: %s: %s"
                % (type(exc).__name__, exc),
            }
        return {"success": True, **info}

    def _images_delivered(self, client_id: str, params: dict, control_epoch, received_ns) -> dict:
        """The sidecar attached these exact images to a tool result; hand each to the panel (one event each).

        Admitted by control like any request, so a stale or retired client never reaches here. Nothing
        is read or captured: the metadata is what the capture already recorded in this process.
        """
        items = params.get("images")
        if not isinstance(items, list):
            return {"success": False, "error": "images_delivered needs a list of images"}
        operation = control_module.current_operation()
        control_id = operation.control_id if operation is not None and operation.control_id else ""
        count = 0
        for item in items:
            if not (
                isinstance(item, dict)
                and isinstance(item.get("delivery_id"), str)
                and isinstance(item.get("path"), str)
                and isinstance(item.get("sha256"), str)
                and isinstance(item.get("bytes"), int)
                and not isinstance(item.get("bytes"), bool)
            ):
                continue
            try:
                metadata = dict(capture_metadata(Path(item["path"])) or {})
            except Exception:
                metadata = {}
            self.image_delivered.emit(
                {
                    "delivery_id": item["delivery_id"],
                    "path": item["path"],
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                    "tool": str(item.get("tool") or ""),
                    "client_id": client_id,
                    "control_id": control_id,
                    "control_epoch": control_epoch,
                    "received_ns": received_ns,
                    "metadata": metadata,
                }
            )
            count += 1
        return {"success": True, "count": count}
