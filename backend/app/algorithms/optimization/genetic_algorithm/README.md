# Genetic Algorithm

- Owner: Hòa
- Branch: `feature/genetic-algorithm`
- Test folder: `backend/tests/unit/algorithms/optimization/genetic_algorithm/`
- Docs folder: `docs/algorithms/genetic_algorithm/`

## API and guarantees

`solve_genetic_algorithm(locations, distance_matrix, start_city, end_city, population_size=20, generations=30, seed=7)` is a deterministic heuristic optimizer for fixed start/end routes. It evolves a population of candidate tours, where each candidate is an ordered list of cities starting at `start_city` and ending at `end_city`, with intermediate cities arranged as a permutation of the remaining locations.

The objective function is the total travel cost defined by the supplied `distance_matrix`, summed over consecutive city pairs in the candidate route. The algorithm stops after the configured number of generations and keeps the best route found in the current population. Because mutation and crossover are heuristic search steps, the method is approximate rather than globally optimal; it is useful for multi-stop routing and benchmark comparison, but it does not guarantee the true minimum tour.

The random search is reproducible because the caller supplies a `seed`, and invalid city entries or missing distances raise `ValueError`.

## Expected output

The result includes the best route path, visiting order, objective cost, total cost, processing time, generation metadata, and structured explanation data so the frontend can present the solution clearly.
