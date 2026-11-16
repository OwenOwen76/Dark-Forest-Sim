from dark_forest_sim.engine.civilization import CivilizationResources


def test_resource_defaults():
    resources = CivilizationResources()

    assert resources.population == 0
    assert resources.annual_population_growth_rate == 0
    assert resources.energy_production_watts == 0
    assert resources.energy_reserve_joules == 0
    assert resources.energy_consumption_watts_per_person == 0


def test_resource_values_are_preserved():
    resources = CivilizationResources(
        population=8_000_000_000,
        annual_population_growth_rate=0.02,
        energy_production_watts=1e16,
        energy_reserve_joules=1e25,
        energy_consumption_watts_per_person=2000,
    )

    assert resources.population == 8_000_000_000
    assert resources.annual_population_growth_rate == 0.02
    assert resources.energy_production_watts == 1e16
    assert resources.energy_reserve_joules == 1e25
    assert resources.energy_consumption_watts_per_person == 2000


def test_resource_values_must_be_valid():
    import pytest

    with pytest.raises(ValueError):
        CivilizationResources(population=-1)

    with pytest.raises(ValueError):
        CivilizationResources(energy_production_watts=-1)

    with pytest.raises(ValueError):
        CivilizationResources(annual_population_growth_rate=-1)
