"""Shared node-graph layout helpers: the known 2D Merge check, a finite arrangement planner and a
read-only layout review.

Pure Python, no ``nuke`` import: everything works on plain fact dicts
``{name, class, inputs[name|None], x, y, width?, height?}`` (``x``/``y`` are Nuke's top-left
``xpos``/``ypos``; ``width``/``height`` are the node's real ``screenWidth``/``screenHeight`` when
known). ``NativeActions`` applies a plan through the real Nuke API and reads it back.

Geometry is approximate by nature: Nuke does not expose where a socket is painted, so an edge is
modelled as a straight line from the source's bottom centre to the consumer's top centre. Crossings
and pass-through reports are therefore candidates, never a certificate of a clean picture.
"""

from __future__ import annotations

LAYOUT_COLUMN_TOLERANCE = 20
LAYOUT_SIDE_MIN = 70

DEFAULT_WIDTH = 80.0
DEFAULT_HEIGHT = 18.0
DOT_PLAN = 20.0  # planned Dot box edge: larger than Nuke's Dot so a plan stays valid for the real size
CLEAR = 8.0  # clearance kept around planned waypoint Dots
ROW_GAP = 40.0
LANE_GAP = 60.0
ROUTE_ROOM = 2 * DOT_PLAN + 3 * CLEAR  # vertical room between a source and consumer for two waypoint Dots
MAX_DOTS = 12
MAX_REPORTED = 20
FAN_ROOM = ROUTE_ROOM  # vertical room kept below a fan-out source for its Dot row and the drops

# Port roles established from the node classes themselves: input 0 is the trunk (B / the copied-onto
# image) and every further input a side input. Nothing else is claimed for other classes.
_TRUNK_SIDE_CLASSES = frozenset({"Merge2", "Merge", "Copy"})
_MASK_SOURCE_CLASSES = frozenset({"Roto", "RotoPaint"})


class LayoutError(ValueError):
    """The arrangement request itself is invalid (nothing was planned)."""


# ---------------------------------------------------------------------------------
# The known 2D Merge check (nuke_workflow layout step)
# ---------------------------------------------------------------------------------


def check_merge_layout(context):
    """Problem text for the bound merge/background/foreground nodes of the 2d workflow, or None."""
    merge, problem = context.role_node("merge")
    if problem:
        return problem
    background, problem = context.role_node("background")
    if problem:
        return problem
    foreground, problem = context.role_node("foreground")
    if problem:
        return problem
    issues = []
    if abs(merge["x"] - background["x"]) > LAYOUT_COLUMN_TOLERANCE:
        issues.append("Merge %s is not in the B column of %s (x %s vs %s)" % (merge["name"], background["name"], merge["x"], background["x"]))
    if merge["y"] <= background["y"]:
        issues.append("Merge %s must sit below its B input %s" % (merge["name"], background["name"]))
    if abs(foreground["x"] - merge["x"]) < LAYOUT_SIDE_MIN:
        issues.append("foreground %s must enter A from the left or right side, not stack on the B trunk" % foreground["name"])
    if foreground["y"] >= merge["y"]:
        issues.append("foreground %s must sit above the Merge %s" % (foreground["name"], merge["name"]))
    return "; ".join(issues) or None


# ---------------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------------


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and value not in (float("inf"), float("-inf"))


def _bounds_known(fact) -> bool:
    return _number(fact.get("width")) and _number(fact.get("height")) and fact["width"] > 0 and fact["height"] > 0


def _size(fact):
    if _bounds_known(fact):
        return float(fact["width"]), float(fact["height"])
    return DEFAULT_WIDTH, DEFAULT_HEIGHT


def _inputs(fact):
    return list(fact.get("inputs") or [])


def _port_role(fact, index):
    """``trunk``, ``side`` or ``unknown`` for one input port, from source-known classes only."""
    if fact.get("class") in _TRUNK_SIDE_CLASSES:
        return "trunk" if index == 0 else "side"
    if len(_inputs(fact)) == 1:
        return "trunk"
    return "unknown"


def _segment(source, consumer):
    sw, sh = _size(source)
    cw, _ = _size(consumer)
    return (
        (source["x"] + sw / 2.0, source["y"] + sh),
        (consumer["x"] + cw / 2.0, consumer["y"]),
    )


def _hits_box(p, q, fact, shrink=2.0) -> bool:
    """Liang-Barsky: does segment p-q pass through the node's box (shrunk slightly)?"""
    w, h = _size(fact)
    left, right = fact["x"] + shrink, fact["x"] + w - shrink
    top, bottom = fact["y"] + shrink, fact["y"] + h - shrink
    if left >= right or top >= bottom:
        return False
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pk, qk in ((-dx, p[0] - left), (dx, right - p[0]), (-dy, p[1] - top), (dy, bottom - p[1])):
        if pk == 0:
            if qk < 0:
                return False
            continue
        t = qk / pk
        if pk < 0:
            if t > t1:
                return False
            t0 = max(t0, t)
        else:
            if t < t0:
                return False
            t1 = min(t1, t)
    return t0 <= t1


def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _cross(p1, p2, p3, p4) -> bool:
    d1, d2 = _orient(p3, p4, p1), _orient(p3, p4, p2)
    d3, d4 = _orient(p1, p2, p3), _orient(p1, p2, p4)
    return d1 * d2 < 0 and d3 * d4 < 0


def _overlap(a, b) -> bool:
    aw, ah = _size(a)
    bw, bh = _size(b)
    return a["x"] < b["x"] + bw and b["x"] < a["x"] + aw and a["y"] < b["y"] + bh and b["y"] < a["y"] + ah


# ---------------------------------------------------------------------------------
# Read-only review
# ---------------------------------------------------------------------------------


def review_layout(facts) -> dict:
    """Review the given nodes' picture: ordering, overlaps, Merge/Copy trunk alignment, edges through nodes.

    Only the edges whose both ends are in ``facts`` are reviewed. Returns ``issues`` (what is wrong),
    ``unknowns`` (what could not be judged), ``reviewed`` (the names looked at) and ``edges``.
    """
    nodes = {}
    for fact in facts:
        if isinstance(fact, dict) and isinstance(fact.get("name"), str) and _number(fact.get("x")) and _number(fact.get("y")):
            nodes[fact["name"]] = fact
    issues, unknowns = [], []
    unsized = sorted(name for name, fact in nodes.items() if not _bounds_known(fact))
    if unsized:
        unknowns.append(
            "node bounds unknown for %s: a default %dx%d box was assumed" % (", ".join(unsized[:8]), DEFAULT_WIDTH, DEFAULT_HEIGHT)
        )
    unknown_roles = sorted(
        {fact["class"] for fact in nodes.values() if len(_inputs(fact)) > 1 and _port_role(fact, 0) == "unknown"}
    )
    if unknown_roles:
        unknowns.append(
            "port roles of %s are not source-known: ordering was checked, trunk/side placement was not judged"
            % ", ".join(unknown_roles[:8])
        )
    edges = []
    external = 0
    for name, fact in nodes.items():
        if fact.get("class") == "Viewer":
            continue  # a Viewer's input changes constantly; its connection is not part of the picture
        for index, source in enumerate(_inputs(fact)):
            if source is None:
                continue
            if source not in nodes:
                external += 1
                continue
            edges.append((source, name, index))
    if external:
        unknowns.append("%d input(s) come from nodes outside the reviewed set and were not reviewed" % external)
    unknowns.append(
        "painted socket positions are not exposed by Nuke: edges are modelled bottom-centre to top-centre, "
        "so reported crossings are candidates and an empty list is not a visual certificate"
    )

    for source, consumer, index in edges:
        s, c = nodes[source], nodes[consumer]
        if s["y"] + _size(s)[1] > c["y"]:
            issues.append("source %s must sit above its consumer %s (input %d)" % (source, consumer, index))
    names = sorted(nodes)
    for i, first in enumerate(names):
        for second in names[i + 1 :]:
            if _overlap(nodes[first], nodes[second]):
                issues.append("nodes %s and %s overlap" % (first, second))
    for source, consumer, index in edges:
        c = nodes[consumer]
        if c.get("class") not in _TRUNK_SIDE_CLASSES:
            continue
        s = nodes[source]
        if s.get("class") == "Dot":
            continue  # a waypoint sits in a gutter on purpose; its own edges are checked for ordering and crossings
        dx = abs((s["x"] + _size(s)[0] / 2.0) - (c["x"] + _size(c)[0] / 2.0))
        if index == 0 and dx > LAYOUT_COLUMN_TOLERANCE:
            issues.append("%s input 0 (the trunk) %s is not in its column (%d px off)" % (consumer, source, round(dx)))
        elif index > 0 and dx < LAYOUT_SIDE_MIN:
            issues.append("%s input %d %s stacks on the trunk column; it must enter from the side" % (consumer, index, source))
    segments = []
    for source, consumer, index in edges:
        p, q = _segment(nodes[source], nodes[consumer])
        segments.append((source, consumer, index, p, q))
        for other in names:
            if other in (source, consumer):
                continue
            if _hits_box(p, q, nodes[other]):
                issues.append("the edge %s -> %s passes through node %s" % (source, consumer, other))
    for i, (s1, c1, i1, p1, q1) in enumerate(segments):
        for s2, c2, i2, p2, q2 in segments[i + 1 :]:
            if {s1, c1} & {s2, c2}:
                continue
            if _cross(p1, q1, p2, q2):
                issues.append("edges %s -> %s and %s -> %s cross" % (s1, c1, s2, c2))
    if len(issues) > MAX_REPORTED:
        issues = issues[:MAX_REPORTED] + ["%d more" % (len(issues) - MAX_REPORTED)]
    return {"issues": issues, "unknowns": unknowns, "reviewed": names, "edges": len(edges)}


# ---------------------------------------------------------------------------------
# Arrangement planner
# ---------------------------------------------------------------------------------


class _Column:
    __slots__ = ("side", "key", "index", "x")

    def __init__(self, side=None, key=(0.0, 0)):
        self.side = side  # None = the tree's trunk column, else "left" / "right"
        self.key = key  # (consumer row, port): nearer lanes belong to consumers higher up
        self.index = 0
        self.x = 0.0  # centre x once the tree is anchored


def plan_arrangement(facts, movable, output=None) -> dict:
    """One finite arrangement of exactly the ``movable`` nodes.

    ``facts`` maps name -> fact for every node of the working group; only ``movable`` positions change.
    Rows: every movable source sits above all of its consumers (longest-path rows, then as low as
    its movable consumers allow). Columns: the trunk input of a Merge/Copy (or the only input of a
    one-input node) stays in its consumer's column, side inputs get their own lane, masks (Roto) a lane
    on the other side. An edge that would pass through another node gets room (listed nodes move apart
    vertically) and one or two waypoint Dots from a bounded candidate set, each validated against every node,
    Dot and edge of the group; with no clear candidate the connection stays and is reported.
    A source with two or more listed consumers is a fan-out source: it sits above its branches, centred over them,
    with a row of Dots directly beneath it (one per consumer column) and vertical drops, vertical room reserved.

    Returns ``positions`` {name: (x, y)}, ``routes`` (waypoint plans), ``unresolved`` and ``unknowns``
    (lists of str). Raises :class:`LayoutError` when the request is invalid.
    """
    movable = list(movable)
    if not movable:
        raise LayoutError("nodes must list at least one node")
    if len(set(movable)) != len(movable):
        raise LayoutError("nodes lists a node more than once")
    absent = [name for name in movable if name not in facts]
    if absent:
        raise LayoutError("no such node(s) in the working group: %s" % ", ".join(absent))
    # Viewer inputs change constantly: a Viewer is never moved and its connections are never routed or used
    # for placement. Listed Viewers are simply left where they are.
    viewers = [name for name in movable if facts[name].get("class") == "Viewer"]
    movable = [name for name in movable if name not in viewers]
    if not movable:
        raise LayoutError("only Viewer nodes were listed: a Viewer is never moved or routed")
    mset = set(movable)
    if output is not None and output not in mset:
        raise LayoutError("output %r must be one of the listed non-Viewer nodes" % output)

    inputs = {
        name: [] if fact.get("class") == "Viewer" else [(i, s) for i, s in enumerate(_inputs(fact)) if s in facts]
        for name, fact in facts.items()
    }
    consumers = {}
    for consumer, lst in inputs.items():
        for index, source in lst:
            consumers.setdefault(source, []).append((consumer, index))
    mcons = {n: [(c, i) for c, i in consumers.get(n, []) if c in mset] for n in movable}
    if output is not None and mcons[output]:
        raise LayoutError("output %r feeds %s, which is also listed: output must be a terminal of nodes" % (output, mcons[output][0][0]))

    indegree = {n: sum(1 for _, s in inputs[n] if s in mset) for n in movable}
    ready = [n for n in movable if indegree[n] == 0]
    order = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for consumer, _ in mcons[node]:
            indegree[consumer] -= 1
            if indegree[consumer] == 0:
                ready.append(consumer)
    if len(order) != len(movable):
        raise LayoutError("the listed nodes contain a connection cycle")

    unknowns = []
    if viewers:
        unknowns.append("Viewer node(s) %s were left in place: Viewer connections are never moved, routed or used for placement" % ", ".join(viewers[:8]))
    unsized = [n for n in movable if not _bounds_known(facts[n])]
    if unsized:
        unknowns.append("node bounds unknown for %s: default %dx%d boxes were used" % (", ".join(unsized[:8]), DEFAULT_WIDTH, DEFAULT_HEIGHT))
    unknown_roles = sorted({facts[n]["class"] for n in movable if len(_inputs(facts[n])) > 1 and _port_role(facts[n], 0) == "unknown"})
    if unknown_roles:
        unknowns.append(
            "port roles of %s are not source-known: input 0 was placed above the node and the other inputs to the side "
            "in input order, which is a placement convention, not a statement of what each port means" % ", ".join(unknown_roles[:8])
        )

    # ---- shared geometry ----
    lane_width = max(_size(facts[n])[0] for n in movable) + LANE_GAP
    height = {n: _size(facts[n])[1] for n in facts}
    top = min(facts[n]["y"] for n in movable)
    # A node with two or more listed consumers is a fan-out source: it is not squeezed into one consumer's
    # column; it sits above its branches with one Dot per consumer column directly beneath it.
    fan = {n for n in movable if len({c for c, _ in mcons[n]}) >= 2}

    def preferred_x(terminal):
        fixed = {c for c, _ in consumers.get(terminal, []) if c not in mset and facts[c].get("class") != "Viewer"}
        base = facts[terminal]
        if terminal != output and len(fixed) == 1:
            base = facts[next(iter(fixed))]
        return base["x"] + _size(base)[0] / 2.0

    def solve(extra):
        """Rows, columns, positions and fan-out Dots; ``extra`` {(source, consumer): gap} adds waypoint room."""

        def gap(source, consumer):
            return max(FAN_ROOM if source in fan else ROW_GAP, extra.get((source, consumer), 0.0))

        y = {}
        for node in order:
            row = top
            for _, source in inputs[node]:
                base = y[source] if source in mset else facts[source]["y"]
                row = max(row, base + height[source] + gap(source, node))
            y[node] = float(row)
        for node in reversed(order):
            limits = [y[c] - gap(node, c) for c, _ in mcons[node]]
            if limits:
                lowest = min(limits) - height[node]
                if lowest > y[node]:
                    y[node] = lowest

        fixed_issues = []
        for node in movable:
            for consumer, index in consumers.get(node, []):
                if consumer in mset or facts[consumer].get("class") == "Viewer":
                    continue
                if y[node] + height[node] + ROW_GAP / 2.0 > facts[consumer]["y"]:
                    fixed_issues.append(
                        "fixed consumer %s (input %d, not listed) sits at y=%d, too close to or above the listed source %s "
                        "(y=%d): it was not moved; list it in nodes to let it move" % (consumer, index, facts[consumer]["y"], node, y[node])
                    )

        col_of, lanes, fan_cols = {}, [], {}

        def build(node, column):
            col_of[node] = column
            for index, source in inputs[node]:
                if source not in mset or source in col_of:
                    continue
                role = _port_role(facts[node], index)
                if role == "trunk" or (role == "unknown" and index == 0):
                    target = column
                else:
                    side = "right" if facts[source].get("class") in _MASK_SOURCE_CLASSES else "left"
                    target = _Column(side, (y[node], index))
                    lanes.append(target)
                if source in fan:
                    fan_cols[(source, node, index)] = target  # a Dot goes into this column, not the source itself
                else:
                    build(source, target)

        def assign(tree_lanes):
            for side in ("left", "right"):
                chosen = sorted((lane for lane in tree_lanes if lane.side == side), key=lambda lane: lane.key)
                for rank, lane in enumerate(chosen, 1):
                    lane.index = rank if side == "right" else -rank

        def settle(trunk, tree_lanes, anchor):
            trunk.x = anchor
            for lane in tree_lanes:
                lane.x = anchor + lane.index * lane_width

        terminals = [n for n in movable if not mcons[n]]
        terminals.sort(key=lambda n: (n != output, preferred_x(n), n))
        trees = []
        for terminal in terminals:
            lane_start = len(lanes)
            trunk = _Column()
            build(terminal, trunk)
            tree_lanes = lanes[lane_start:]
            assign(tree_lanes)
            trees.append((terminal, trunk, tree_lanes))
        cursor = None
        for terminal, trunk, tree_lanes in trees:
            left = max([-lane.index for lane in tree_lanes if lane.index < 0] or [0])
            right = max([lane.index for lane in tree_lanes if lane.index > 0] or [0])
            anchor = preferred_x(terminal)
            if cursor is not None:
                anchor = max(anchor, cursor + (left + 1) * lane_width)
            cursor = anchor + right * lane_width
            settle(trunk, tree_lanes, anchor)

        # Fan-out sources, consumers first: centred over the columns of their Dots, upstream chain above them.
        for source in reversed(order):
            if source not in fan:
                continue
            xs = [column.x for (s, _c, _i), column in fan_cols.items() if s == source]
            anchor = sum(xs) / len(xs) if xs else preferred_x(source)
            lane_start = len(lanes)
            trunk = _Column()
            build(source, trunk)
            tree_lanes = lanes[lane_start:]
            assign(tree_lanes)
            settle(trunk, tree_lanes, anchor)

        positions = {
            node: (int(round(col_of[node].x - _size(facts[node])[0] / 2.0)), int(round(y[node]))) for node in movable
        }
        fan_routes = []
        for (source, consumer, index), column in sorted(fan_cols.items(), key=lambda item: (y[item[0][1]], item[0])):
            fan_routes.append(
                {
                    "source": source,
                    "consumer": consumer,
                    "port": index,
                    "waypoints": [[column.x, y[source] + height[source] + CLEAR + DOT_PLAN / 2.0]],
                }
            )
        return positions, fixed_issues, fan_routes

    def place(positions):
        placed = {name: dict(fact) for name, fact in facts.items()}
        for node, (px, py) in positions.items():
            placed[node]["x"], placed[node]["y"] = px, py
        return placed

    def passing(placed, skip):
        """Edges into a listed consumer whose straight line passes through another node (except ``skip``)."""
        out = []
        for consumer in movable:
            for index, source in inputs[consumer]:
                if (source, consumer, index) in skip:
                    continue
                p, q = _segment(placed[source], placed[consumer])
                if any(_hits_box(p, q, placed[other]) for other in placed if other not in (source, consumer)):
                    out.append((source, consumer, index))
        return out

    positions, fixed_issues, fan_routes = solve({})
    placed = place(positions)
    pre = {(r["source"], r["consumer"], r["port"]) for r in fan_routes}
    need = passing(placed, pre)
    if need:
        # Vertical room for waypoints is allocated by moving only the listed nodes, then re-checked once.
        positions, fixed_issues, fan_routes = solve({(source, consumer): ROUTE_ROOM for source, consumer, _ in need})
        placed = place(positions)
        pre = {(r["source"], r["consumer"], r["port"]) for r in fan_routes}
        need = passing(placed, pre)

    routes, route_issues = _admit_routes(placed, inputs, need, fan_routes, height, lane_width)
    unresolved = fixed_issues + route_issues
    if routes:
        unknowns.append(
            "waypoint Dots were planned as %dx%d boxes with %d px clearance (larger than Nuke's real Dot); "
            "their real size is read back after creation" % (DOT_PLAN, DOT_PLAN, CLEAR)
        )
    return {"positions": positions, "routes": routes, "unresolved": unresolved, "unknowns": unknowns}


def _dot_fact(name, cx, cy):
    return {"name": name, "class": "Dot", "inputs": [], "x": cx - DOT_PLAN / 2.0, "y": cy - DOT_PLAN / 2.0, "width": DOT_PLAN, "height": DOT_PLAN}


def _padded(fact, pad):
    w, h = _size(fact)
    return {"x": fact["x"] - pad, "y": fact["y"] - pad, "width": w + 2 * pad, "height": h + 2 * pad}


def _admit_routes(placed, inputs, need, planned, height, lane_width):
    """Waypoint routes, each validated against the whole group before it is admitted.

    ``planned`` are the fan-out Dots (one per consumer column, directly beneath their source); ``need`` are
    other edges whose straight line passes through a node. A route is admitted only if its Dots keep clear of
    every node and earlier Dot, none of its segments passes through a node or Dot or properly crosses an edge
    that stays as it is or an earlier route, and it fits the Dot limit. A planned route that is not admissible
    falls back to the bounded candidate search (one or two Dots in a gutter beside the source or consumer);
    with no clear candidate the connection stays as it was and is reported. Returns (routes, unresolved).
    """
    routes, unresolved = [], []
    need = list(need)
    need_set = set(need) | {(r["source"], r["consumer"], r["port"]) for r in planned}
    direct = []
    for consumer, lst in inputs.items():
        for index, source in lst:
            if (source, consumer, index) not in need_set:
                direct.append(_segment(placed[source], placed[consumer]))
    accepted_dots, accepted_segments = [], []
    half = lane_width / 2.0
    counter = 0

    def admissible(chain):
        obstacles = list(placed.values()) + accepted_dots
        for dot in chain[1:-1]:
            box = _padded(dot, CLEAR)
            if any(_overlap(box, other) for other in obstacles):
                return False
        for first, second in zip(chain, chain[1:]):
            p, q = _segment(first, second)
            if p[1] >= q[1]:
                return False
            for other in obstacles:
                if other["name"] not in (first["name"], second["name"]) and _hits_box(p, q, other):
                    return False
            if any(_cross(p, q, pp, qq) for pp, qq in direct + accepted_segments):
                return False
        return True

    def try_shape(source, consumer, index, shape):
        nonlocal counter
        if len(shape) > MAX_DOTS - len(accepted_dots):
            return False
        dots = []
        for cx_, cy_ in shape:
            counter += 1
            dots.append(_dot_fact("~waypoint%d" % counter, cx_, cy_))
        chain = [placed[source]] + dots + [placed[consumer]]
        if not admissible(chain):
            return False
        routes.append({"source": source, "consumer": consumer, "port": index, "waypoints": [list(point) for point in shape]})
        accepted_dots.extend(dots)
        accepted_segments.extend(_segment(a, b) for a, b in zip(chain, chain[1:]))
        return True

    for route in planned:
        if not try_shape(route["source"], route["consumer"], route["port"], [tuple(point) for point in route["waypoints"]]):
            need.append((route["source"], route["consumer"], route["port"]))  # not clear: bounded search below

    for source, consumer, index in sorted(need, key=lambda edge: (placed[edge[1]]["y"], edge[1], edge[2])):
        s, c = placed[source], placed[consumer]
        p, q = _segment(s, c)
        blockers = sorted(o for o in placed if o not in (source, consumer) and _hits_box(p, q, placed[o]))
        label = "%s -> %s (input %d)" % (source, consumer, index)
        label += " passes through %s" % ", ".join(blockers[:3]) if blockers else ": its planned fan-out Dot is not clear of other nodes or edges"
        s_bottom, c_top = s["y"] + height[source], c["y"]
        y1 = s_bottom + CLEAR + DOT_PLAN / 2.0
        y2 = c_top - CLEAR - DOT_PLAN / 2.0
        sx, cx = p[0], q[0]
        d = -1 if cx < sx else 1
        xs = []
        for x in (sx + d * half, cx - d * half, sx - d * half, cx + d * half, sx + d * (half + lane_width), sx - d * (half + lane_width)):
            if round(x) not in [round(v) for v in xs]:
                xs.append(x)
        shapes = []
        if y2 - y1 >= DOT_PLAN + CLEAR:
            shapes += [[(x, y1), (x, y2)] for x in xs]
        if y2 - DOT_PLAN / 2.0 - CLEAR >= s_bottom:
            shapes += [[(x, y2)] for x in xs]
        shapes = [shape for shape in shapes if len(shape) <= MAX_DOTS - len(accepted_dots)]
        if not shapes:
            unresolved.append(
                "%s, and no waypoint route fits (not enough vertical room between source and consumer, or the %d-Dot limit "
                "was reached); the connection was left as it is" % (label, MAX_DOTS)
            )
            continue
        if not any(try_shape(source, consumer, index, shape) for shape in shapes):
            unresolved.append(
                "%s, and none of the %d waypoint candidates is clear of other nodes and edges; the connection was left as it is"
                % (label, len(shapes))
            )
    return routes, unresolved
