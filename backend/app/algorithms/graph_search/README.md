# Graph search

## English

This group searches for a route from one start node to one goal node on a
directed graph.

| Algorithm | Strategy | Main guarantee |
| --- | --- | --- |
| BFS | FIFO queue | Minimum hops when all edges are equal |
| DFS | LIFO stack | Finds a route on a finite explored graph; not optimal |
| UCS | Minimum `g(n)` | Optimal with non-negative costs |
| Dijkstra | Minimum accumulated weight | Optimal with non-negative weights |
| A* | Minimum `g(n) + h(n)` | Optimal with an admissible heuristic |

All implementations use deterministic neighbor ordering, do not mutate the
input graph, and record events through `SearchTraceHistory`. Each frontier is
captured immediately before the current node is expanded.

---

## Tiếng Việt

Nhóm này tìm tuyến từ một node bắt đầu đến một node đích trên đồ thị có hướng.

| Thuật toán | Chiến lược | Bảo đảm chính |
| --- | --- | --- |
| BFS | Hàng đợi FIFO | Ít cạnh nhất khi mọi cạnh ngang nhau |
| DFS | Ngăn xếp LIFO | Tìm được một đường trên graph hữu hạn, không tối ưu |
| UCS | Ưu tiên `g(n)` | Tối ưu với cost không âm |
| Dijkstra | Ưu tiên tổng trọng số | Tối ưu với trọng số không âm |
| A* | Ưu tiên `g(n) + h(n)` | Tối ưu khi heuristic admissible |

Mọi thuật toán dùng thứ tự neighbor xác định, không sửa graph đầu vào và ghi
trace qua `SearchTraceHistory`. Frontier được chụp ngay trước khi mở rộng node
hiện tại để frontend có thể phát lại nhất quán.
