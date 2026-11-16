import pytest

from dark_forest_sim.engine.civilization import Civilization
from dark_forest_sim.engine.scheduler import CivilizationScheduler
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.agents import ToolCallStatus
from dark_forest_sim.narrator.runtime import NarratorRuntime


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


def register_call(runtime, call_id="call-001"):
    return runtime.register_tool_call(
        call_id=call_id,
        civilization_id="civ-001",
        tool_name="get_civilization",
        arguments={"civilization_id": "civ-001"},
    )


def test_registration_persists_before_execution(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = make_runtime(path)
    record = register_call(runtime)

    assert record.status == ToolCallStatus.PENDING
    assert record.attempts == 0

    recovered = NarratorRuntime(save_path=path)

    assert "call-001" in recovered.tool_call_journal
    assert (
        recovered.tool_call_journal["call-001"].status
        == ToolCallStatus.PENDING
    )
    assert (
        "call-001"
        in recovered.agent_states["civ-001"].pending_tool_call_ids
    )


def test_execution_increments_attempts_and_persists(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = make_runtime(path)
    register_call(runtime)

    record = runtime.mark_tool_call_executing("call-001")

    assert record.status == ToolCallStatus.EXECUTING
    assert record.attempts == 1

    recovered = NarratorRuntime(save_path=path)

    saved = recovered.tool_call_journal["call-001"]
    assert saved.status == ToolCallStatus.UNCERTAIN
    assert saved.attempts == 1


def test_completion_stores_result_and_updates_agent(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")
    register_call(runtime)
    runtime.mark_tool_call_executing("call-001")

    result = {"year": 100, "name": "Test Civilization"}
    record = runtime.complete_tool_call("call-001", result)

    assert record.status == ToolCallStatus.COMPLETED
    assert record.result == result
    assert record.error is None

    agent = runtime.agent_states["civ-001"]
    assert "call-001" not in agent.pending_tool_call_ids
    assert agent.status.value == "thinking"


def test_failure_stores_error_and_updates_agent(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")
    register_call(runtime)
    runtime.mark_tool_call_executing("call-001")

    record = runtime.fail_tool_call("call-001", "Tool execution failed")

    assert record.status == ToolCallStatus.FAILED
    assert record.error == "Tool execution failed"

    agent = runtime.agent_states["civ-001"]
    assert "call-001" not in agent.pending_tool_call_ids
    assert agent.status.value == "thinking"


def test_cannot_complete_call_before_execution(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")
    register_call(runtime)

    with pytest.raises(ValueError):
        runtime.complete_tool_call("call-001", {"result": "unexpected"})


def test_cannot_register_duplicate_call_id(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")
    register_call(runtime)

    with pytest.raises(ValueError):
        register_call(runtime)


def test_cannot_execute_call_twice_without_completion(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")
    register_call(runtime)

    runtime.mark_tool_call_executing("call-001")

    with pytest.raises(ValueError):
        runtime.mark_tool_call_executing("call-001")


def test_unknown_call_is_rejected(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")

    with pytest.raises(ValueError):
        runtime.mark_tool_call_executing("missing-call")


def test_executing_call_becomes_uncertain_after_restart(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = make_runtime(path)
    register_call(runtime)
    runtime.mark_tool_call_executing("call-001")

    recovered = NarratorRuntime(save_path=path)
    record = recovered.tool_call_journal["call-001"]

    assert record.status == ToolCallStatus.UNCERTAIN
    assert record.attempts == 1

    agent = recovered.agent_states["civ-001"]
    assert "call-001" in agent.pending_tool_call_ids

    # Uncertain calls must not be executed automatically again.
    with pytest.raises(ValueError):
        recovered.mark_tool_call_executing("call-001")


def test_pending_call_survives_restart_without_execution(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = make_runtime(path)
    register_call(runtime)

    recovered = NarratorRuntime(save_path=path)
    record = recovered.tool_call_journal["call-001"]

    assert record.status == ToolCallStatus.PENDING
    assert record.attempts == 0
    assert (
        "call-001"
        in recovered.agent_states["civ-001"].pending_tool_call_ids
    )
