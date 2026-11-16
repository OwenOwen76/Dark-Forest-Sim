from math import isfinite
from dataclasses import asdict

from ..engine.event import DeliveryStatus
from ..engine.space import Position
from ..engine.universe import Universe


def get_universe_status(universe: Universe) -> dict:
    """Return a summary of the universe."""

    return {
        "current_time": universe.current_time,
        "civilization_count": len(universe.civilizations),
        "event_count": len(universe.events),
        "delivery_count": len(universe.deliveries),
        "pending_deliveries": sum(
            delivery.status == DeliveryStatus.PENDING
            for delivery in universe.deliveries.values()
        ),
    }


def list_civilizations(universe: Universe) -> list[dict]:
    """List all civilizations."""

    return [
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
            "resources": asdict(civ.resources),
        }
        for civ in universe.list_civilizations()
    ]


def inspect_civilization(
    universe: Universe,
    civilization_id: str,
) -> dict:
    """Inspect an individual civilization."""

    civ = universe.get_civilization(civilization_id)

    return {
        "id": civ.id,
        "name": civ.name,
        "position": {
            "x": civ.position.x,
            "y": civ.position.y,
            "z": civ.position.z,
        },
        "year": civ.year,
        "status": civ.status.value,
        "resources": asdict(civ.resources),
    }


def list_events(universe: Universe) -> list[dict]:
    """List all events."""

    return [
        {
            "id": event.id,
            "type": event.event_type,
            "created_at": event.created_at,
            "description": event.description,
            "origin": {
                "x": event.origin.x,
                "y": event.origin.y,
                "z": event.origin.z,
            },
            "propagation_speed": event.propagation_speed,
            "targets": event.target_civilization_ids,
        }
        for event in universe.list_events()
    ]


def inspect_event(universe: Universe, event_id: str) -> dict:
    """Inspect an individual event and its deliveries."""

    event = universe.get_event(event_id)

    deliveries = [
        delivery
        for delivery in universe.list_deliveries()
        if delivery.event_id == event_id
    ]

    return {
        "id": event.id,
        "type": event.event_type,
        "created_at": event.created_at,
        "description": event.description,
        "origin": {
            "x": event.origin.x,
            "y": event.origin.y,
            "z": event.origin.z,
        },
        "propagation_speed": event.propagation_speed,
        "targets": event.target_civilization_ids,
        "deliveries": [
            {
                "recipient": delivery.recipient_civilization_id,
                "distance": delivery.distance,
                "departure_time": delivery.departure_time,
                "arrival_time": delivery.arrival_time,
                "status": delivery.status.value,
            }
            for delivery in deliveries
        ],
    }


def list_deliveries(universe: Universe) -> list[dict]:
    """List all event deliveries."""

    return [
        {
            "event_id": delivery.event_id,
            "recipient": delivery.recipient_civilization_id,
            "distance": delivery.distance,
            "departure_time": delivery.departure_time,
            "arrival_time": delivery.arrival_time,
            "status": delivery.status.value,
        }
        for delivery in universe.list_deliveries()
    ]


def calculate_distance(
    x1: float,
    y1: float,
    z1: float,
    x2: float,
    y2: float,
    z2: float,
) -> float:
    """Calculate the distance between two 3D positions."""

    first = Position(x1, y1, z1)
    second = Position(x2, y2, z2)

    return first.distance_to(second)


def calculate_travel_time(
    distance: float,
    speed: float,
) -> float:
    """Calculate travel time in years."""

    if not isfinite(distance) or distance < 0:
        raise ValueError("Distance must be finite and non-negative.")

    if not isfinite(speed) or speed <= 0:
        raise ValueError("Speed must be finite and positive.")

    return round(distance / speed, 1)

def can_civilization_know_event(
    universe: Universe,
    event_id: str,
    civilization_id: str,
) -> bool:
    """Check whether an event has reached a civilization."""

    universe.get_event(event_id)
    universe.get_civilization(civilization_id)

    delivery = universe.deliveries.get((event_id, civilization_id))

    if delivery is None:
        return False

    return (
        delivery.status == DeliveryStatus.ARRIVED
        and delivery.arrival_time <= universe.current_time
    )

def list_known_events(
    universe: Universe,
    civilization_id: str,
) -> list[dict]:
    """Return only events that have arrived at this civilization."""

    universe.get_civilization(civilization_id)

    known_events = []

    for delivery in universe.list_deliveries():
        if delivery.recipient_civilization_id != civilization_id:
            continue

        if delivery.status != DeliveryStatus.ARRIVED:
            continue

        if delivery.arrival_time > universe.current_time:
            continue

        event = universe.get_event(delivery.event_id)

        known_events.append({
            "event_id": event.id,
            "event_type": event.event_type,
            "description": event.description,
            "created_at": event.created_at,
            "origin": {
                "x": event.origin.x,
                "y": event.origin.y,
                "z": event.origin.z,
            },
            "delivery": {
                "distance": delivery.distance,
                "departure_time": delivery.departure_time,
                "arrival_time": delivery.arrival_time,
            },
        })

    return sorted(
        known_events,
        key=lambda event: (
            event["delivery"]["arrival_time"],
            event["event_id"],
        ),
    )
