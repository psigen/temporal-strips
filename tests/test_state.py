"""Tests for domain/state.py: state transformations and goal checking."""

import pytest

from temporal_strips.domain.state import (
    apply_drop,
    apply_move,
    apply_perceive,
    apply_pick_up,
    check_goals,
)


def _base_state() -> dict:
    """A minimal world state for testing."""
    return {
        "robot_at(robot1, warehouse)": True,
        "robot_at(robot1, dock)": False,
        "package_at(pkg1, warehouse)": True,
        "connected(warehouse, dock)": True,
        "connected(dock, warehouse)": True,
        "hands_free(robot1)": True,
        "observed(warehouse)": False,
        "visible(pkg1, warehouse)": False,
    }


class TestCheckGoals:
    def test_goals_met(self):
        state = {"a": True, "b": False, "c": 42}
        goals = {"a": True, "b": False}
        assert check_goals(state, goals) is True

    def test_goals_not_met(self):
        state = {"a": False}
        goals = {"a": True}
        assert check_goals(state, goals) is False

    def test_missing_key(self):
        state = {}
        goals = {"a": True}
        assert check_goals(state, goals) is False

    def test_empty_goals(self):
        assert check_goals({"a": True}, {}) is True


class TestApplyPerceive:
    def test_perceive_reveals_packages(self):
        state = _base_state()
        result = apply_perceive(state, "robot1", "warehouse")
        assert result["observed(warehouse)"] is True
        assert result["visible(pkg1, warehouse)"] is True

    def test_perceive_precondition_failure(self):
        state = _base_state()
        with pytest.raises(ValueError, match="not at"):
            apply_perceive(state, "robot1", "dock")

    def test_perceive_no_packages(self):
        state = _base_state()
        state["robot_at(robot1, dock)"] = True
        state["robot_at(robot1, warehouse)"] = False
        result = apply_perceive(state, "robot1", "dock")
        assert result["observed(dock)"] is True


class TestApplyMove:
    def test_move_success(self):
        state = _base_state()
        result = apply_move(state, "robot1", "warehouse", "dock")
        assert result["robot_at(robot1, warehouse)"] is False
        assert result["robot_at(robot1, dock)"] is True

    def test_move_not_at_location(self):
        state = _base_state()
        with pytest.raises(ValueError, match="not at"):
            apply_move(state, "robot1", "dock", "warehouse")

    def test_move_not_connected(self):
        state = _base_state()
        state["robot_at(robot1, warehouse)"] = True
        with pytest.raises(ValueError, match="not connected"):
            apply_move(state, "robot1", "warehouse", "store")


class TestApplyPickUp:
    def test_pick_up_success(self):
        state = _base_state()
        state["visible(pkg1, warehouse)"] = True
        result = apply_pick_up(state, "robot1", "pkg1", "warehouse")
        assert result["holding(robot1, pkg1)"] is True
        assert result["visible(pkg1, warehouse)"] is False
        assert result["hands_free(robot1)"] is False

    def test_pick_up_not_visible(self):
        state = _base_state()
        with pytest.raises(ValueError, match="not visible"):
            apply_pick_up(state, "robot1", "pkg1", "warehouse")

    def test_pick_up_hands_not_free(self):
        state = _base_state()
        state["visible(pkg1, warehouse)"] = True
        state["hands_free(robot1)"] = False
        with pytest.raises(ValueError, match="hands not free"):
            apply_pick_up(state, "robot1", "pkg1", "warehouse")


class TestApplyDrop:
    def test_drop_success(self):
        state = _base_state()
        state["holding(robot1, pkg1)"] = True
        state["hands_free(robot1)"] = False
        result = apply_drop(state, "robot1", "pkg1", "warehouse")
        assert result["holding(robot1, pkg1)"] is False
        assert result["package_at(pkg1, warehouse)"] is True
        assert result["visible(pkg1, warehouse)"] is True
        assert result["hands_free(robot1)"] is True

    def test_drop_not_holding(self):
        state = _base_state()
        with pytest.raises(ValueError, match="not holding"):
            apply_drop(state, "robot1", "pkg1", "warehouse")

    def test_drop_not_at_location(self):
        state = _base_state()
        state["holding(robot1, pkg1)"] = True
        with pytest.raises(ValueError, match="not at"):
            apply_drop(state, "robot1", "pkg1", "dock")
