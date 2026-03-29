"""Activity: perceive a location to discover objects there."""

from __future__ import annotations

import asyncio

from temporalio import activity

from temporal_strips.domain.state import apply_perceive
from temporal_strips.models import ActionInput, ActionResult


@activity.defn(name="perceive")
async def perceive(input: ActionInput) -> ActionResult:
    """Perceive a location, revealing packages present there."""
    robot = input.parameters.get("r", "")
    location = input.parameters.get("l", "")

    activity.logger.info("Perceiving location %s with %s", location, robot)
    await asyncio.sleep(0.3)  # simulate sensor scan

    try:
        new_state = apply_perceive(input.state, robot, location)
        return ActionResult(
            success=True,
            updated_state=new_state,
            description=f"{robot} perceived {location}",
        )
    except ValueError as e:
        return ActionResult(success=False, description=str(e))
