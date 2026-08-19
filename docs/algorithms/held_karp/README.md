# Thiết kế Held–Karp

## English

### Objective

Held-Karp finds the optimal waypoint order with fixed start and goal locations.
Its input is a pairwise cost matrix previously computed by the routing service.

State `(mask, last)` stores the minimum cost of leaving the start, visiting
exactly the waypoint set in `mask`, and ending at `last`. Predecessors reconstruct
the final order.

```text
initialize costs from start to each waypoint

for each valid mask and last waypoint:
    for each next waypoint not in mask:
        candidate <- dp[mask, last] + pair_cost[last, next]
        update dp and predecessor when candidate is better

connect every full-mask state to goal
choose the minimum total cost and reconstruct the order
```

The method is exact on the supplied matrix, runs in `O(k² 2ᵏ)` time, and stores
`O(k 2ᵏ)` states. The API limits input to 10 waypoints. Pairwise segment
optimality still depends on the two-location search method.

---

## Tiếng Việt

## Mục tiêu

Held–Karp tìm thứ tự waypoint tối ưu với start và goal cố định. Input là
pairwise cost matrix đã được routing service tính từ thuật toán hai điểm.

Trạng thái `(mask, last)` lưu cost nhỏ nhất để đi từ start, ghé đúng tập waypoint
trong `mask` và kết thúc tại `last`. Predecessor dùng để dựng lại thứ tự.

## Pseudocode

```text
khởi tạo cost từ start tới từng waypoint

với mỗi mask và last hợp lệ:
    với mỗi next chưa có trong mask:
        candidate <- dp[mask, last] + pair_cost[last, next]
        cập nhật dp và predecessor nếu candidate tốt hơn

nối mỗi trạng thái full-mask tới goal
chọn cost nhỏ nhất và dựng lại visiting order
```

## Thuộc tính

- Tối ưu trên pairwise cost matrix được cung cấp.
- Thời gian `O(k² 2ᵏ)`, bộ nhớ `O(k 2ᵏ)` với `k` waypoint.
- API giới hạn 10 waypoint để kiểm soát thời gian và bộ nhớ.
- Bảo đảm thứ tự tối ưu không đồng nghĩa từng đoạn tối ưu nếu thuật toán tìm
  đường hai điểm chỉ là heuristic.
