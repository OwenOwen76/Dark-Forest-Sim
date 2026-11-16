import pytest

from dark_forest_sim.engine.civilization import Civilization
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.agents import (
    AgentStatus,
    ToolCallStatus,
)
from dark_forest_sim.narrator.runtime import NarratorRuntime


def make_runtime(tmp_path):
    universe = Universe(current_time=0)
    universe.add_civilization(
        Civilization(
            id="civ-001",
            name="Test Civilization",
            position=Position(x=0, y=0, z=0),
            year=100,
        )
    )
    return NarratorRuntime(
        universe=universe,
        save_path=tmp_path / "simulation.json",
    )


def test_register_tool_call_creates_pending_record(tmp_path):
    runtime = make_runtime(tmp_path)

    record = runtime.register_tool_call(
        call_id="call-001",
        civilization_id="civ-001",
        tool_name="observe",
        arguments={"target": "stars"},
    )

    assert record.status == ToolCallStatus.PENDING
    assert record.attempts == 0
    assert "call-001" in runtime.agent_states["civ-001"].pending_tool_call_ids


def test_tool_call_transitions_to_executing(tmp_path):
    runtime = make_runtime(tmp_path)

    runtime.register_tool_call(
        "call-001", "civ-001", "observe", {"target": "stars"}
    )

    record = runtime.mark_tool_call_executing("call-001")

    assert record.status == ToolCallStatus.EXECUTING
    assert record.attempts == 1


def test_tool_call_completes_and_stores_result(tmp_path):
    runtime = make_runtime(tmp_path)

    runtime.register_tool_call(
        "call-001", "civ-001", "observe", {"target": "stars"}
    )
    runtime.mark_tool_call_executing("call-001")

    record = runtime.complete_tool_call(
        "call-001",
        {"observations": ["A nearby star"]},
    )

    assert record.status == ToolCallStatus.COMPLETED
    assert record.result == {"observations": ["A nearby star"]}
    assert "call-001" not in runtime.agent_states["civ-001"].pending_tool_call_ids


def test_tool_call_can_be_marked_failed(tmp_path):
    runtime = make_runtime(tmp_path)

    runtime.register_tool_call(
        "call-001", "civ-001", "observe", {"target": "stars"}
    )
    runtime.mark_tool_call_executing("call-001")

    record = runtime.fail_tool_call("call-001", "Tool execution failed")

    assert record.status == ToolCallStatus.FAILED
    assert record.error == "Tool execution failed"


def test_executing_tool_call_becomes_uncertain_after_restart(tmp_path):
    runtime = make_runtime(tmp_path)

    runtime.register_tool_call(
        "call-001", "civ-001", "observe", {"target": "stars"}
    )
    runtime.mark_tool_call_executing("call-001")

    restored = NarratorRuntime(save_path=runtime.save_path)

    record = restored.tool_call_journal["call-001"]

    assert record.status == ToolCallStatus.UNCERTAIN
    assert record.attempts == 1


def test_pending_tool_call_remains_pending_after_restart(tmp_path):
    runtime = make_runtime(tmp_path)

    runtime.register_tool_call(
        "call-001", "civ-001", "observe", {"target": "stars"}
    )

    restored = NarratorRuntime(save_path=runtime.save_path)

    assert (
        restored.tool_call_journal["call-001"].status
        == ToolCallStatus.PENDING
    )


def test_completed_tool_call_remains_completed_after_restart(tmp_path):
    runtime = make_runtime(tmp_path)

    runtime.register_tool_call(
        "call-001", "civ-001", "observe", {"target": "stars"}
    )
    runtime.mark_tool_call_executing("call-001")
    runtime.complete_tool_call("call-001", {"ok": True})

    restored = NarratorRuntime(save_path=runtime.save_path)

    assert (
        restored.tool_call_journal["call-001"].status
        == ToolCallStatus.COMPLETED
    )
    assert restored.tool_call_journal["call-001"].result == {"ok": True}


def test_duplicate_tool_call_id_is_rejected(tmp_path):
    runtime = make_runtime(tmp_path)

    runtime.register_tool_call(
        "call-001", "civ-001", "observe", {}
    )

    with pytest.raises(ValueError):
        runtime.register_tool_call(
            "call-001", "civ-001", "observe", {}
        )


def test_non_pending_tool_call_cannot_start_execution(tmp_path):
    runtime = make_runtime(tmp_path)

    runtime.register_tool_call(
        "call-001", "civ-001", "observe", {}
    )
    runtime.mark_tool_call_executing("call-001")

    with pytest.raises(ValueError):
        runtime.mark_tool_call_executing("call-001")
