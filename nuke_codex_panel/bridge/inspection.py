"""Graph revision and delivery accounting kept by the application-owned bridge.

Not a gate and not a sandbox: Python stays unrestricted and nothing is owed before it runs.
The revision is a global counter that advances whenever the root-anchored graph fingerprint
differs from the last one the bridge recorded (edits by Python, by the user, or by anything
else) and whenever the fingerprint cannot be taken. Each observation also names which nodes
differ, so results can report outside edits and unknown changes truthfully.

A delivery token is provisional: the MCP sidecar confirms it only after it has read the result
(and image) it is about to hand to the model. An unconfirmed token never counts as delivered.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import secrets

LEGACY_CLIENT = "legacy"

_MAX_PENDING_DELIVERIES = 256
_MAX_CLIENT_ID = 64
_MAX_CHANGED_LISTED = 10


def normalize_client_id(value) -> str:
    """Stable caller id from the private envelope; callers without one share the legacy id."""
    text = str(value).strip()[:_MAX_CLIENT_ID] if value else ""
    return text or LEGACY_CLIENT


@dataclass(frozen=True)
class Observation:
    """One fingerprint of the current graph taken against the recorded revision."""

    revision: int
    snapshot: dict | None
    # False when no fingerprint could be taken: nothing may be certified at this revision.
    certified: bool
    # Nodes (capped) whose fingerprint differs from the previous observation; empty when
    # nothing changed or there was no known baseline to compare with.
    changed: tuple[str, ...] = ()


class InspectionGate:
    def __init__(self, take_snapshot):
        self._take_snapshot = take_snapshot
        self.revision = 1
        # None = baseline unknown; the next fingerprint is adopted as is, because the
        # revision already advanced when the baseline became unknown (or this is the first look).
        self._fingerprint = None
        self._deliveries: OrderedDict[str, tuple[str, str, int]] = OrderedDict()

    def observe(self) -> Observation:
        """Fingerprint the graph now; advance the revision if it is not what was last recorded."""
        snapshot = self._take_snapshot()
        if snapshot is None:
            self.revision += 1
            self._fingerprint = None
            return Observation(self.revision, None, False)
        changed = ()
        if self._fingerprint is not None and snapshot != self._fingerprint:
            self.revision += 1
            previous = self._fingerprint
            differing = sorted(name for name in snapshot.keys() | previous.keys() if snapshot.get(name) != previous.get(name))
            changed = tuple(differing[:_MAX_CHANGED_LISTED])
        self._fingerprint = snapshot
        return Observation(self.revision, snapshot, True, changed)

    def graph_may_have_changed(self) -> int:
        """Code ran and the graph is changed or unknown afterwards: advance the revision, drop the baseline."""
        self.revision += 1
        self._fingerprint = None
        return self.revision

    def issue_delivery(self, client_id: str, kind: str, revision: int) -> str:
        """Provisional evidence; it counts only once ``confirm_delivery`` is called with the token."""
        token = secrets.token_urlsafe(18)
        self._deliveries[token] = (client_id, kind, revision)
        while len(self._deliveries) > _MAX_PENDING_DELIVERIES:
            self._deliveries.popitem(last=False)
        return token

    def confirm_delivery(self, client_id: str, token: str) -> str:
        """Count the delivery behind ``token`` for the client that was issued it; return its kind.

        Raises KeyError for an unknown, repeated, evicted, or other client's token.
        """
        entry = self._deliveries.get(token)
        if entry is None or entry[0] != client_id:
            raise KeyError(token)
        del self._deliveries[token]
        return entry[1]

    def forget(self, client_id: str) -> None:
        """Drop this client's undelivered tokens (its session ended)."""
        for token in [key for key, entry in self._deliveries.items() if entry[0] == client_id]:
            del self._deliveries[token]
