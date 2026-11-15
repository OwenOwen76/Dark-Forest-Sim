from ..engine.civilization import Civilization, CivilizationStatus
from ..engine.event import Event
from ..engine.scheduler import CivilizationScheduler
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

    if any(value is not None for value in coordinates):
        if not all(value is not None for value in coordinates):
            raise ValueError("Provide all three coordinates: x, y, and z.")

        civilization.position = Position(x, y, z)

    if name is not None:
        if not name.strip():
            raise ValueError("Civilization name cannot be empty.")

        civilization.name = name

    if name is None and all(value is None for value in coordinates):
        raise ValueError("No modifications were provided.")

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
    scheduler.wake_times.pop(civilization_id, None)

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
) -> dict:
    """Advance the universe's internal timeline."""

    arrivals = universe.advance_time(to_time)

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
) -> dict:
    """Advance to the next scheduled wake or pending event arrival."""

    update = scheduler.advance_when_idle(universe)

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
