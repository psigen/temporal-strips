"""Temporal worker entry point with OpenTelemetry tracing."""

from __future__ import annotations

import asyncio
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from temporalio.client import Client
from temporalio.contrib.opentelemetry import OpenTelemetryPlugin, create_tracer_provider
from temporalio.worker import Worker

TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
OTEL_ENDPOINT = os.environ.get("OTEL_ENDPOINT", "http://localhost:4317")
TASK_QUEUE = "planner-task-queue"


def init_telemetry() -> None:
    """Configure OpenTelemetry with OTLP gRPC exporter."""
    resource = Resource.create({SERVICE_NAME: "temporal-planner-worker"})
    provider = create_tracer_provider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


async def main() -> None:
    init_telemetry()

    client = await Client.connect(
        TEMPORAL_ADDRESS,
        plugins=[OpenTelemetryPlugin(add_temporal_spans=True)],
    )

    from temporal_planner.activities.drop import drop
    from temporal_planner.activities.get_state import get_state
    from temporal_planner.activities.move import move
    from temporal_planner.activities.perceive import perceive
    from temporal_planner.activities.pick_up import pick_up
    from temporal_planner.activities.plan import plan
    from temporal_planner.workflows.achieve import AchieveWorkflow

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AchieveWorkflow],
        activities=[get_state, plan, perceive, move, pick_up, drop],
    )
    print(f"Worker started, listening on task queue: {TASK_QUEUE}")
    print(f"  Temporal: {TEMPORAL_ADDRESS}")
    print(f"  OTLP:    {OTEL_ENDPOINT}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
