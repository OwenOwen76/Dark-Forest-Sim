import pytest

from dark_forest_sim.engine.civilization import Civilization
from dark_forest_sim.engine.scheduler import CivilizationScheduler
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.agents import AgentStatus
from dark_forest_sim.narrator.runtime import NarratorRuntime
from dark_forest_sim.engine.civilization import CivilizationStatus


def make_runtime(path):
    universe = Universe()
    universe.add_civilization(
        Civilization(
            id="civ-001",
            name="Test Civilization",
            position=Position(1, 2, 3),
            year=100,
        )
    )

    return NarratorRuntime(
        universe=universe,
        scheduler=CivilizationScheduler(),
        save_path=path,
    )


async def activate(runtime):
    await runtime.activate_civilization("civ-001")


@pytest.mark.asyncio
async def test_activation_creates_ready_agent(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")

    context = await runtime.activate_civilization("civ-001")

    assert context["civilization_id"] == "civ-001"
    assert context["status"] == "active"
    assert runtime.active_civilization_id == "civ-001"
    assert runtime.status == "running"

    agent = runtime.agent_states["civ-001"]
    assert agent.status == AgentStatus.READY


@pytest.mark.asyncio
async def test_activation_persists_agent_state(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = make_runtime(path)
    await activate(runtime)

    recovered = NarratorRuntime(save_path=path)

    assert recovered.active_civilization_id == "civ-001"
    assert recovered.status == "interrupted"

    agent = recovered.agent_states["civ-001"]
    assert agent.status == AgentStatus.INTERRUPTED


@pytest.mark.asyncio
async def test_agent_messages_persist(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = make_runtime(path)
    await activate(runtime)

    agent = runtime.agent_states["civ-001"]
    agent.messages.append(
        {"role": "user", "content": "The stars are strangely quiet."}
    )
    agent.messages.append(
        {"role": "assistant", "content": "I should investigate."}
    )
    runtime.save()

    recovered = NarratorRuntime(save_path=path)
    recovered_agent = recovered.agent_states["civ-001"]

    assert recovered_agent.messages == [
        {"role": "user", "content": "The stars are strangely quiet."},
        {"role": "assistant", "content": "I should investigate."},
    ]


@pytest.mark.asyncio
async def test_tool_waiting_returns_agent_to_thinking(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")
    await activate(runtime)

    record = runtime.register_tool_call(
        call_id="call-001",
        civilization_id="civ-001",
        tool_name="get_civilization",
        arguments={"civilization_id": "civ-001"},
    )

    assert record.call_id == "call-001"
    assert runtime.agent_states["civ-001"].status == AgentStatus.WAITING_FOR_TOOL

    runtime.mark_tool_call_executing("call-001")
    runtime.complete_tool_call("call-001", {"year": 100})

    assert runtime.agent_states["civ-001"].status == AgentStatus.THINKING


@pytest.mark.asyncio
async def test_end_turn_puts_agent_to_sleeping(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = make_runtime(path)
    await activate(runtime)

    result = await runtime.end_turn(50)

    assert result["civilization_id"] == "civ-001"

    civ = runtime.universe.get_civilization("civ-001")
    assert civ.year == 100
    assert civ.status == CivilizationStatus.SLEEPING

    agent = runtime.agent_states["civ-001"]
    assert agent.status == AgentStatus.SLEEPING
    assert runtime.active_civilization_id is None
    assert runtime.status == "stopped"


@pytest.mark.asyncio
async def test_end_turn_persists_sleeping_state(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = make_runtime(path)
    await activate(runtime)

    await runtime.end_turn(50)

    recovered = NarratorRuntime(save_path=path)

    agent = recovered.agent_states["civ-001"]

    assert recovered.active_civilization_id is None
    assert recovered.status == "stopped"
    assert agent.status == AgentStatus.SLEEPING


@pytest.mark.asyncio
async def test_cannot_activate_second_civilization_while_one_is_active(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")

    runtime.universe.add_civilization(
        Civilization(
            id="civ-002",
            name="Second Civilization",
            position=Position(10, 20, 30),
            year=200,
        )
    )

    await activate(runtime)

    with pytest.raises(ValueError):
        await runtime.activate_civilization("civ-002")


@pytest.mark.asyncio
async def test_cannot_end_turn_with_pending_action(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")
    await activate(runtime)

    runtime.pending_action = {
        "proposal_id": "proposal-001",
        "description": "Do something",
        "civilization_id": "civ-001",
    }

    with pytest.raises(ValueError):
        await runtime.end_turn(50)


@pytest.mark.asyncio
async def test_civilization_context_matches_active_agent(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")
    await activate(runtime)

    context = runtime.civilization_context()

    assert context == {
        "civilization_id": "civ-001",
        "name": "Test Civilization",
        "year": 100,
        "position": {
            "x": 1,
            "y": 2,
            "z": 3,
        },
        "status": "active",
        "state": {
            "demographics": {
                "population": 0,
                "annual_population_growth_rate": 0.0,
            },
            "energy": {
                "energy_production_watts": 0.0,
                "energy_reserve_joules": 0.0,
                "energy_consumption_watts_per_person": 0.0,
            },
        },
    }
