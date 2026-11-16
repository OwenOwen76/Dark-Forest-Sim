from dark_forest_sim.engine.civilization import (
    Civilization,
    CivilizationResources,
)
from dark_forest_sim.engine.scheduler import CivilizationScheduler
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.persistence import SimulationPersistence


def test_civilization_resources_survive_save_and_load(tmp_path):
    universe = Universe()

    resources = CivilizationResources(
        population=8_000_000_000,
        annual_population_growth_rate=0.015,
        energy_production_watts=1e16,
        energy_reserve_joules=1e25,
        energy_consumption_watts_per_person=1500,
    )

    civilization = Civilization(
        id="earth",
        name="Earth",
        position=Position(0, 0, 0),
        year=2026,
        resources=resources,
    )

    universe.add_civilization(civilization)

    persistence = SimulationPersistence(
        tmp_path / "simulation.json"
    )

    persistence.save(
        universe,
        CivilizationScheduler(),
        {},
    )

    loaded = persistence.load()
    restored = loaded["universe"].get_civilization("earth").resources

    assert restored.population == 8_000_000_000
    assert restored.annual_population_growth_rate == 0.015
    assert restored.energy_production_watts == 1e16
    assert restored.energy_reserve_joules == 1e25
    assert restored.energy_consumption_watts_per_person == 1500


def test_old_saves_receive_default_resources(tmp_path):
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

    persistence.save(
        universe,
        CivilizationScheduler(),
        {},
    )

    loaded = persistence.load()
    resources = loaded["universe"].get_civilization("earth").resources

    assert resources.population == 0
    assert resources.energy_production_watts == 0
