"""Question card (the pinned ask_user dialog) and the end-of-run operation report view."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from .theme import set_variant


class QuestionCard(QtWidgets.QFrame):
    """One answerable question: its text, option buttons (select) or a hint to type (input), and Cancel.

    Cancel is the ordinary run stop, not a soft "decline": the whole run stops. The card never answers
    by itself and has no timer.
    """

    option_chosen = QtCore.Signal(int, str)  # (question token, exact option text)
    cancel_requested = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._token = 0
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        self._heading = QtWidgets.QLabel("The agent is asking you")
        self._heading.setObjectName("heading")
        layout.addWidget(self._heading)
        self._text = QtWidgets.QLabel()
        self._text.setWordWrap(True)
        self._text.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self._text.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(190)
        scroll.setWidget(self._text)
        layout.addWidget(scroll)
        self._options = QtWidgets.QVBoxLayout()
        self._options.setSpacing(4)
        layout.addLayout(self._options)
        self._hint = QtWidgets.QLabel()
        self._hint.setWordWrap(True)
        set_variant(self._hint, "status", "muted")
        layout.addWidget(self._hint)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        self._cancel = QtWidgets.QPushButton("Cancel (stops the run)")
        self._cancel.setProperty("variant", "danger")
        self._cancel.clicked.connect(self.cancel_requested)
        row.addWidget(self._cancel)
        layout.addLayout(row)
        self.setVisible(False)

    def show_question(self, state: dict):
        """Render ``PiRpcClient.question_changed`` payloads; inactive hides the card."""
        self._clear_options()
        if not state.get("active"):
            self.setVisible(False)
            return
        self._token = int(state["token"])
        answerable = bool(state.get("answerable"))
        self._text.setText(state.get("title") or "")
        if not answerable:
            self._hint.setText("Waiting for a running Nuke operation to finish before you can answer…")
        elif state.get("method") == "multi":
            self._hint.setText("Tick one or more options, then click Answer.")
        elif state.get("method") == "select":
            self._hint.setText("Choose one option.")
        elif (state.get("placeholder") or "").lower().startswith("optional"):
            self._hint.setText("Optional: type a comment and click Answer, or leave the message box empty and click Answer to skip.")
        else:
            self._hint.setText("Type your answer in the message box below and click Answer.")
        if state.get("method") == "select":
            for option in state.get("options") or []:
                button = QtWidgets.QPushButton(option)
                button.setToolTip(option)
                button.setEnabled(answerable)
                button.setStyleSheet("text-align: left;")
                button.clicked.connect(lambda _checked=False, value=option: self.option_chosen.emit(self._token, value))
                self._options.addWidget(button)
        if state.get("method") == "multi":
            self._add_multi(state.get("choices") or [], answerable)
        self.setVisible(True)

    def _clear_options(self):
        while self._options.count():
            item = self._options.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _add_multi(self, choices: list, answerable: bool):
        """Checkboxes (title + description) and one Answer button; the answer is the ticked exact titles."""
        box = QtWidgets.QWidget()
        rows = QtWidgets.QVBoxLayout(box)
        rows.setContentsMargins(0, 0, 0, 0)
        rows.setSpacing(4)
        checks = []
        for choice in choices:
            check = QtWidgets.QCheckBox(choice.get("title", ""))
            check.setEnabled(answerable)
            rows.addWidget(check)
            if choice.get("description"):
                detail = QtWidgets.QLabel(choice["description"])
                detail.setWordWrap(True)
                set_variant(detail, "status", "muted")
                detail.setContentsMargins(22, 0, 0, 0)
                rows.addWidget(detail)
            checks.append(check)
        self._options.addWidget(box)
        answer = QtWidgets.QPushButton("Answer")
        answer.setProperty("variant", "primary")
        answer.setEnabled(False)

        def refresh(_state=None):
            answer.setEnabled(answerable and any(check.isChecked() for check in checks))

        def send():
            picked = [check.text() for check in checks if check.isChecked()]
            if picked:
                self.option_chosen.emit(self._token, ", ".join(picked))

        for check in checks:
            check.toggled.connect(refresh)
        answer.clicked.connect(send)
        self._options.addWidget(answer)


class OperationReportView(QtWidgets.QFrame):
    """The bridge's factual ``operation_report`` at a normal run end. Evidence, not a verdict."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)
        row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Run report — recorded evidence, not a quality judgement")
        title.setObjectName("usageLabel")
        row.addWidget(title, 1)
        close = QtWidgets.QToolButton()
        close.setText("×")
        close.setToolTip("Dismiss this report")
        close.setProperty("variant", "ghost")
        close.clicked.connect(self.clear)
        row.addWidget(close)
        layout.addLayout(row)
        self._body = QtWidgets.QLabel()
        self._body.setWordWrap(True)
        self._body.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(170)
        scroll.setWidget(self._body)
        layout.addWidget(scroll)
        self.setVisible(False)

    def clear(self):
        self._body.setText("")
        self.setVisible(False)

    def show_report(self, report: dict):
        text = format_operation_report(report)
        self._body.setText(text)
        self.setVisible(bool(text))


_OUTPUT_TEXT = {
    "rendered_not_delivered": "rendered, but the image never reached the agent",
    "delivered_no_assessment_recorded": "shown to the agent; no assessment recorded",
    "assessment_recorded": "shown to the agent and assessed",
    "only_stale_renders": "only images from before later changes were shown",
}
_VIEW_TEXT = {"rgb": "colour (RGB) view", "alpha": "matte (alpha) view"}


def _render_line(render: dict) -> str:
    parts = [_VIEW_TEXT.get(render.get("view_mode"), "unknown view")]
    parts.append("shown to the agent" if render.get("delivered") else "not shown to the agent")
    if render.get("content_unchanged_since") is True:
        parts.append("image still current")
    elif render.get("content_unchanged_since") is False:
        parts.append("out of date: the image has changed since")
    if render.get("assessment_recorded"):
        parts.append("assessed")
    line = "    frame %s: %s" % (render.get("frame", "?"), ", ".join(parts))
    for key in ("invalidated", "not_certifiable"):
        if render.get(key):
            line += "; %s: %s" % (key.replace("_", " "), render[key])
    return line


def format_operation_report(report: dict) -> str:
    """Plain-language rendering of the bridge's operation_report. Evidence, not a verdict."""
    if not isinstance(report, dict):
        return ""
    lines = []
    for node in report.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        head = "%s (%s)" % (node.get("node", "?"), node.get("class", "?"))
        facts = [
            "purpose: %s" % (node.get("purpose") or "not recorded"),
            "treatment: %s" % (node.get("treatment") or "none read"),
            "output: %s" % _OUTPUT_TEXT.get(node.get("output"), node.get("output", "unknown")),
        ]
        if node.get("state"):
            facts.append("state: %s" % node["state"])
        if node.get("diagnostic_only"):
            facts.append("recorded from raw Python (diagnostic only)")
        if node.get("rendered_only"):
            facts.append(str(node["rendered_only"]))
        lines.append("%s — %s" % (head, "; ".join(facts)))
        modes = node.get("review_modes")
        if isinstance(modes, dict):
            lines.append(
                "    views needed: %s; shown for the current image: %s; missing: %s"
                % (
                    ", ".join(modes.get("expected") or []) or "none",
                    ", ".join(modes.get("viewed") or []) or "none",
                    ", ".join(modes.get("missing") or []) or "none",
                )
            )
            if modes.get("unconfirmed_renders"):
                lines.append("    %s render(s) recorded no recognisable view mode" % modes["unconfirmed_renders"])
            if modes.get("note"):
                lines.append("    %s" % modes["note"])
        for render in node.get("renders") or []:
            if isinstance(render, dict):
                lines.append(_render_line(render))
    if report.get("omitted_nodes"):
        lines.append("(%s further nodes omitted)" % report["omitted_nodes"])
    layout = report.get("layout_report")
    if isinstance(layout, dict):
        for label, text in (("issues", "layout issue"), ("unknowns", "layout unknown")):
            for item in layout.get(label) or []:
                lines.append("%s: %s" % (text, item))
    for item in report.get("unknowns") or []:
        lines.append("unknown: %s" % item)
    if report.get("note"):
        lines.append(str(report["note"]))
    return "\n".join(lines)
