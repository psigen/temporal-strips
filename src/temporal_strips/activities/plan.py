"""Activity that invokes the unified-planning solver to generate a plan."""

from __future__ import annotations

from temporalio import activity

from temporal_strips.models import Action, PlanInput, PlanResult


@activity.defn(name="plan")
async def plan(input: PlanInput) -> PlanResult:
    """Generate a plan from current state to goals using unified-planning."""
    activity.logger.info(
        "Planning with %d fluents toward %d goals",
        len(input.state.fluents),
        len(input.goals),
    )

    try:
        # Import UP only inside the activity (not at module level)
        # to avoid issues with Temporal workflow sandbox
        import unified_planning.engines.results as results
        from unified_planning.shortcuts import OneshotPlanner

        from temporal_strips.domain.definition import build_problem

        problem = build_problem(input.state, input.goals)
        activity.logger.info("Problem constructed: %s", problem.name)

        with OneshotPlanner(problem_kind=problem.kind) as planner:
            result = planner.solve(problem) # type: ignore

        if result.status not in results.POSITIVE_OUTCOMES:
            return PlanResult(
                success=False,
                error=f"Planner returned status: {result.status.name}",
            )

        actions: list[Action] = []
        for action_instance in result.plan.actions:
            action_name = action_instance.action.name
            param_names = [p.name for p in action_instance.action.parameters]
            param_values = [str(p) for p in action_instance.actual_parameters]
            parameters = dict(zip(param_names, param_values))

            # Handle perceive_<pkg>_at_<loc> synthetic actions:
            # extract the location from the action name and add it to params
            if action_name.startswith("perceive_") and "_at_" in action_name:
                loc = action_name.split("_at_", 1)[1]
                parameters["l"] = loc
                actions.append(Action(action_name="perceive", parameters=parameters))
            else:
                actions.append(Action(action_name=action_name, parameters=parameters))

        activity.logger.info("Plan found with %d actions", len(actions))
        return PlanResult(success=True, actions=actions)

    except Exception as e:
        activity.logger.error("Planning failed: %s", e)
        return PlanResult(success=False, error=str(e))
