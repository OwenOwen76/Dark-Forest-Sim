import asyncio
import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..engine.civilization import CivilizationStatus
from ..engine.scheduler import CivilizationScheduler
from ..engine.simulation import SimulationEngine
from ..engine.universe import Universe
from . import data
from .agents import (
    AgentState,
    AgentStatus,
    ToolCallRecord,
    ToolCallStatus,
)
from .civilization_mcp_client import CivilizationMCPClient
from .persistence import SimulationPersistence
from .registry import NarratorToolbox


DEFAULT_SAVE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "simulation.json"
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class CivilizationTurnResult:
    civilization_id: str
    outcome: str
    response: dict | None = None
    elapsed_years: int | None = None
    wake_time: float | None = None

    def to_dict(self) -> dict:
        return {
            "civilization_id": self.civilization_id,
            "outcome": self.outcome,
            "response": deepcopy(self.response),
            "elapsed_years": self.elapsed_years,
            "wake_time": self.wake_time,
        }


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

    # Runtime status:
    #
    # stopped
    # running
    # waiting_for_user
    # paused
    # suspended
    # interrupted
    status: str = "stopped"

    # A control request is persisted so a safe-boundary decision survives
    # ordinary runtime persistence.
    control_request: str = "none"

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

    _autonomous_run: bool = field(
        default=False,
        init=False,
        repr=False,
    )
    _run_task: asyncio.Task | None = field(
        default=None,
        init=False,
        repr=False,
    )

    _action_future: asyncio.Future | None = field(
        default=None,
        init=False,
        repr=False,
    )

    _lock: asyncio.Lock = field(
        default_factory=asyncio.Lock,
        init=False,
        repr=False,
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
            self.pending_action = simulation.get(
                "pending_action"
            )
            self.status = simulation.get(
                "status",
                "stopped",
            )
            self.control_request = simulation.get(
                "control_request",
                "none",
            )

            self.active_request_id = simulation.get(
                "active_request_id"
            )
            self.active_request_civilization_id = simulation.get(
                "active_request_civilization_id"
            )

            self.civilization_histories = simulation.get(
                "civilization_histories",
                {},
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
                    "agent_states",
                    {},
                ).items()
            }

            self.tool_call_journal = {
                call_id: ToolCallRecord.from_dict(record_data)
                for call_id, record_data in saved.get(
                    "tool_call_journal",
                    {},
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

        self.simulation_engine = SimulationEngine(
            self.universe,
            simulation_engine_state,
        )

        if saved is not None:
            recovery_required = False

            # An external tool may have completed after this process
            # disappeared. Never replay it automatically.
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

            # An LLM request cannot survive a process restart.
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

    # ------------------------------------------------------------------
    # Persistence and state
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist the complete durable runtime state."""

        self.persistence.save(
            self.universe,
            self.scheduler,
            {
                "status": self.status,
                "control_request": self.control_request,
                "active_civilization_id": (
                    self.active_civilization_id
                ),
                "pending_action": self.pending_action,
                "civilization_histories": (
                    self.civilization_histories
                ),
                "last_action_result": self.last_action_result,
                "active_request_id": self.active_request_id,
                "active_request_civilization_id": (
                    self.active_request_civilization_id
                ),
            },
            agent_states=self.agent_states,
            tool_call_journal=self.tool_call_journal,
            simulation_engine_state=self.simulation_engine.to_dict(),
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
                    if (
                        civilization is not None
                        and civilization.status
                        == CivilizationStatus.SLEEPING
                    ):
                        agent.status = AgentStatus.SLEEPING
                    else:
                        agent.status = AgentStatus.INTERRUPTED

                    agent.updated_at = _timestamp()

                self.active_request_id = None
                self.active_request_civilization_id = None
                self.active_civilization_id = None

                if not self._autonomous_run:
                    self.status = "stopped"

                if (
                    self.pending_action is not None
                    and self.pending_action.get("civilization_id")
                    == civilization_id
                ):
                    result = {
                        "proposal_id": (
                            self.pending_action["proposal_id"]
                        ),
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

    def get_active_civilization(self):
        if self.active_civilization_id is None:
            raise ValueError(
                "No civilization is currently active."
            )

        civilization = self.universe.get_civilization(
            self.active_civilization_id
        )

        if civilization.status != CivilizationStatus.ACTIVE:
            raise ValueError(
                "The active civilization is not awake."
            )

        return civilization

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

    # ------------------------------------------------------------------
    # Civilization activation
    # ------------------------------------------------------------------

    async def activate_civilization(
        self,
        civilization_id: str,
    ):
        async with self._lock:
            if self.status == "interrupted":
                raise ValueError(
                    "Resume the interrupted runtime before activating "
                    "another civilization."
                )

            if self.active_civilization_id is not None:
                raise ValueError(
                    "Another civilization is already active."
                )

            civilization = self.universe.get_civilization(
                civilization_id
            )

            if civilization.status != CivilizationStatus.ACTIVE:
                raise ValueError(
                    "Only awake civilizations can be activated."
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
                    "Resolve uncertain tool calls before activating "
                    "this civilization: "
                    + ", ".join(uncertain_calls)
                )

            agent = self.agent_states.setdefault(
                civilization_id,
                AgentState(
                    civilization_id=civilization_id
                ),
            )

            agent.status = AgentStatus.READY
            agent.updated_at = _timestamp()

            self.active_civilization_id = civilization_id

            if self.status in {
                "stopped",
                "paused",
                "suspended",
            }:
                self.status = "running"

            self.control_request = "none"
            self.save()

            return self.civilization_context()

    # ------------------------------------------------------------------
    # Narrator action handling
    # ------------------------------------------------------------------

    async def submit_action(self, description: str):
        description = description.strip()

        if not description:
            raise ValueError(
                "Action description cannot be empty."
            )

        async with self._lock:
            civilization = self.get_active_civilization()

            if self.pending_action is not None:
                raise ValueError(
                    "An action is already awaiting a ruling."
                )

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
                raise ValueError(
                    "There is no pending action."
                )

            if (
                self.pending_action["proposal_id"]
                != proposal_id
            ):
                raise ValueError(
                    "Proposal ID does not match."
                )

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

    # ------------------------------------------------------------------
    # Tool-call journal
    # ------------------------------------------------------------------

    def register_tool_call(
        self,
        call_id: str,
        civilization_id: str,
        tool_name: str,
        arguments: dict,
    ) -> ToolCallRecord:
        """Durably register a tool call before execution."""

        if self.status != "running":
            raise ValueError(
                "Runtime is not running."
            )

        if (
            civilization_id
            != self.active_civilization_id
        ):
            raise ValueError(
                "Tool call does not belong to the active "
                "civilization."
            )

        if call_id in self.tool_call_journal:
            raise ValueError(
                f"Tool call already exists: {call_id}"
            )

        if (
            not isinstance(tool_name, str)
            or not tool_name.strip()
        ):
            raise ValueError(
                "Tool name cannot be empty."
            )

        if not isinstance(arguments, dict):
            raise ValueError(
                "Tool arguments must be a dictionary."
            )

        self.get_active_civilization()

        agent = self.agent_states.setdefault(
            civilization_id,
            AgentState(
                civilization_id=civilization_id
            ),
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
            agent.pending_tool_call_ids.append(
                call_id
            )

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
            raise ValueError(
                "Runtime is not running."
            )

        if (
            record.civilization_id
            != self.active_civilization_id
        ):
            raise ValueError(
                "Cannot execute a tool call belonging to "
                "an inactive civilization."
            )

        self.get_active_civilization()

        if record.status != ToolCallStatus.PENDING:
            raise ValueError(
                f"Cannot execute tool call in state: "
                f"{record.status}"
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
                f"Cannot complete tool call in state: "
                f"{record.status}"
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
                f"Cannot fail tool call in state: "
                f"{record.status}"
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
            if (
                not isinstance(error, str)
                or not error.strip()
            ):
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

    def _get_tool_call(
        self,
        call_id: str,
    ) -> ToolCallRecord:
        try:
            return self.tool_call_journal[call_id]
        except KeyError:
            raise ValueError(
                f"Unknown tool call: {call_id}"
            ) from None

    def _finish_tool_call(
        self,
        record: ToolCallRecord,
    ) -> None:
        agent = self.agent_states.get(
            record.civilization_id
        )

        if agent is None:
            return

        if record.call_id in agent.pending_tool_call_ids:
            agent.pending_tool_call_ids.remove(
                record.call_id
            )

        civilization = self.universe.civilizations.get(
            record.civilization_id
        )

        if (
            civilization is not None
            and civilization.status
            == CivilizationStatus.SLEEPING
        ):
            agent.status = AgentStatus.SLEEPING
        else:
            agent.status = AgentStatus.THINKING

        agent.updated_at = _timestamp()

    # ------------------------------------------------------------------
    # LLM turn execution
    # ------------------------------------------------------------------

    async def run_agent_turn(self, client):
        """
        Run one complete reasoning cycle for the active civilization.

        The civilization continues thinking after ordinary tool results.
        A successful time_lapse ends the reasoning cycle and puts the
        civilization to sleep.

        An assistant response with no tool calls means the civilization
        is asking the human for input.
        """

        max_tool_rounds = 32

        async with self._lock:
            if self.status != "running":
                raise ValueError(
                    "Runtime is not running."
                )

            civilization = self.get_active_civilization()
            civilization_id = civilization.id

            agent = self.agent_states.setdefault(
                civilization_id,
                AgentState(
                    civilization_id=civilization_id
                ),
            )

            if agent.pending_tool_call_ids:
                raise ValueError(
                    "Cannot continue while tool calls are pending."
                )

            uncertain_calls = [
                record.call_id
                for record in self.tool_call_journal.values()
                if (
                    record.civilization_id
                    == civilization_id
                    and record.status
                    == ToolCallStatus.UNCERTAIN
                )
            ]

            if uncertain_calls:
                raise ValueError(
                    "Resolve uncertain tool calls before continuing: "
                    + ", ".join(uncertain_calls)
                )

            if self.active_request_id is not None:
                raise ValueError(
                    "An LLM request is already active."
                )

            messages = []

            if agent.system_prompt:
                messages.append({
                    "role": "system",
                    "content": agent.system_prompt,
                })

            messages.extend(
                deepcopy(agent.messages)
            )

            agent.status = AgentStatus.THINKING
            agent.updated_at = _timestamp()
            self.save()

        mcp_client = CivilizationMCPClient()

        async with mcp_client.connect() as session:
            tools = await mcp_client.get_openai_tools(
                session
            )

            for _ in range(max_tool_rounds):
                request_id = str(uuid4())

                async with self._lock:
                    if (
                        self.status != "running"
                        or self.active_civilization_id
                        != civilization_id
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
                    self.active_request_civilization_id = (
                        civilization_id
                    )

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
                        or response.get("role")
                        != "assistant"
                    ):
                        raise ValueError(
                            "LLM returned an invalid assistant message."
                        )

                except asyncio.CancelledError:
                    async with self._lock:
                        if (
                            self.active_request_id
                            == request_id
                        ):
                            self.active_request_id = None
                            self.active_request_civilization_id = (
                                None
                            )
                            self.status = "interrupted"

                            agent.status = (
                                AgentStatus.INTERRUPTED
                            )
                            agent.updated_at = _timestamp()
                            self.save()

                    raise

                except Exception:
                    async with self._lock:
                        if (
                            self.active_request_id
                            == request_id
                        ):
                            self.active_request_id = None
                            self.active_request_civilization_id = (
                                None
                            )

                            agent.status = (
                                AgentStatus.ERROR
                            )
                            agent.updated_at = _timestamp()
                            self.save()

                    raise

                async with self._lock:
                    if (
                        self.active_request_id
                        != request_id
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

                    agent.messages.append(
                        deepcopy(response)
                    )
                    messages.append(
                        deepcopy(response)
                    )

                    agent.updated_at = _timestamp()

                    self.civilization_histories[
                        civilization_id
                    ] = deepcopy(
                        agent.messages
                    )

                    self.save()

                tool_calls = (
                    response.get("tool_calls")
                    or []
                )

                # An ordinary assistant response is a request for
                # human input. It does not complete the civilization's
                # turn.
                if not tool_calls:
                    async with self._lock:
                        agent.status = (
                            AgentStatus.WAITING_FOR_CLARIFICATION
                        )
                        agent.updated_at = _timestamp()

                        self.status = "waiting_for_user"

                        self.civilization_histories[
                            civilization_id
                        ] = deepcopy(
                            agent.messages
                        )

                        self.save()

                    return CivilizationTurnResult(
                        civilization_id=civilization_id,
                        outcome="waiting_for_user",
                        response=deepcopy(response),
                    ).to_dict()

                time_lapse_called = False
                time_lapse_result = None

                for index, tool_call in enumerate(
                    tool_calls
                ):
                    call_id = tool_call["id"]
                    function = tool_call["function"]
                    tool_name = function["name"]

                    try:
                        arguments = json.loads(
                            function["arguments"]
                        )
                    except (
                        json.JSONDecodeError,
                        TypeError,
                    ) as exc:
                        raise ValueError(
                            "Tool call arguments contain invalid JSON."
                        ) from exc

                    if not isinstance(
                        arguments,
                        dict,
                    ):
                        raise ValueError(
                            "Tool call arguments must decode "
                            "to an object."
                        )

                    record = self.register_tool_call(
                        call_id=call_id,
                        civilization_id=(
                            civilization_id
                        ),
                        tool_name=tool_name,
                        arguments=arguments,
                    )

                    self.mark_tool_call_executing(
                        record.call_id
                    )

                    try:
                        result = (
                            await mcp_client.call_tool(
                                session,
                                tool_name,
                                arguments,
                            )
                        )

                    except asyncio.CancelledError:
                        async with self._lock:
                            record.status = (
                                ToolCallStatus.UNCERTAIN
                            )
                            record.updated_at = _timestamp()

                            self._finish_tool_call(
                                record
                            )

                            self.status = "interrupted"

                            agent.status = (
                                AgentStatus.INTERRUPTED
                            )
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
                        agent.messages.append(
                            deepcopy(
                                tool_message
                            )
                        )
                        messages.append(
                            deepcopy(
                                tool_message
                            )

                        self.civilization_histories[
                            civilization_id
                        ] = deepcopy(
                            agent.messages
                        )

                        agent.updated_at = (
                            _timestamp()
                        )
                        self.save()

                    if (
                        tool_name == "time_lapse"
                        and not (
                            isinstance(
                                result,
                                dict,
                            )
                            and "error" in result
                        )
                    ):
                        time_lapse_called = True
                        time_lapse_result = result

                        # time_lapse is the terminal tool of a
                        # reasoning cycle. Any calls after it cannot
                        # execute because the civilization has already
                        # yielded control.
                        if index != len(tool_calls) - 1:
                            raise RuntimeError(
                                "time_lapse must be the final tool "
                                "call in an assistant response."
                            )

                        break

                if time_lapse_called:
                    elapsed_years = None
                    wake_time = None

                    if isinstance(
                        time_lapse_result,
                        dict,
                    ):
                        elapsed_years = (
                            time_lapse_result.get(
                                "years"
                            )
                        )
                        wake_time = (
                            time_lapse_result.get(
                                "requested_wake_time"
                            )
                        )

                    return CivilizationTurnResult(
                        civilization_id=(
                            civilization_id
                        ),
                        outcome="time_lapse",
                        response=deepcopy(
                            response
                        ),
                        elapsed_years=(
                            elapsed_years
                            if isinstance(
                                elapsed_years,
                                int,
                            )
                            else None
                        ),
                        wake_time=(
                            wake_time
                            if isinstance(
                                wake_time,
                                (int, float),
                            )
                            else None
                        ),
                    ).to_dict()

                # Every ordinary tool result returns control to the
                # LLM for another reasoning cycle.
                continue

            async with self._lock:
                agent.status = AgentStatus.ERROR
                agent.updated_at = _timestamp()
                self.save()

            raise RuntimeError(
                "Civilization exceeded the maximum of "
                f"{max_tool_rounds} consecutive reasoning rounds."
            )

    # ------------------------------------------------------------------
    # Human response handling
    # ------------------------------------------------------------------

    async def submit_civilization_response(
        self,
        content: str,
        client,
    ):
        """
        Supply human input after the civilization explicitly asked
        for it, then continue that civilization's reasoning cycle.
        """

        content = content.strip()

        if not content:
            raise ValueError(
                "Response cannot be empty."
            )

        async with self._lock:
            if self.status != "waiting_for_user":
                raise ValueError(
                    "The civilization is not waiting for a response."
                )

            civilization = self.get_active_civilization()

            agent = self.agent_states.setdefault(
                civilization.id,
                AgentState(
                    civilization_id=civilization.id
                ),
            )

            if (
                agent.status
                != AgentStatus.WAITING_FOR_CLARIFICATION
            ):
                raise ValueError(
                    "The civilization is not waiting for clarification."
                )

            agent.messages.append({
                "role": "user",
                "content": content,
            })

            agent.status = AgentStatus.READY
            agent.updated_at = _timestamp()

            self.civilization_histories[
                civilization.id
            ] = deepcopy(agent.messages)

            self.status = "running"
            self.control_request = "none"

            self.save()

        result = await self.run_agent_turn(client)

        if (
            result["outcome"] == "time_lapse"
        ):
            self._start_autonomous_run_if_needed(
                client
            )

        return result

    # ------------------------------------------------------------------
    # Time advancement
    # ------------------------------------------------------------------

    async def end_turn(
        self,
        years: int,
    ):
        """
        Put the active civilization to sleep.

        In autonomous execution this only ends the current civilization
        reasoning cycle; the runtime itself remains running so the
        scheduler can select the next civilization.
        """

        async with self._lock:
            civilization = self.get_active_civilization()

            if (
                self.active_request_civilization_id
                == civilization.id
            ):
                raise ValueError(
                    "Cannot end the turn while an LLM request "
                    "is active."
                )

            if self.pending_action is not None:
                raise ValueError(
                    "Cannot end the turn while an action "
                    "awaits a ruling."
                )

            agent = self.agent_states.get(
                civilization.id
            )

            if (
                agent is not None
                and agent.pending_tool_call_ids
            ):
                raise ValueError(
                    "Cannot end the turn while tool calls "
                    "are pending."
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

            if not self._autonomous_run:
                self.status = "stopped"

            self.save()

            return {
                "turn_ended": True,
                "civilization_id": (
                    civilization.id
                ),
                "civilization_name": (
                    civilization.name
                ),
                "years": years,
                "requested_wake_time": (
                    wake_time
                ),
            }

    # ------------------------------------------------------------------
    # Scheduler / autonomous runtime
    # ------------------------------------------------------------------

    def _build_wake_message(
        self,
        civilization_id: str,
        elapsed_years: float,
        arrivals,
    ) -> str:
        civilization = self.universe.get_civilization(
            civilization_id
        )

        lines = [
            "Simulation update:",
            f"{elapsed_years:g} years have passed.",
            (
                "Your civilization is now in local year "
                f"{civilization.year}."
            ),
        ]

        relevant_arrivals = [
            delivery
            for delivery in arrivals
            if delivery.recipient_civilization_id
            == civilization_id
        ]

        if relevant_arrivals:
            lines.append("")
            lines.append(
                "Information that reached your civilization "
                "during this interval:"
            )

            for delivery in relevant_arrivals:
                event = self.universe.events.get(
                    delivery.event_id
                )

                if event is None:
                    continue

                lines.append(
                    f"- {event.description}"
                )
        else:
            lines.append("")
            lines.append(
                "No new event information reached your "
                "civilization during this interval."
            )

        return "\n".join(lines)

    def _apply_wake_results(
        self,
        update,
        previous_sleep_starts: dict[str, float],
    ) -> None:
        for civilization in update.awakened:
            started_at = previous_sleep_starts.get(
                civilization.id,
                self.universe.current_time,
            )

            elapsed_years = max(
                0.0,
                self.universe.current_time
                - started_at,
            )

            message = self._build_wake_message(
                civilization.id,
                elapsed_years,
                update.arrivals,
            )

            agent = self.agent_states.setdefault(
                civilization.id,
                AgentState(
                    civilization_id=civilization.id
                ),
            )

            agent.messages.append({
                "role": "user",
                "content": message,
            })

            agent.last_wake_reason = {
                "universe_time": (
                    self.universe.current_time
                ),
                "elapsed_years": elapsed_years,
                "local_year": civilization.year,
                "arrived_event_ids": [
                    delivery.event_id
                    for delivery in update.arrivals
                    if (
                        delivery.recipient_civilization_id
                        == civilization.id
                    )
                ],
            }

            agent.status = AgentStatus.READY
            agent.updated_at = _timestamp()

            self.civilization_histories[
                civilization.id
            ] = deepcopy(agent.messages)

    async def run_simulation(
        self,
        client,
    ) -> None:
        """
        Run civilization turns continuously.

        A civilization reasons until it calls time_lapse or explicitly
        asks the human for input. Sleeping civilizations are advanced
        through the scheduler until one becomes eligible again.
        """

        async with self._lock:
            if self.status == "interrupted":
                raise ValueError(
                    "Resume the interrupted runtime before starting it."
                )

            if self.status == "running":
                if self._autonomous_run:
                    raise ValueError(
                        "Simulation is already running."
                    )

            if self.status not in {
                "stopped",
                "paused",
                "suspended",
                "waiting_for_user",
            }:
                raise ValueError(
                    f"Cannot start simulation from status: "
                    f"{self.status}"
                )

            self.status = "running"
            self.control_request = "none"
            self._autonomous_run = True
            self.save()

        try:
            while True:
                async with self._lock:
                    if (
                        self.control_request
                        == "terminate"
                    ):
                        self.status = "stopped"
                        self.control_request = "none"
                        self.active_civilization_id = None
                        self.save()
                        return

                    if (
                        self.control_request
                        == "pause"
                    ):
                        self.status = "paused"
                        self.control_request = "none"
                        self.save()
                        return

                    if (
                        self.control_request
                        == "suspend"
                    ):
                        self.status = "suspended"
                        self.control_request = "none"
                        self.save()
                        return

                    if self.status != "running":
                        return

                async with self._lock:
                    if self.active_civilization_id is None:
                        civilization = (
                            self.scheduler.get_next_civilization(
                                self.universe
                            )
                        )
                    else:
                        civilization = (
                            self.get_active_civilization()
                        )

                if civilization is not None:
                    if (
                        self.active_civilization_id
                        is None
                    ):
                        await self.activate_civilization(
                            civilization.id
                        )

                    result = await self.run_agent_turn(
                        client
                    )

                    if (
                        result["outcome"]
                        == "waiting_for_user"
                    ):
                        return

                    if (
                        result["outcome"]
                        == "time_lapse"
                    ):
                        continue

                    raise RuntimeError(
                        "Civilization turn ended with an "
                        f"unexpected outcome: "
                        f"{result['outcome']}"
                    )

                async with self._lock:
                    previous_sleep_starts = dict(
                        self.scheduler.sleep_started_at
                    )

                    update = (
                        self.scheduler.advance_when_idle(
                            self.universe,
                            simulation_engine=(
                                self.simulation_engine
                            ),
                        )
                    )

                    self._apply_wake_results(
                        update,
                        previous_sleep_starts,
                    )

                    self.save()

                if (
                    update.advanced_to is None
                    and not update.arrivals
                    and not update.awakened
                ):
                    async with self._lock:
                        self.status = "stopped"
                        self.control_request = "none"
                        self.save()

                    return

                await asyncio.sleep(0)

        except asyncio.CancelledError:
            async with self._lock:
                if self.status == "running":
                    self.status = "suspended"

                self.save()

            raise

        except Exception:
            async with self._lock:
                self.status = "interrupted"

                if (
                    self.active_civilization_id
                    is not None
                ):
                    agent = self.agent_states.get(
                        self.active_civilization_id
                    )

                    if agent is not None:
                        agent.status = (
                            AgentStatus.INTERRUPTED
                        )
                        agent.updated_at = _timestamp()

                self.save()

            raise

        finally:
            self._autonomous_run = False

    def _start_autonomous_run_if_needed(
        self,
        client,
    ) -> None:
        if (
            self._run_task is not None
            and not self._run_task.done()
        ):
            return

        self._run_task = asyncio.create_task(
            self.run_simulation(client)
        )

    async def start_simulation(
        self,
        client,
    ) -> dict:
        async with self._lock:
            if (
                self._run_task is not None
                and not self._run_task.done()
            ):
                raise ValueError(
                    "Simulation is already running."
                )

            if client is None:
                raise ValueError(
                    "An LLM client is required."
                )

            if self.status == "interrupted":
                raise ValueError(
                    "Resume the interrupted runtime first."
                )

        self._run_task = asyncio.create_task(
            self.run_simulation(client)
        )

        return {
            "status": "running",
        }

    # ------------------------------------------------------------------
    # Runtime controls
    # ------------------------------------------------------------------

    async def request_pause(self) -> dict:
        async with self._lock:
            if self.status != "running":
                raise ValueError(
                    "Simulation is not running."
                )

            self.control_request = "pause"
            self.save()

            return {
                "status": self.status,
                "request": "pause",
            }

    async def request_suspend(self) -> dict:
        async with self._lock:
            if self.status != "running":
                raise ValueError(
                    "Simulation is not running."
                )

            self.control_request = "suspend"
            self.save()

            return {
                "status": self.status,
                "request": "suspend",
            }

    async def request_terminate(self) -> dict:
        async with self._lock:
            if self.status not in {
                "paused",
                "suspended",
            }:
                raise ValueError(
                    "Simulation must be paused or suspended "
                    "before termination."
                )

            self.control_request = "terminate"
            self.status = "stopped"
            self.active_civilization_id = None
            self.active_request_id = None
            self.active_request_civilization_id = None
            self.save()

            return {
                "status": "stopped",
                "terminated": True,
            }

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    async def resume_interrupted(self):
        async with self._lock:
            if self.status != "interrupted":
                raise ValueError(
                    "Runtime is not in an interrupted state."
                )

            if self.pending_action is not None:
                raise ValueError(
                    "Resolve the pending action before resuming."
                )

            if self.active_civilization_id is None:
                raise ValueError(
                    "There is no active civilization to resume."
                )

            civilization = (
                self.get_active_civilization()
            )

            uncertain_calls = [
                record.call_id
                for record in self.tool_call_journal.values()
                if (
                    record.civilization_id
                    == civilization.id
                    and record.status
                    == ToolCallStatus.UNCERTAIN
                )
            ]

            if uncertain_calls:
                raise ValueError(
                    "Resolve uncertain tool calls before "
                    "resuming: "
                    + ", ".join(
                        uncertain_calls
                    )
                )

            agent = self.agent_states.setdefault(
                civilization.id,
                AgentState(
                    civilization_id=civilization.id
                ),
            )

            agent.status = AgentStatus.READY
            agent.updated_at = _timestamp()

            self.active_request_id = None
            self.active_request_civilization_id = None
            self.status = "running"
            self.control_request = "none"
            self.save()

            return self.civilization_context()
