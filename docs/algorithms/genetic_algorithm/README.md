# Thiết kế Genetic Algorithm

## English

### Objective

The Genetic Algorithm searches for a low-cost waypoint order with fixed start
and end locations. Each individual is a permutation of intermediate waypoints,
and fitness is the sum of consecutive pairwise costs.

### Pseudocode

```text
population <- random waypoint permutations generated from seed
best <- individual with the lowest cost

for each generation:
    score and sort the population
    retain an elite set
    until the next population is full:
        choose two elite parents
        perform segment crossover
        optionally swap two waypoints as mutation
    update best

return best
```

The method is approximate and has no global-optimum guarantee. It is
reproducible with a fixed `seed`; start and end locations never participate in
crossover or mutation. Tests verify route validity, deterministic seeds,
invalid input, direct routes, and improvement on small matrices.

---

## Tiếng Việt

## Mục tiêu

Genetic Algorithm tìm thứ tự ghé waypoint có cost thấp với start/end cố định.
Mỗi cá thể là một hoán vị của các waypoint trung gian; fitness là tổng cost
của các cặp liên tiếp trong route.

## Pseudocode

```text
population <- các hoán vị ngẫu nhiên theo seed
best <- cá thể có cost nhỏ nhất

lặp qua từng generation:
    chấm điểm và sắp population theo cost
    giữ nhóm elite
    đến khi đủ population mới:
        chọn hai parent từ elite
        crossover một đoạn waypoint
        có xác suất mutation bằng cách đổi hai waypoint
    cập nhật best

trả best
```

## Thuộc tính

- Là heuristic, không bảo đảm tối ưu toàn cục.
- Kết quả tái lập được khi cố định `seed`.
- Chi phí tăng theo `population_size × generations × số waypoint`.
- Start/end không tham gia crossover hoặc mutation.

Test xác nhận route hợp lệ, seed xác định, input lỗi, route chỉ có start/end và
khả năng cải thiện trên cost matrix nhỏ.
