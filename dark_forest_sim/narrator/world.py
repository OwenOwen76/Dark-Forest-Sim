from dataclasses import asdict, replace

from ..engine.civilization import (
    Civilization,
    CivilizationState,
    CivilizationStatus,
    DemographicsState,
    EnergyState,
)
from ..engine.event import Event
from ..engine.scheduler import CivilizationScheduler
from ..engine.simulation import SimulationEngine
from ..engine.space import Position
from ..engine.universe import Universe


def create_civilization(
    universe: Universe,
    civilization_id: str,
    name: str,
    x: float,
    y: float,
    z: float,
    year: int,
) -> dict:
    """Create a civilization at a specified capital-planet position."""

    civilization = Civilization(
        id=civilization_id,
        name=name,
        position=Position(x, y, z),
        year=year,
    )

    universe.add_civilization(civilization)

    return {
        "id": civilization.id,
        "name": civilization.name,
        "position": {
            "x": civilization.position.x,
            "y": civilization.position.y,
            "z": civilization.position.z,
        },
        "year": civilization.year,
        "status": civilization.status.value,
    }


def modify_civilization(
    universe: Universe,
    civilization_id: str,
    name: str | None = None,
    x: float | None = None,
    y: float | None = None,
    z: float | None = None,
) -> dict:
    """Modify a civilization's name or capital-planet position."""

    civilization = universe.get_civilization(civilization_id)

    coordinates = (x, y, z)
    updated_position = None

    if any(value is not None for value in coordinates):
        if not all(value is not None for value in coordinates):
            raise ValueError(
                "Provide all three coordinates: x, y, and z."
            )

        updated_position = Position(x, y, z)  # type: ignore

    if name is not None:
        if not isinstance(name, str):
            raise TypeError("Civilization name must be a string.")

        if not name.strip():
            raise ValueError("Civilization name cannot be empty.")

    if name is None and all(value is None for value in coordinates):
        raise ValueError("No modifications were provided.")

    # All validation is complete. Apply changes now.
    if updated_position is not None:
        civilization.position = updated_position

    if name is not None:
        civilization.name = name

    return {
        "id": civilization.id,
        "name": civilization.name,
        "position": {
            "x": civilization.position.x,
            "y": civilization.position.y,
            "z": civilization.position.z,
        },
    }


def destroy_civilization(
    universe: Universe,
    scheduler: CivilizationScheduler,
    civilization_id: str,
) -> dict:
    """Mark a civilization as destroyed."""

    civilization = universe.get_civilization(civilization_id)

    civilization.status = CivilizationStatus.DESTROYED
    scheduler._clear_schedule(civilization_id)

    return {
        "id": civilization.id,
        "status": civilization.status.value,
    }


def create_event(
    universe: Universe,
    event_id: str,
    event_type: str,
    created_at: float,
    description: str,
    x: float,
    y: float,
    z: float,
    propagation_speed: float,
    target_civilization_ids: list[str] | None = None,
) -> dict:
    """Create an event without automatically propagating it."""

    event = Event(
        id=event_id,
        event_type=event_type,
        created_at=created_at,
        description=description,
        origin=Position(x, y, z),
        propagation_speed=propagation_speed,
        target_civilization_ids=(
            tuple(target_civilization_ids)
            if target_civilization_ids is not None
            else None
        ),
    )

    universe.add_event(event)

    return {
        "id": event.id,
        "type": event.event_type,
        "created_at": event.created_at,
        "description": event.description,
    }


def propagate_event(
    universe: Universe,
    event_id: str,
) -> list[dict]:
    """Create individual deliveries for an event's recipients."""

    deliveries = universe.propagate_event(event_id)

    return [
        {
            "event_id": delivery.event_id,
            "recipient": delivery.recipient_civilization_id,
            "distance": delivery.distance,
            "departure_time": delivery.departure_time,
            "arrival_time": delivery.arrival_time,
            "status": delivery.status.value,
        }
        for delivery in deliveries
    ]


def advance_time(
    universe: Universe,
    to_time: float,
    simulation_engine: SimulationEngine | None = None,
) -> dict:
    """Advance the universe and all active simulation domains."""

    if simulation_engine is not None:
        if simulation_engine.universe is not universe:
            raise ValueError(
                "Simulation engine belongs to a different universe."
            )

        update = simulation_engine.advance_to(to_time)
        arrivals = update.arrivals
    else:
        arrivals = universe.advance_time(to_time)
        update = None

    return {
        "current_time": universe.current_time,
        "arrivals": [
            {
                "event_id": delivery.event_id,
                "recipient": delivery.recipient_civilization_id,
                "arrival_time": delivery.arrival_time,
            }
            for delivery in arrivals
        ],
        "civilization_updates": (
            [
                {
                    "civilization_id": report.civilization_id,
                    "population_before": report.population_before,
                    "population_after": report.population_after,
                    "generated_joules": report.generated_joules,
                    "demanded_joules": report.demanded_joules,
                    "supplied_joules": report.supplied_joules,
                    "unmet_demand_joules": report.unmet_demand_joules,
                    "waste_heat_joules": report.waste_heat_joules,
                }
                for report in update.civilizations
            ]
            if update is not None
            else []
        ),
    }


def sleep_civilization(
    universe: Universe,
    scheduler: CivilizationScheduler,
    civilization_id: str,
    years: int,
) -> dict:
    """Put a civilization to sleep for a specified duration."""

    wake_time = scheduler.sleep_civilization(
        universe,
        civilization_id,
        years,
    )

    return {
        "civilization_id": civilization_id,
        "wake_time": wake_time,
    }


def wake_civilization(
    universe: Universe,
    scheduler: CivilizationScheduler,
    civilization_id: str,
    interrupt: bool = False,
) -> dict:
    """Wake a civilization, optionally interrupting its sleep."""

    civilization = scheduler.wake_civilization(
        universe,
        civilization_id,
        interrupt,
    )

    return {
        "civilization_id": civilization.id,
        "local_year": civilization.year,
        "status": civilization.status.value,
    }


def advance_when_idle(
    universe: Universe,
    scheduler: CivilizationScheduler,
    simulation_engine: SimulationEngine | None = None,
) -> dict:
    """Advance to the next wake or event arrival and simulate elapsed time."""

    update = scheduler.advance_when_idle(
        universe,
        simulation_engine,
    )

    return {
        "current_time": universe.current_time,
        "advanced_to": update.advanced_to,
        "arrivals": [
            {
                "event_id": delivery.event_id,
                "recipient": delivery.recipient_civilization_id,
                "arrival_time": delivery.arrival_time,
            }
            for delivery in update.arrivals
        ],
        "awakened": [
            {
                "id": civilization.id,
                "year": civilization.year,
            }
            for civilization in update.awakened
        ],
    }


def update_civilization_state(
    universe: Universe,
    civilization_id: str,
    demographics: dict | None = None,
    energy: dict | None = None,
) -> dict:
    """Atomically update one or more civilization state domains."""

    civilization = universe.get_civilization(civilization_id)

    if demographics is None and energy is None:
        raise ValueError("At least one domain update must be provided.")

    if demographics is not None:
        if not isinstance(demographics, dict) or not demographics:
            raise ValueError(
                "demographics must be a non-empty dictionary."
            )

        allowed = set(DemographicsState.__dataclass_fields__)
        unexpected = set(demographics) - allowed

        if unexpected:
            raise ValueError(
                f"Unknown demographic fields: {sorted(unexpected)}"
            )

    if energy is not None:
        if not isinstance(energy, dict) or not energy:
            raise ValueError(
                "energy must be a non-empty dictionary."
            )

        allowed = set(EnergyState.__dataclass_fields__)
        unexpected = set(energy) - allowed

        if unexpected:
            raise ValueError(
                f"Unknown energy fields: {sorted(unexpected)}"
            )

    # Construct all replacements before mutating the civilization.
    updated_demographics = (
        replace(civilization.state.demographics, **demographics)
        if demographics is not None
        else civilization.state.demographics
    )

    updated_energy = (
        replace(civilization.state.energy, **energy)
        if energy is not None
        else civilization.state.energy
    )

    updated_state = CivilizationState(
        demographics=updated_demographics,
        energy=updated_energy,
    )

    civilization.state = updated_state

    return {
        "civilization_id": civilization.id,
        "state": asdict(updated_state),
    }
