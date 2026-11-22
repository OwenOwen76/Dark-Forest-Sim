import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from dark_forest_sim.engine.civilization import (
    Civilization,
    CivilizationState,
    CivilizationStatus,
    DemographicsState,
    EnergyState,
)
from dark_forest_sim.engine.space import Position
from dark_forest_sim.narrator.agents import (
    AgentState,
    AgentStatus,
    ToolCallStatus,
)
from dark_forest_sim.narrator.runtime import NarratorRuntime


def create_active_runtime(path):
    runtime = NarratorRuntime(save_path=path)

    civilization = Civilization(
        id="alpha",
        name="Alpha",
        position=Position(0, 0, 0),
        year=100,
        state=CivilizationState(
            demographics=DemographicsState(
                population=100,
                annual_population_growth_rate=0.1,
            ),
            energy=EnergyState(),
        ),
    )

    runtime.universe.add_civilization(civilization)
    runtime.active_civilization_id = "alpha"
    runtime.status = "running"
    runtime.agent_states["alpha"] = AgentState(
        civilization_id="alpha",
        messages=[
            {"role": "user", "content": "Continue the simulation."}
        ],
    )

    return runtime


def test_fresh_process_restores_and_continues(tmp_path):
    save_path = tmp_path / "simulation.json"

    original = create_active_runtime(save_path)
    original.simulation_engine.advance_to(0.4)
    original.save()

    script = """
import asyncio
import json
import sys
from pathlib import Path
from dark_forest_sim.narrator.runtime import NarratorRuntime

runtime = NarratorRuntime(save_path=Path(sys.argv[1]))

assert runtime.status == "interrupted"
assert runtime.active_civilization_id == "alpha"
assert runtime.agent_states["alpha"].messages[0]["role"] == "user"
assert abs(
    runtime.simulation_engine.demographic_elapsed_years["alpha"] - 0.4
) < 1e-9

asyncio.run(runtime.resume_interrupted())

runtime.simulation_engine.advance_to(1.0)
runtime.save()

print(json.dumps({
    "status": runtime.status,
    "current_time": runtime.universe.current_time,
    "population": runtime.universe.get_civilization("alpha").state.demographics.population,
}))
"""

    completed = subprocess.run(
        [sys.executable, "-c", script, str(save_path)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )

    result = json.loads(completed.stdout.strip())

    assert result["status"] == "running"
    assert result["current_time"] == 1.0
    assert result["population"] == 110

    # A third runtime instance must recover the state written by process 2.
    restored = NarratorRuntime(save_path=save_path)

    assert restored.status == "interrupted"
    assert restored.universe.current_time == 1.0
    assert (
        restored.universe.get_civilization("alpha")
        .state.demographics.population
        == 110
    )


def test_executing_tool_call_becomes_uncertain_after_restart(tmp_path):
    save_path = tmp_path / "simulation.json"
    runtime = create_active_runtime(save_path)

    runtime.register_tool_call(
        "call-executing",
        "alpha",
        "modify_world",
        {"value": 1},
    )
    runtime.mark_tool_call_executing("call-executing")

    runtime.register_tool_call(
        "call-pending",
        "alpha",
        "query_world",
        {"value": 2},
    )

    runtime.save()

    restored = NarratorRuntime(save_path=save_path)

    executing = restored.tool_call_journal["call-executing"]
    pending = restored.tool_call_journal["call-pending"]

    assert executing.status == ToolCallStatus.UNCERTAIN
    assert pending.status == ToolCallStatus.PENDING

    agent = restored.agent_states["alpha"]
    assert "call-executing" not in agent.pending_tool_call_ids
    assert "call-pending" in agent.pending_tool_call_ids

    with pytest.raises(ValueError, match="uncertain"):
        asyncio.run(restored.resume_interrupted())

    with pytest.raises(ValueError, match="state"):
        restored.mark_tool_call_executing("call-executing")

    restored.resolve_uncertain_tool_call(
        "call-executing",
        "completed",
        result={"verified": True},
    )

    asyncio.run(restored.resume_interrupted())

    assert restored.status == "running"
    assert restored.agent_states["alpha"].status == (
        AgentStatus.WAITING_FOR_TOOL
    )


def test_stale_tool_call_cannot_execute_for_another_civilization(tmp_path):
    runtime = create_active_runtime(tmp_path / "simulation.json")

    runtime.universe.add_civilization(
        Civilization(
            id="beta",
            name="Beta",
            position=Position(1, 1, 1),
            year=100,
        )
    )

    runtime.register_tool_call(
        "call-alpha",
        "alpha",
        "modify_world",
        {},
    )

    runtime.active_civilization_id = "beta"

    with pytest.raises(ValueError, match="inactive civilization"):
        runtime.mark_tool_call_executing("call-alpha")

@pytest.mark.asyncio
async def test_stale_llm_response_is_discarded(tmp_path):
    runtime = create_active_runtime(tmp_path / "simulation.json")

    class DelayedClient:
        def __init__(self):
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def complete(self, messages):
            self.started.set()
            await self.release.wait()
            return {
                "role": "assistant",
                "content": "This response must be discarded.",
            }

    client = DelayedClient()
    task = asyncio.create_task(runtime.run_agent_turn(client))

    await client.started.wait()

    runtime.universe.get_civilization(
        "alpha"
    ).status = CivilizationStatus.DESTROYED

    runtime._handle_world_change()
    client.release.set()

    with pytest.raises(RuntimeError, match="inactive request"):
        await task

    assert not any(
        message.get("content") == "This response must be discarded."
        for message in runtime.agent_states["alpha"].messages
    )
