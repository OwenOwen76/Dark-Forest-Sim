from dataclasses import dataclass
from math import ceil

from .civilization import Civilization, CivilizationStatus
from .event import DeliveryStatus, EventDelivery
from .universe import Universe


@dataclass(slots=True)
class SchedulerUpdate:
    """Reports what happened during an idle timeline advancement."""

    advanced_to: float | None
    arrivals: list[EventDelivery]
    awakened: list[Civilization]


@dataclass(slots=True)
class CivilizationScheduler:
    """Manages civilization sleep schedules and turn selection."""

    wake_times: dict[str, float]

    def __init__(self):
        self.wake_times = {}

    def sleep_civilization(
        self,
        universe: Universe,
        civilization_id: str,
        years: int,
    ) -> float:
        """Put a civilization to sleep for a requested number of years."""

        if isinstance(years, bool) or not isinstance(years, int):
            raise TypeError("Sleep duration must be an integer.")

        if years <= 0:
            raise ValueError("Sleep duration must be positive.")

        civilization = universe.get_civilization(civilization_id)

        if civilization.status != CivilizationStatus.ACTIVE:
            raise ValueError("Only active civilizations can go to sleep.")

        wake_time = float(civilization.year + years)

        civilization.status = CivilizationStatus.SLEEPING
        self.wake_times[civilization_id] = wake_time

        return wake_time

    def wake_civilization(
        self,
        universe: Universe,
        civilization_id: str,
        interrupt: bool = False,
    ) -> Civilization:
        """Wake a civilization, optionally interrupting its sleep."""

        civilization = universe.get_civilization(civilization_id)

        if civilization.status != CivilizationStatus.SLEEPING:
            raise ValueError("Civilization is not sleeping.")

        wake_time = self.wake_times.get(civilization_id)

        if wake_time is None:
            raise ValueError("Sleeping civilization has no wake schedule.")

        if universe.current_time < wake_time and not interrupt:
            raise ValueError("Civilization's scheduled wake time has not arrived.")

        actual_year = ceil(universe.current_time - 1e-9)

        civilization.year = max(civilization.year, actual_year)
        civilization.status = CivilizationStatus.ACTIVE

        del self.wake_times[civilization_id]

        return civilization

    def wake_due_civilizations(
        self,
        universe: Universe,
    ) -> list[Civilization]:
        """Wake all civilizations whose scheduled time has arrived."""

        due = sorted(
            (
                (wake_time, civilization_id)
                for civilization_id, wake_time in self.wake_times.items()
                if wake_time <= universe.current_time
            ),
            key=lambda item: (item[0], item[1]),
        )

        awakened = []

        for _, civilization_id in due:
            awakened.append(
                self.wake_civilization(universe, civilization_id)
            )

        return awakened

    def get_next_civilization(
        self,
        universe: Universe,
    ) -> Civilization | None:
        """Select the active civilization with the lowest local year."""

        eligible = [
            civilization
            for civilization in universe.civilizations.values()
            if civilization.status == CivilizationStatus.ACTIVE
        ]

        if not eligible:
            return None

        return min(
            eligible,
            key=lambda civilization: (
                civilization.year,
                civilization.id,
            ),
        )

    def advance_when_idle(
        self,
        universe: Universe,
    ) -> SchedulerUpdate:
        """
        Advance the timeline when no civilization is active.

        Stops at the next event arrival or scheduled civilization wake.
        """

        if self.get_next_civilization(universe) is not None:
            raise ValueError("Cannot advance automatically while a civilization is active.")

        # Process anything already due at the current time.
        arrivals = universe.process_arrivals()
        awakened = self.wake_due_civilizations(universe)

        if arrivals or awakened:
            return SchedulerUpdate(
                advanced_to=None,
                arrivals=arrivals,
                awakened=awakened,
            )

        future_times = [
            wake_time
            for wake_time in self.wake_times.values()
            if wake_time > universe.current_time
        ]

        future_times.extend(
            delivery.arrival_time
            for delivery in universe.deliveries.values()
            if (
                delivery.status == DeliveryStatus.PENDING
                and delivery.arrival_time > universe.current_time
            )
        )

        if not future_times:
            return SchedulerUpdate(
                advanced_to=None,
                arrivals=[],
                awakened=[],
            )

        next_time = min(future_times)

        arrivals = universe.advance_time(next_time)
        awakened = self.wake_due_civilizations(universe)

        return SchedulerUpdate(
            advanced_to=next_time,
            arrivals=arrivals,
            awakened=awakened,
        )
