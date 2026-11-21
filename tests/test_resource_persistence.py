import json

from dark_forest_sim.engine.civilization import (
    Civilization,
    CivilizationState,
    DemographicsState,
    EnergyState,
)
from dark_forest_sim.engine.scheduler import CivilizationScheduler
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.persistence import SimulationPersistence


def make_universe():
    universe = Universe()

    universe.add_civilization(
        Civilization(
            id="earth",
            name="Earth",
            position=Position(0, 0, 0),
            year=2026,
            state=CivilizationState(
                demographics=DemographicsState(
                    population=8_000_000_000,
                    annual_population_growth_rate=0.015,
                ),
                energy=EnergyState(
                    energy_production_watts=1e16,
                    energy_reserve_joules=1e25,
                    energy_consumption_watts_per_person=1500,
                ),
            ),
        )
    )

    return universe


def test_civilization_state_survives_save_and_load(tmp_path):
    persistence = SimulationPersistence(
        tmp_path / "simulation.json"
    )

    persistence.save(
        make_universe(),
        CivilizationScheduler(),
        {},
    )

    loaded = persistence.load()
    restored = loaded["universe"].get_civilization("earth")

    assert restored.state.demographics.population == 8_000_000_000
    assert restored.state.demographics.annual_population_growth_rate == 0.015

    assert restored.state.energy.energy_production_watts == 1e16
    assert restored.state.energy.energy_reserve_joules == 1e25
    assert restored.state.energy.energy_consumption_watts_per_person == 1500


def test_unusual_state_values_survive_save_and_load(tmp_path):
    universe = Universe()

    universe.add_civilization(
        Civilization(
            id="unusual",
            name="Unusual",
            position=Position(0, 0, 0),
            year=100,
            state=CivilizationState(
                demographics=DemographicsState(
                    population=-10,
                    annual_population_growth_rate=-1.5,
                ),
                energy=EnergyState(
                    energy_production_watts=-100,
                ),
            ),
        )
    )

    persistence = SimulationPersistence(
        tmp_path / "simulation.json"
    )

    persistence.save(universe, CivilizationScheduler(), {})
    loaded = persistence.load()

    restored = loaded["universe"].get_civilization("unusual")

    assert restored.state.demographics.population == -10
    assert restored.state.demographics.annual_population_growth_rate == -1.5
    assert restored.state.energy.energy_production_watts == -100


def test_legacy_v2_resources_are_migrated(tmp_path):
    universe = make_universe()

    persistence = SimulationPersistence(
        tmp_path / "simulation.json"
    )

    persistence.save(universe, CivilizationScheduler(), {})

    data = json.loads(persistence.path.read_text(encoding="utf-8"))

    civilization = data["universe"]["civilizations"][0]
    state = civilization.pop("state")

    civilization["resources"] = {
        "population": state["demographics"]["population"],
        "annual_population_growth_rate": (
            state["demographics"]["annual_population_growth_rate"]
        ),
        **state["energy"],
    }

    data["schema_version"] = 2

    persistence.path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    loaded = persistence.load()
    restored = loaded["universe"].get_civilization("earth")

    assert restored.state.demographics.population == 8_000_000_000
    assert restored.state.energy.energy_production_watts == 1e16


def test_legacy_v1_without_resources_receives_defaults(tmp_path):
    universe = Universe()

    universe.add_civilization(
        Civilization(
            id="earth",
            name="Earth",
            position=Position(0, 0, 0),
            year=2026,
        )
    )

    persistence = SimulationPersistence(
        tmp_path / "simulation.json"
    )

    persistence.save(universe, CivilizationScheduler(), {})

    data = json.loads(persistence.path.read_text(encoding="utf-8"))

    data["schema_version"] = 1
    data["universe"]["civilizations"][0].pop("state")

    persistence.path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    loaded = persistence.load()
    restored = loaded["universe"].get_civilization("earth")

    assert restored.state.demographics.population == 0
    assert restored.state.energy.energy_production_watts == 0
