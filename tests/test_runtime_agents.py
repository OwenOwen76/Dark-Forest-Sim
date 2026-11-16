from dark_forest_sim.engine.civilization import Civilization
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.agents import (
    AgentState,
    AgentStatus,
    ToolCallRecord,
    ToolCallStatus,
)
from dark_forest_sim.narrator.runtime import NarratorRuntime


def make_runtime(tmp_path):
    universe = Universe(current_time=0)

    civilization = Civilization(
        id="civ-001",
        name="Test Civilization",
        position=Position(x=0, y=0, z=0),
        year=100,
    )

    universe.add_civilization(civilization)

    return NarratorRuntime(
        universe=universe,
        save_path=tmp_path / "simulation.json",
    )


def test_runtime_initializes_agent_states(tmp_path):
    runtime = make_runtime(tmp_path)

    assert runtime.agent_states == {}
    assert runtime.tool_call_journal == {}


def test_runtime_creates_agent_on_activation(tmp_path):
    runtime = make_runtime(tmp_path)

    import asyncio

    asyncio.run(runtime.activate_civilization("civ-001"))

    agent = runtime.agent_states["civ-001"]

    assert isinstance(agent, AgentState)
    assert agent.civilization_id == "civ-001"
    assert agent.status == AgentStatus.READY


def test_runtime_saves_agent_states(tmp_path):
    runtime = make_runtime(tmp_path)

    agent = AgentState(
        civilization_id="civ-001",
        system_prompt="Civilization agent",
    )

    runtime.agent_states["civ-001"] = agent
    runtime.save()

    restored = NarratorRuntime(save_path=runtime.save_path)

    assert restored.agent_states["civ-001"].to_dict() == agent.to_dict()


def test_runtime_saves_tool_call_journal(tmp_path):
    runtime = make_runtime(tmp_path)

    record = ToolCallRecord(
        call_id="call-001",
        civilization_id="civ-001",
        tool_name="observe",
        arguments={"target": "stars"},
        status=ToolCallStatus.PENDING,
    )

    runtime.tool_call_journal["call-001"] = record
    runtime.save()

    restored = NarratorRuntime(save_path=runtime.save_path)

    assert (
        restored.tool_call_journal["call-001"].to_dict()
        == record.to_dict()
    )


def test_runtime_migrates_existing_histories(tmp_path):
    runtime = make_runtime(tmp_path)

    history = [
        {"role": "user", "content": "Observe the universe."},
        {"role": "assistant", "content": "Beginning observation."},
    ]

    runtime.civilization_histories["civ-001"] = history
    runtime.save()

    restored = NarratorRuntime(save_path=runtime.save_path)

    assert restored.agent_states["civ-001"].messages == history


def test_existing_agent_state_takes_precedence_over_history(tmp_path):
    runtime = make_runtime(tmp_path)

    agent = AgentState(
        civilization_id="civ-001",
        messages=[
            {"role": "assistant", "content": "New conversation."},
        ],
    )

    runtime.agent_states["civ-001"] = agent
    runtime.civilization_histories["civ-001"] = [
        {"role": "assistant", "content": "Old conversation."},
    ]

    runtime.save()

    restored = NarratorRuntime(save_path=runtime.save_path)

    assert restored.agent_states["civ-001"].messages == agent.messages


def test_end_turn_marks_agent_sleeping(tmp_path):
    import asyncio

    runtime = make_runtime(tmp_path)

    asyncio.run(runtime.activate_civilization("civ-001"))

    result = asyncio.run(runtime.end_turn(100))

    assert result["turn_ended"] is True
    assert runtime.agent_states["civ-001"].status == AgentStatus.SLEEPING
    assert runtime.active_civilization_id is None
