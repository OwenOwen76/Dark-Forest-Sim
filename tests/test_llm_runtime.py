import pytest

from dark_forest_sim.engine.civilization import Civilization
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.agents import AgentStatus
from dark_forest_sim.narrator.runtime import NarratorRuntime


class FakeLLM:
    def __init__(self, response=None, error=None):
        self.response = response or {
            "role": "assistant",
            "content": "We should explore the nearby star system.",
        }
        self.error = error
        self.received_messages = None

    async def complete(self, messages):
        self.received_messages = messages

        if self.error:
            raise self.error

        return self.response


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
        save_path=path,
    )


@pytest.mark.asyncio
async def test_agent_turn_sends_context_and_persists_response(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = make_runtime(path)
    await runtime.activate_civilization("civ-001")

    agent = runtime.agent_states["civ-001"]
    agent.system_prompt = "You control a spacefaring civilization."
    agent.messages.append({
        "role": "user",
        "content": "What should we do next?",
    })

    client = FakeLLM()

    result = await runtime.run_agent_turn(client)

    assert client.received_messages == [
        {
            "role": "system",
            "content": "You control a spacefaring civilization.",
        },
        {
            "role": "user",
            "content": "What should we do next?",
        },
    ]

    assert result["role"] == "assistant"
    assert agent.messages[-1] == result
    assert agent.status == AgentStatus.READY

    restored = NarratorRuntime(save_path=path)
    restored_agent = restored.agent_states["civ-001"]

    assert restored_agent.messages[-1] == result


@pytest.mark.asyncio
async def test_agent_turn_marks_error_when_llm_fails(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")
    await runtime.activate_civilization("civ-001")

    client = FakeLLM(error=RuntimeError("Model unavailable"))

    with pytest.raises(RuntimeError, match="Model unavailable"):
        await runtime.run_agent_turn(client)

    agent = runtime.agent_states["civ-001"]

    assert agent.status == AgentStatus.ERROR
