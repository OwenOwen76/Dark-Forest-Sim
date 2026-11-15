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
        if not self.id.strip():
            raise ValueError("Event ID cannot be empty.")

        if not self.event_type.strip():
            raise ValueError("Event type cannot be empty.")

        if not self.description.strip():
            raise ValueError("Event description cannot be empty.")

        if not isinstance(self.origin, Position):
            raise TypeError("Event origin must be a Position.")

        if isinstance(self.created_at, bool) or not isinstance(
            self.created_at, (int, float)
        ):
            raise TypeError("Event creation time must be numeric.")

        if not isfinite(self.created_at) or self.created_at < 0:
            raise ValueError("Event creation time must be finite and non-negative.")

        if isinstance(self.propagation_speed, bool) or not isinstance(
            self.propagation_speed, (int, float)
        ):
            raise TypeError("Propagation speed must be numeric.")

        if not isfinite(self.propagation_speed) or self.propagation_speed <= 0:
            raise ValueError("Propagation speed must be finite and positive.")

        self.created_at = round(self.created_at, 1)

        if self.target_civilization_ids is not None:
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
        if not isfinite(self.distance) or self.distance < 0:
            raise ValueError("Delivery distance must be finite and non-negative.")

        if not isfinite(self.departure_time) or not isfinite(self.arrival_time):
            raise ValueError("Delivery timestamps must be finite.")

        if self.arrival_time < self.departure_time:
            raise ValueError("Arrival cannot precede departure.")
