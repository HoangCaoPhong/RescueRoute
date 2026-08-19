# Genetic Algorithm

## English

Entry point:

```python
solve_genetic_algorithm(locations, distance_matrix, start_city, end_city,
                        population_size=20, generations=30, seed=7)
```

Each individual is a waypoint permutation with fixed start and end locations.
The algorithm retains elites, performs segment crossover, and applies swap
mutation to reduce the total pairwise route cost.

- Heuristic only; no global-optimum guarantee.
- Reproducible for the same input and `seed`.
- Minimum population size is 2 and minimum generation count is 1.
- Missing locations or invalid pairwise costs raise `ValueError`.

Tests: `backend/tests/unit/algorithms/optimization/genetic_algorithm/`.

---

## Tiếng Việt

Entry point:

```python
solve_genetic_algorithm(locations, distance_matrix, start_city, end_city,
                        population_size=20, generations=30, seed=7)
```

Mỗi cá thể là một hoán vị waypoint với start/end cố định. Thuật toán giữ nhóm
elite, lai ghép theo đoạn và đột biến hoán đổi để giảm tổng cost giữa các cặp
liên tiếp.

- Lời giải là heuristic, không bảo đảm tối ưu toàn cục.
- Cùng input và `seed` cho kết quả tái lập được.
- `population_size` tối thiểu 2, `generations` tối thiểu 1.
- Input thiếu location hoặc pairwise cost không hợp lệ gây `ValueError`.

Test: `backend/tests/unit/algorithms/optimization/genetic_algorithm/`.
