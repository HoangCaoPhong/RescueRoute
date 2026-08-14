"""Simulated Annealing algorithm for fixed-start/fixed-goal route search.

This module implements the Simulated Annealing algorithm for multi-location
routing (TSP style). It evaluates neighboring route mutations and occasionally
accepts worse routes based on a temperature parameter to escape local minima.
"""

from __future__ import annotations

import math
import random
from time import perf_counter
from typing import Any


def solve_simulated_annealing(
    locations: list[Any],
    distance_matrix: dict[Any, dict[Any, float]],
    start_city: Any,
    end_city: Any,
    *,
    initial_temperature: float = 10000.0,
    cooling_rate: float = 0.99,
    min_temperature: float = 0.01,
    iterations_per_temp: int = 100,
    seed: int = 7,
) -> dict[str, Any]:
    """Return a deterministic approximate route using Simulated Annealing."""
    started_at = perf_counter()
    locations = list(dict.fromkeys(locations))

    if start_city == end_city:
        return {
            "found": True,
            "path": [start_city],
            "visiting_order": [start_city],
            "objective_cost": 0.0,
            "total_cost": 0.0,
            "is_optimal": True,
            "method": "simulated_annealing",
            "processing_time_ms": (perf_counter() - started_at) * 1000.0,
            "explanation_data": {
                "algorithm": "Simulated Annealing",
                "optimality": "approximate",
                "message": (
                    "Simulated Annealing probabilistically explores route mutations "
                    "and allows temporary cost increases to avoid local optima. It is a "
                    "heuristic search and does not guarantee global optimality."
                ),
            },
        }

    if start_city not in locations or end_city not in locations:
        raise ValueError(f"Start city '{start_city}' or end city '{end_city}' is missing.")

    remaining = _validate_inputs(locations, distance_matrix, start_city, end_city)
    rng = random.Random(seed)

    if not remaining:
        best_route = [start_city, end_city]
        best_cost = _route_cost(best_route, distance_matrix)
    else:
        # Create an initial route
        current_route = [start_city] + remaining[:] + [end_city]
        rng.shuffle(current_route[1:-1])
        current_cost = _route_cost(current_route, distance_matrix)

        best_route = list(current_route)
        best_cost = current_cost

        temp = initial_temperature

        # Note for the user: For larger datasets (many waypoints), the default parameters
        # (initial_temperature=10000.0, cooling_rate=0.99, iterations_per_temp=100) are
        # set generously to allow longer exploration. The >200,000 nodes mentioned in the 
        # whole graph do not affect this directly; this algorithm's performance only depends 
        # on the number of WAYPOINTS chosen for the multi-location optimization.
        while temp > min_temperature:
            for _ in range(iterations_per_temp):
                neighbor = _get_neighbor(current_route, rng)
                neighbor_cost = _route_cost(neighbor, distance_matrix)

                delta_cost = neighbor_cost - current_cost

                # Accept the neighbor if it's better, or probabilistically if it's worse
                if delta_cost < 0 or rng.random() < math.exp(-delta_cost / temp):
                    current_route = neighbor
                    current_cost = neighbor_cost

                    if current_cost < best_cost:
                        best_route = list(current_route)
                        best_cost = current_cost

            temp *= cooling_rate

    objective_cost = float(best_cost)
    return {
        "found": True,
        "path": best_route,
        "visiting_order": best_route,
        "objective_cost": objective_cost,
        "total_cost": objective_cost,
        "is_optimal": False,
        "method": "simulated_annealing",
        "processing_time_ms": (perf_counter() - started_at) * 1000.0,
        "explanation_data": {
            "algorithm": "Simulated Annealing",
            "optimality": "approximate",
            "message": (
                "Simulated Annealing probabilistically explores route mutations "
                "and allows temporary cost increases to avoid local optima. It is a "
                "heuristic search and does not guarantee global optimality."
            ),
        },
    }


def _validate_inputs(
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


def _route_cost(route: list[Any], distance_matrix: dict[Any, dict[Any, float]]) -> float:
    total = 0.0
    for source, target in zip(route, route[1:]):
        value = float(distance_matrix[source][target])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Edge cost from '{source}' to '{target}' must be finite and non-negative.")
        total += value
    return total


def _get_neighbor(route: list[Any], rng: random.Random) -> list[Any]:
    """Generate a neighbor by applying a 2-opt move to the route.
    
    This creates a mutation by randomly selecting a subsegment of the route 
    (excluding start and end cities) and reversing it. 2-opt is generally 
    preferred over simple random swaps for routing problems as it efficiently
    untangles crossing paths.
    """
    neighbor = list(route)
    if len(neighbor) <= 3:
        return neighbor

    # Select two distinct indices between 1 and len(route)-2 inclusive
    i, j = rng.sample(range(1, len(neighbor) - 1), 2)
    
    # Ensure i < j
    if i > j:
        i, j = j, i
        
    # Reverse the subsegment between i and j inclusive
    neighbor[i : j + 1] = reversed(neighbor[i : j + 1])
    
    return neighbor
