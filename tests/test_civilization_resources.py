import pytest

from dark_forest_sim.engine.civilization import (
    CivilizationState,
    DemographicsState,
    EnergyState,
)


def test_state_defaults():
    state = CivilizationState()

    assert state.demographics.population == 0
    assert state.demographics.annual_population_growth_rate == 0
    assert state.energy.energy_production_watts == 0
    assert state.energy.energy_reserve_joules == 0
    assert state.energy.energy_consumption_watts_per_person == 0


def test_domain_values_are_preserved():
    state = CivilizationState(
        demographics=DemographicsState(
            population=8_000_000_000,
            annual_population_growth_rate=0.02,
        ),
        energy=EnergyState(
            energy_production_watts=1e16,
            energy_reserve_joules=1e25,
            energy_consumption_watts_per_person=2000,
        ),
    )

    assert state.demographics.population == 8_000_000_000
    assert state.demographics.annual_population_growth_rate == 0.02
    assert state.energy.energy_production_watts == 1e16
    assert state.energy.energy_reserve_joules == 1e25
    assert state.energy.energy_consumption_watts_per_person == 2000


def test_physically_unusual_values_are_representable():
    state = CivilizationState(
        demographics=DemographicsState(
            population=-100,
            annual_population_growth_rate=-1.5,
        ),
        energy=EnergyState(
            energy_production_watts=-100,
            energy_reserve_joules=-500,
            energy_consumption_watts_per_person=-10,
        ),
    )

    assert state.demographics.population == -100
    assert state.demographics.annual_population_growth_rate == -1.5
    assert state.energy.energy_production_watts == -100
    assert state.energy.energy_reserve_joules == -500
    assert state.energy.energy_consumption_watts_per_person == -10


def test_population_must_be_an_integer():
    with pytest.raises(TypeError):
        DemographicsState(population=10.5)

    with pytest.raises(TypeError):
        DemographicsState(population=True)


def test_numeric_values_must_be_finite():
    with pytest.raises(ValueError):
        DemographicsState(
            annual_population_growth_rate=float("inf")
        )

    with pytest.raises(ValueError):
        EnergyState(energy_production_watts=float("nan"))


def test_numeric_fields_reject_booleans():
    with pytest.raises(TypeError):
        EnergyState(energy_production_watts=True)


def test_civilizations_do_not_share_default_state():
    from dark_forest_sim.engine.civilization import Civilization
    from dark_forest_sim.engine.space import Position

    first = Civilization(
        id="first",
        name="First",
        position=Position(0, 0, 0),
        year=100,
    )

    second = Civilization(
        id="second",
        name="Second",
        position=Position(0, 0, 0),
        year=100,
    )

    first.state.demographics.population = 100

    assert second.state.demographics.population == 0
