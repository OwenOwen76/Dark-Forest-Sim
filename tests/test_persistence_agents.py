import json

from dark_forest_sim.engine.scheduler import CivilizationScheduler
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.agents import (
    AgentState,
    AgentStatus,
    ToolCallRecord,
    ToolCallStatus,
)
from dark_forest_sim.narrator.persistence import SimulationPersistence


def test_save_and_load_agent_states(tmp_path):
    persistence = SimulationPersistence(tmp_path / "simulation.json")
    universe = Universe(current_time=0)
    scheduler = CivilizationScheduler()

    agent = AgentState(
        civilization_id="civ-001",
        system_prompt="You are an autonomous civilization.",
        messages=[
            {"role": "user", "content": "Observe the universe."},
            {"role": "assistant", "content": "Beginning observation."},
        ],
        status=AgentStatus.SLEEPING,
        wake_conditions={"years": 100},
    )

    persistence.save(
        universe,
        scheduler,
        {},
        agent_states={"civ-001": agent},
    )

    loaded = persistence.load()

    assert loaded["agent_states"]["civ-001"] == agent.to_dict()


def test_save_and_load_tool_call_journal(tmp_path):
    persistence = SimulationPersistence(tmp_path / "simulation.json")
    universe = Universe(current_time=0)
    scheduler = CivilizationScheduler()

    record = ToolCallRecord(
        call_id="call-001",
        civilization_id="civ-001",
        tool_name="observe",
        arguments={"target": "nearby_stars"},
        status=ToolCallStatus.COMPLETED,
        result={"observations": 12},
        attempts=1,
    )

    persistence.save(
        universe,
        scheduler,
        {},
        tool_call_journal={"call-001": record},
    )

    loaded = persistence.load()

    assert loaded["tool_call_journal"]["call-001"] == record.to_dict()


def test_save_and_load_both_agent_records(tmp_path):
    persistence = SimulationPersistence(tmp_path / "simulation.json")
    universe = Universe(current_time=0)
    scheduler = CivilizationScheduler()

    agent = AgentState(civilization_id="civ-001")
    record = ToolCallRecord(
        call_id="call-001",
        civilization_id="civ-001",
        tool_name="observe",
        arguments={},
    )

    persistence.save(
        universe,
        scheduler,
        {"status": "running"},
        agent_states={"civ-001": agent},
        tool_call_journal={"call-001": record},
    )

    loaded = persistence.load()

    assert loaded["agent_states"]["civ-001"] == agent.to_dict()
    assert loaded["tool_call_journal"]["call-001"] == record.to_dict()
    assert loaded["simulation"] == {"status": "running"}


def test_schema_v1_save_remains_loadable(tmp_path):
    path = tmp_path / "simulation.json"
    persistence = SimulationPersistence(path)

    universe = Universe(current_time=0)
    scheduler = CivilizationScheduler()

    # Generate a valid save, then convert it into the old schema.
    persistence.save(universe, scheduler, {"status": "stopped"})

    data = json.loads(path.read_text(encoding="utf-8"))
    data["schema_version"] = 1
    data.pop("agent_states", None)
    data.pop("tool_call_journal", None)

    path.write_text(json.dumps(data), encoding="utf-8")

    loaded = persistence.load()

    assert loaded is not None
    assert loaded["simulation"] == {"status": "stopped"}
    assert loaded["agent_states"] == {}
    assert loaded["tool_call_journal"] == {}


def test_new_saves_use_schema_v4(tmp_path):
    path = tmp_path / "simulation.json"
    persistence = SimulationPersistence(path)

    persistence.save(
        Universe(current_time=0),
        CivilizationScheduler(),
        {},
    )

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["schema_version"] == 4
    assert data["agent_states"] == {}
    assert data["tool_call_journal"] == {}
    assert data["simulation_engine"] == {}


def test_unsupported_schema_version_is_rejected(tmp_path):
    path = tmp_path / "simulation.json"
    path.write_text(
        json.dumps({"schema_version": 999}),
        encoding="utf-8",
    )

    persistence = SimulationPersistence(path)

    try:
        persistence.load()
    except ValueError as exc:
        assert "Unsupported save version" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
