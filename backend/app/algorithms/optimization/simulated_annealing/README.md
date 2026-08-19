# Simulated Annealing

## English

Entry point:

```python
solve_simulated_annealing(locations, distance_matrix, start_city, end_city,
                          initial_temperature=1000.0, cooling_rate=0.95,
                          min_temperature=0.01, iterations_per_temp=15,
                          seed=7)
```

The algorithm generates 2-opt waypoint neighbors, always accepts improvements,
and may accept worse candidates according to the current temperature. Start and
end locations remain fixed.

- Heuristic only; no global-optimum guarantee.
- Reproducible for the same input and `seed`.
- Intended for small-to-medium waypoint counts in the demo.
- Missing locations or invalid pairwise costs raise `ValueError`.

Tests: `backend/tests/unit/algorithms/optimization/simulated_annealing/`.

---

## Tiếng Việt

Entry point:

```python
solve_simulated_annealing(locations, distance_matrix, start_city, end_city,
                          initial_temperature=1000.0, cooling_rate=0.95,
                          min_temperature=0.01, iterations_per_temp=15,
                          seed=7)
```

Thuật toán tạo neighbor bằng phép 2-opt trên các waypoint, luôn nhận lời giải
tốt hơn và có thể nhận lời giải xấu hơn theo nhiệt độ. Start/end luôn cố định.

- Lời giải là heuristic, không bảo đảm tối ưu toàn cục.
- Cùng input và `seed` cho kết quả tái lập được.
- Phù hợp với số waypoint nhỏ đến vừa trong demo.
- Input thiếu location hoặc pairwise cost không hợp lệ gây `ValueError`.

Test: `backend/tests/unit/algorithms/optimization/simulated_annealing/`.
