"""Activity: move a robot between locations."""

from __future__ import annotations

import asyncio

from temporalio import activity

from temporal_strips.domain.state import apply_move
from temporal_strips.models import ActionInput, ActionResult


@activity.defn(name="move")
async def move(input: ActionInput) -> ActionResult:
    """Move a robot from one location to another."""
    robot = input.parameters.get("r", "")
    from_loc = input.parameters.get("from_loc", "")
    to_loc = input.parameters.get("to_loc", "")

    activity.logger.info("Moving %s from %s to %s", robot, from_loc, to_loc)
    await asyncio.sleep(1.0)  # simulate travel time

    try:
        new_state = apply_move(input.state, robot, from_loc, to_loc)
        return ActionResult(
            success=True,
            updated_state=new_state,
            description=f"{robot} moved from {from_loc} to {to_loc}",
        )
    except ValueError as e:
        return ActionResult(success=False, description=str(e))
