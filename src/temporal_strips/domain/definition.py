"""Build a unified-planning Problem from a WorldState and goals dict."""

from __future__ import annotations

from unified_planning.shortcuts import (
    BoolType,
    Fluent,
    InstantaneousAction,
    Not,
    Object,
    Problem,
    UserType,
)

from temporal_strips.models import FluentValue, WorldState, decode_fluent


def build_problem(
    state: WorldState, goals: dict[str, FluentValue]
) -> Problem:
    """Construct a UP Problem from current world state and goal specification."""
    problem = Problem("logistics")

    # --- Types ---
    location_type = UserType("Location")
    robot_type = UserType("Robot")
    package_type = UserType("Package")

    type_map = {
        "Location": location_type,
        "Robot": robot_type,
        "Package": package_type,
    }

    # --- Objects ---
    objects: dict[str, Object] = {}
    for obj_name, obj_type_name in state.objects.items():
        up_type = type_map[obj_type_name]
        obj = Object(obj_name, up_type)
        objects[obj_name] = obj
        problem.add_object(obj)

    # --- Fluents ---
    robot_at = Fluent("robot_at", BoolType(), r=robot_type, l=location_type)
    package_at = Fluent("package_at", BoolType(), p=package_type, l=location_type)
    holding = Fluent("holding", BoolType(), r=robot_type, p=package_type)
    connected = Fluent("connected", BoolType(), l1=location_type, l2=location_type)
    hands_free = Fluent("hands_free", BoolType(), r=robot_type)
    observed = Fluent("observed", BoolType(), l=location_type)
    visible = Fluent("visible", BoolType(), p=package_type, l=location_type)

    for f in [robot_at, package_at, holding, connected, hands_free, observed, visible]:
        problem.add_fluent(f)

    # --- Actions ---

    # perceive(r, l): robot perceives a location, revealing what's there
    perceive = InstantaneousAction("perceive", r=robot_type, l=location_type)
    r_param, l_param = perceive.parameter("r"), perceive.parameter("l")
    perceive.add_precondition(robot_at(r_param, l_param))
    perceive.add_effect(observed(l_param), True)
    problem.add_action(perceive)

    # move(r, from_loc, to_loc)
    move = InstantaneousAction(
        "move", r=robot_type, from_loc=location_type, to_loc=location_type
    )
    r_p = move.parameter("r")
    from_p = move.parameter("from_loc")
    to_p = move.parameter("to_loc")
    move.add_precondition(robot_at(r_p, from_p))
    move.add_precondition(connected(from_p, to_p))
    move.add_effect(robot_at(r_p, from_p), False)
    move.add_effect(robot_at(r_p, to_p), True)
    problem.add_action(move)

    # pick_up(r, p, l): requires visibility (must have perceived)
    pick_up = InstantaneousAction(
        "pick_up", r=robot_type, p=package_type, l=location_type
    )
    r_p = pick_up.parameter("r")
    p_p = pick_up.parameter("p")
    l_p = pick_up.parameter("l")
    pick_up.add_precondition(robot_at(r_p, l_p))
    pick_up.add_precondition(visible(p_p, l_p))
    pick_up.add_precondition(hands_free(r_p))
    pick_up.add_effect(holding(r_p, p_p), True)
    pick_up.add_effect(visible(p_p, l_p), False)
    pick_up.add_effect(hands_free(r_p), False)
    problem.add_action(pick_up)

    # drop(r, p, l)
    drop = InstantaneousAction(
        "drop", r=robot_type, p=package_type, l=location_type
    )
    r_p = drop.parameter("r")
    p_p = drop.parameter("p")
    l_p = drop.parameter("l")
    drop.add_precondition(robot_at(r_p, l_p))
    drop.add_precondition(holding(r_p, p_p))
    drop.add_effect(holding(r_p, p_p), False)
    drop.add_effect(package_at(p_p, l_p), True)
    drop.add_effect(visible(p_p, l_p), True)
    drop.add_effect(hands_free(r_p), True)
    problem.add_action(drop)

    # --- perceive visibility effects ---
    # UP doesn't support conditional effects well, so we add per-object
    # perceive actions for each package at each location where package_at is true.
    # These are additional "perceive_<pkg>_<loc>" actions.
    _add_perceive_visibility_actions(
        problem, state, objects, robot_type, package_type, location_type,
        robot_at, package_at, visible, observed,
    )

    # --- Initial State ---
    _set_initial_state(problem, state, objects, {
        "robot_at": robot_at,
        "package_at": package_at,
        "holding": holding,
        "connected": connected,
        "hands_free": hands_free,
        "observed": observed,
        "visible": visible,
    })

    # --- Goals ---
    _set_goals(problem, goals, objects, {
        "robot_at": robot_at,
        "package_at": package_at,
        "holding": holding,
        "connected": connected,
        "hands_free": hands_free,
        "observed": observed,
        "visible": visible,
    })

    return problem


def _add_perceive_visibility_actions(
    problem: Problem,
    state: WorldState,
    objects: dict[str, Object],
    robot_type: UserType,
    package_type: UserType,
    location_type: UserType,
    robot_at: Fluent,
    package_at: Fluent,
    visible: Fluent,
    observed: Fluent,
) -> None:
    """Add per-package perceive actions that set visibility when a package is at a location."""
    # Find all (package, location) pairs where package_at is True
    for key, value in state.fluents.items():
        if not value:
            continue
        name, params = decode_fluent(key)
        if name != "package_at" or len(params) != 2:
            continue
        pkg_name, loc_name = params
        if pkg_name not in objects or loc_name not in objects:
            continue

        pkg_obj = objects[pkg_name]
        loc_obj = objects[loc_name]

        # Create a specific perceive action that also sets visibility for this package
        action_name = f"perceive_{pkg_name}_at_{loc_name}"
        act = InstantaneousAction(action_name, r=robot_type)
        r_p = act.parameter("r")
        act.add_precondition(robot_at(r_p, loc_obj))
        act.add_precondition(package_at(pkg_obj, loc_obj))
        act.add_effect(observed(loc_obj), True)
        act.add_effect(visible(pkg_obj, loc_obj), True)
        problem.add_action(act)


def _set_initial_state(
    problem: Problem,
    state: WorldState,
    objects: dict[str, Object],
    fluents: dict[str, Fluent],
) -> None:
    """Set initial fluent values from the state dict."""
    for key, value in state.fluents.items():
        name, params = decode_fluent(key)
        if name not in fluents:
            continue
        fluent = fluents[name]
        obj_params = []
        for p in params:
            if p in objects:
                obj_params.append(objects[p])
            else:
                obj_params.append(p)
        problem.set_initial_value(fluent(*obj_params), value)

    # Set default False for all fluents not explicitly in the state
    _set_closed_world_defaults(problem, state, objects, fluents)


def _set_closed_world_defaults(
    problem: Problem,
    state: WorldState,
    objects: dict[str, Object],
    fluents: dict[str, Fluent],
) -> None:
    """Apply closed-world assumption: any fluent not explicitly true is false."""
    from itertools import product

    type_to_objects: dict[str, list[Object]] = {}
    for obj in objects.values():
        type_name = obj.type.name
        type_to_objects.setdefault(type_name, []).append(obj)

    for fluent_name, fluent in fluents.items():
        param_types = [p.type for p in fluent.signature]
        if not param_types:
            continue

        param_object_lists = []
        for pt in param_types:
            param_object_lists.append(type_to_objects.get(pt.name, []))

        for combo in product(*param_object_lists):
            from temporal_strips.models import encode_fluent
            key = encode_fluent(fluent_name, [str(o) for o in combo])
            if key not in state.fluents:
                problem.set_initial_value(fluent(*combo), False)


def _set_goals(
    problem: Problem,
    goals: dict[str, FluentValue],
    objects: dict[str, Object],
    fluents: dict[str, Fluent],
) -> None:
    """Set goal fluent values."""
    for key, value in goals.items():
        name, params = decode_fluent(key)
        if name not in fluents:
            continue
        fluent = fluents[name]
        obj_params = []
        for p in params:
            if p in objects:
                obj_params.append(objects[p])
            else:
                obj_params.append(p)
        if value is True:
            problem.add_goal(fluent(*obj_params))
        elif value is False:
            problem.add_goal(Not(fluent(*obj_params)))
