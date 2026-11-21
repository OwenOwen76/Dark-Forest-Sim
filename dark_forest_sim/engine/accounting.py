from dataclasses import dataclass
from math import isfinite
from collections.abc import Iterable


@dataclass(frozen=True, slots=True)
class StockFlowResult:
    initial_stock: float
    inflows: float
    requested_outflows: float
    actual_outflows: float
    unmet_outflows: float
    final_stock: float


def _quantity(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric.")

    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if value < 0:
        raise ValueError(f"{name} cannot be negative.")

    return float(value)


def settle_stock(
    initial_stock: float,
    inflows: Iterable[float],
    requested_outflows: Iterable[float],
) -> StockFlowResult:
    """Apply inflows and constrained outflows to a physical stock."""

    initial = _quantity(initial_stock, "Initial stock")
    total_inflows = sum(
        _quantity(value, "Inflow") for value in inflows
    )
    total_requested = sum(
        _quantity(value, "Requested outflow")
        for value in requested_outflows
    )

    available = initial + total_inflows
    actual_outflows = min(available, total_requested)
    unmet_outflows = total_requested - actual_outflows
    final_stock = available - actual_outflows

    return StockFlowResult(
        initial_stock=initial,
        inflows=total_inflows,
        requested_outflows=total_requested,
        actual_outflows=actual_outflows,
        unmet_outflows=unmet_outflows,
        final_stock=final_stock,
    )
