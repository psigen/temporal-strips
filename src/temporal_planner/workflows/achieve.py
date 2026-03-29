"""AchieveWorkflow: re-plan and execute loop until goals are met."""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from temporal_planner.activities.drop import drop
    from temporal_planner.activities.get_state import get_state
    from temporal_planner.activities.move import move
    from temporal_planner.activities.perceive import perceive
    from temporal_planner.activities.pick_up import pick_up
    from temporal_planner.activities.plan import plan
    from temporal_planner.domain.state import check_goals
    from temporal_planner.models import (
        ActionInput,
        ActionResult,
        PlanInput,
        PlanRequest,
        WorldState,
    )

ACTIVITY_TIMEOUT = timedelta(seconds=10)
PLAN_TIMEOUT = timedelta(seconds=60)
MAX_ITERATIONS = 50

# Map action names to their activity functions
ACTION_ACTIVITIES = {
    "perceive": perceive,
    "move": move,
    "pick_up": pick_up,
    "drop": drop,
}


@workflow.defn(name="AchieveWorkflow")
class AchieveWorkflow:
    @workflow.run
    async def run(self, request: PlanRequest) -> dict:
        goals = request.goals

        # Get initial world state via activity
        workflow.logger.info("Querying initial world state")
        world_state: WorldState = await workflow.execute_activity(
            get_state,
            request,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
        )
        current_state = world_state.fluents
        steps_executed = 0

        for iteration in range(MAX_ITERATIONS):
            if check_goals(current_state, goals):
                workflow.logger.info(
                    "Goals achieved after %d steps", steps_executed
                )
                return {
                    "success": True,
                    "steps": steps_executed,
                    "final_state": current_state,
                }

            # Re-plan from current state
            plan_input = PlanInput(
                state=WorldState(objects=request.objects, fluents=current_state),
                goals=goals,
            )
            plan_result = await workflow.execute_activity(
                plan,
                plan_input,
                start_to_close_timeout=PLAN_TIMEOUT,
            )

            if not plan_result.success or not plan_result.actions:
                workflow.logger.error("Planning failed: %s", plan_result.error)
                return {
                    "success": False,
                    "error": plan_result.error or "No actions in plan",
                    "steps": steps_executed,
                    "final_state": current_state,
                }

            # Execute only the FIRST action from the plan
            action = plan_result.actions[0]
            workflow.logger.info(
                "Step %d: executing %s(%s)",
                steps_executed + 1,
                action.action_name,
                action.parameters,
            )

            activity_fn = ACTION_ACTIVITIES.get(action.action_name)
            if activity_fn is None:
                return {
                    "success": False,
                    "error": f"Unknown action: {action.action_name}",
                    "steps": steps_executed,
                    "final_state": current_state,
                }

            action_result: ActionResult = await workflow.execute_activity(
                activity_fn,
                ActionInput(state=current_state, parameters=action.parameters),
                start_to_close_timeout=ACTIVITY_TIMEOUT,
            )

            if not action_result.success:
                workflow.logger.error(
                    "Action failed: %s", action_result.description
                )
                return {
                    "success": False,
                    "error": f"Action {action.action_name} failed: {action_result.description}",
                    "steps": steps_executed,
                    "final_state": current_state,
                }

            current_state = action_result.updated_state
            steps_executed += 1
            workflow.logger.info("Step %d complete: %s", steps_executed, action_result.description)

        return {
            "success": False,
            "error": "Max iterations reached",
            "steps": steps_executed,
            "final_state": current_state,
        }
