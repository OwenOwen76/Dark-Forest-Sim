import pytest

from dark_forest_sim import civilization_mcp as civ_mcp
from dark_forest_sim.narrator import economics, physics


EXPECTED_TOOLS = {
    "inspect_self",
    "inspect_knowledge",
    "calculate_distance",
    "calculate_travel_time",
    "calculate_signal_detection_range",
    "calculate_waste_heat_power",
    "calculate_infrared_detection_range",
    "calculate_cooling_duration",
    "calculate_signal_travel_time",
    "calculate_signal_arrival_time",
    "calculate_lorentz_factor",
    "calculate_relativistic_travel_time",
    "calculate_proper_travel_time",
    "calculate_energy_budget",
    "calculate_population_growth",
    "propose_action",
    "time_lapse",
}


@pytest.mark.asyncio
async def test_all_civilization_tools_registered():
    tools = await civ_mcp.mcp.list_tools()

    assert {tool.name for tool in tools} == EXPECTED_TOOLS
    assert len(tools) == 17


@pytest.mark.asyncio
async def test_civilization_tools_have_input_schemas():
    tools = await civ_mcp.mcp.list_tools()

    for tool in tools:
        assert isinstance(tool.input_schema, dict)
        assert tool.input_schema["type"] == "object"


@pytest.mark.asyncio
async def test_calculate_distance():
    result = await civ_mcp.calculate_distance(
        0, 0, 0,
        3, 4, 0,
    )

    assert result == {"distance_light_years": 5}


@pytest.mark.asyncio
async def test_calculate_travel_time():
    result = await civ_mcp.calculate_travel_time(10, 0.5)

    assert result == {"travel_time_years": 20.0}


@pytest.mark.asyncio
async def test_calculate_signal_detection_range():
    result = await civ_mcp.calculate_signal_detection_range(
        signal_power_at_1_ly=100,
        background_noise=2,
        detection_threshold=2,
    )

    assert result == {"detection_range_light_years": 5.0}


@pytest.mark.asyncio
async def test_calculate_waste_heat_power():
    result = await civ_mcp.calculate_waste_heat_power(
        energy_joules=1000,
        waste_heat_fraction=0.5,
        duration_seconds=10,
    )

    assert result == {"waste_heat_power_watts": 50}


@pytest.mark.asyncio
async def test_calculate_infrared_detection_range():
    result = await civ_mcp.calculate_infrared_detection_range(
        heat_power_watts=50,
        detection_threshold_watts_per_square_meter=1e-10,
    )

    expected = physics.calculate_infrared_detection_range(50, 1e-10)

    assert result == {
        "detection_range_light_years": expected,
    }


@pytest.mark.asyncio
async def test_calculate_cooling_duration():
    result = await civ_mcp.calculate_cooling_duration(
        energy_joules=1000,
        waste_heat_fraction=0.5,
        cooling_power_watts=10,
    )

    assert result == {"cooling_duration_seconds": 50}


@pytest.mark.asyncio
async def test_calculate_signal_travel_time():
    result = await civ_mcp.calculate_signal_travel_time(
        distance_light_years=10,
        speed_fraction_of_c=0.5,
    )

    assert result == {"travel_time_years": 20}


@pytest.mark.asyncio
async def test_calculate_signal_arrival_time():
    result = await civ_mcp.calculate_signal_arrival_time(
        departure_time=100,
        distance_light_years=10,
        speed_fraction_of_c=0.5,
    )

    assert result == {"arrival_time": 120}


@pytest.mark.asyncio
async def test_calculate_lorentz_factor():
    result = await civ_mcp.calculate_lorentz_factor(
        speed_fraction_of_c=0.8,
    )

    assert result["lorentz_factor"] == pytest.approx(1.6666667)


@pytest.mark.asyncio
async def test_calculate_relativistic_travel_time():
    result = await civ_mcp.calculate_relativistic_travel_time(
        distance_light_years=10,
        speed_fraction_of_c=0.8,
    )

    assert result == {"travel_time_years": 12.5}


@pytest.mark.asyncio
async def test_calculate_proper_travel_time():
    result = await civ_mcp.calculate_proper_travel_time(
        distance_light_years=10,
        speed_fraction_of_c=0.8,
    )

    assert result["proper_travel_time_years"] == pytest.approx(7.5)


@pytest.mark.asyncio
async def test_calculate_energy_budget():
    result = await civ_mcp.calculate_energy_budget(
        population=100,
        energy_production_watts=1000,
        energy_consumption_watts_per_person=5,
    )

    assert result == economics.calculate_energy_budget(
        100,
        1000,
        5,
    )


@pytest.mark.asyncio
async def test_calculate_population_growth():
    result = await civ_mcp.calculate_population_growth(
        population=100,
        annual_growth_rate=0.02,
        years=10,
    )

    assert result["initial_population"] == 100
    assert result["annual_growth_rate"] == 0.02
    assert result["years"] == 10
    assert result["projected_population"] == pytest.approx(121.8994)


@pytest.mark.asyncio
async def test_calculation_tools_reject_invalid_inputs():
    invalid_calls = [
        lambda: civ_mcp.calculate_travel_time(10, 0),
        lambda: civ_mcp.calculate_signal_detection_range(100, 0, 2),
        lambda: civ_mcp.calculate_waste_heat_power(1000, 0.5, 0),
        lambda: civ_mcp.calculate_infrared_detection_range(50, 0),
        lambda: civ_mcp.calculate_cooling_duration(1000, 0.5, 0),
        lambda: civ_mcp.calculate_signal_travel_time(10, 0),
        lambda: civ_mcp.calculate_signal_arrival_time(0, 10, 0),
        lambda: civ_mcp.calculate_lorentz_factor(1),
        lambda: civ_mcp.calculate_relativistic_travel_time(10, 1),
        lambda: civ_mcp.calculate_proper_travel_time(10, 1),
    ]

    for call in invalid_calls:
        with pytest.raises(ValueError):
            await call()


@pytest.mark.asyncio
async def test_api_backed_tools_use_correct_endpoints(monkeypatch):
    calls = []

    async def fake_api_request(method, path, payload=None):
        calls.append((method, path, payload))
        return {"success": True}

    monkeypatch.setattr(civ_mcp, "api_request", fake_api_request)

    assert await civ_mcp.inspect_self() == {"success": True}
    assert await civ_mcp.inspect_knowledge() == {"success": True}
    assert await civ_mcp.propose_action("Build a probe") == {
        "success": True
    }
    assert await civ_mcp.time_lapse(100) == {"success": True}

    assert calls == [
        ("GET", "/api/civilization/context", None),
        ("GET", "/api/civilization/knowledge", None),
        (
            "POST",
            "/api/civilization/action",
            {"description": "Build a probe"},
        ),
        (
            "POST",
            "/api/civilization/time-lapse",
            {"years": 100},
        ),
    ]
