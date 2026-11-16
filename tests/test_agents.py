from dark_forest_sim.narrator.agents import (
    AgentState,
    AgentStatus,
    ToolCallRecord,
    ToolCallStatus,
)


def test_agent_state_defaults():
    agent = AgentState(civilization_id="civ-001")

    assert agent.civilization_id == "civ-001"
    assert agent.system_prompt == ""
    assert agent.messages == []
    assert agent.status == AgentStatus.READY
    assert agent.pending_tool_call_ids == []
    assert agent.wake_conditions is None
    assert agent.last_wake_reason is None
    assert agent.updated_at


def test_agent_state_serialization_roundtrip():
    agent = AgentState(
        civilization_id="civ-001",
        system_prompt="You are an autonomous civilization.",
        messages=[
            {"role": "user", "content": "Observe the universe."},
            {"role": "assistant", "content": "I will begin observing."},
        ],
        status=AgentStatus.SLEEPING,
        pending_tool_call_ids=["call-001"],
        wake_conditions={"years": 100},
        last_wake_reason={"type": "initialization"},
    )

    restored = AgentState.from_dict(agent.to_dict())

    assert restored.civilization_id == agent.civilization_id
    assert restored.system_prompt == agent.system_prompt
    assert restored.messages == agent.messages
    assert restored.status == agent.status
    assert restored.pending_tool_call_ids == agent.pending_tool_call_ids
    assert restored.wake_conditions == agent.wake_conditions
    assert restored.last_wake_reason == agent.last_wake_reason


def test_agent_state_preserves_all_statuses():
    for status in AgentStatus:
        agent = AgentState(
            civilization_id="civ-001",
            status=status,
        )

        restored = AgentState.from_dict(agent.to_dict())

        assert restored.status == status


def test_agent_state_rejects_empty_civilization_id():
    try:
        AgentState(civilization_id="")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_agent_state_rejects_invalid_messages():
    try:
        AgentState(
            civilization_id="civ-001",
            messages=["not a message dictionary"],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_tool_call_record_defaults():
    record = ToolCallRecord(
        call_id="call-001",
        civilization_id="civ-001",
        tool_name="observe",
        arguments={"target": "nearby_stars"},
    )

    assert record.status == ToolCallStatus.PENDING
    assert record.result is None
    assert record.error is None
    assert record.attempts == 0
    assert record.created_at
    assert record.updated_at


def test_tool_call_record_serialization_roundtrip():
    record = ToolCallRecord(
        call_id="call-001",
        civilization_id="civ-001",
        tool_name="observe",
        arguments={"target": "nearby_stars"},
        status=ToolCallStatus.COMPLETED,
        result={"observations": 12},
        attempts=1,
    )

    restored = ToolCallRecord.from_dict(record.to_dict())

    assert restored.call_id == record.call_id
    assert restored.civilization_id == record.civilization_id
    assert restored.tool_name == record.tool_name
    assert restored.arguments == record.arguments
    assert restored.status == record.status
    assert restored.result == record.result
    assert restored.error == record.error
    assert restored.attempts == record.attempts


def test_tool_call_record_preserves_all_statuses():
    for status in ToolCallStatus:
        record = ToolCallRecord(
            call_id="call-001",
            civilization_id="civ-001",
            tool_name="observe",
            arguments={},
            status=status,
        )

        restored = ToolCallRecord.from_dict(record.to_dict())

        assert restored.status == status


def test_tool_call_record_rejects_invalid_arguments():
    try:
        ToolCallRecord(
            call_id="call-001",
            civilization_id="civ-001",
            tool_name="observe",
            arguments=["invalid"],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_tool_call_record_rejects_negative_attempts():
    try:
        ToolCallRecord(
            call_id="call-001",
            civilization_id="civ-001",
            tool_name="observe",
            arguments={},
            attempts=-1,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
