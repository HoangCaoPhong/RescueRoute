"""Compatibility wrapper for the public Genetic Algorithm entry point.

This module keeps older imports working while the canonical implementation lives
in ``algorithm.py`` to match the repository convention for algorithm folders.
"""

from backend.app.algorithms.optimization.genetic_algorithm.algorithm import (
    solve_genetic_algorithm,
)

__all__ = ["solve_genetic_algorithm"]
