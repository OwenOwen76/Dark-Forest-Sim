from dataclasses import dataclass, field
from math import isfinite

from .civilization import Civilization, CivilizationStatus
from .event import Event, EventDelivery, DeliveryStatus


@dataclass(slots=True)
class Universe:
    """Owns and manages the simulation's world state."""

    current_time: float = 0.0

    civilizations: dict[str, Civilization] = field(default_factory=dict)
    events: dict[str, Event] = field(default_factory=dict)
    deliveries: dict[tuple[str, str], EventDelivery] = field(
        default_factory=dict
    )

    def __post_init__(self):
        if isinstance(self.current_time, bool) or not isinstance(
            self.current_time, (int, float)
        ):
            raise TypeError("Universe time must be numeric.")

        if not isfinite(self.current_time) or self.current_time < 0:
            raise ValueError("Universe time must be finite and non-negative.")

        self.current_time = round(self.current_time, 1)

    # Civilization management

    def add_civilization(self, civilization: Civilization) -> None:
        if civilization.id in self.civilizations:
            raise ValueError(
                f"Civilization '{civilization.id}' already exists."
            )

        self.civilizations[civilization.id] = civilization

    def get_civilization(self, civilization_id: str) -> Civilization:
        try:
            return self.civilizations[civilization_id]
        except KeyError:
            raise KeyError(
                f"Civilization '{civilization_id}' does not exist."
            ) from None

    def list_civilizations(self) -> list[Civilization]:
        return list(self.civilizations.values())

    # Event management

    def add_event(self, event: Event) -> None:
        if event.id in self.events:
            raise ValueError(f"Event '{event.id}' already exists.")

        self.events[event.id] = event

    def get_event(self, event_id: str) -> Event:
        try:
            return self.events[event_id]
        except KeyError:
            raise KeyError(
                f"Event '{event_id}' does not exist."
            ) from None

    def list_events(self) -> list[Event]:
        return list(self.events.values())

    # Event propagation

    def propagate_event(self, event_id: str) -> list[EventDelivery]:
        event = self.get_event(event_id)

        if event.target_civilization_ids is None:
            recipients = list(self.civilizations.values())
        else:
            recipients = [
                self.get_civilization(civ_id)
                for civ_id in event.target_civilization_ids
            ]

        # Prepare the complete batch before modifying universe state.
        new_deliveries = []

        for civilization in recipients:
            if civilization.status == CivilizationStatus.DESTROYED:
                continue

            key = (event.id, civilization.id)

            if key in self.deliveries:
                raise ValueError(
                    f"Event '{event.id}' has already been sent "
                    f"to '{civilization.id}'."
                )

            distance = event.origin.distance_to(civilization.position)
            travel_time = distance / event.propagation_speed
            arrival_time = round(event.created_at + travel_time, 1)

            delivery = EventDelivery(
                event_id=event.id,
                recipient_civilization_id=civilization.id,
                distance=distance,
                departure_time=event.created_at,
                arrival_time=arrival_time,
                status=DeliveryStatus.PENDING,
            )

            new_deliveries.append((key, delivery))

        # Commit only after every delivery has been successfully constructed.
        for key, delivery in new_deliveries:
            self.deliveries[key] = delivery

        return [
            delivery
            for _, delivery in new_deliveries
        ]

    def get_delivery(
        self, event_id: str, civilization_id: str
    ) -> EventDelivery:
        try:
            return self.deliveries[(event_id, civilization_id)]
        except KeyError:
            raise KeyError(
                f"No delivery of event '{event_id}' "
                f"to civilization '{civilization_id}'."
            ) from None

    def list_deliveries(self) -> list[EventDelivery]:
        return list(self.deliveries.values())

    # Timeline management

    def advance_time(self, to_time: float) -> list[EventDelivery]:
        """Advance the internal timeline and process event arrivals."""

        if isinstance(to_time, bool) or not isinstance(to_time, (int, float)):
            raise TypeError("Target time must be numeric.")

        if not isfinite(to_time):
            raise ValueError("Target time must be finite.")

        to_time = round(to_time, 1)

        if to_time < self.current_time:
            raise ValueError("Universe time cannot move backwards.")

        self.current_time = to_time

        return self.process_arrivals()

    def process_arrivals(self) -> list[EventDelivery]:
        """Mark all due pending deliveries as arrived."""

        arrived = []

        for delivery in self.deliveries.values():
            if (
                delivery.status == DeliveryStatus.PENDING
                and delivery.arrival_time <= self.current_time
            ):
                delivery.status = DeliveryStatus.ARRIVED
                arrived.append(delivery)

        arrived.sort(
            key=lambda delivery: (
                delivery.arrival_time,
                delivery.event_id,
                delivery.recipient_civilization_id,
            )
        )

        return arrived
