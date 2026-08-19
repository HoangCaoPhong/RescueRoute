# Thiết kế A*

## English

### Objective

A* searches for a minimum-cost route by prioritizing the node with the lowest
`f(n) = g(n) + h(n)`. Here, `g(n)` is the accumulated cost from the start and
`h(n)` estimates the remaining cost in the same unit.

For geographic routing, straight-line distance is admissible only after it has
been converted into a valid lower bound for the active objective. Do not set
`heuristic_is_admissible=True` without that proof.

### Pseudocode

```text
g[start] <- 0
open <- priority queue containing start with f = h(start)

while open is not empty:
    current <- valid node with the lowest f
    record current and the frontier
    if current is goal: reconstruct and return the path

    for each directed neighbor of current:
        tentative <- g[current] + edge_cost(current, neighbor)
        if tentative improves g[neighbor]:
            update g, parent, and open

report no route while preserving the partial trace
```

With a binary heap, the typical bound is `O((V + E) log V)` when each node has
one best score, with `O(V)` auxiliary memory excluding stale heap entries.
Tests compare A* with UCS and cover directed graphs, reopening, invalid
heuristics, no-route behavior, and deterministic traces.

---

## Tiếng Việt

## Mục tiêu

A* tìm tuyến có cost nhỏ nhất bằng cách ưu tiên node có
`f(n) = g(n) + h(n)` nhỏ nhất. `g(n)` là cost từ start; `h(n)` ước lượng phần
còn lại đến goal và phải cùng đơn vị với `g(n)`.

Với định tuyến địa lý, khoảng cách đường chim bay chỉ admissible khi được đổi
sang một lower bound hợp lệ của cost đang tối ưu. Nếu chưa chứng minh được,
không đánh dấu `heuristic_is_admissible=True`.

## Pseudocode

```text
g[start] <- 0
open <- priority queue chứa start với f = h(start)

while open không rỗng:
    current <- node hợp lệ có f nhỏ nhất
    ghi frontier và current vào trace
    nếu current là goal: dựng lại path và trả kết quả

    với mỗi neighbor có hướng của current:
        tentative <- g[current] + edge_cost(current, neighbor)
        nếu tentative tốt hơn g[neighbor]:
            cập nhật g, parent và đưa neighbor vào open

báo không có đường và giữ partial trace
```

## Độ phức tạp và kiểm tra

Worst case phụ thuộc heuristic và priority queue, thường được mô tả là
`O((V + E) log V)` khi mỗi node giữ một best score. Bộ nhớ `O(V)` ngoài các
heap entry cũ.

Test đối chiếu A* với UCS, kiểm tra graph có hướng, node reopening, heuristic
không hợp lệ, không có đường và tính xác định của frontier.
