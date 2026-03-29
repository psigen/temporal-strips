"""Activity that returns the current world state.

In a real system this would query sensors, databases, or external APIs.
For this demo, it returns a hardcoded initial state based on the objects
provided in the PlanRequest.
"""

from __future__ import annotations

import asyncio

from temporalio import activity

from temporal_planner.models import PlanRequest, WorldState, encode_fluent


# Scenario initial states keyed by a frozenset of object names for lookup.
# In a real system, this would be replaced by actual state queries.
SCENARIOS: dict[str, dict] = {
    "delivery": {
        "objects": {
            "robot1": "Robot",
            "pkg1": "Package",
            "warehouse": "Location",
            "dock": "Location",
            "store": "Location",
        },
        "fluents": {
            "robot_at(robot1, warehouse)": True,
            "package_at(pkg1, warehouse)": True,
            "connected(warehouse, dock)": True,
            "connected(dock, warehouse)": True,
            "connected(dock, store)": True,
            "connected(store, dock)": True,
            "hands_free(robot1)": True,
            "observed(warehouse)": False,
            "observed(dock)": False,
            "observed(store)": False,
            "visible(pkg1, warehouse)": False,
            "visible(pkg1, dock)": False,
            "visible(pkg1, store)": False,
        },
    },
    "multi": {
        "objects": {
            "robot1": "Robot",
            "pkg1": "Package",
            "pkg2": "Package",
            "warehouse": "Location",
            "dock": "Location",
            "store": "Location",
            "depot": "Location",
        },
        "fluents": {
            "robot_at(robot1, warehouse)": True,
            "package_at(pkg1, warehouse)": True,
            "package_at(pkg2, warehouse)": True,
            "connected(warehouse, dock)": True,
            "connected(dock, warehouse)": True,
            "connected(dock, store)": True,
            "connected(store, dock)": True,
            "connected(store, depot)": True,
            "connected(depot, store)": True,
            "hands_free(robot1)": True,
            "observed(warehouse)": False,
            "observed(dock)": False,
            "observed(store)": False,
            "observed(depot)": False,
            "visible(pkg1, warehouse)": False,
            "visible(pkg1, dock)": False,
            "visible(pkg1, store)": False,
            "visible(pkg1, depot)": False,
            "visible(pkg2, warehouse)": False,
            "visible(pkg2, dock)": False,
            "visible(pkg2, store)": False,
            "visible(pkg2, depot)": False,
        },
    },
}


def _match_scenario(objects: dict[str, str]) -> dict | None:
    """Match request objects to a known scenario."""
    for scenario in SCENARIOS.values():
        if scenario["objects"] == objects:
            return scenario
    return None


@activity.defn(name="get_state")
async def get_state(request: PlanRequest) -> WorldState:
    """Query the current world state."""
    activity.logger.info("Querying world state for %d objects", len(request.objects))
    await asyncio.sleep(0.1)  # simulate sensor/db query

    scenario = _match_scenario(request.objects)
    if scenario:
        return WorldState(
            objects=scenario["objects"],
            fluents=dict(scenario["fluents"]),
        )

    # Fallback: return empty state with just the objects
    activity.logger.warning("No matching scenario found, returning minimal state")
    return WorldState(objects=request.objects, fluents={})
