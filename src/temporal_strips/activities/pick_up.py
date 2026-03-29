"""Activity: pick up a package at a location."""

from __future__ import annotations

import asyncio

from temporalio import activity

from temporal_strips.domain.state import apply_pick_up
from temporal_strips.models import ActionInput, ActionResult


@activity.defn(name="pick_up")
async def pick_up(input: ActionInput) -> ActionResult:
    """Pick up a visible package at the robot's current location."""
    robot = input.parameters.get("r", "")
    package = input.parameters.get("p", "")
    location = input.parameters.get("l", "")

    activity.logger.info("%s picking up %s at %s", robot, package, location)
    await asyncio.sleep(0.5)  # simulate gripper action

    try:
        new_state = apply_pick_up(input.state, robot, package, location)
        return ActionResult(
            success=True,
            updated_state=new_state,
            description=f"{robot} picked up {package} at {location}",
        )
    except ValueError as e:
        return ActionResult(success=False, description=str(e))
