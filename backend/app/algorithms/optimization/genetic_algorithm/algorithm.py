"""Deterministic genetic algorithm for fixed-start/fixed-goal route search."""

from __future__ import annotations

import random
from math import isfinite
from time import perf_counter
from typing import Any


def solve_genetic_algorithm(
    locations: list[Any],
    distance_matrix: dict[Any, dict[Any, float]],
    start_city: Any,
    end_city: Any,
    *,
    population_size: int = 20,
    generations: int = 30,
    seed: int = 7,
) -> dict[str, Any]:
    """Return a deterministic approximate route between two cities."""
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
            "method": "genetic_algorithm",
            "processing_time_ms": (perf_counter() - started_at) * 1000.0,
            "population_size": max(2, population_size),
            "generations": max(1, generations),
            "generation_history": [],
            "explanation_data": {
                "algorithm": "Genetic Algorithm",
                "optimality": "approximate",
                "message": (
                    "Genetic Algorithm evolves a population of candidate routes and "
                    "keeps the lowest-cost route under the supplied distance matrix; "
                    "it is a heuristic search and does not guarantee global optimality."
                ),
            },
        }

    if start_city not in locations or end_city not in locations:
        raise ValueError(f"Start city '{start_city}' or end city '{end_city}' is missing.")

    remaining = _validate_inputs(locations, distance_matrix, start_city, end_city)
    rng = random.Random(seed)
    population_size = max(2, population_size)
    generations = max(1, generations)

    if not remaining:
        best_route = [start_city, end_city]
    else:
        population: list[list[Any]] = []
        for _ in range(population_size):
            route = [start_city] + remaining[:] + [end_city]
            rng.shuffle(route[1:-1])
            population.append(route)

        best_route = min(population, key=lambda route: _route_cost(route, distance_matrix))
        best_cost = _route_cost(best_route, distance_matrix)

        for _ in range(generations):
            scored = [(route, _route_cost(route, distance_matrix)) for route in population]
            scored.sort(key=lambda item: item[1])
            elites = [route for route, _ in scored[: max(2, population_size // 2)]]
            next_population = elites[:]

            while len(next_population) < population_size:
                parent_a = rng.choice(elites)
                parent_b = rng.choice(elites)
                child = _crossover(parent_a, parent_b, rng)
                if rng.random() < 0.3:
                    child = _mutate(child, rng)
                child[0] = start_city
                child[-1] = end_city
                if len(set(child)) == len(child):
                    next_population.append(child)

            population = next_population
            candidate = min(population, key=lambda route: _route_cost(route, distance_matrix))
            candidate_cost = _route_cost(candidate, distance_matrix)
            if candidate_cost < best_cost:
                best_route = candidate
                best_cost = candidate_cost

    objective_cost = float(_route_cost(best_route, distance_matrix))
    return {
        "found": True,
        "path": best_route,
        "visiting_order": best_route,
        "objective_cost": objective_cost,
        "total_cost": objective_cost,
        "is_optimal": False,
        "method": "genetic_algorithm",
        "processing_time_ms": (perf_counter() - started_at) * 1000.0,
        "population_size": population_size,
        "generations": generations,
        "generation_history": [],
        "explanation_data": {
            "algorithm": "Genetic Algorithm",
            "optimality": "approximate",
            "message": (
                "Genetic Algorithm evolves a population of routes and favors lower-cost "
                "candidates; it is not guaranteed to return a globally optimal tour."
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
        if not isfinite(value) or value < 0:
            raise ValueError(f"Edge cost from '{source}' to '{target}' must be finite and non-negative.")
        total += value
    return total


def _mutate(route: list[Any], rng: random.Random) -> list[Any]:
    route = list(route)
    if len(route) <= 3:
        return route
    i, j = rng.sample(range(1, len(route) - 1), 2)
    route[i], route[j] = route[j], route[i]
    return route


def _crossover(parent_a: list[Any], parent_b: list[Any], rng: random.Random) -> list[Any]:
    if len(parent_a) <= 3:
        return list(parent_a)

    start = rng.randint(1, len(parent_a) - 2)
    end = rng.randint(start, len(parent_a) - 2)
    segment = parent_a[start : end + 1]

    child = [None] * len(parent_a)
    child[start : end + 1] = segment
    fill = [city for city in parent_b[1:-1] if city not in segment]
    cursor = 0
    for idx in range(1, len(parent_a) - 1):
        if idx >= start and idx <= end:
            continue
        child[idx] = fill[cursor]
        cursor += 1
    child[0] = parent_a[0]
    child[-1] = parent_a[-1]
    return child
