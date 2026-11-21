from dataclasses import dataclass, replace
from math import isfinite

from ..accounting import settle_stock
from ..civilization import EnergyState


SECONDS_PER_YEAR = 365.25 * 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class EnergyAdvance:
    state: EnergyState
    generated_joules: float
    demanded_joules: float
    supplied_joules: float
    unmet_demand_joules: float
    waste_heat_joules: float


def advance_energy(
    state: EnergyState,
    population: int,
    elapsed_years: float,
) -> EnergyAdvance:
    """Advance a civilization's energy balance over an interval."""

    if isinstance(population, bool) or not isinstance(population, int):
        raise TypeError("Population must be an integer.")

    if population < 0:
        raise ValueError("Energy simulation requires non-negative population.")

    if isinstance(elapsed_years, bool) or not isinstance(
        elapsed_years, (int, float)
    ):
        raise TypeError("Elapsed time must be numeric.")

    if not isfinite(elapsed_years) or elapsed_years < 0:
        raise ValueError("Elapsed time must be finite and non-negative.")

    for name, value in (
        ("Energy production", state.energy_production_watts),
        ("Energy reserves", state.energy_reserve_joules),
        ("Energy consumption per person",
         state.energy_consumption_watts_per_person),
    ):
        if value < 0:
            raise ValueError(
                f"{name} cannot be negative during energy simulation."
            )

    seconds = elapsed_years * SECONDS_PER_YEAR

    generated = state.energy_production_watts * seconds
    demanded = (
        population
        * state.energy_consumption_watts_per_person
        * seconds
    )

    balance = settle_stock(
        initial_stock=state.energy_reserve_joules,
        inflows=(generated,),
        requested_outflows=(demanded,),
    )

    updated_state = replace(
        state,
        energy_reserve_joules=balance.final_stock,
    )

    # This initial model assumes consumed energy ultimately dissipates
    # as waste heat within the civilization's environment.
    return EnergyAdvance(
        state=updated_state,
        generated_joules=generated,
        demanded_joules=demanded,
        supplied_joules=balance.actual_outflows,
        unmet_demand_joules=balance.unmet_outflows,
        waste_heat_joules=balance.actual_outflows,
    )
