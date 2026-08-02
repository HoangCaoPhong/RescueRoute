# Shared domain contract

Đây là phần dùng chung của toàn bộ thuật toán. Team nên thống nhất và merge phần này trước khi chia branch implementation.

## Thành phần dự kiến

```text
domain/
├── graph.py          # Node, Edge, Graph và truy vấn neighbor
├── route.py          # Route, RouteSegment và route totals
├── cost.py           # CostProfile và hàm tính edge cost
└── exceptions.py     # NoRouteFound, InvalidGraph...
```

## Quy ước tối thiểu

- Node và Edge có ID duy nhất, ổn định.
- Graph hỗ trợ cạnh có hướng và không bị thuật toán sửa đổi.
- Đơn vị thống nhất: khoảng cách bằng mét, thời gian bằng giây.
- Cost function được dùng chung; không sao chép vào từng thuật toán.
- Đường bị chặn được biểu diễn bằng trạng thái/constraint rõ ràng, không dùng magic number gần vô cực.
- SearchResult phải đủ dữ liệu để frontend vẽ visited nodes, frontier và final path.

Branch đề xuất: `feature/graph-search-contract`.

