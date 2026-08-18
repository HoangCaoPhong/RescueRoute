# Optimization algorithms

Nhóm này dành cho tối ưu nhiều điểm hoặc tìm lời giải xấp xỉ trong không gian lớn.

```text
optimization/
├── genetic_algorithm/
├── held_karp/
├── hill_climbing/
├── nearest_neighbor/
└── simulated_annealing/
```

Mỗi thuật toán phải ghi rõ cách biểu diễn candidate route, objective function, điều kiện dừng và việc có bảo đảm tối ưu hay không. Thuật toán dùng ngẫu nhiên bắt buộc nhận seed để benchmark/test tái lập được.

- Nearest Neighbor chọn waypoint có pairwise cost nhỏ nhất tại mỗi bước;
  deterministic nhưng chỉ là nghiệm xấp xỉ.
- Held–Karp dùng dynamic programming để tìm thứ tự waypoint tối ưu
  trên pairwise cost matrix, giới hạn 10 waypoint để kiểm soát bộ nhớ.
- Genetic Algorithm dùng giải thuật di truyền (selection, crossover, mutation)
  để tìm thứ tự waypoint xấp xỉ trong không gian lớn.
