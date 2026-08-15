"""Shared utilities for optimization algorithms."""

import math
from collections.abc import Mapping
from typing import Any


def validate_locations_and_matrix(
    locations: list[Any],
    distance_matrix: dict[Any, dict[Any, float]],
    start_city: Any,
    end_city: Any,
) -> list[Any]:
    if start_city not in locations:
        raise ValueError(f"Start city '{start_city}' is not in locations.")
    if end_city not in locations:
        raise ValueError(f"End city '{end_city}' is not in locations.")
    if start_city == end_city:
        return [start_city]

    missing = [city for city in locations if city not in distance_matrix]
    if missing:
        raise ValueError(f"Missing city entries in distance matrix: {missing}")

    for city, row in distance_matrix.items():
        for target in row:
            if target not in distance_matrix:
                raise ValueError(f"Distance matrix is incomplete for city '{target}'.")

    return [city for city in locations if city not in {start_city, end_city}]


def calculate_route_cost(route: list[Any], distance_matrix: dict[Any, dict[Any, float]]) -> float:
    total = 0.0
    for source, target in zip(route, route[1:]):
        value = float(distance_matrix[source][target])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Edge cost from '{source}' to '{target}' must be finite and non-negative.")
        total += value
    return total


def get_pairwise_cost(
    pair_costs: Mapping[tuple[Any, Any], float],
    source: Any,
    target: Any,
) -> float:
    value = float(pair_costs.get((source, target), float("inf")))
    if value < 0:
        raise ValueError("Pair costs must be non-negative.")
    return value
