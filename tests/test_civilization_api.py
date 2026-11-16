import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from dark_forest_sim.engine.civilization import Civilization
from dark_forest_sim.engine.event import Event
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.api import router, civilization_router
from dark_forest_sim.narrator.runtime import NarratorRuntime


def make_runtime(save_path):
    universe = Universe()

    universe.add_civilization(
        Civilization(
            id="civ-001",
            name="Nearby Civilization",
            position=Position(0, 0, 0),
            year=100,
        )
    )

    universe.add_civilization(
        Civilization(
            id="civ-002",
            name="Distant Civilization",
            position=Position(5, 0, 0),
            year=100,
        )
    )

    universe.add_event(
        Event(
            id="event-001",
            event_type="signal",
            created_at=0,
            description="An artificial signal was detected.",
            origin=Position(0, 0, 0),
            propagation_speed=1,
        )
    )

    universe.propagate_event("event-001")
    universe.advance_time(0)

    return NarratorRuntime(
        universe=universe,
        save_path=save_path,
    )


@pytest.mark.asyncio
async def test_civilization_knowledge_endpoint(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")

    await runtime.activate_civilization("civ-001")

    app = FastAPI()
    app.state.narrator_runtime = runtime
    app.include_router(router)
    app.include_router(civilization_router)

    with TestClient(app) as client:
        response = client.get("/api/civilization/knowledge")

    assert response.status_code == 200

    data = response.json()

    assert len(data["known_events"]) == 1
    assert data["known_events"][0]["event_id"] == "event-001"


@pytest.mark.asyncio
async def test_civilization_context_includes_resources(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")

    await runtime.activate_civilization("civ-001")

    app = FastAPI()
    app.state.narrator_runtime = runtime
    app.include_router(router)
    app.include_router(civilization_router)

    with TestClient(app) as client:
        response = client.get("/api/civilization/context")

    assert response.status_code == 200

    context = response.json()

    assert context["civilization_id"] == "civ-001"
    assert context["year"] == 100
    assert "resources" in context
    assert context["resources"]["population"] == 0


def test_knowledge_endpoint_requires_active_civilization(tmp_path):
    runtime = make_runtime(tmp_path / "simulation.json")

    app = FastAPI()
    app.state.narrator_runtime = runtime
    app.include_router(router)
    app.include_router(civilization_router)

    with TestClient(app) as client:
        response = client.get("/api/civilization/knowledge")

    assert response.status_code == 409
