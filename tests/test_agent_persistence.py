import json

from dark_forest_sim.engine.civilization import Civilization
from dark_forest_sim.engine.scheduler import CivilizationScheduler
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.agents import (
    AgentState,
    AgentStatus,
    ToolCallRecord,
    ToolCallStatus,
)
from dark_forest_sim.narrator.persistence import SimulationPersistence


def make_world():
    universe = Universe(current_time=100)

    universe.add_civilization(
        Civilization(
            id="civ-001",
            name="Test Civilization",
            position=Position(1, 2, 3),
            year=100,
        )
    )

    scheduler = CivilizationScheduler()
    scheduler.wake_times["civ-001"] = 200.0

    return universe, scheduler


def test_save_and_load_agent_state(tmp_path):
    persistence = SimulationPersistence(tmp_path / "simulation.json")
    universe, scheduler = make_world()

    agent = AgentState(
        civilization_id="civ-001",
        system_prompt="You are a civilization.",
        messages=[{"role": "assistant", "content": "Hello."}],
        status=AgentStatus.SLEEPING,
        wake_conditions={"year": 200},
    )

    persistence.save(
        universe,
        scheduler,
        {},
        agent_states={"civ-001": agent},
    )

    loaded = persistence.load()
    restored = AgentState.from_dict(
        loaded["agent_states"]["civ-001"]
    )

    assert restored.to_dict() == agent.to_dict()


def test_save_and_load_tool_call_journal(tmp_path):
    persistence = SimulationPersistence(tmp_path / "simulation.json")
    universe, scheduler = make_world()

    record = ToolCallRecord(
        call_id="call-001",
        civilization_id="civ-001",
        tool_name="observe",
        arguments={"target": "nearby"},
        status=ToolCallStatus.COMPLETED,
        result={"count": 5},
        attempts=1,
    )

    persistence.save(
        universe,
        scheduler,
        {},
        tool_call_journal={"call-001": record},
    )

    loaded = persistence.load()
    restored = ToolCallRecord.from_dict(
        loaded["tool_call_journal"]["call-001"]
    )

    assert restored.to_dict() == record.to_dict()


def test_schema_v1_loads_without_agent_data(tmp_path):
    path = tmp_path / "simulation.json"
    persistence = SimulationPersistence(path)
    universe, scheduler = make_world()

    persistence.save(universe, scheduler, {})

    data = json.loads(path.read_text())
    data["schema_version"] = 1
    data.pop("agent_states", None)
    data.pop("tool_call_journal", None)
    path.write_text(json.dumps(data))

    loaded = persistence.load()

    assert loaded["loaded_schema_version"] == 1
    assert loaded["agent_states"] == {}
    assert loaded["tool_call_journal"] == {}


def test_save_preserves_universe_and_scheduler(tmp_path):
    persistence = SimulationPersistence(tmp_path / "simulation.json")
    universe, scheduler = make_world()

    persistence.save(universe, scheduler, {"status": "running"})

    loaded = persistence.load()

    assert loaded["universe"].current_time == 100
    assert loaded["universe"].get_civilization("civ-001").name == (
        "Test Civilization"
    )
    assert loaded["scheduler"].wake_times == {"civ-001": 200.0}
    assert loaded["simulation"]["status"] == "running"


def test_empty_agent_data_is_saved(tmp_path):
    persistence = SimulationPersistence(tmp_path / "simulation.json")
    universe, scheduler = make_world()

    persistence.save(universe, scheduler, {})

    loaded = persistence.load()

    assert loaded["agent_states"] == {}
    assert loaded["tool_call_journal"] == {}
    assert loaded["loaded_schema_version"] == 2
