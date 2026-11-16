import json

import pytest

from dark_forest_sim.engine.civilization import (
    Civilization,
    CivilizationStatus,
)
from dark_forest_sim.engine.event import (
    Event,
    EventDelivery,
    DeliveryStatus,
)
from dark_forest_sim.engine.scheduler import CivilizationScheduler
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.persistence import SimulationPersistence
from dark_forest_sim.narrator.runtime import NarratorRuntime


def create_world():
    universe = Universe(current_time=12.0)

    alpha = Civilization(
        id="alpha",
        name="Alpha",
        position=Position(1, 2, 3),
        year=100,
    )

    beta = Civilization(
        id="beta",
        name="Beta",
        position=Position(4, 5, 6),
        year=200,
        status=CivilizationStatus.SLEEPING,
    )

    universe.add_civilization(alpha)
    universe.add_civilization(beta)

    event = Event(
        id="event-1",
        event_type="signal",
        created_at=10.0,
        description="A distant transmission.",
        origin=Position(0, 0, 0),
        propagation_speed=1.0,
        target_civilization_ids=("beta",),
    )

    universe.add_event(event)

    delivery = EventDelivery(
        event_id="event-1",
        recipient_civilization_id="beta",
        distance=8.774964387,
        departure_time=10.0,
        arrival_time=18.8,
        status=DeliveryStatus.PENDING,
    )

    universe.deliveries[("event-1", "beta")] = delivery

    scheduler = CivilizationScheduler()
    scheduler.wake_times["beta"] = 200.0

    return universe, scheduler


def test_universe_round_trip(tmp_path):
    path = tmp_path / "simulation.json"
    persistence = SimulationPersistence(path)

    universe, scheduler = create_world()

    persistence.save(
        universe,
        scheduler,
        {"status": "stopped"},
    )

    loaded = persistence.load()

    assert loaded is not None

    restored = loaded["universe"]
    restored_scheduler = loaded["scheduler"]

    assert restored.current_time == 12.0
    assert restored.get_civilization("alpha").position == Position(1, 2, 3)
    assert restored.get_civilization("beta").status == CivilizationStatus.SLEEPING

    assert restored.get_event("event-1").target_civilization_ids == ("beta",)

    restored_delivery = restored.get_delivery("event-1", "beta")
    assert restored_delivery.status == DeliveryStatus.PENDING

    assert restored_scheduler.wake_times == {"beta": 200.0}


def test_missing_save_returns_none(tmp_path):
    persistence = SimulationPersistence(
        tmp_path / "missing.json"
    )

    assert persistence.load() is None


def test_corrupted_save_is_rejected(tmp_path):
    path = tmp_path / "simulation.json"
    path.write_text("{invalid json", encoding="utf-8")

    persistence = SimulationPersistence(path)

    with pytest.raises(ValueError, match="corrupted"):
        persistence.load()


def test_unsupported_version_is_rejected(tmp_path):
    path = tmp_path / "simulation.json"
    path.write_text(
        json.dumps({"schema_version": 999}),
        encoding="utf-8",
    )

    persistence = SimulationPersistence(path)

    with pytest.raises(ValueError, match="Unsupported save version"):
        persistence.load()


@pytest.mark.asyncio
async def test_runtime_restores_pending_action(tmp_path):
    path = tmp_path / "simulation.json"

    runtime = NarratorRuntime(save_path=path)

    civilization = Civilization(
        id="alpha",
        name="Alpha",
        position=Position(0, 0, 0),
        year=100,
    )

    runtime.universe.add_civilization(civilization)
    runtime.active_civilization_id = "alpha"
    runtime.status = "running"
    runtime.pending_action = {
        "proposal_id": "proposal-1",
        "civilization_id": "alpha",
        "civilization_name": "Alpha",
        "description": "Build a radio telescope.",
    }

    runtime.save()

    restored = NarratorRuntime(save_path=path)

    assert restored.status == "interrupted"
    assert restored.active_civilization_id == "alpha"
    assert restored.pending_action["proposal_id"] == "proposal-1"

    result = await restored.resolve_action(
        "proposal-1",
        True,
        "Approved.",
    )

    assert result["approved"] is True
    assert restored.pending_action is None
    assert restored.last_action_result["explanation"] == "Approved."


def test_world_tools_trigger_persistence_callback():
    from dark_forest_sim.narrator.registry import NarratorToolbox

    universe = Universe()
    scheduler = CivilizationScheduler()
    save_calls = []

    toolbox = NarratorToolbox(
        universe,
        scheduler,
        on_change=lambda: save_calls.append(True),
    )

    result = toolbox.call(
        "manage_civilization",
        {
            "operation": "create",
            "civilization_id": "alpha",
            "name": "Alpha",
            "x": 0,
            "y": 0,
            "z": 0,
            "year": 100,
        },
    )

    assert result["ok"] is True
    assert len(save_calls) == 1

    # Read-only operations must not trigger persistence.
    result = toolbox.call(
        "query_universe",
        {"operation": "universe_status"},
    )

    assert result["ok"] is True
    assert len(save_calls) == 1

    # Creating a duplicate civilization must fail without saving.
    result = toolbox.call(
        "manage_civilization",
        {
            "operation": "create",
            "civilization_id": "alpha",
            "name": "Alpha",
            "x": 0,
            "y": 0,
            "z": 0,
            "year": 100,
        },
    )

    assert result["ok"] is False
    assert len(save_calls) == 1
