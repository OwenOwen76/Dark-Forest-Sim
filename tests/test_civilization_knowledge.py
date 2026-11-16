from dark_forest_sim.engine.civilization import Civilization
from dark_forest_sim.engine.event import Event, DeliveryStatus
from dark_forest_sim.engine.space import Position
from dark_forest_sim.engine.universe import Universe
from dark_forest_sim.narrator.data import list_known_events


def make_universe():
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

    return universe


def test_only_arrived_events_are_known():
    universe = make_universe()

    universe.advance_time(0)

    nearby = list_known_events(universe, "civ-001")
    distant = list_known_events(universe, "civ-002")

    assert len(nearby) == 1
    assert nearby[0]["event_id"] == "event-001"

    assert distant == []


def test_event_becomes_known_after_arrival():
    universe = make_universe()

    universe.advance_time(4.9)

    assert list_known_events(universe, "civ-002") == []

    universe.advance_time(5)

    known = list_known_events(universe, "civ-002")

    assert len(known) == 1
    assert known[0]["event_id"] == "event-001"
    assert known[0]["delivery"]["arrival_time"] == 5


def test_knowledge_is_scoped_to_recipient():
    universe = make_universe()

    universe.advance_time(5)

    nearby = list_known_events(universe, "civ-001")
    distant = list_known_events(universe, "civ-002")

    assert len(nearby) == 1
    assert len(distant) == 1

    assert nearby[0]["event_id"] == distant[0]["event_id"]


def test_unknown_civilization_is_rejected():
    universe = make_universe()

    try:
        list_known_events(universe, "missing-civ")
    except KeyError:
        pass
    else:
        raise AssertionError("Expected unknown civilization to be rejected.")
