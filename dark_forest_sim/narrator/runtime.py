import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from ..engine.civilization import CivilizationStatus
from ..engine.scheduler import CivilizationScheduler
from ..engine.universe import Universe
from .persistence import SimulationPersistence
from .registry import NarratorToolbox


DEFAULT_SAVE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "simulation.json"
)


@dataclass(slots=True)
class NarratorRuntime:
    universe: Universe = field(default_factory=Universe)
    scheduler: CivilizationScheduler = field(
        default_factory=CivilizationScheduler
    )
    save_path: Path = DEFAULT_SAVE_PATH

    toolbox: NarratorToolbox = field(init=False)
    persistence: SimulationPersistence = field(init=False)

    active_civilization_id: str | None = None
    pending_action: dict | None = None
    status: str = "stopped"

    civilization_histories: dict[str, list] = field(
        default_factory=dict
    )
    last_action_result: dict | None = None

    _action_future: asyncio.Future | None = field(
        default=None, init=False, repr=False
    )
    _lock: asyncio.Lock = field(
        default_factory=asyncio.Lock, init=False, repr=False
    )

    def __post_init__(self):
        self.persistence = SimulationPersistence(self.save_path)

        saved = self.persistence.load()

        if saved is not None:
            self.universe = saved["universe"]
            self.scheduler = saved["scheduler"]

            simulation = saved["simulation"]

            self.active_civilization_id = simulation.get(
                "active_civilization_id"
            )
            self.pending_action = simulation.get("pending_action")
            self.status = simulation.get("status", "stopped")
            self.civilization_histories = simulation.get(
                "civilization_histories", {}
            )
            self.last_action_result = simulation.get(
                "last_action_result"
            )

            # A process cannot resume an asyncio task from a previous
            # process. Preserve its state but mark it interrupted.
            if self.status == "running":
                self.status = "interrupted"

            if self.active_civilization_id is not None:
                civilization = self.universe.get_civilization(
                    self.active_civilization_id
                )

                if civilization.status != CivilizationStatus.ACTIVE:
                    raise ValueError(
                        "Saved active civilization is not awake."
                    )

        self.toolbox = NarratorToolbox(
            self.universe,
            self.scheduler,
            on_change=self.save,
        )

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
            },
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
            if self.active_civilization_id is not None:
                raise ValueError("Another civilization is already active.")

            civilization = self.universe.get_civilization(civilization_id)

            if civilization.status != CivilizationStatus.ACTIVE:
                raise ValueError("Only awake civilizations can be activated.")

            self.active_civilization_id = civilization_id
            self.status = "running"
            self.save()

            return self.civilization_context()

    def civilization_context(self):
        civilization = self.get_active_civilization()

        return {
            "civilization_id": civilization.id,
            "name": civilization.name,
            "year": civilization.year,
            "status": civilization.status.value,
        }

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

            # Save before waiting for the narrator.
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

            # This also works after a restart, when no Future exists.
            self.save()

            if future is not None and not future.done():
                future.set_result(result)

            return result

    async def end_turn(self, years: int):
        async with self._lock:
            civilization = self.get_active_civilization()

            if self.pending_action is not None:
                raise ValueError(
                    "Cannot end the turn while an action awaits a ruling."
                )

            wake_time = self.scheduler.sleep_civilization(
                self.universe,
                civilization.id,
                years,
            )

            self.active_civilization_id = None
            self.status = "stopped"
            self.save()

            return {
                "turn_ended": True,
                "civilization_id": civilization.id,
                "civilization_name": civilization.name,
                "requested_wake_time": wake_time,
            }
