import math

import pytest

from dark_forest_sim.narrator.physics import (
    calculate_detection_range,
    calculate_waste_heat_power,
    calculate_infrared_detection_range,
    calculate_cooling_duration,
)


def test_detection_range_uses_inverse_square_law():
    normal = calculate_detection_range(
        signal_power_at_1_ly=100,
        background_noise=1,
        detection_threshold=1,
    )

    weaker_signal = calculate_detection_range(
        signal_power_at_1_ly=25,
        background_noise=1,
        detection_threshold=1,
    )

    assert normal == pytest.approx(10)
    assert weaker_signal == pytest.approx(5)


def test_detection_range_accounts_for_background_noise():
    quiet = calculate_detection_range(100, 1, 1)
    noisy = calculate_detection_range(100, 4, 1)

    assert quiet == pytest.approx(10)
    assert noisy == pytest.approx(5)


def test_detection_range_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_detection_range(-1, 1, 1)

    with pytest.raises(ValueError):
        calculate_detection_range(100, 0, 1)

    with pytest.raises(ValueError):
        calculate_detection_range(100, 1, 0)


def test_waste_heat_power():
    power = calculate_waste_heat_power(
        energy_joules=1_000_000,
        waste_heat_fraction=0.5,
        duration_seconds=10,
    )

    assert power == pytest.approx(50_000)


def test_infrared_detection_range():
    power = 4 * math.pi * (1000 ** 2)

    distance = calculate_infrared_detection_range(
        heat_power_watts=power,
        detection_threshold_watts_per_square_meter=1,
    )

    assert distance == pytest.approx(1000 / 9.4607304725808e15)


def test_cooling_duration():
    duration = calculate_cooling_duration(
        energy_joules=1_000_000,
        waste_heat_fraction=0.5,
        cooling_power_watts=10_000,
    )

    assert duration == pytest.approx(50)


def test_thermodynamics_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_waste_heat_power(-100, 0.5, 10)

    with pytest.raises(ValueError):
        calculate_waste_heat_power(100, 1.5, 10)

    with pytest.raises(ValueError):
        calculate_cooling_duration(100, 0.5, 0)
