import pytest

from dark_forest_sim.engine.scheduler import CivilizationScheduler
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.registry import NarratorToolbox


def make_toolbox(on_change=None):
    universe = Universe()
    scheduler = CivilizationScheduler()

    toolbox = NarratorToolbox(
        universe,
        scheduler,
        on_change=on_change,
    )

    return toolbox, universe, scheduler


def call(toolbox, tool, operation, **arguments):
    return toolbox.call(
        tool,
        {
            "operation": operation,
            **arguments,
        },
    )


def create_civilization(toolbox, civilization_id="civ-1"):
    return call(
        toolbox,
        "manage_civilization",
        "create",
        civilization_id=civilization_id,
        name="Test Civilization",
        x=0,
        y=0,
        z=0,
        year=100,
    )


# ---------------------------------------------------------------------
# Consolidated tool interface
# ---------------------------------------------------------------------


def test_only_five_consolidated_tools_are_registered():
    toolbox, _, _ = make_toolbox()

    names = {tool["name"] for tool in toolbox.list_tools()}

    assert names == {
        "manage_civilization",
        "manage_event",
        "manage_simulation",
        "query_universe",
        "calculate",
    }


def test_all_tools_have_openai_compatible_definitions():
    toolbox, _, _ = make_toolbox()

    definitions = toolbox.get_definitions()

    assert len(definitions) == 5

    for definition in definitions:
        assert definition["type"] == "function"
        assert "name" in definition["function"]
        assert "description" in definition["function"]
        assert "parameters" in definition["function"]


def test_each_tool_has_an_operation_selector():
    toolbox, _, _ = make_toolbox()

    for tool in toolbox.list_tools():
        operation = tool["parameters"]["properties"]["operation"]

        assert operation["type"] == "string"
        assert isinstance(operation["enum"], list)
        assert operation["enum"]


def test_operation_schemas_are_exposed_for_gui_use():
    toolbox, _, _ = make_toolbox()

    for tool in toolbox.list_tools():
        assert "operations" in tool

        operation_names = {
            operation["name"]
            for operation in tool["operations"]
        }

        assert operation_names == set(
            tool["parameters"]["properties"]["operation"]["enum"]
        )


def test_invalid_operation_is_rejected():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "not_a_real_operation",
    )

    assert result["ok"] is False


def test_missing_operation_is_rejected():
    toolbox, _, _ = make_toolbox()

    result = toolbox.call("calculate", {})

    assert result["ok"] is False


def test_irrelevant_arguments_are_rejected():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "distance",
        x1=0,
        y1=0,
        z1=0,
        x2=3,
        y2=4,
        z2=0,
        civilization_id="unexpected",
    )

    assert result["ok"] is False


# ---------------------------------------------------------------------
# Event knowledge and light-cone calculations
# ---------------------------------------------------------------------


def test_event_knowledge_is_unavailable_before_arrival():
    toolbox, _, _ = make_toolbox()

    assert create_civilization(toolbox)["ok"] is True

    event = call(
        toolbox,
        "manage_event",
        "create",
        event_id="event-1",
        event_type="signal",
        created_at=0,
        description="Test signal",
        x=0,
        y=0,
        z=0,
        propagation_speed=1,
        target_civilization_ids=["civ-1"],
    )

    assert event["ok"] is True

    propagation = call(
        toolbox,
        "manage_event",
        "propagate",
        event_id="event-1",
    )

    assert propagation["ok"] is True

    knowledge = call(
        toolbox,
        "query_universe",
        "event_knowledge",
        event_id="event-1",
        civilization_id="civ-1",
    )

    assert knowledge["ok"] is True
    assert knowledge["result"] is False


def test_event_knowledge_becomes_available_after_arrival():
    toolbox, _, _ = make_toolbox()

    assert create_civilization(toolbox)["ok"] is True

    assert call(
        toolbox,
        "manage_event",
        "create",
        event_id="event-1",
        event_type="signal",
        created_at=0,
        description="Test signal",
        x=0,
        y=0,
        z=0,
        propagation_speed=1,
        target_civilization_ids=["civ-1"],
    )["ok"] is True

    assert call(
        toolbox,
        "manage_event",
        "propagate",
        event_id="event-1",
    )["ok"] is True

    assert call(
        toolbox,
        "manage_simulation",
        "advance_time",
        to_time=0,
    )["ok"] is True

    knowledge = call(
        toolbox,
        "query_universe",
        "event_knowledge",
        event_id="event-1",
        civilization_id="civ-1",
    )

    assert knowledge["ok"] is True
    assert knowledge["result"] is True


def test_signal_travel_time():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "signal_travel_time",
        distance_light_years=4,
        speed_fraction_of_c=0.5,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(8)


def test_signal_arrival_time():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "signal_arrival_time",
        departure_time=10,
        distance_light_years=4,
        speed_fraction_of_c=0.5,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(18)


# ---------------------------------------------------------------------
# Physics, stealth, sensors, and thermodynamics
# ---------------------------------------------------------------------


def test_signal_detection_range():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "signal_detection_range",
        signal_power_at_1_ly=100,
        background_noise=1,
        detection_threshold=4,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(5)


def test_waste_heat_power():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "waste_heat_power",
        energy_joules=1000,
        waste_heat_fraction=0.5,
        duration_seconds=10,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(50)


def test_infrared_detection_range():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "infrared_detection_range",
        heat_power_watts=1e20,
        detection_threshold_watts_per_square_meter=1e-10,
    )

    assert result["ok"] is True
    assert result["result"] > 0


def test_cooling_duration():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "cooling_duration",
        energy_joules=1000,
        waste_heat_fraction=0.5,
        cooling_power_watts=10,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(50)


def test_invalid_physics_input_is_rejected():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "signal_travel_time",
        distance_light_years=10,
        speed_fraction_of_c=0,
    )

    assert result["ok"] is False


# ---------------------------------------------------------------------
# Economics and technology
# ---------------------------------------------------------------------


def test_kardashev_energy_output():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "kardashev_energy_output",
        kardashev_scale=0,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(1e6)


def test_population_growth():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "population_after_growth",
        population=1000,
        annual_growth_rate=0.1,
        years=2,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(1210)


def test_energy_budget():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "energy_budget",
        population=100,
        energy_production_watts=1500,
        energy_consumption_watts_per_person=10,
    )

    assert result["ok"] is True

    budget = result["result"]

    assert budget["total_demand_watts"] == pytest.approx(1000)
    assert budget["surplus_watts"] == pytest.approx(500)
    assert budget["deficit_watts"] == pytest.approx(0)


def test_technology_breakthrough():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "technology_breakthrough",
        minor_probability=0.2,
        major_probability=0.1,
        revolutionary_probability=0.05,
        seed=42,
    )

    assert result["ok"] is True
    assert result["result"]["outcome"] in {
        "minor",
        "major",
        "revolutionary",
        "none",
    }


def test_invalid_economic_input_is_rejected():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "population_after_growth",
        population=1000,
        annual_growth_rate=-1,
        years=10,
    )

    assert result["ok"] is False


# ---------------------------------------------------------------------
# Relativistic calculations
# ---------------------------------------------------------------------


def test_lorentz_factor():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "lorentz_factor",
        speed_fraction_of_c=0.6,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(1.25)


def test_relativistic_travel_time():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "relativistic_travel_time",
        distance_light_years=10,
        speed_fraction_of_c=0.8,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(12.5)


def test_proper_travel_time():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "proper_travel_time",
        distance_light_years=10,
        speed_fraction_of_c=0.8,
    )

    assert result["ok"] is True
    assert result["result"] == pytest.approx(7.5)


def test_relativistic_kinetic_energy():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "relativistic_kinetic_energy",
        mass_kg=1000,
        speed_fraction_of_c=0.8,
    )

    assert result["ok"] is True
    assert result["result"] > 0


def test_relativistic_momentum():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "relativistic_momentum",
        mass_kg=1000,
        speed_fraction_of_c=0.8,
    )

    assert result["ok"] is True
    assert result["result"] > 0


def test_invalid_relativistic_speed_is_rejected():
    toolbox, _, _ = make_toolbox()

    result = call(
        toolbox,
        "calculate",
        "lorentz_factor",
        speed_fraction_of_c=1,
    )

    assert result["ok"] is False


# ---------------------------------------------------------------------
# Persistence behavior
# ---------------------------------------------------------------------


def test_world_mutations_trigger_persistence_callback():
    changes = []

    toolbox, _, _ = make_toolbox(
        on_change=lambda: changes.append(True)
    )

    result = create_civilization(toolbox)

    assert result["ok"] is True
    assert len(changes) == 1


def test_read_only_queries_do_not_trigger_persistence():
    changes = []

    toolbox, _, _ = make_toolbox(
        on_change=lambda: changes.append(True)
    )

    create_civilization(toolbox)
    changes.clear()

    result = call(
        toolbox,
        "query_universe",
        "list_civilizations",
    )

    assert result["ok"] is True
    assert changes == []


def test_failed_world_mutation_does_not_trigger_persistence():
    changes = []

    toolbox, _, _ = make_toolbox(
        on_change=lambda: changes.append(True)
    )

    result = call(
        toolbox,
        "manage_civilization",
        "create",
        civilization_id="",
        name="Invalid",
        x=0,
        y=0,
        z=0,
        year=100,
    )

    assert result["ok"] is False
    assert changes == []
