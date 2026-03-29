"""Tests for models.py: fluent encoding/decoding and dataclass construction."""

from temporal_strips.models import (
    Action,
    ActionInput,
    ActionResult,
    PlanRequest,
    PlanResult,
    WorldState,
    decode_fluent,
    encode_fluent,
)


class TestEncodeFluent:
    def test_no_params(self):
        assert encode_fluent("light", []) == "light"

    def test_single_param(self):
        assert encode_fluent("observed", ["warehouse"]) == "observed(warehouse)"

    def test_two_params(self):
        assert (
            encode_fluent("robot_at", ["robot1", "warehouse"])
            == "robot_at(robot1, warehouse)"
        )

    def test_three_params(self):
        result = encode_fluent("between", ["a", "b", "c"])
        assert result == "between(a, b, c)"


class TestDecodeFluent:
    def test_no_params(self):
        name, params = decode_fluent("light")
        assert name == "light"
        assert params == []

    def test_single_param(self):
        name, params = decode_fluent("observed(warehouse)")
        assert name == "observed"
        assert params == ["warehouse"]

    def test_two_params(self):
        name, params = decode_fluent("robot_at(robot1, warehouse)")
        assert name == "robot_at"
        assert params == ["robot1", "warehouse"]

    def test_round_trip(self):
        original = "package_at(pkg1, dock)"
        name, params = decode_fluent(original)
        assert encode_fluent(name, params) == original

    def test_round_trip_no_params(self):
        name, params = decode_fluent("flag")
        assert encode_fluent(name, params) == "flag"


class TestDataclasses:
    def test_plan_request(self):
        req = PlanRequest(
            objects={"robot1": "Robot"},
            goals={"robot_at(robot1, store)": True},
        )
        assert req.objects["robot1"] == "Robot"
        assert req.goals["robot_at(robot1, store)"] is True

    def test_world_state(self):
        ws = WorldState(
            objects={"robot1": "Robot"},
            fluents={"hands_free(robot1)": True, "battery": 0.95},
        )
        assert ws.fluents["battery"] == 0.95

    def test_action(self):
        a = Action(action_name="move", parameters={"r": "robot1", "from_loc": "a", "to_loc": "b"})
        assert a.action_name == "move"
        assert a.parameters["from_loc"] == "a"

    def test_plan_result_defaults(self):
        pr = PlanResult(success=True)
        assert pr.actions == []
        assert pr.error == ""

    def test_action_input(self):
        ai = ActionInput(
            state={"robot_at(robot1, warehouse)": True},
            parameters={"r": "robot1", "l": "warehouse"},
        )
        assert ai.state["robot_at(robot1, warehouse)"] is True

    def test_action_result_defaults(self):
        ar = ActionResult(success=False)
        assert ar.updated_state == {}
        assert ar.description == ""
