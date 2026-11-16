import pytest

from dark_forest_sim.narrator.technology import (
    roll_technology_breakthrough,
)


def test_technology_roll_is_reproducible():
    first = roll_technology_breakthrough(
        minor_probability=0.1,
        major_probability=0.02,
        revolutionary_probability=0.005,
        seed=123,
    )
    second = roll_technology_breakthrough(
        minor_probability=0.1,
        major_probability=0.02,
        revolutionary_probability=0.005,
        seed=123,
    )

    assert first == second


def test_technology_roll_returns_minor_breakthrough():
    result = roll_technology_breakthrough(
        minor_probability=0.1,
        major_probability=0.02,
        revolutionary_probability=0.005,
        seed=123,
    )

    assert result["outcome"] == "minor"
    assert 0 <= result["roll"] < 1


def test_technology_roll_can_return_no_breakthrough():
    result = roll_technology_breakthrough(
        minor_probability=0,
        major_probability=0,
        revolutionary_probability=0,
        seed=123,
    )

    assert result["outcome"] == "none"


def test_technology_roll_can_return_revolutionary_breakthrough():
    result = roll_technology_breakthrough(
        minor_probability=0,
        major_probability=0,
        revolutionary_probability=1,
        seed=123,
    )

    assert result["outcome"] == "revolutionary"


@pytest.mark.parametrize(
    "probabilities",
    [
        (-0.1, 0, 0),
        (0, -0.1, 0),
        (0, 0, -0.1),
        (0.5, 0.5, 0.1),
        (float("nan"), 0, 0),
        (float("inf"), 0, 0),
    ],
)
def test_technology_roll_rejects_invalid_probabilities(probabilities):
    with pytest.raises(ValueError):
        roll_technology_breakthrough(
            minor_probability=probabilities[0],
            major_probability=probabilities[1],
            revolutionary_probability=probabilities[2],
            seed=123,
        )
