import json
import os
import tempfile
from pathlib import Path
from typing import Any
from math import isfinite

from ..engine.civilization import (
    Civilization,
    CivilizationStatus,
    CivilizationResources,
)
from ..engine.event import Event, EventDelivery, DeliveryStatus
from ..engine.scheduler import CivilizationScheduler
from ..engine.space import Position
from ..engine.universe import Universe


SCHEMA_VERSION = 2
SUPPORTED_SCHEMA_VERSIONS = {1, 2}


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
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "schema_version": SCHEMA_VERSION,
            "simulation": runtime_state,
            "universe": self._serialize_universe(universe),
            "scheduler": {
                "wake_times": scheduler.wake_times,
            },
            "agent_states": self._serialize_records(agent_states),
            "tool_call_journal": self._serialize_records(tool_call_journal),
        }

        content = json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )

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
    def _serialize_records(records: dict | None) -> dict:
        if records is None:
            return {}

        if not isinstance(records, dict):
            raise ValueError("Persistent records must be dictionaries")

        serialized = {}

        for key, record in records.items():
            if hasattr(record, "to_dict"):
                serialized[key] = record.to_dict()
            elif isinstance(record, dict):
                serialized[key] = record
            else:
                raise ValueError(
                    f"Record {key!r} must be a dictionary or support to_dict()"
                )

        return serialized

    def load(self) -> dict | None:
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
            raise ValueError("Simulation save must contain a JSON object.")

        version = data.get("schema_version")

        if (
            isinstance(version, bool)
            or not isinstance(version, int)
            or version not in SUPPORTED_SCHEMA_VERSIONS
        ):
            raise ValueError(
                f"Unsupported save version: {version}. "
                f"Supported versions: {sorted(SUPPORTED_SCHEMA_VERSIONS)}."
            )

        try:
            universe = self._deserialize_universe(data["universe"])

            scheduler_data = data["scheduler"]

            if not isinstance(scheduler_data, dict):
                raise ValueError("scheduler must be a dictionary.")

            wake_times = scheduler_data["wake_times"]

            if not isinstance(wake_times, dict):
                raise ValueError("scheduler wake_times must be a dictionary.")

            scheduler = CivilizationScheduler()

            for civilization_id, wake_time in wake_times.items():
                if not isinstance(civilization_id, str):
                    raise ValueError("Wake schedule IDs must be strings.")

                if (
                    isinstance(wake_time, bool)
                    or not isinstance(wake_time, (int, float))
                ):
                    raise ValueError(
                        f"Wake time for {civilization_id!r} must be numeric."
                    )

                if not isfinite(wake_time) or wake_time < 0:
                    raise ValueError(
                        f"Wake time for {civilization_id!r} "
                        "must be finite and non-negative."
                    )

                civilization = universe.get_civilization(civilization_id)

                scheduler.wake_times[civilization_id] = float(wake_time)

            for civilization in universe.civilizations.values():
                if (
                    civilization.status == CivilizationStatus.SLEEPING
                    and civilization.id not in scheduler.wake_times
                ):
                    raise ValueError(
                        f"Sleeping civilization {civilization.id!r} "
                        "has no wake schedule."
                    )

            simulation = data["simulation"]

            if not isinstance(simulation, dict):
                raise ValueError("simulation must be a dictionary.")

            agent_states = data.get("agent_states", {})
            tool_call_journal = data.get("tool_call_journal", {})

            if not isinstance(agent_states, dict):
                raise ValueError("agent_states must be a dictionary.")

            if not isinstance(tool_call_journal, dict):
                raise ValueError("tool_call_journal must be a dictionary.")

            return {
                "universe": universe,
                "scheduler": scheduler,
                "simulation": simulation,
                "agent_states": agent_states,
                "tool_call_journal": tool_call_journal,
                "loaded_schema_version": version,
            }

        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                f"Simulation save has an invalid structure: {exc}"
            ) from exc

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
                    "resources": {
                        "population": civ.resources.population,
                        "annual_population_growth_rate":
                            civ.resources.annual_population_growth_rate,
                        "energy_production_watts": civ.resources.energy_production_watts,
                        "energy_reserve_joules": civ.resources.energy_reserve_joules,
                        "energy_consumption_watts_per_person":
                            civ.resources.energy_consumption_watts_per_person,
                    },
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
                    "recipient_civilization_id":
                        delivery.recipient_civilization_id,
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
            raise ValueError("universe must be a dictionary.")

        civilizations_data = data["civilizations"]
        events_data = data["events"]
        deliveries_data = data["deliveries"]

        if not isinstance(civilizations_data, list):
            raise ValueError("civilizations must be a list.")

        if not isinstance(events_data, list):
            raise ValueError("events must be a list.")

        if not isinstance(deliveries_data, list):
            raise ValueError("deliveries must be a list.")

        universe = Universe(current_time=data["current_time"])

        for item in civilizations_data:
            if not isinstance(item, dict):
                raise ValueError("Civilization records must be dictionaries.")

            position = Position(**item["position"])
            resources = CivilizationResources(**item.get("resources", {}))

            civilization = Civilization(
                id=item["id"],
                name=item["name"],
                position=position,
                year=item["year"],
                status=CivilizationStatus(item["status"]),
                resources=resources,
            )

            universe.add_civilization(civilization)

        for item in events_data:
            if not isinstance(item, dict):
                raise ValueError("Event records must be dictionaries.")

            targets = item["target_civilization_ids"]

            event = Event(
                id=item["id"],
                event_type=item["event_type"],
                created_at=item["created_at"],
                description=item["description"],
                origin=Position(**item["origin"]),
                propagation_speed=item["propagation_speed"],
                target_civilization_ids=(
                    tuple(targets) if targets is not None else None
                ),
            )

            universe.add_event(event)

        for item in deliveries_data:
            if not isinstance(item, dict):
                raise ValueError("Delivery records must be dictionaries.")

            delivery = EventDelivery(
                event_id=item["event_id"],
                recipient_civilization_id=item[
                    "recipient_civilization_id"
                ],
                distance=item["distance"],
                departure_time=item["departure_time"],
                arrival_time=item["arrival_time"],
                status=DeliveryStatus(item["status"]),
            )

            if delivery.event_id not in universe.events:
                raise ValueError(
                    f"Delivery references unknown event {delivery.event_id!r}."
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
