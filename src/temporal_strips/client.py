"""Client script to start an AchieveWorkflow with a sample scenario."""

from __future__ import annotations

import argparse
import asyncio
import os
import uuid

from temporalio.client import Client
from temporalio.contrib.opentelemetry import OpenTelemetryPlugin

from temporal_strips.models import PlanRequest

TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
TASK_QUEUE = "planner-task-queue"

SCENARIOS: dict[str, PlanRequest] = {
    "delivery": PlanRequest(
        objects={
            "robot1": "Robot",
            "pkg1": "Package",
            "warehouse": "Location",
            "dock": "Location",
            "store": "Location",
        },
        goals={
            "package_at(pkg1, store)": True,
        },
    ),
    "multi": PlanRequest(
        objects={
            "robot1": "Robot",
            "pkg1": "Package",
            "pkg2": "Package",
            "warehouse": "Location",
            "dock": "Location",
            "store": "Location",
            "depot": "Location",
        },
        goals={
            "package_at(pkg1, dock)": True,
            "package_at(pkg2, store)": True,
        },
    ),
}


async def main(scenario: str) -> None:
    if scenario not in SCENARIOS:
        print(f"Unknown scenario: {scenario}")
        print(f"Available: {', '.join(SCENARIOS)}")
        return

    request = SCENARIOS[scenario]

    client = await Client.connect(
        TEMPORAL_ADDRESS,
        plugins=[OpenTelemetryPlugin(add_temporal_spans=True)],
    )

    workflow_id = f"achieve-{scenario}-{uuid.uuid4().hex[:8]}"
    print(f"Starting AchieveWorkflow: {workflow_id}")
    print(f"  Scenario: {scenario}")
    print(f"  Goals: {request.goals}")

    result = await client.execute_workflow(
        "AchieveWorkflow",
        request,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"\nResult: {result}")
    if result.get("success"):
        print(f"  Goals achieved in {result.get('steps', '?')} steps")
    else:
        print(f"  Failed: {result.get('error', 'unknown')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start an AchieveWorkflow")
    parser.add_argument(
        "--scenario",
        default="delivery",
        choices=list(SCENARIOS.keys()),
        help="Scenario to run (default: delivery)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.scenario))
