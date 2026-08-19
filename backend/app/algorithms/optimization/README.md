# Optimization

## English

This group optimizes waypoint order or constructs heuristic route solutions.

| Algorithm | Type | Guarantee |
| --- | --- | --- |
| Nearest Neighbor | Greedy waypoint ordering | Approximate with multiple waypoints |
| Held-Karp | Dynamic programming | Exact on the supplied pairwise matrix |
| Genetic Algorithm | Population heuristic | Approximate and reproducible by seed |
| Simulated Annealing | Stochastic local search | Approximate and reproducible by seed |
| Hill Climbing | Greedy local search | Incomplete and not globally optimal |

Multi-location methods receive a pairwise matrix computed by the routing
service. They optimize visit order; the quality of each route segment still
depends on the selected two-location search method.

---

## Tiếng Việt

Nhóm này tối ưu thứ tự ghé nhiều điểm hoặc xây dựng lời giải heuristic.

| Thuật toán | Loại | Bảo đảm |
| --- | --- | --- |
| Nearest Neighbor | Greedy waypoint ordering | Xấp xỉ khi có nhiều waypoint |
| Held–Karp | Dynamic programming | Tối ưu trên pairwise cost matrix |
| Genetic Algorithm | Population heuristic | Xấp xỉ, tái lập theo seed |
| Simulated Annealing | Stochastic local search | Xấp xỉ, tái lập theo seed |
| Hill Climbing | Greedy local search | Không complete, không tối ưu toàn cục |

Thuật toán nhiều điểm nhận cost matrix đã được routing service tính trước.
Chúng tối ưu thứ tự ghé; tính đúng/tối ưu của từng đoạn vẫn phụ thuộc thuật
toán tìm đường hai điểm được chọn.
