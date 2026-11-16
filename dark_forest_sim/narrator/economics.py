from math import isfinite


def calculate_kardashev_energy_output(kardashev_scale: float) -> float:
    """Calculate energy production in watts for a Kardashev scale."""

    if not isfinite(kardashev_scale):
        raise ValueError("Kardashev scale must be finite.")

    if kardashev_scale < 0:
        raise ValueError("Kardashev scale must be non-negative.")

    return 10 ** (10 * kardashev_scale + 6)


def calculate_population_after_growth(
    population: int,
    annual_growth_rate: float,
    years: int,
) -> float:
    """Calculate population using compound annual growth."""

    if isinstance(population, bool) or not isinstance(population, int):
        raise ValueError("Population must be an integer.")

    if population < 0:
        raise ValueError("Population must be non-negative.")

    if not isfinite(annual_growth_rate) or annual_growth_rate <= -1:
        raise ValueError("Growth rate must be finite and greater than -1.")

    if isinstance(years, bool) or not isinstance(years, int) or years < 0:
        raise ValueError("Years must be a non-negative integer.")

    return population * (1 + annual_growth_rate) ** years


def calculate_energy_budget(
    population: int,
    energy_production_watts: float,
    energy_consumption_watts_per_person: float,
) -> dict:
    """Calculate civilization energy demand, surplus, and deficit."""

    if isinstance(population, bool) or not isinstance(population, int):
        raise ValueError("Population must be an integer.")

    if population < 0:
        raise ValueError("Population must be non-negative.")

    for name, value in (
        ("Energy production", energy_production_watts),
        ("Energy consumption", energy_consumption_watts_per_person),
    ):
        if not isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and non-negative.")

    demand = population * energy_consumption_watts_per_person
    surplus = max(0.0, energy_production_watts - demand)
    deficit = max(0.0, demand - energy_production_watts)

    return {
        "total_demand_watts": demand,
        "surplus_watts": surplus,
        "deficit_watts": deficit,
        "energy_production_watts": energy_production_watts,
    }
