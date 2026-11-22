from dataclasses import dataclass, field

from .civilization import Civilization, CivilizationStatus
from .event import DeliveryStatus, EventDelivery
from .universe import Universe


@dataclass(slots=True)
class SchedulerUpdate:
    advanced_to: float | None
    arrivals: list[EventDelivery]
    awakened: list[Civilization]


@dataclass(slots=True)
class CivilizationScheduler:
    wake_times: dict[str, float] = field(default_factory=dict)
    sleep_started_at: dict[str, float] = field(default_factory=dict)
    sleep_start_local_year: dict[str, int] = field(default_factory=dict)

    def sleep_civilization(
        self,
        universe: Universe,
        civilization_id: str,
        years: int,
    ) -> float:
        if isinstance(years, bool) or not isinstance(years, int):
            raise TypeError(
                "Sleep duration must be an integer."
            )

        if years <= 0:
            raise ValueError(
                "Sleep duration must be positive."
            )

        civilization = universe.get_civilization(
            civilization_id
        )

        if civilization.status != CivilizationStatus.ACTIVE:
            raise ValueError(
                "Only active civilizations can go to sleep."
            )

        if civilization_id in self.wake_times:
            raise ValueError(
                "Civilization already has a wake schedule."
            )

        wake_time = float(
            universe.current_time + years
        )

        civilization.status = (
            CivilizationStatus.SLEEPING
        )

        self.wake_times[civilization_id] = (
            wake_time
        )
        self.sleep_started_at[civilization_id] = (
            float(universe.current_time)
        )
        self.sleep_start_local_year[civilization_id] = (
            civilization.year
        )

        return wake_time

    def wake_civilization(
        self,
        universe: Universe,
        civilization_id: str,
        interrupt: bool = False,
    ) -> Civilization:
        civilization = universe.get_civilization(
            civilization_id
        )

        if civilization.status != CivilizationStatus.SLEEPING:
            raise ValueError(
                "Civilization is not sleeping."
            )

        wake_time = self.wake_times.get(
            civilization_id
        )

        if wake_time is None:
            raise ValueError(
                "Sleeping civilization has no wake schedule."
            )

        if (
            universe.current_time < wake_time
            and not interrupt
        ):
            raise ValueError(
                "Civilization's scheduled wake time "
                "has not arrived."
            )

        started_at = self.sleep_started_at.get(
            civilization_id
        )
        starting_year = (
            self.sleep_start_local_year.get(
                civilization_id
            )
        )

        if (
            started_at is None
            or starting_year is None
        ):
            raise ValueError(
                "Civilization's sleep metadata is incomplete."
            )

        elapsed = max(
            0.0,
            universe.current_time - started_at,
        )

        completed_years = int(
            elapsed + 1e-9
        )

        civilization.year = (
            starting_year + completed_years
        )
        civilization.status = (
            CivilizationStatus.ACTIVE
        )

        self._clear_schedule(
            civilization_id
        )

        return civilization

    def _clear_schedule(
        self,
        civilization_id: str,
    ) -> None:
        self.wake_times.pop(
            civilization_id,
            None,
        )
        self.sleep_started_at.pop(
            civilization_id,
            None,
        )
        self.sleep_start_local_year.pop(
            civilization_id,
            None,
        )

    def wake_due_civilizations(
        self,
        universe: Universe,
    ) -> list[Civilization]:
        due = sorted(
            (
                (
                    wake_time,
                    civilization_id,
                )
                for (
                    civilization_id,
                    wake_time,
                ) in self.wake_times.items()
                if wake_time
                <= universe.current_time
            ),
            key=lambda item: (
                item[0],
                item[1],
            ),
        )

        return [
            self.wake_civilization(
                universe,
                civilization_id,
            )
            for (
                _,
                civilization_id,
            ) in due
        ]

    def get_next_civilization(
        self,
        universe: Universe,
    ) -> Civilization | None:
        eligible = [
            civilization
            for civilization
            in universe.civilizations.values()
            if civilization.status
            == CivilizationStatus.ACTIVE
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

    def get_next_wake_time(
        self,
        universe: Universe,
    ) -> float | None:
        future_times = [
            wake_time
            for wake_time
            in self.wake_times.values()
            if wake_time
            > universe.current_time
        ]

        future_times.extend(
            delivery.arrival_time
            for delivery
            in universe.deliveries.values()
            if (
                delivery.status
                == DeliveryStatus.PENDING
                and delivery.arrival_time
                > universe.current_time
            )
        )

        if not future_times:
            return None

        return min(future_times)

    def advance_when_idle(
        self,
        universe: Universe,
        simulation_engine=None,
    ) -> SchedulerUpdate:
        """
        Advance simulation time when no civilization is
        currently eligible to act.
        """

        if (
            self.get_next_civilization(
                universe
            )
            is not None
        ):
            raise ValueError(
                "Cannot advance automatically while "
                "a civilization is active."
            )

        if simulation_engine is not None:
            if (
                simulation_engine.universe
                is not universe
            ):
                raise ValueError(
                    "Simulation engine belongs to "
                    "a different universe."
                )

        arrivals = (
            universe.process_arrivals()
        )
        awakened = (
            self.wake_due_civilizations(
                universe
            )
        )

        if arrivals or awakened:
            return SchedulerUpdate(
                None,
                arrivals,
                awakened,
            )

        next_time = (
            self.get_next_wake_time(
                universe
            )
        )

        if next_time is None:
            return SchedulerUpdate(
                None,
                [],
                [],
            )

        if simulation_engine is None:
            arrivals = (
                universe.advance_time(
                    next_time
                )
            )
        else:
            update = (
                simulation_engine.advance_to(
                    next_time
                )
            )
            arrivals = update.arrivals

        awakened = (
            self.wake_due_civilizations(
                universe
            )
        )

        return SchedulerUpdate(
            next_time,
            arrivals,
            awakened,
        )
