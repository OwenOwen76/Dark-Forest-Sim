import random
from math import isfinite


def roll_technology_breakthrough(
    minor_probability: float,
    major_probability: float,
    revolutionary_probability: float,
    seed: int | None = None,
) -> dict:
    """Roll for a technology breakthrough using reproducible randomness."""

    probabilities = {
        "minor": minor_probability,
        "major": major_probability,
        "revolutionary": revolutionary_probability,
    }

    for name, probability in probabilities.items():
        if not isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError(f"{name} probability must be between 0 and 1.")

    if sum(probabilities.values()) > 1:
        raise ValueError("Combined breakthrough probability cannot exceed 1.")

    if seed is not None and (
        isinstance(seed, bool) or not isinstance(seed, int)
    ):
        raise ValueError("Seed must be an integer or None.")

    roll = random.Random(seed).random()

    if roll < revolutionary_probability:
        outcome = "revolutionary"
    elif roll < revolutionary_probability + major_probability:
        outcome = "major"
    elif roll < (
        revolutionary_probability + major_probability + minor_probability
    ):
        outcome = "minor"
    else:
        outcome = "none"

    return {
        "roll": roll,
        "outcome": outcome,
    }
