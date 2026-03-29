"""Dict-based state transformations mirroring the UP domain actions.

These operate on plain dicts so they can run inside Temporal activities
without importing unified-planning.
"""

from __future__ import annotations

from temporal_strips.models import FluentValue, encode_fluent


def check_goals(state: dict[str, FluentValue], goals: dict[str, FluentValue]) -> bool:
    """Return True if every goal fluent matches the current state."""
    return all(state.get(k) == v for k, v in goals.items())


def apply_perceive(
    state: dict[str, FluentValue],
    robot: str,
    location: str,
) -> dict[str, FluentValue]:
    """Perceive a location, marking it observed and revealing packages there."""
    new = dict(state)

    robot_at_key = encode_fluent("robot_at", [robot, location])
    if not new.get(robot_at_key):
        raise ValueError(f"Precondition failed: {robot} not at {location}")

    new[encode_fluent("observed", [location])] = True

    # Reveal all packages that are actually at this location
    for key, value in state.items():
        if not value:
            continue
        if key.startswith("package_at(") and key.endswith(f", {location})"):
            # Extract package name from "package_at(pkg, loc)"
            inner = key[len("package_at("):-1]
            pkg = inner.split(",")[0].strip()
            new[encode_fluent("visible", [pkg, location])] = True

    return new


def apply_move(
    state: dict[str, FluentValue],
    robot: str,
    from_loc: str,
    to_loc: str,
) -> dict[str, FluentValue]:
    """Move robot from one location to another."""
    new = dict(state)

    robot_at_from = encode_fluent("robot_at", [robot, from_loc])
    connected_key = encode_fluent("connected", [from_loc, to_loc])

    if not new.get(robot_at_from):
        raise ValueError(f"Precondition failed: {robot} not at {from_loc}")
    if not new.get(connected_key):
        raise ValueError(f"Precondition failed: {from_loc} not connected to {to_loc}")

    new[robot_at_from] = False
    new[encode_fluent("robot_at", [robot, to_loc])] = True
    return new


def apply_pick_up(
    state: dict[str, FluentValue],
    robot: str,
    package: str,
    location: str,
) -> dict[str, FluentValue]:
    """Pick up a package at a location."""
    new = dict(state)

    robot_at_key = encode_fluent("robot_at", [robot, location])
    visible_key = encode_fluent("visible", [package, location])
    hands_free_key = encode_fluent("hands_free", [robot])

    if not new.get(robot_at_key):
        raise ValueError(f"Precondition failed: {robot} not at {location}")
    if not new.get(visible_key):
        raise ValueError(f"Precondition failed: {package} not visible at {location}")
    if not new.get(hands_free_key):
        raise ValueError(f"Precondition failed: {robot} hands not free")

    new[encode_fluent("holding", [robot, package])] = True
    new[visible_key] = False
    new[hands_free_key] = False
    return new


def apply_drop(
    state: dict[str, FluentValue],
    robot: str,
    package: str,
    location: str,
) -> dict[str, FluentValue]:
    """Drop a package at a location."""
    new = dict(state)

    robot_at_key = encode_fluent("robot_at", [robot, location])
    holding_key = encode_fluent("holding", [robot, package])

    if not new.get(robot_at_key):
        raise ValueError(f"Precondition failed: {robot} not at {location}")
    if not new.get(holding_key):
        raise ValueError(f"Precondition failed: {robot} not holding {package}")

    new[holding_key] = False
    new[encode_fluent("package_at", [package, location])] = True
    new[encode_fluent("visible", [package, location])] = True
    new[encode_fluent("hands_free", [robot])] = True
    return new
