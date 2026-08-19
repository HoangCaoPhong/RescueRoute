# Thiết kế Nearest Neighbor

## English

### Objective

Nearest Neighbor quickly creates a visit order by selecting the remaining
waypoint with the lowest pairwise cost from the current location. Start and goal
locations remain fixed.

### Pseudocode

```text
current <- start
remaining <- unvisited waypoints
order <- [start]

while remaining is not empty:
    next <- waypoint with the lowest pairwise cost from current
    if no waypoint is reachable: report failure
    append next, remove it from remaining, and set current <- next

connect current to goal or report failure
return order and total objective cost
```

After the matrix is available, the method uses `O(k²)` time and `O(k)`
additional memory. Stable ID tie-breaking makes it deterministic, but it does
not guarantee a globally optimal order when more than one waypoint is present.

---

## Tiếng Việt

## Mục tiêu

Nearest Neighbor tạo thứ tự ghé nhanh bằng cách chọn waypoint còn lại có
pairwise cost nhỏ nhất từ điểm hiện tại. Start và goal được giữ cố định.

## Pseudocode

```text
current <- start
remaining <- các waypoint chưa ghé
order <- [start]

while remaining không rỗng:
    next <- waypoint có pairwise cost nhỏ nhất từ current
    nếu không có next tới được: báo lỗi
    thêm next vào order và xóa khỏi remaining
    current <- next

nối current tới goal hoặc báo lỗi
trả order và tổng objective cost
```

## Thuộc tính

- Thời gian `O(k²)` sau khi đã có pairwise matrix.
- Bộ nhớ `O(k)` ngoài matrix.
- Xác định nhờ tie-break theo ID ổn định.
- Không bảo đảm tối ưu toàn cục khi có nhiều hơn một waypoint.

Thuật toán phù hợp làm baseline nhanh để so với Held–Karp, GA và Simulated
Annealing trên cùng matrix.
