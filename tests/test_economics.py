import pytest

from dark_forest_sim.narrator.economics import (
    calculate_kardashev_energy_output,
    calculate_population_after_growth,
    calculate_energy_budget,
)


def test_kardashev_type_zero_energy_output():
    assert calculate_kardashev_energy_output(0) == pytest.approx(1e6)


def test_kardashev_type_one_energy_output():
    assert calculate_kardashev_energy_output(1) == pytest.approx(1e16)


def test_kardashev_fractional_energy_output():
    assert calculate_kardashev_energy_output(0.7) == pytest.approx(1e13)


@pytest.mark.parametrize("scale", [-0.1, float("nan"), float("inf")])
def test_kardashev_rejects_invalid_scale(scale):
    with pytest.raises(ValueError):
        calculate_kardashev_energy_output(scale)


def test_population_growth():
    assert calculate_population_after_growth(
        population=1000,
        annual_growth_rate=0.1,
        years=2,
    ) == pytest.approx(1210)


def test_population_decline():
    assert calculate_population_after_growth(
        population=1000,
        annual_growth_rate=-0.1,
        years=2,
    ) == pytest.approx(810)


def test_population_without_growth():
    assert calculate_population_after_growth(
        population=1000,
        annual_growth_rate=0,
        years=100,
    ) == pytest.approx(1000)


@pytest.mark.parametrize(
    "population, rate, years",
    [
        (-1, 0.1, 10),
        (100, -1, 10),
        (100, 0.1, -1),
        (100, float("nan"), 10),
        (100, 0.1, 1.5),
    ],
)
def test_population_growth_rejects_invalid_inputs(population, rate, years):
    with pytest.raises(ValueError):
        calculate_population_after_growth(population, rate, years)


def test_energy_budget_surplus():
    result = calculate_energy_budget(
        population=1000,
        energy_production_watts=2_000_000,
        energy_consumption_watts_per_person=1000,
    )

    assert result["total_demand_watts"] == pytest.approx(1_000_000)
    assert result["surplus_watts"] == pytest.approx(1_000_000)
    assert result["deficit_watts"] == pytest.approx(0)


def test_energy_budget_deficit():
    result = calculate_energy_budget(
        population=1000,
        energy_production_watts=500_000,
        energy_consumption_watts_per_person=1000,
    )

    assert result["total_demand_watts"] == pytest.approx(1_000_000)
    assert result["surplus_watts"] == pytest.approx(0)
    assert result["deficit_watts"] == pytest.approx(500_000)


def test_energy_budget_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_energy_budget(-1, 100, 10)

    with pytest.raises(ValueError):
        calculate_energy_budget(100, -1, 10)

    with pytest.raises(ValueError):
        calculate_energy_budget(100, 100, -1)
