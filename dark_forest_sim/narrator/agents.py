from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentStatus(StrEnum):
    READY = "ready"
    THINKING = "thinking"
    WAITING_FOR_TOOL = "waiting_for_tool"
    SLEEPING = "sleeping"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class ToolCallStatus(StrEnum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNCERTAIN = "uncertain"


@dataclass
class AgentState:
    civilization_id: str
    system_prompt: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    status: AgentStatus = AgentStatus.READY
    pending_tool_call_ids: list[str] = field(default_factory=list)
    wake_conditions: dict[str, Any] | None = None
    last_wake_reason: dict[str, Any] | None = None
    updated_at: str = field(default_factory=_timestamp)

    def __post_init__(self) -> None:
        if not isinstance(self.civilization_id, str) or not self.civilization_id.strip():
            raise ValueError("civilization_id must be a non-empty string")

        if not isinstance(self.system_prompt, str):
            raise ValueError("system_prompt must be a string")

        if not isinstance(self.messages, list):
            raise ValueError("messages must be a list")

        if not all(isinstance(message, dict) for message in self.messages):
            raise ValueError("Every message must be a dictionary")

        if not isinstance(self.pending_tool_call_ids, list):
            raise ValueError("pending_tool_call_ids must be a list")

        if not all(
            isinstance(call_id, str) and call_id
            for call_id in self.pending_tool_call_ids
        ):
            raise ValueError("Every pending tool call ID must be a non-empty string")

        if len(set(self.pending_tool_call_ids)) != len(self.pending_tool_call_ids):
            raise ValueError("pending_tool_call_ids must be unique")

        if self.wake_conditions is not None and not isinstance(
            self.wake_conditions, dict
        ):
            raise ValueError("wake_conditions must be a dictionary or None")

        if self.last_wake_reason is not None and not isinstance(
            self.last_wake_reason, dict
        ):
            raise ValueError("last_wake_reason must be a dictionary or None")

        if not isinstance(self.updated_at, str) or not self.updated_at:
            raise ValueError("updated_at must be a non-empty string")

        try:
            self.status = AgentStatus(self.status)
        except ValueError as exc:
            raise ValueError(f"Invalid agent status: {self.status}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "civilization_id": self.civilization_id,
            "system_prompt": self.system_prompt,
            "messages": deepcopy(self.messages),
            "status": self.status.value,
            "pending_tool_call_ids": list(self.pending_tool_call_ids),
            "wake_conditions": deepcopy(self.wake_conditions),
            "last_wake_reason": deepcopy(self.last_wake_reason),
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentState:
        if not isinstance(data, dict):
            raise ValueError("Agent state must be a dictionary")

        return cls(
            civilization_id=data["civilization_id"],
            system_prompt=data.get("system_prompt", ""),
            messages=data.get("messages", []),
            status=data.get("status", AgentStatus.READY),
            pending_tool_call_ids=data.get("pending_tool_call_ids", []),
            wake_conditions=data.get("wake_conditions"),
            last_wake_reason=data.get("last_wake_reason"),
            updated_at=data.get("updated_at", _timestamp()),
        )


@dataclass
class ToolCallRecord:
    call_id: str
    civilization_id: str
    tool_name: str
    arguments: dict[str, Any]
    status: ToolCallStatus = ToolCallStatus.PENDING
    result: Any = None
    error: str | None = None
    attempts: int = 0
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)

    def __post_init__(self) -> None:
        for name in ("call_id", "civilization_id", "tool_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not isinstance(self.arguments, dict):
            raise ValueError("arguments must be a dictionary")

        if not isinstance(self.attempts, int) or isinstance(self.attempts, bool):
            raise ValueError("attempts must be an integer")

        if self.attempts < 0:
            raise ValueError("attempts cannot be negative")

        if self.error is not None and not isinstance(self.error, str):
            raise ValueError("error must be a string or None")

        if not isinstance(self.created_at, str) or not self.created_at:
            raise ValueError("created_at must be a non-empty string")

        if not isinstance(self.updated_at, str) or not self.updated_at:
            raise ValueError("updated_at must be a non-empty string")

        try:
            self.status = ToolCallStatus(self.status)
        except ValueError as exc:
            raise ValueError(f"Invalid tool call status: {self.status}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "civilization_id": self.civilization_id,
            "tool_name": self.tool_name,
            "arguments": deepcopy(self.arguments),
            "status": self.status.value,
            "result": deepcopy(self.result),
            "error": self.error,
            "attempts": self.attempts,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolCallRecord:
        if not isinstance(data, dict):
            raise ValueError("Tool call record must be a dictionary")

        return cls(
            call_id=data["call_id"],
            civilization_id=data["civilization_id"],
            tool_name=data["tool_name"],
            arguments=data.get("arguments", {}),
            status=data.get("status", ToolCallStatus.PENDING),
            result=data.get("result"),
            error=data.get("error"),
            attempts=data.get("attempts", 0),
            created_at=data.get("created_at", _timestamp()),
            updated_at=data.get("updated_at", _timestamp()),
        )
