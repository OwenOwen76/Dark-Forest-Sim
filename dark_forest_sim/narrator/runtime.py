import asyncio
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json

from ..engine.civilization import CivilizationStatus
from ..engine.scheduler import CivilizationScheduler
from ..engine.simulation import SimulationEngine
from ..engine.universe import Universe
from .civilization_mcp_client import CivilizationMCPClient
from .persistence import SimulationPersistence
from .registry import NarratorToolbox
from .agents import AgentState, AgentStatus, ToolCallRecord, ToolCallStatus
from . import data

DEFAULT_SAVE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "simulation.json"
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class NarratorRuntime:
    universe: Universe = field(default_factory=Universe)
    scheduler: CivilizationScheduler = field(
        default_factory=CivilizationScheduler
    )
    save_path: Path = DEFAULT_SAVE_PATH

    toolbox: NarratorToolbox = field(init=False)
    persistence: SimulationPersistence = field(init=False)
    simulation_engine: SimulationEngine = field(init=False)

    active_civilization_id: str | None = None
    pending_action: dict | None = None
    status: str = "stopped"

    civilization_histories: dict[str, list] = field(
        default_factory=dict
    )
    agent_states: dict[str, AgentState] = field(
        default_factory=dict
    )
    tool_call_journal: dict[str, ToolCallRecord] = field(
        default_factory=dict
    )

    last_action_result: dict | None = None

    active_request_id: str | None = None
    active_request_civilization_id: str | None = None

    _action_future: asyncio.Future | None = field(
        default=None, init=False, repr=False
    )
    _lock: asyncio.Lock = field(
        default_factory=asyncio.Lock, init=False, repr=False
    )

    def __post_init__(self):
        self.persistence = SimulationPersistence(self.save_path)

        saved = self.persistence.load()
        simulation_engine_state = {}

        if saved is not None:
            self.universe = saved["universe"]
            self.scheduler = saved["scheduler"]

            simulation = saved["simulation"]

            self.active_civilization_id = simulation.get(
                "active_civilization_id"
            )
            self.pending_action = simulation.get("pending_action")
            self.status = simulation.get("status", "stopped")

            self.active_request_id = simulation.get(
                "active_request_id"
            )
            self.active_request_civilization_id = simulation.get(
                "active_request_civilization_id"
            )

            self.civilization_histories = simulation.get(
                "civilization_histories", {}
            )
            self.last_action_result = simulation.get(
                "last_action_result"
            )

            simulation_engine_state = saved.get(
                "simulation_engine_state",
                {},
            )

            self.agent_states = {
                civ_id: AgentState.from_dict(agent_data)
                for civ_id, agent_data in saved.get(
                    "agent_states", {}
                ).items()
            }

            self.tool_call_journal = {
                call_id: ToolCallRecord.from_dict(record_data)
                for call_id, record_data in saved.get(
                    "tool_call_journal", {}
                ).items()
            }

            # Migrate legacy conversation histories without overwriting
            # agent states that already exist.
            for civ_id, history in self.civilization_histories.items():
                self.agent_states.setdefault(
                    civ_id,
                    AgentState(
                        civilization_id=civ_id,
                        messages=deepcopy(history),
                    ),
                )

        # Initialize the engine before recovery saves occur.
        self.simulation_engine = SimulationEngine(
            self.universe,
            simulation_engine_state,
        )

        if saved is not None:
            recovery_required = False

            # An executing call may have completed externally before
            # the previous process crashed. Never replay it automatically.
            for record in self.tool_call_journal.values():
                if record.status == ToolCallStatus.EXECUTING:
                    record.status = ToolCallStatus.UNCERTAIN
                    record.updated_at = _timestamp()
                    recovery_required = True

                    agent = self.agent_states.get(
                        record.civilization_id
                    )

                    if agent is not None:
                        if record.call_id in agent.pending_tool_call_ids:
                            agent.pending_tool_call_ids.remove(
                                record.call_id
                            )

                        agent.status = AgentStatus.INTERRUPTED
                        agent.updated_at = _timestamp()

            # An asyncio request cannot survive its originating process.
            if (
                self.status == "running"
                or self.active_request_id is not None
            ):
                self.status = "interrupted"

                if self.active_civilization_id in self.agent_states:
                    agent = self.agent_states[
                        self.active_civilization_id
                    ]
                    agent.status = AgentStatus.INTERRUPTED
                    agent.updated_at = _timestamp()

                self.active_request_id = None
                self.active_request_civilization_id = None

                recovery_required = True

            if self.active_civilization_id is not None:
                civilization = self.universe.get_civilization(
                    self.active_civilization_id
                )

                if civilization.status != CivilizationStatus.ACTIVE:
                    raise ValueError(
                        "Saved active civilization is not awake."
                    )

            if recovery_required:
                self.save()

        self.toolbox = NarratorToolbox(
            self.universe,
            self.scheduler,
            on_change=self._handle_world_change,
            simulation_engine=self.simulation_engine,
        )

    def _handle_world_change(self) -> None:
        civilization_id = self.active_civilization_id

        if civilization_id is not None:
            civilization = self.universe.civilizations.get(
                civilization_id
            )

            if (
                civilization is None
                or civilization.status != CivilizationStatus.ACTIVE
            ):
                agent = self.agent_states.get(civilization_id)

                if agent is not None:
                    agent.status = (
                        AgentStatus.SLEEPING
                        if civilization is not None
                        and civilization.status == CivilizationStatus.SLEEPING
                        else AgentStatus.INTERRUPTED
                    )
                    agent.updated_at = _timestamp()

                # Invalidate any outstanding LLM response.
                self.active_request_id = None
                self.active_request_civilization_id = None

                self.active_civilization_id = None
                self.status = "stopped"

                if (
                    self.pending_action is not None
                    and self.pending_action.get("civilization_id")
                    == civilization_id
                ):
                    result = {
                        "proposal_id": self.pending_action["proposal_id"],
                        "approved": False,
                        "explanation": (
                            "The civilization became inactive before "
                            "the action was ruled on."
                        ),
                    }

                    self.pending_action = None
                    self.last_action_result = result

                    future = self._action_future
                    self._action_future = None

                    if future is not None and not future.done():
                        future.get_loop().call_soon_threadsafe(
                            lambda: (
                                not future.done()
                                and future.set_result(result)
                            )
                        )

        self.save()

    def save(self) -> None:
        """Persist the complete durable runtime state."""

        self.persistence.save(
            self.universe,
            self.scheduler,
            {
                "status": self.status,
                "active_civilization_id":
                    self.active_civilization_id,
                "pending_action": self.pending_action,
                "civilization_histories":
                    self.civilization_histories,
                "last_action_result": self.last_action_result,
                "active_request_id": self.active_request_id,
                "active_request_civilization_id":
                    self.active_request_civilization_id,
            },
            agent_states=self.agent_states,
            tool_call_journal=self.tool_call_journal,
            simulation_engine_state=self.simulation_engine.to_dict(),
        )

    def get_active_civilization(self):
        if self.active_civilization_id is None:
            raise ValueError("No civilization is currently active.")

        civilization = self.universe.get_civilization(
            self.active_civilization_id
        )

        if civilization.status != CivilizationStatus.ACTIVE:
            raise ValueError("The active civilization is not awake.")

        return civilization

    async def activate_civilization(self, civilization_id: str):
        async with self._lock:
            if self.status == "interrupted":
                raise ValueError(
                    "Resume the interrupted runtime before activating "
                    "another civilization."
                )

            if self.active_civilization_id is not None:
                raise ValueError("Another civilization is already active.")

            civilization = self.universe.get_civilization(civilization_id)

            if civilization.status != CivilizationStatus.ACTIVE:
                raise ValueError("Only awake civilizations can be activated.")

            uncertain_calls = [
                record.call_id
                for record in self.tool_call_journal.values()
                if (
                    record.civilization_id == civilization_id
                    and record.status == ToolCallStatus.UNCERTAIN
                )
            ]

            if uncertain_calls:
                raise ValueError(
                    "Resolve uncertain tool calls before activating "
                    "this civilization: "
                    + ", ".join(uncertain_calls)
                )

            agent = self.agent_states.setdefault(
                civilization_id,
                AgentState(civilization_id=civilization_id),
            )

            agent.status = AgentStatus.READY
            agent.updated_at = _timestamp()

            self.active_civilization_id = civilization_id
            self.status = "running"
            self.save()

            return self.civilization_context()

    def civilization_context(self):
        civilization = self.get_active_civilization()

        return {
            "civilization_id": civilization.id,
            "name": civilization.name,
            "position": {
                "x": civilization.position.x,
                "y": civilization.position.y,
                "z": civilization.position.z,
            },
            "year": civilization.year,
            "status": civilization.status.value,
            "state": asdict(civilization.state),
        }

    def civilization_knowledge(self):
        civilization = self.get_active_civilization()

        return data.list_known_events(
            self.universe,
            civilization.id,
        )

    async def submit_action(self, description: str):
        description = description.strip()

        if not description:
            raise ValueError("Action description cannot be empty.")

        async with self._lock:
            civilization = self.get_active_civilization()

            if self.pending_action is not None:
                raise ValueError("An action is already awaiting a ruling.")

            proposal_id = str(uuid4())

            self.pending_action = {
                "proposal_id": proposal_id,
                "civilization_id": civilization.id,
                "civilization_name": civilization.name,
                "description": description,
            }

            self._action_future = (
                asyncio.get_running_loop().create_future()
            )
            future = self._action_future

            self.save()

        return await asyncio.shield(future)

    async def resolve_action(
        self,
        proposal_id: str,
        approved: bool,
        explanation: str = "",
    ):
        async with self._lock:
            if self.pending_action is None:
                raise ValueError("There is no pending action.")

            if self.pending_action["proposal_id"] != proposal_id:
                raise ValueError("Proposal ID does not match.")

            result = {
                "proposal_id": proposal_id,
                "approved": approved,
                "explanation": explanation,
            }

            future = self._action_future

            self.pending_action = None
            self._action_future = None
            self.last_action_result = result

            self.save()

            if future is not None and not future.done():
                future.set_result(result)

            return result

    def register_tool_call(
        self,
        call_id: str,
        civilization_id: str,
        tool_name: str,
        arguments: dict,
    ) -> ToolCallRecord:
        """Durably register a tool call before execution."""

        if self.status != "running":
            raise ValueError("Runtime is not running.")

        if civilization_id != self.active_civilization_id:
            raise ValueError(
                "Tool call does not belong to the active civilization."
            )

        if call_id in self.tool_call_journal:
            raise ValueError(f"Tool call already exists: {call_id}")

        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError("Tool name cannot be empty.")

        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a dictionary.")

        self.get_active_civilization()

        agent = self.agent_states.setdefault(
            civilization_id,
            AgentState(civilization_id=civilization_id),
        )

        record = ToolCallRecord(
            call_id=call_id,
            civilization_id=civilization_id,
            tool_name=tool_name,
            arguments=deepcopy(arguments),
            status=ToolCallStatus.PENDING,
        )

        self.tool_call_journal[call_id] = record

        if call_id not in agent.pending_tool_call_ids:
            agent.pending_tool_call_ids.append(call_id)

        agent.status = AgentStatus.WAITING_FOR_TOOL
        agent.updated_at = _timestamp()

        self.save()
        return record

    def mark_tool_call_executing(
        self,
        call_id: str,
    ) -> ToolCallRecord:
        """Persist execution intent before invoking the external tool."""

        record = self._get_tool_call(call_id)

        if self.status != "running":
            raise ValueError("Runtime is not running.")

        if record.civilization_id != self.active_civilization_id:
            raise ValueError(
                "Cannot execute a tool call belonging to an inactive "
                "civilization."
            )

        self.get_active_civilization()

        if record.status != ToolCallStatus.PENDING:
            raise ValueError(
                f"Cannot execute tool call in state: {record.status}"
            )

        record.status = ToolCallStatus.EXECUTING
        record.attempts += 1
        record.updated_at = _timestamp()

        self.save()
        return record

    def complete_tool_call(
        self,
        call_id: str,
        result,
    ) -> ToolCallRecord:
        """Persist a successful tool result."""

        record = self._get_tool_call(call_id)

        if record.status != ToolCallStatus.EXECUTING:
            raise ValueError(
                f"Cannot complete tool call in state: {record.status}"
            )

        record.status = ToolCallStatus.COMPLETED
        record.result = deepcopy(result)
        record.error = None
        record.updated_at = _timestamp()

        self._finish_tool_call(record)
        self.save()
        return record

    def fail_tool_call(
        self,
        call_id: str,
        error: str,
    ) -> ToolCallRecord:
        """Persist a failed tool execution."""

        record = self._get_tool_call(call_id)

        if record.status != ToolCallStatus.EXECUTING:
            raise ValueError(
                f"Cannot fail tool call in state: {record.status}"
            )

        record.status = ToolCallStatus.FAILED
        record.error = error
        record.updated_at = _timestamp()

        self._finish_tool_call(record)
        self.save()
        return record

    def resolve_uncertain_tool_call(
        self,
        call_id: str,
        outcome: str,
        result=None,
        error: str | None = None,
    ) -> ToolCallRecord:
        """Resolve an uncertain call after external verification."""

        record = self._get_tool_call(call_id)

        if record.status != ToolCallStatus.UNCERTAIN:
            raise ValueError(
                "Only uncertain tool calls can be manually resolved."
            )

        if outcome == "completed":
            if error is not None:
                raise ValueError(
                    "A completed call cannot have an error."
                )

            record.status = ToolCallStatus.COMPLETED
            record.result = deepcopy(result)
            record.error = None

        elif outcome == "failed":
            if not isinstance(error, str) or not error.strip():
                raise ValueError(
                    "A failed call requires an explanation."
                )

            record.status = ToolCallStatus.FAILED
            record.error = error
            record.result = None

        else:
            raise ValueError(
                "Outcome must be 'completed' or 'failed'."
            )

        record.updated_at = _timestamp()
        self._finish_tool_call(record)
        self.save()

        return record

    def _get_tool_call(self, call_id: str) -> ToolCallRecord:
        try:
            return self.tool_call_journal[call_id]
        except KeyError:
            raise ValueError(f"Unknown tool call: {call_id}") from None

    def _finish_tool_call(self, record: ToolCallRecord) -> None:
        agent = self.agent_states.get(record.civilization_id)

        if agent is None:
            return

        if record.call_id in agent.pending_tool_call_ids:
            agent.pending_tool_call_ids.remove(record.call_id)

        agent.status = AgentStatus.THINKING
        agent.updated_at = _timestamp()

    async def run_agent_turn(self, client):
        """Run a complete civilization LLM and MCP tool interaction cycle."""

        max_tool_rounds = 32

        async with self._lock:
            if self.status != "running":
                raise ValueError("Runtime is not running.")

            civilization = self.get_active_civilization()
            civilization_id = civilization.id

            agent = self.agent_states.setdefault(
                civilization_id,
                AgentState(civilization_id=civilization_id),
            )

            if agent.pending_tool_call_ids:
                raise ValueError(
                    "Cannot continue while tool calls are pending."
                )

            uncertain_calls = [
                record.call_id
                for record in self.tool_call_journal.values()
                if (
                    record.civilization_id == civilization_id
                    and record.status == ToolCallStatus.UNCERTAIN
                )
            ]

            if uncertain_calls:
                raise ValueError(
                    "Resolve uncertain tool calls before continuing: "
                    + ", ".join(uncertain_calls)
                )

            if self.active_request_id is not None:
                raise ValueError("An LLM request is already active.")

            messages = []

            if agent.system_prompt:
                messages.append({
                    "role": "system",
                    "content": agent.system_prompt,
                })

            messages.extend(deepcopy(agent.messages))

            agent.status = AgentStatus.THINKING
            agent.updated_at = _timestamp()
            self.save()

        mcp_client = CivilizationMCPClient()

        async with mcp_client.connect() as session:
            tools = await mcp_client.get_openai_tools(session)

            for round_number in range(max_tool_rounds):
                request_id = str(uuid4())

                async with self._lock:
                    if (
                        self.status != "running"
                        or self.active_civilization_id != civilization_id
                    ):
                        raise RuntimeError(
                            "Civilization became inactive before "
                            "the next LLM request."
                        )

                    if self.active_request_id is not None:
                        raise ValueError(
                            "Another LLM request is already active."
                        )

                    self.active_request_id = request_id
                    self.active_request_civilization_id = civilization_id
                    agent.status = AgentStatus.THINKING
                    agent.updated_at = _timestamp()
                    self.save()

                try:
                    response = await client.complete(
                        messages,
                        tools=tools,
                    )

                    if (
                        not isinstance(response, dict)
                        or response.get("role") != "assistant"
                    ):
                        raise ValueError(
                            "LLM returned an invalid assistant message."
                        )

                except asyncio.CancelledError:
                    async with self._lock:
                        if self.active_request_id == request_id:
                            self.active_request_id = None
                            self.active_request_civilization_id = None
                            self.status = "interrupted"

                            agent.status = AgentStatus.INTERRUPTED
                            agent.updated_at = _timestamp()
                            self.save()

                    raise

                except Exception:
                    async with self._lock:
                        if self.active_request_id == request_id:
                            self.active_request_id = None
                            self.active_request_civilization_id = None

                            agent.status = AgentStatus.ERROR
                            agent.updated_at = _timestamp()
                            self.save()

                    raise

                async with self._lock:
                    if (
                        self.active_request_id != request_id
                        or self.active_request_civilization_id
                        != civilization_id
                        or self.active_civilization_id
                        != civilization_id
                        or self.status != "running"
                    ):
                        raise RuntimeError(
                            "Discarded an LLM response from "
                            "an inactive request."
                        )

                    self.active_request_id = None
                    self.active_request_civilization_id = None

                    agent.messages.append(deepcopy(response))
                    messages.append(deepcopy(response))

                    agent.updated_at = _timestamp()

                    self.civilization_histories[civilization_id] = (
                        deepcopy(agent.messages)
                    )

                    self.save()

                tool_calls = response.get("tool_calls") or []

                if not tool_calls:
                    async with self._lock:
                        agent.status = AgentStatus.READY
                        agent.updated_at = _timestamp()

                        self.civilization_histories[civilization_id] = (
                            deepcopy(agent.messages)
                        )

                        self.save()

                    return response

                turn_ended = False

                for tool_call in tool_calls:
                    call_id = tool_call["id"]
                    function = tool_call["function"]
                    tool_name = function["name"]
                    arguments = json.loads(function["arguments"])

                    record = self.register_tool_call(
                        call_id=call_id,
                        civilization_id=civilization_id,
                        tool_name=tool_name,
                        arguments=arguments,
                    )

                    self.mark_tool_call_executing(record.call_id)

                    try:
                        result = await mcp_client.call_tool(
                            session,
                            tool_name,
                            arguments,
                        )

                    except asyncio.CancelledError:
                        async with self._lock:
                            record.status = ToolCallStatus.UNCERTAIN
                            record.updated_at = _timestamp()

                            self._finish_tool_call(record)

                            self.status = "interrupted"
                            agent.status = AgentStatus.INTERRUPTED
                            agent.updated_at = _timestamp()

                            self.save()

                        raise

                    except Exception as exc:
                        self.fail_tool_call(
                            record.call_id,
                            str(exc),
                        )

                        result = {
                            "error": str(exc),
                        }

                    else:
                        self.complete_tool_call(
                            record.call_id,
                            result,
                        )

                    tool_message = {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(
                            result,
                            ensure_ascii=False,
                            default=str,
                        ),
                    }

                    async with self._lock:
                        agent.messages.append(deepcopy(tool_message))
                        messages.append(deepcopy(tool_message))

                        self.civilization_histories[civilization_id] = (
                            deepcopy(agent.messages)
                        )

                        agent.updated_at = _timestamp()
                        self.save()

                    if tool_name == "time_lapse" and "error" not in (
                        result if isinstance(result, dict) else {}
                    ):
                        turn_ended = True
                        break

                if turn_ended:
                    return response

            async with self._lock:
                agent.status = AgentStatus.ERROR
                agent.updated_at = _timestamp()
                self.save()

            raise RuntimeError(
                f"Civilization exceeded the maximum of "
                f"{max_tool_rounds} consecutive tool-call rounds."
            )

    async def end_turn(self, years: int):
        async with self._lock:
            civilization = self.get_active_civilization()

            if self.active_request_civilization_id == civilization.id:
                raise ValueError(
                    "Cannot end the turn while an LLM request is active."
                )

            if self.pending_action is not None:
                raise ValueError(
                    "Cannot end the turn while an action awaits a ruling."
                )

            agent = self.agent_states.get(civilization.id)

            if agent is not None and agent.pending_tool_call_ids:
                raise ValueError(
                    "Cannot end the turn while tool calls are pending."
                )

            wake_time = self.scheduler.sleep_civilization(
                self.universe,
                civilization.id,
                years,
            )

            if agent is not None:
                agent.status = AgentStatus.SLEEPING
                agent.updated_at = _timestamp()

            self.active_civilization_id = None
            self.status = "stopped"
            self.save()

            return {
                "turn_ended": True,
                "civilization_id": civilization.id,
                "civilization_name": civilization.name,
                "requested_wake_time": wake_time,
            }

    async def resume_interrupted(self):
        """Resume a civilization after recovering a previous process."""

        async with self._lock:
            if self.status != "interrupted":
                raise ValueError("Runtime is not in an interrupted state.")

            if self.active_civilization_id is None:
                raise ValueError(
                    "There is no active civilization to resume."
                )

            if self.pending_action is not None:
                raise ValueError(
                    "Resolve the pending action before resuming."
                )

            civilization = self.get_active_civilization()

            uncertain_calls = [
                record.call_id
                for record in self.tool_call_journal.values()
                if (
                    record.civilization_id == civilization.id
                    and record.status == ToolCallStatus.UNCERTAIN
                )
            ]

            if uncertain_calls:
                raise ValueError(
                    "Resolve uncertain tool calls before resuming: "
                    + ", ".join(uncertain_calls)
                )

            agent = self.agent_states.setdefault(
                civilization.id,
                AgentState(civilization_id=civilization.id),
            )

            agent.status = (
                AgentStatus.WAITING_FOR_TOOL
                if agent.pending_tool_call_ids
                else AgentStatus.READY
            )
            agent.updated_at = _timestamp()

            self.active_request_id = None
            self.active_request_civilization_id = None
            self.status = "running"
            self.save()

            return self.civilization_context()
