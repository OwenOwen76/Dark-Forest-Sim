import json
import os
import tempfile
from dataclasses import asdict
from math import isfinite
from pathlib import Path

from ..engine.civilization import (
    Civilization,
    CivilizationStatus,
    CivilizationState,
    DemographicsState,
    EnergyState,
)
from ..engine.event import Event, EventDelivery, DeliveryStatus
from ..engine.scheduler import CivilizationScheduler
from ..engine.space import Position
from ..engine.universe import Universe


SCHEMA_VERSION = 4
SUPPORTED_SCHEMA_VERSIONS = {1, 2, 3, 4}


class SimulationPersistence:
    """Loads and saves the durable simulation state."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def save(
        self,
        universe: Universe,
        scheduler: CivilizationScheduler,
        runtime_state: dict,
        agent_states: dict | None = None,
        tool_call_journal: dict | None = None,
        simulation_engine_state: dict | None = None,
    ) -> None:
        """Atomically save the complete durable simulation state."""

        if not isinstance(runtime_state, dict):
            raise ValueError("Runtime state must be a dictionary.")

        self._validate_scheduler_for_save(universe, scheduler)

        if simulation_engine_state is None:
            simulation_engine_state = {}

        if not isinstance(simulation_engine_state, dict):
            raise ValueError(
                "Simulation engine state must be a dictionary."
            )

        data = {
            "schema_version": SCHEMA_VERSION,
            "simulation": runtime_state,
            "universe": self._serialize_universe(universe),
            "scheduler": {
                "wake_times": dict(scheduler.wake_times),
                "sleep_started_at": dict(
                    scheduler.sleep_started_at
                ),
                "sleep_start_local_year": dict(
                    scheduler.sleep_start_local_year
                ),
            },
            "simulation_engine": simulation_engine_state,
            "agent_states": self._serialize_records(agent_states),
            "tool_call_journal": self._serialize_records(
                tool_call_journal
            ),
        }

        content = json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )

        self.path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                file.write(content)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary_path, self.path)
            temporary_path = None

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _validate_scheduler_for_save(
        universe: Universe,
        scheduler: CivilizationScheduler,
    ) -> None:
        """Reject incomplete or inconsistent scheduler state."""

        if not isinstance(scheduler, CivilizationScheduler):
            raise ValueError(
                "Scheduler must be a CivilizationScheduler."
            )

        wake_times = scheduler.wake_times
        sleep_started_at = scheduler.sleep_started_at
        sleep_start_local_year = (
            scheduler.sleep_start_local_year
        )

        if not all(
            isinstance(value, dict)
            for value in (
                wake_times,
                sleep_started_at,
                sleep_start_local_year,
            )
        ):
            raise ValueError(
                "Scheduler metadata must use dictionaries."
            )

        scheduled_ids = set(wake_times)

        if (
            scheduled_ids != set(sleep_started_at)
            or scheduled_ids != set(sleep_start_local_year)
        ):
            raise ValueError(
                "Scheduler metadata dictionaries must contain "
                "the same civilization IDs."
            )

        for civilization_id in scheduled_ids:
            if not isinstance(civilization_id, str):
                raise ValueError(
                    "Scheduler civilization IDs must be strings."
                )

            civilization = universe.get_civilization(
                civilization_id
            )

            if civilization.status != CivilizationStatus.SLEEPING:
                raise ValueError(
                    f"Civilization {civilization_id!r} has a "
                    "wake schedule but is not sleeping."
                )

            SimulationPersistence._validate_time(
                wake_times[civilization_id],
                f"Wake time for {civilization_id!r}",
            )

            sleep_start = (
                SimulationPersistence._validate_time(
                    sleep_started_at[civilization_id],
                    f"Sleep start for {civilization_id!r}",
                )
            )

            if sleep_start > universe.current_time:
                raise ValueError(
                    f"Sleep start for {civilization_id!r} "
                    "is later than the current universe time."
                )

            local_year = sleep_start_local_year[civilization_id]

            if (
                isinstance(local_year, bool)
                or not isinstance(local_year, (int, float))
                or not isfinite(local_year)
            ):
                raise ValueError(
                    f"Sleep start local year for "
                    f"{civilization_id!r} must be finite and numeric."
                )

        for civilization in universe.civilizations.values():
            if (
                civilization.status == CivilizationStatus.SLEEPING
                and civilization.id not in scheduled_ids
            ):
                raise ValueError(
                    f"Sleeping civilization {civilization.id!r} "
                    "has no wake schedule."
                )

    @staticmethod
    def _serialize_records(records: dict | None) -> dict:
        if records is None:
            return {}

        if not isinstance(records, dict):
            raise ValueError("Persistent records must be dictionaries.")

        serialized = {}

        for key, record in records.items():
            if hasattr(record, "to_dict"):
                serialized[key] = record.to_dict()
            elif isinstance(record, dict):
                serialized[key] = record
            else:
                raise ValueError(
                    f"Record {key!r} must be a dictionary "
                    "or support to_dict()."
                )

        return serialized

    def load(self) -> dict | None:
        """Load a save and migrate older schemas into the current format."""

        if not self.path.exists():
            return None

        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)

        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(
                f"Simulation save is corrupted: {self.path}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "Simulation save must contain a JSON object."
            )

        version = data.get("schema_version")

        if (
            isinstance(version, bool)
            or not isinstance(version, int)
            or version not in SUPPORTED_SCHEMA_VERSIONS
        ):
            raise ValueError(
                f"Unsupported save version: {version}. "
                f"Supported versions: "
                f"{sorted(SUPPORTED_SCHEMA_VERSIONS)}."
            )

        try:
            universe = self._deserialize_universe(data["universe"])

            scheduler_data = data["scheduler"]

            if not isinstance(scheduler_data, dict):
                raise ValueError(
                    "scheduler must be a dictionary."
                )

            wake_times = scheduler_data.get("wake_times")

            if not isinstance(wake_times, dict):
                raise ValueError(
                    "scheduler wake_times must be a dictionary."
                )

            scheduler = CivilizationScheduler()

            if version < 4:
                self._migrate_legacy_scheduler(
                    scheduler,
                    wake_times,
                    universe,
                )
            else:
                self._load_scheduler_v4(
                    scheduler,
                    scheduler_data,
                    universe,
                )

            simulation = data["simulation"]

            if not isinstance(simulation, dict):
                raise ValueError(
                    "simulation must be a dictionary."
                )

            simulation_engine_state = data.get(
                "simulation_engine",
                {},
            )

            if not isinstance(simulation_engine_state, dict):
                raise ValueError(
                    "simulation_engine must be a dictionary."
                )

            agent_states = data.get("agent_states", {})
            tool_call_journal = data.get(
                "tool_call_journal",
                {},
            )

            if not isinstance(agent_states, dict):
                raise ValueError(
                    "agent_states must be a dictionary."
                )

            if not isinstance(tool_call_journal, dict):
                raise ValueError(
                    "tool_call_journal must be a dictionary."
                )

            return {
                "universe": universe,
                "scheduler": scheduler,
                "simulation": simulation,
                "simulation_engine_state": simulation_engine_state,
                "agent_states": agent_states,
                "tool_call_journal": tool_call_journal,
                "loaded_schema_version": version,
            }

        except (
            KeyError,
            TypeError,
            ValueError,
            OverflowError,
        ) as exc:
            raise ValueError(
                f"Simulation save has an invalid structure: {exc}"
            ) from exc

    @staticmethod
    def _validate_time(value, name: str) -> float:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
            raise ValueError(f"{name} must be numeric.")

        if not isfinite(value) or value < 0:
            raise ValueError(
                f"{name} must be finite and non-negative."
            )

        return float(value)

    @staticmethod
    def _migrate_legacy_scheduler(
        scheduler: CivilizationScheduler,
        wake_times: dict,
        universe: Universe,
    ) -> None:
        """
        Convert legacy civilization-local wake times into absolute
        universe timestamps.

        Older schemas did not preserve the actual time at which a
        civilization went to sleep. Migration therefore preserves
        the remaining intended sleep duration, starting from the
        saved universe time.
        """

        for civilization_id, old_wake_time in wake_times.items():
            if not isinstance(civilization_id, str):
                raise ValueError(
                    "Wake schedule IDs must be strings."
                )

            old_wake_time = SimulationPersistence._validate_time(
                old_wake_time,
                f"Legacy wake time for {civilization_id!r}",
            )

            civilization = universe.get_civilization(
                civilization_id
            )

            remaining_duration = max(
                0.0,
                old_wake_time - civilization.year,
            )

            scheduler.wake_times[civilization_id] = (
                universe.current_time + remaining_duration
            )

            scheduler.sleep_started_at[civilization_id] = (
                universe.current_time
            )

            scheduler.sleep_start_local_year[civilization_id] = (
                civilization.year
            )

        SimulationPersistence._validate_scheduler_membership(
            scheduler,
            universe,
        )

    @staticmethod
    def _load_scheduler_v4(
        scheduler: CivilizationScheduler,
        scheduler_data: dict,
        universe: Universe,
    ) -> None:
        """Load and validate the current scheduler representation."""

        required_fields = (
            "wake_times",
            "sleep_started_at",
            "sleep_start_local_year",
        )

        for field in required_fields:
            if field not in scheduler_data:
                raise ValueError(
                    f"Schema v4 scheduler is missing {field!r}."
                )

        wake_times = scheduler_data["wake_times"]
        sleep_started_at = scheduler_data["sleep_started_at"]
        sleep_start_local_year = scheduler_data[
            "sleep_start_local_year"
        ]

        if not isinstance(wake_times, dict):
            raise ValueError(
                "scheduler wake_times must be a dictionary."
            )

        if not isinstance(sleep_started_at, dict):
            raise ValueError(
                "scheduler sleep_started_at must be a dictionary."
            )

        if not isinstance(sleep_start_local_year, dict):
            raise ValueError(
                "scheduler sleep_start_local_year must be a dictionary."
            )

        if (
            set(wake_times) != set(sleep_started_at)
            or set(wake_times) != set(sleep_start_local_year)
        ):
            raise ValueError(
                "Scheduler metadata dictionaries must contain "
                "the same civilization IDs."
            )

        for civilization_id, wake_time in wake_times.items():
            if not isinstance(civilization_id, str):
                raise ValueError(
                    "Wake schedule IDs must be strings."
                )

            civilization = universe.get_civilization(
                civilization_id
            )

            scheduler.wake_times[civilization_id] = (
                SimulationPersistence._validate_time(
                    wake_time,
                    f"Wake time for {civilization_id!r}",
                )
            )

            sleep_start = (
                SimulationPersistence._validate_time(
                    sleep_started_at[civilization_id],
                    f"Sleep start for {civilization_id!r}",
                )
            )

            if sleep_start > universe.current_time:
                raise ValueError(
                    f"Sleep start for {civilization_id!r} "
                    "is later than the current universe time."
                )

            local_year = sleep_start_local_year[
                civilization_id
            ]

            if (
                isinstance(local_year, bool)
                or not isinstance(local_year, (int, float))
                or not isfinite(local_year)
            ):
                raise ValueError(
                    f"Sleep start local year for "
                    f"{civilization_id!r} must be finite and numeric."
                )

            scheduler.sleep_started_at[civilization_id] = (
                sleep_start
            )

            scheduler.sleep_start_local_year[civilization_id] = (
                float(local_year)
            )

        SimulationPersistence._validate_scheduler_membership(
            scheduler,
            universe,
        )

    @staticmethod
    def _validate_scheduler_membership(
        scheduler: CivilizationScheduler,
        universe: Universe,
    ) -> None:
        """Ensure sleeping civilizations and schedules agree."""

        scheduled_ids = set(scheduler.wake_times)

        for civilization_id in scheduled_ids:
            civilization = universe.get_civilization(
                civilization_id
            )

            if civilization.status != CivilizationStatus.SLEEPING:
                raise ValueError(
                    f"Civilization {civilization_id!r} has a wake "
                    "schedule but is not sleeping."
                )

        for civilization in universe.civilizations.values():
            if (
                civilization.status == CivilizationStatus.SLEEPING
                and civilization.id not in scheduled_ids
            ):
                raise ValueError(
                    f"Sleeping civilization {civilization.id!r} "
                    "has no wake schedule."
                )

    @staticmethod
    def _serialize_universe(universe: Universe) -> dict:
        return {
            "current_time": universe.current_time,
            "civilizations": [
                {
                    "id": civ.id,
                    "name": civ.name,
                    "position": {
                        "x": civ.position.x,
                        "y": civ.position.y,
                        "z": civ.position.z,
                    },
                    "year": civ.year,
                    "status": civ.status.value,
                    "state": asdict(civ.state),
                }
                for civ in universe.civilizations.values()
            ],
            "events": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "created_at": event.created_at,
                    "description": event.description,
                    "origin": {
                        "x": event.origin.x,
                        "y": event.origin.y,
                        "z": event.origin.z,
                    },
                    "propagation_speed": event.propagation_speed,
                    "target_civilization_ids": (
                        list(event.target_civilization_ids)
                        if event.target_civilization_ids is not None
                        else None
                    ),
                }
                for event in universe.events.values()
            ],
            "deliveries": [
                {
                    "event_id": delivery.event_id,
                    "recipient_civilization_id": (
                        delivery.recipient_civilization_id
                    ),
                    "distance": delivery.distance,
                    "departure_time": delivery.departure_time,
                    "arrival_time": delivery.arrival_time,
                    "status": delivery.status.value,
                }
                for delivery in universe.deliveries.values()
            ],
        }

    @staticmethod
    def _deserialize_universe(data: dict) -> Universe:
        if not isinstance(data, dict):
            raise ValueError(
                "universe must be a dictionary."
            )

        civilizations_data = data["civilizations"]
        events_data = data["events"]
        deliveries_data = data["deliveries"]

        if not isinstance(civilizations_data, list):
            raise ValueError(
                "civilizations must be a list."
            )

        if not isinstance(events_data, list):
            raise ValueError(
                "events must be a list."
            )

        if not isinstance(deliveries_data, list):
            raise ValueError(
                "deliveries must be a list."
            )

        universe = Universe(
            current_time=data["current_time"]
        )

        for item in civilizations_data:
            if not isinstance(item, dict):
                raise ValueError(
                    "Civilization records must be dictionaries."
                )

            position = Position(**item["position"])

            state = (
                SimulationPersistence
                ._deserialize_civilization_state(item)
            )

            civilization = Civilization(
                id=item["id"],
                name=item["name"],
                position=position,
                year=item["year"],
                status=CivilizationStatus(item["status"]),
                state=state,
            )

            universe.add_civilization(civilization)

        for item in events_data:
            if not isinstance(item, dict):
                raise ValueError(
                    "Event records must be dictionaries."
                )

            targets = item["target_civilization_ids"]

            event = Event(
                id=item["id"],
                event_type=item["event_type"],
                created_at=item["created_at"],
                description=item["description"],
                origin=Position(**item["origin"]),
                propagation_speed=item["propagation_speed"],
                target_civilization_ids=(
                    tuple(targets)
                    if targets is not None
                    else None
                ),
            )

            universe.add_event(event)

        for item in deliveries_data:
            if not isinstance(item, dict):
                raise ValueError(
                    "Delivery records must be dictionaries."
                )

            delivery = EventDelivery(
                event_id=item["event_id"],
                recipient_civilization_id=(
                    item["recipient_civilization_id"]
                ),
                distance=item["distance"],
                departure_time=item["departure_time"],
                arrival_time=item["arrival_time"],
                status=DeliveryStatus(item["status"]),
            )

            if delivery.event_id not in universe.events:
                raise ValueError(
                    f"Delivery references unknown event "
                    f"{delivery.event_id!r}."
                )

            if (
                delivery.recipient_civilization_id
                not in universe.civilizations
            ):
                raise ValueError(
                    "Delivery references unknown civilization "
                    f"{delivery.recipient_civilization_id!r}."
                )

            key = (
                delivery.event_id,
                delivery.recipient_civilization_id,
            )

            if key in universe.deliveries:
                raise ValueError(
                    f"Duplicate delivery for event {key[0]!r} "
                    f"and civilization {key[1]!r}."
                )

            universe.deliveries[key] = delivery

        return universe

    @staticmethod
    def _deserialize_civilization_state(
        item: dict,
    ) -> CivilizationState:
        """Load current state or migrate legacy resource data."""

        state_data = item.get("state")

        if state_data is None:
            # Migrate schema v1/v2 resource representation.
            resources = item.get("resources", {})

            if not isinstance(resources, dict):
                raise ValueError(
                    "Legacy civilization resources "
                    "must be a dictionary."
                )

            state_data = {
                "demographics": {
                    "population": resources.get(
                        "population",
                        0,
                    ),
                    "annual_population_growth_rate": (
                        resources.get(
                            "annual_population_growth_rate",
                            0.0,
                        )
                    ),
                },
                "energy": {
                    "energy_production_watts": (
                        resources.get(
                            "energy_production_watts",
                            0.0,
                        )
                    ),
                    "energy_reserve_joules": (
                        resources.get(
                            "energy_reserve_joules",
                            0.0,
                        )
                    ),
                    "energy_consumption_watts_per_person": (
                        resources.get(
                            "energy_consumption_watts_per_person",
                            0.0,
                        )
                    ),
                },
            }

        if not isinstance(state_data, dict):
            raise ValueError(
                "Civilization state must be a dictionary."
            )

        demographics_data = state_data.get(
            "demographics",
            {},
        )

        energy_data = state_data.get(
            "energy",
            {},
        )

        if not isinstance(demographics_data, dict):
            raise ValueError(
                "Demographics state must be a dictionary."
            )

        if not isinstance(energy_data, dict):
            raise ValueError(
                "Energy state must be a dictionary."
            )

        return CivilizationState(
            demographics=DemographicsState(
                **demographics_data
            ),
            energy=EnergyState(
                **energy_data
            ),
        )
