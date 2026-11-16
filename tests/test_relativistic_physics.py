import pytest

from dark_forest_sim.narrator.physics import (
    calculate_lorentz_factor,
    calculate_relativistic_travel_time,
    calculate_proper_travel_time,
    calculate_relativistic_kinetic_energy,
    calculate_relativistic_momentum,
)


def test_lorentz_factor_at_rest():
    assert calculate_lorentz_factor(0) == pytest.approx(1)


def test_lorentz_factor_at_point_six_c():
    assert calculate_lorentz_factor(0.6) == pytest.approx(1.25)


def test_lorentz_factor_rejects_invalid_speeds():
    for speed in (-0.1, 1, 1.1, float("inf"), float("nan")):
        with pytest.raises(ValueError):
            calculate_lorentz_factor(speed)


def test_relativistic_travel_time():
    assert calculate_relativistic_travel_time(10, 0.5) == pytest.approx(20)


def test_relativistic_travel_time_at_point_six_c():
    assert calculate_relativistic_travel_time(10, 0.6) == pytest.approx(
        10 / 0.6
    )


def test_relativistic_travel_time_zero_distance():
    assert calculate_relativistic_travel_time(0, 0.5) == pytest.approx(0)


def test_relativistic_travel_time_rejects_invalid_inputs():
    for distance, speed in [
        (-1, 0.5),
        (10, 0),
        (10, 1),
        (10, 1.5),
        (float("inf"), 0.5),
        (10, float("nan")),
    ]:
        with pytest.raises(ValueError):
            calculate_relativistic_travel_time(distance, speed)


def test_proper_travel_time():
    # At 0.6c, gamma = 1.25.
    # 10 light-years takes 16.666... years externally,
    # but 13.333... years aboard the ship.
    assert calculate_proper_travel_time(10, 0.6) == pytest.approx(
        13.3333333333
    )


def test_proper_travel_time_at_zero_distance():
    assert calculate_proper_travel_time(0, 0.5) == pytest.approx(0)


def test_proper_travel_time_rejects_invalid_inputs():
    for distance, speed in [
        (-1, 0.5),
        (10, 0),
        (10, 1),
        (10, float("inf")),
    ]:
        with pytest.raises(ValueError):
            calculate_proper_travel_time(distance, speed)


def test_relativistic_kinetic_energy():
    # 1 kg at 0.6c has gamma = 1.25.
    expected = 0.25 * 299792458**2

    assert calculate_relativistic_kinetic_energy(
        1, 0.6
    ) == pytest.approx(expected)


def test_relativistic_kinetic_energy_at_rest():
    assert calculate_relativistic_kinetic_energy(1000, 0) == pytest.approx(0)


def test_relativistic_kinetic_energy_rejects_invalid_inputs():
    for mass, speed in [
        (-1, 0.5),
        (0, 0.5),
        (1, -0.1),
        (1, 1),
        (1, float("nan")),
        (float("inf"), 0.5),
    ]:
        with pytest.raises(ValueError):
            calculate_relativistic_kinetic_energy(mass, speed)


def test_relativistic_momentum():
    # gamma = 1.25 at 0.6c.
    expected = 1.25 * 0.6 * 299792458

    assert calculate_relativistic_momentum(
        1, 0.6
    ) == pytest.approx(expected)


def test_relativistic_momentum_at_rest():
    assert calculate_relativistic_momentum(1000, 0) == pytest.approx(0)


def test_relativistic_momentum_rejects_invalid_inputs():
    for mass, speed in [
        (-1, 0.5),
        (0, 0.5),
        (1, -0.1),
        (1, 1),
        (1, 1.5),
        (1, float("inf")),
    ]:
        with pytest.raises(ValueError):
            calculate_relativistic_momentum(mass, speed)
