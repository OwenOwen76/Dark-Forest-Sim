from dataclasses import dataclass, replace
from math import floor, isfinite

from .civilization import CivilizationStatus
from .domains.energy import EnergyAdvance, advance_energy
from .universe import Universe


@dataclass(frozen=True, slots=True)
class CivilizationAdvance:
    civilization_id: str
    elapsed_years: float
    population_before: int
    population_after: int
    generated_joules: float
    demanded_joules: float
    supplied_joules: float
    unmet_demand_joules: float
    waste_heat_joules: float


@dataclass(frozen=True, slots=True)
class SimulationAdvance:
    previous_time: float
    current_time: float
    elapsed_years: float
    arrivals: list
    civilizations: list[CivilizationAdvance]


class SimulationEngine:
    """Coordinates authoritative domain updates over simulation time."""

    def __init__(self, universe: Universe, state: dict | None = None):
        self.universe = universe
        self.demographic_elapsed_years: dict[str, float] = {}

        if state is not None:
            clocks = state.get("demographic_elapsed_years", {})

            if not isinstance(clocks, dict):
                raise ValueError(
                    "Demographic elapsed-time state must be a dictionary."
                )

            for civilization_id, elapsed in clocks.items():
                if civilization_id not in universe.civilizations:
                    raise ValueError(
                        f"Unknown civilization in simulation clocks: "
                        f"{civilization_id!r}"
                    )

                if (
                    isinstance(elapsed, bool)
                    or not isinstance(elapsed, (int, float))
                    or not isfinite(elapsed)
                    or not 0 <= elapsed < 1
                ):
                    raise ValueError(
                        f"Invalid demographic clock for {civilization_id!r}."
                    )

                self.demographic_elapsed_years[civilization_id] = float(
                    elapsed
                )

    def to_dict(self) -> dict:
        return {
            "demographic_elapsed_years": dict(
                self.demographic_elapsed_years
            ),
        }

    def advance_to(self, to_time: float) -> SimulationAdvance:
        if isinstance(to_time, bool) or not isinstance(
            to_time, (int, float)
        ):
            raise TypeError("Target time must be numeric.")

        if not isfinite(to_time):
            raise ValueError("Target time must be finite.")

        if to_time < self.universe.current_time:
            raise ValueError("Universe time cannot move backwards.")

        previous_time = self.universe.current_time
        elapsed = float(to_time - previous_time)

        staged_states = {}
        staged_clocks = dict(self.demographic_elapsed_years)
        reports = []

        # Calculate every civilization's changes before committing any.
        for civilization in self.universe.civilizations.values():
            if civilization.status == CivilizationStatus.DESTROYED:
                staged_clocks.pop(civilization.id, None)
                continue

            demographics = civilization.state.demographics
            energy = civilization.state.energy

            population = demographics.population
            growth_rate = demographics.annual_population_growth_rate

            if population < 0:
                raise ValueError(
                    f"{civilization.id}: population cannot be negative "
                    "during demographic simulation."
                )

            if growth_rate < -1:
                raise ValueError(
                    f"{civilization.id}: annual population growth rate "
                    "cannot be below -100%."
                )

            remaining = elapsed
            demographic_clock = staged_clocks.get(civilization.id, 0.0)

            population_before = population
            generated = 0.0
            demanded = 0.0
            supplied = 0.0
            unmet = 0.0
            waste_heat = 0.0
            updated_energy = energy

            while remaining > 1e-12:
                until_annual_update = 1.0 - demographic_clock
                interval = min(remaining, until_annual_update)

                energy_result: EnergyAdvance = advance_energy(
                    updated_energy,
                    population,
                    interval,
                )

                updated_energy = energy_result.state
                generated += energy_result.generated_joules
                demanded += energy_result.demanded_joules
                supplied += energy_result.supplied_joules
                unmet += energy_result.unmet_demand_joules
                waste_heat += energy_result.waste_heat_joules

                remaining -= interval
                demographic_clock += interval

                if demographic_clock >= 1.0 - 1e-12:
                    # Deterministic nearest-integer population update.
                    population = floor(
                        population * (1.0 + growth_rate) + 0.5
                    )
                    demographic_clock = 0.0

            staged_clocks[civilization.id] = demographic_clock

            staged_states[civilization.id] = replace(
                civilization.state,
                demographics=replace(
                    demographics,
                    population=population,
                ),
                energy=updated_energy,
            )

            reports.append(
                CivilizationAdvance(
                    civilization_id=civilization.id,
                    elapsed_years=elapsed,
                    population_before=population_before,
                    population_after=population,
                    generated_joules=generated,
                    demanded_joules=demanded,
                    supplied_joules=supplied,
                    unmet_demand_joules=unmet,
                    waste_heat_joules=waste_heat,
                )
            )

        # All domain calculations succeeded. Commit the timeline and state.
        arrivals = self.universe.advance_time(to_time)

        for civilization_id, state in staged_states.items():
            self.universe.civilizations[civilization_id].state = state

        self.demographic_elapsed_years = staged_clocks

        return SimulationAdvance(
            previous_time=previous_time,
            current_time=self.universe.current_time,
            elapsed_years=elapsed,
            arrivals=arrivals,
            civilizations=reports,
        )
