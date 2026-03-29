from __future__ import annotations

import re
from dataclasses import dataclass, field

FluentValue = bool | int | float


def encode_fluent(name: str, params: list[str]) -> str:
    if not params:
        return name
    return f"{name}({', '.join(params)})"


def decode_fluent(key: str) -> tuple[str, list[str]]:
    match = re.match(r"^(\w+)\((.+)\)$", key)
    if not match:
        return key, []
    name = match.group(1)
    params = [p.strip() for p in match.group(2).split(",")]
    return name, params


@dataclass
class PlanRequest:
    """Input to the achieve workflow. Contains only the desired end state."""

    objects: dict[str, str]
    goals: dict[str, FluentValue]


@dataclass
class WorldState:
    """Snapshot of the current world state, returned by get_state activity."""

    objects: dict[str, str]
    fluents: dict[str, FluentValue]


@dataclass
class PlanInput:
    """Input to the plan activity: current state + desired goals."""

    state: WorldState
    goals: dict[str, FluentValue]


@dataclass
class Action:
    """A single action from a generated plan."""

    action_name: str
    parameters: dict[str, str]


@dataclass
class PlanResult:
    """Output of the plan activity."""

    success: bool
    actions: list[Action] = field(default_factory=list)
    error: str = ""


@dataclass
class ActionInput:
    """Input for executing a domain action activity."""

    state: dict[str, FluentValue]
    parameters: dict[str, str]


@dataclass
class ActionResult:
    """Output of executing a single action activity."""

    success: bool
    updated_state: dict[str, FluentValue] = field(default_factory=dict)
    description: str = ""
