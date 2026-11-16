from math import isfinite, pi, sqrt


METERS_PER_LIGHT_YEAR = 9.4607304725808e15


def _require_finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be a finite number.")


def calculate_detection_range(
    signal_power_at_1_ly: float,
    background_noise: float,
    detection_threshold: float,
) -> float:
    """Calculate signal detection range in light-years.

    Uses a simplified inverse-square radiation model.
    """
    _require_finite("Signal power", signal_power_at_1_ly)
    _require_finite("Background noise", background_noise)
    _require_finite("Detection threshold", detection_threshold)

    if signal_power_at_1_ly < 0:
        raise ValueError("Signal power must be non-negative.")
    if background_noise <= 0:
        raise ValueError("Background noise must be positive.")
    if detection_threshold <= 0:
        raise ValueError("Detection threshold must be positive.")

    return sqrt(
        signal_power_at_1_ly
        / (background_noise * detection_threshold)
    )


def calculate_waste_heat_power(
    energy_joules: float,
    waste_heat_fraction: float,
    duration_seconds: float,
) -> float:
    """Calculate average waste heat power in watts."""
    _require_finite("Energy", energy_joules)
    _require_finite("Waste heat fraction", waste_heat_fraction)
    _require_finite("Duration", duration_seconds)

    if energy_joules < 0:
        raise ValueError("Energy must be non-negative.")
    if not 0 <= waste_heat_fraction <= 1:
        raise ValueError("Waste heat fraction must be between 0 and 1.")
    if duration_seconds <= 0:
        raise ValueError("Duration must be positive.")

    return energy_joules * waste_heat_fraction / duration_seconds


def calculate_infrared_detection_range(
    heat_power_watts: float,
    detection_threshold_watts_per_square_meter: float,
) -> float:
    """Calculate infrared detection range in light-years.

    Assumes isotropic radiation spreading through empty space.
    """
    _require_finite("Heat power", heat_power_watts)
    _require_finite(
        "Detection threshold",
        detection_threshold_watts_per_square_meter,
    )

    if heat_power_watts < 0:
        raise ValueError("Heat power must be non-negative.")
    if detection_threshold_watts_per_square_meter <= 0:
        raise ValueError("Detection threshold must be positive.")

    distance_meters = sqrt(
        heat_power_watts
        / (4 * pi * detection_threshold_watts_per_square_meter)
    )

    return distance_meters / METERS_PER_LIGHT_YEAR


def calculate_cooling_duration(
    energy_joules: float,
    waste_heat_fraction: float,
    cooling_power_watts: float,
) -> float:
    """Calculate cooling duration in seconds."""
    _require_finite("Energy", energy_joules)
    _require_finite("Waste heat fraction", waste_heat_fraction)
    _require_finite("Cooling power", cooling_power_watts)

    if energy_joules < 0:
        raise ValueError("Energy must be non-negative.")
    if not 0 <= waste_heat_fraction <= 1:
        raise ValueError("Waste heat fraction must be between 0 and 1.")
    if cooling_power_watts <= 0:
        raise ValueError("Cooling power must be positive.")

    return energy_joules * waste_heat_fraction / cooling_power_watts

def calculate_signal_travel_time(
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> float:
    """Calculate signal travel time in years."""

    _require_finite("Distance", distance_light_years)
    _require_finite("Signal speed", speed_fraction_of_c)

    if distance_light_years < 0:
        raise ValueError("Distance must be non-negative.")

    if not 0 < speed_fraction_of_c <= 1:
        raise ValueError("Signal speed must be greater than zero and at most c.")

    return distance_light_years / speed_fraction_of_c


def calculate_signal_arrival_time(
    departure_time: float,
    distance_light_years: float,
    speed_fraction_of_c: float,
) -> float:
    """Calculate when a signal arrives, in simulation years."""

    _require_finite("Departure time", departure_time)

    if departure_time < 0:
        raise ValueError("Departure time must be non-negative.")

    travel_time = calculate_signal_travel_time(
        distance_light_years,
        speed_fraction_of_c,
    )

    return departure_time + travel_time
