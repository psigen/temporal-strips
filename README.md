# temporal-strips

AI planning with [unified-planning](https://github.com/aiplan4eu/unified-planning) executed as [Temporal](https://temporal.io) workflows. A robot logistics domain demonstrates how an AI planner can drive workflow orchestration to achieve goal states.

## Architecture

```
Client (client.py)
  |  PlanRequest (goals only)
  v
Temporal Dev Server (:7233 gRPC, :8233 UI)
  |
  v
Worker ──> OTel traces ──> Tempo (:4317) ──> Grafana (:3000)
  |
  v
AchieveWorkflow (re-plans after every action)
  ├── get_state   → query current world state
  ├── plan        → unified-planning solver generates action sequence
  └── execute     → perceive / move / pick_up / drop
  └── loop until goals met
```

The workflow queries current state, invokes the planner, executes only the first planned action, then re-plans from the new state. This loop continues until all goals are satisfied.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (for Temporal, Tempo, Grafana)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python 3.12+
- Java runtime (for the Tamer solver -- optional, pyperplan works as a fallback)
- [Tilt](https://tilt.dev/) (optional, for dev dashboard)

## Quick Start

### With Docker Compose

```bash
# Start infrastructure (Temporal, Tempo, Grafana, Worker)
docker compose up -d

# Run a workflow
uv sync
uv run python -m temporal_strips.client --scenario delivery
```

### With Tilt (recommended for development)

```bash
tilt up
# Use the Tilt dashboard buttons to trigger workflows
```

### Local worker (for debugging)

```bash
# Start only infrastructure
docker compose up -d temporal tempo grafana

# Install deps and run worker locally
uv sync
uv run python -m temporal_strips.worker

# In another terminal, run a workflow
uv run python -m temporal_strips.client --scenario delivery
```

## Scenarios

| Scenario | Description | Goals |
|----------|-------------|-------|
| `delivery` | 1 robot, 1 package, 3 locations | Deliver pkg1 to store |
| `multi` | 1 robot, 2 packages, 4 locations | Deliver pkg1 to dock, pkg2 to store |

## Domain

The logistics domain models a warehouse robot that must:

1. **perceive** locations to discover what packages are there (objects start unobservable)
2. **move** between connected locations
3. **pick_up** visible packages
4. **drop** packages at target locations

The unified-planning library constructs the planning problem and the Tamer solver finds a valid action sequence.

## Observability

- **Temporal UI**: http://localhost:8233 -- workflow execution history, activity details
- **Grafana**: http://localhost:3000 -- Explore > Tempo datasource > search traces
- All workflow and activity executions are traced via OpenTelemetry

## Project Structure

```
├── compose.yaml              # Temporal + Tempo + Grafana + Worker
├── Dockerfile                # Worker container image
├── Tiltfile                  # Tilt dev dashboard
├── docker/                   # Infrastructure config (Tempo, Grafana)
├── src/temporal_strips/     # Python package (src layout)
│   ├── models.py             # Shared dataclasses (PlanRequest, Action, etc.)
│   ├── domain/
│   │   ├── definition.py     # Unified-planning problem construction
│   │   └── state.py          # Dict-based state transforms
│   ├── activities/
│   │   ├── get_state.py      # Query current world state
│   │   ├── plan.py           # Invoke UP solver
│   │   ├── perceive.py       # Perceive a location
│   │   ├── move.py           # Move robot
│   │   ├── pick_up.py        # Pick up package
│   │   └── drop.py           # Drop package
│   ├── workflows/
│   │   └── achieve.py        # AchieveWorkflow: plan-execute loop
│   ├── worker.py             # Worker entry point + OTel setup
│   └── client.py             # Start workflows with scenarios
└── tests/                    # Serialization and state tests
```

## Running Tests

```bash
uv run pytest
```

## Solver Backends

The project installs multiple unified-planning solver backends:

| Solver | Package | Requires | Temporal Planning |
|--------|---------|----------|-------------------|
| Tamer | `unified-planning[tamer]` | Java | Yes |
| LPG | `up-lpg` | None (prebuilt binary) | Yes |
| Pyperplan | bundled | None (pure Python) | No (classical only) |

The planner auto-selects the best available solver for the problem type.
