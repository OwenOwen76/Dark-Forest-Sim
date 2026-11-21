import pytest

from dark_forest_sim.engine.scheduler import CivilizationScheduler
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.civilization import Civilization
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.registry import NarratorToolbox


@pytest.fixture
def toolbox():
    universe = Universe()
    scheduler = CivilizationScheduler()
    return NarratorToolbox(universe, scheduler), universe


def test_narrator_exposes_only_five_tools(toolbox):
    tools, _ = toolbox
    names = {tool["name"] for tool in tools.list_tools()}

    assert names == {
        "manage_civilization",
        "manage_event",
        "manage_simulation",
        "query_universe",
        "calculate",
    }


def test_operation_fields_are_selectable(toolbox):
    tools, _ = toolbox
    definitions = {
        tool["name"]: tool["parameters"]
        for tool in tools.list_tools()
    }

    expected = {
        "manage_civilization": {
            "create",
            "modify",
            "update_state",
            "destroy",
        },
        "manage_event": {
            "create",
            "propagate",
        },
        "manage_simulation": {
            "advance_time",
            "advance_when_idle",
            "sleep",
            "wake",
        },
        "query_universe": {
            "universe_status",
            "list_civilizations",
            "inspect_civilization",
            "list_events",
            "inspect_event",
            "list_deliveries",
            "event_knowledge",
        },
        "calculate": {
            "distance",
            "travel_time",
            "signal_detection_range",
            "waste_heat_power",
            "infrared_detection_range",
            "cooling_duration",
            "signal_travel_time",
            "signal_arrival_time",
            "lorentz_factor",
            "relativistic_travel_time",
            "proper_travel_time",
            "relativistic_kinetic_energy",
            "relativistic_momentum",
            "kardashev_energy_output",
            "population_after_growth",
            "energy_budget",
            "technology_breakthrough",
        },
    }

    for name, operations in expected.items():
        assert set(
            definitions[name]["properties"]["operation"]["enum"]
        ) == operations


def test_create_civilization(toolbox):
    tools, universe = toolbox

    result = tools.call(
        "manage_civilization",
        {
            "operation": "create",
            "civilization_id": "humanity",
            "name": "Humanity",
            "x": 0,
            "y": 0,
            "z": 0,
            "year": 2026,
        },
    )

    assert result["ok"] is True
    assert universe.get_civilization("humanity").name == "Humanity"


def test_update_civilization_state(toolbox):
    tools, universe = toolbox

    universe.add_civilization(
        Civilization(
            id="humanity",
            name="Humanity",
            position=Position(0, 0, 0),
            year=2026,
        )
    )

    result = tools.call(
        "manage_civilization",
        {
            "operation": "update_state",
            "civilization_id": "humanity",
            "demographics": {
                "population": 8_000_000_000,
                "annual_population_growth_rate": 0.01,
            },
            "energy": {
                "energy_production_watts": 1e15,
                "energy_reserve_joules": 1e25,
                "energy_consumption_watts_per_person": 10_000,
            },
        },
    )

    assert result["ok"] is True

    state = universe.get_civilization("humanity").state

    assert state.demographics.population == 8_000_000_000
    assert state.energy.energy_production_watts == 1e15


def test_state_update_can_change_one_field(toolbox):
    tools, universe = toolbox

    universe.add_civilization(
        Civilization(
            id="humanity",
            name="Humanity",
            position=Position(0, 0, 0),
            year=2026,
        )
    )

    result = tools.call(
        "manage_civilization",
        {
            "operation": "update_state",
            "civilization_id": "humanity",
            "demographics": {
                "population": 200,
            },
        },
    )

    assert result["ok"] is True

    state = universe.get_civilization("humanity").state
    assert state.demographics.population == 200


def test_physically_unusual_state_update_is_allowed(toolbox):
    tools, universe = toolbox

    universe.add_civilization(
        Civilization(
            id="humanity",
            name="Humanity",
            position=Position(0, 0, 0),
            year=2026,
        )
    )

    result = tools.call(
        "manage_civilization",
        {
            "operation": "update_state",
            "civilization_id": "humanity",
            "demographics": {
                "population": -100,
            },
            "energy": {
                "energy_production_watts": -500,
            },
        },
    )

    assert result["ok"] is True

    state = universe.get_civilization("humanity").state

    assert state.demographics.population == -100
    assert state.energy.energy_production_watts == -500


def test_invalid_state_update_does_not_partially_mutate(toolbox):
    tools, universe = toolbox

    universe.add_civilization(
        Civilization(
            id="humanity",
            name="Humanity",
            position=Position(0, 0, 0),
            year=2026,
        )
    )

    result = tools.call(
        "manage_civilization",
        {
            "operation": "update_state",
            "civilization_id": "humanity",
            "demographics": {
                "population": 200,
            },
            "energy": {
                "unknown_field": 10,
            },
        },
    )

    assert result["ok"] is False

    state = universe.get_civilization("humanity").state

    assert state.demographics.population == 0
    assert state.energy.energy_production_watts == 0


def test_empty_state_update_is_rejected(toolbox):
    tools, universe = toolbox

    universe.add_civilization(
        Civilization(
            id="humanity",
            name="Humanity",
            position=Position(0, 0, 0),
            year=2026,
        )
    )

    result = tools.call(
        "manage_civilization",
        {
            "operation": "update_state",
            "civilization_id": "humanity",
        },
    )

    assert result["ok"] is False


def test_invalid_operation_is_rejected(toolbox):
    tools, _ = toolbox

    result = tools.call(
        "manage_civilization",
        {
            "operation": "invent_a_command",
            "civilization_id": "humanity",
        },
    )

    assert result["ok"] is False


def test_irrelevant_arguments_are_rejected(toolbox):
    tools, _ = toolbox

    result = tools.call(
        "manage_civilization",
        {
            "operation": "destroy",
            "civilization_id": "humanity",
            "population": 100,
        },
    )

    assert result["ok"] is False

def test_query_civilization_includes_state(toolbox):
    tools, universe = toolbox
    universe.add_civilization(
        Civilization(
            id="humanity",
            name="Humanity",
            position=Position(0, 0, 0),
            year=2026,
        )
    )

    result = tools.call(
        "query_universe",
        {
            "operation": "inspect_civilization",
            "civilization_id": "humanity",
        },
    )

    assert result["ok"] is True

    state = result["result"]["state"]

    assert state["demographics"]["population"] == 0
    assert state["energy"]["energy_production_watts"] == 0


def test_calculate_dispatches_to_distance(toolbox):
    tools, _ = toolbox

    result = tools.call(
        "calculate",
        {
            "operation": "distance",
            "x1": 0,
            "y1": 0,
            "z1": 0,
            "x2": 3,
            "y2": 4,
            "z2": 0,
        },
    )

    assert result["ok"] is True
    assert result["result"] == 5


def test_world_mutations_trigger_persistence(toolbox):
    tools, _ = toolbox
    calls = []
    tools._on_change = lambda: calls.append(True)

    result = tools.call(
        "manage_civilization",
        {
            "operation": "create",
            "civilization_id": "humanity",
            "name": "Humanity",
            "x": 0,
            "y": 0,
            "z": 0,
            "year": 2026,
        },
    )

    assert result["ok"] is True
    assert len(calls) == 1


def test_read_only_queries_do_not_trigger_persistence(toolbox):
    tools, _ = toolbox
    calls = []
    tools._on_change = lambda: calls.append(True)

    result = tools.call(
        "query_universe",
        {"operation": "universe_status"},
    )

    assert result["ok"] is True
    assert calls == []
