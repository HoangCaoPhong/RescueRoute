# Thiết kế Dijkstra

## English

### Objective

Dijkstra finds a minimum-total-weight route on a graph with non-negative edge
weights. The selected weight may be physical distance or a caller-provided cost,
but it must remain consistent throughout one run.

### Pseudocode

```text
distance[start] <- 0
open <- priority queue containing (0, start)

while open is not empty:
    current <- node with the lowest accumulated weight
    skip stale entries and record the frontier
    if current is goal: reconstruct and return the path

    for each neighbor:
        candidate <- distance[current] + edge_weight(current, neighbor)
        if candidate improves distance[neighbor]:
            update distance, parent, and open

report no route with a partial trace
```

Dijkstra is complete and optimal with finite, non-negative weights. Using a
binary heap, it runs in `O((V + E) log V)` time. Tests compare it with UCS and
A* using `h=0`, and cover custom weights, directed graphs, invalid inputs, and
no-route traces.

---

## Tiếng Việt

## Mục tiêu

Dijkstra tìm tuyến có tổng trọng số nhỏ nhất trên graph có trọng số không âm.
Trọng số có thể là khoảng cách hoặc cost do caller cung cấp, nhưng phải được
dùng nhất quán trong toàn bộ lần chạy.

## Pseudocode

```text
distance[start] <- 0
open <- priority queue chứa (0, start)

while open không rỗng:
    current <- node có accumulated weight nhỏ nhất
    bỏ qua heap entry cũ
    ghi frontier vào trace
    nếu current là goal: dựng lại path và trả kết quả

    với mỗi neighbor:
        candidate <- distance[current] + edge_weight(current, neighbor)
        nếu candidate tốt hơn distance[neighbor]:
            cập nhật distance, parent và open

báo không có đường kèm partial trace
```

## Thuộc tính

- Tối ưu và complete khi mọi trọng số hữu hạn, không âm.
- Thời gian `O((V + E) log V)` với binary heap.
- Bộ nhớ `O(V + E)` tùy số heap entry đang giữ.
- Không cần heuristic.

Test so sánh kết quả với UCS/A* dùng `h=0`, đồng thời kiểm tra edge weight tùy
chọn, graph có hướng, input không hợp lệ và no-route trace.
