# Genetic Algorithm

## Objective

Genetic Algorithm (GA) is used to find a practical route for multi-stop or structurally complex routing problems where an exact optimal solution may be too expensive to compute within a short time. In RescueRoute, this algorithm is used to optimize the visiting order of target points or to find a low-cost feasible tour.

## Assumptions

- A set of locations or nodes must be visited.
- Each candidate route is an ordered sequence of locations, beginning at the start node and ending at the goal node.
- A distance or cost matrix between city pairs is provided in advance.
- Randomized execution must use a fixed `seed` to keep benchmarks and tests reproducible.

## Candidate route and objective

- Candidate route: a node sequence such as `[start, ...waypoints..., goal]`.
- Objective function: the total travel cost across consecutive node pairs according to `distance_matrix`.
- The goal is to minimize total route cost, not necessarily to guarantee the absolute optimum.

## Algorithm

1. Create an initial population of random candidate routes.
2. Evaluate each route using total route cost as fitness.
3. Select the best elites or parents.
4. Generate new children via crossover.
5. Apply mutation with a fixed probability.
6. Repeat for the configured number of generations.
7. Return the best route found.

## Pseudocode

```text
population = initialize_random_routes()
for generation in range(generations):
    scored = [(route, route_cost(route)) for route in population]
    elites = select_best_routes(scored)
    next_population = elites
    while len(next_population) < population_size:
        parent_a, parent_b = choose_parents(elites)
        child = crossover(parent_a, parent_b)
        if random() < mutation_rate:
            child = mutate(child)
        next_population.append(child)
    population = next_population

best_route = min(population, key=route_cost)
return best_route
```

## Stop condition

- Stop after the configured number of generations.
- There is no global optimality guarantee.
- The algorithm returns the lowest-cost route found during the evolution process.

## Optimality

- It does not guarantee the absolute optimum for multi-point routing.
- It is suitable for medium- to large-scale routing when exact methods are too expensive.
- It can serve as a heuristic baseline and benchmark against Held-Karp, Nearest Neighbor, and Hill Climbing.

## Trace and UI

GA does not provide a classical graph-search trace like A* or Dijkstra, but it still returns:
- `path` or `visiting_order`
- `objective_cost`
- `generation_history`
- `processing_time_ms`
- `explanation_data`

This is sufficient for the UI to explain how the route was chosen and why it is a heuristic solution.

## Example benchmark

- Demo dataset: 4–8 points to visit in order.
- Expected outcome: GA finds a route with lower cost than the initial random route, but it does not guarantee the globally optimal tour.
- Compared with Nearest Neighbor, GA may yield better results in some cases because of crossover and mutation.
