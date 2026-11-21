from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .space import Position


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    ARRIVED = "arrived"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Event:
    """Represents an event occurring in the universe."""

    id: str
    event_type: str
    created_at: float
    description: str
    origin: Position
    propagation_speed: float
    target_civilization_ids: tuple[str, ...] | None = None

    def __post_init__(self):
        for name in ("id", "event_type", "description"):
            value = getattr(self, name)

            if not isinstance(value, str):
                raise TypeError(f"Event {name} must be a string.")

            if not value.strip():
                raise ValueError(f"Event {name} cannot be empty.")

        if not isinstance(self.origin, Position):
            raise TypeError("Event origin must be a Position.")

        if isinstance(self.created_at, bool) or not isinstance(
            self.created_at, (int, float)
        ):
            raise TypeError("Event creation time must be numeric.")

        if not isfinite(self.created_at) or self.created_at < 0:
            raise ValueError(
                "Event creation time must be finite and non-negative."
            )

        if isinstance(self.propagation_speed, bool) or not isinstance(
            self.propagation_speed, (int, float)
        ):
            raise TypeError("Propagation speed must be numeric.")

        if not isfinite(self.propagation_speed) or self.propagation_speed <= 0:
            raise ValueError(
                "Propagation speed must be finite and positive."
            )

        if self.target_civilization_ids is not None:
            if not isinstance(self.target_civilization_ids, (tuple, list)):
                raise TypeError("Event targets must be a list or tuple.")

            if not all(
                isinstance(target, str)
                for target in self.target_civilization_ids
            ):
                raise TypeError("Event target IDs must be strings.")

            if len(set(self.target_civilization_ids)) != len(
                self.target_civilization_ids
            ):
                raise ValueError("Event targets cannot contain duplicates.")

            if any(not target.strip() for target in self.target_civilization_ids):
                raise ValueError("Event target IDs cannot be empty.")


@dataclass(slots=True)
class EventDelivery:
    """Tracks one event travelling to one civilization."""

    event_id: str
    recipient_civilization_id: str
    distance: float
    departure_time: float
    arrival_time: float
    status: DeliveryStatus = DeliveryStatus.PENDING

    def __post_init__(self):
        for name in ("event_id", "recipient_civilization_id"):
            value = getattr(self, name)

            if not isinstance(value, str):
                raise TypeError(f"Delivery {name} must be a string.")

            if not value.strip():
                raise ValueError(f"Delivery {name} cannot be empty.")

        for name in ("distance", "departure_time", "arrival_time"):
            value = getattr(self, name)

            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"Delivery {name} must be numeric.")

            if not isfinite(value):
                raise ValueError(f"Delivery {name} must be finite.")

        if self.distance < 0:
            raise ValueError(
                "Delivery distance must be finite and non-negative."
            )

        if self.departure_time < 0 or self.arrival_time < 0:
            raise ValueError("Delivery timestamps must be non-negative.")

        if self.arrival_time < self.departure_time:
            raise ValueError("Arrival cannot precede departure.")

        try:
            self.status = DeliveryStatus(self.status)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid delivery status: {self.status}"
            ) from exc
