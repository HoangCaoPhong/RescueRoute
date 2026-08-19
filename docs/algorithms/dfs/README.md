# Thiết kế DFS

## English

### Objective

Depth-First Search explores one branch deeply before backtracking. In
RescueRoute, DFS is a route-finding and visualization baseline, not an
optimal-route method.

The implementation provides unbounded `solve_dfs` and bounded
`solve_depth_limited_dfs`, which can limit depth or node expansions.

### Pseudocode

```text
stack <- [(start, parent=null, depth=0)]
visited <- empty

while stack is not empty:
    current <- pop stack
    if current was visited: continue
    record current and the frontier
    mark current and save its parent

    if current is goal: reconstruct and return the path
    if the expansion limit is reached: fail with a partial trace
    if the depth limit is reached: do not expand this branch

    push unvisited neighbors in reverse order

report no route with the partial trace
```

Unbounded DFS runs in `O(V + E)` time and `O(V)` auxiliary space on a finite
graph. A cutoff can remove completeness, and DFS never guarantees minimum hops,
distance, time, or cost. See [flowchart.mmd](flowchart.mmd).

---

## Tiếng Việt

## Mục tiêu

Depth-First Search đi sâu theo một nhánh trước khi quay lui. Trong RescueRoute,
DFS đóng vai trò baseline về khả năng tìm đường và trực quan hóa; nó không được
dùng để khẳng định tuyến tối ưu.

Implementation có hai chế độ:

- `solve_dfs`: DFS không giới hạn.
- `solve_depth_limited_dfs`: giới hạn độ sâu hoặc số node mở rộng.

## Pseudocode

```text
stack <- [(start, parent=null, depth=0)]
visited <- rỗng

while stack không rỗng:
    current <- pop stack
    nếu current đã thăm: bỏ qua
    ghi current và frontier vào trace
    đánh dấu current, lưu parent

    nếu current là goal: dựng lại path và trả kết quả
    nếu đạt expansion limit: báo dừng kèm partial trace
    nếu đạt depth limit: không mở rộng nhánh này

    push các neighbor chưa thăm theo thứ tự đảo

báo không có đường kèm partial trace
```

## Thuộc tính

- Thời gian: `O(V + E)` trên graph hữu hạn khi không cutoff.
- Bộ nhớ: `O(V)` cho stack, visited và parent.
- Complete trên phần graph hữu hạn được duyệt; cutoff có thể làm mất lời giải.
- Không tối ưu theo số hop, khoảng cách, thời gian hoặc cost.

Flowchart: [flowchart.mmd](flowchart.mmd). Test kiểm tra chu trình, graph có
hướng, cutoff, start bằng goal, không có đường và trace xác định.
