# Graph-search algorithms

Nhóm này tìm tuyến từ một start node đến một goal node trên cùng Graph abstraction.

```text
graph_search/
├── astar/
├── bfs/
├── dfs/
├── dijkstra/
└── ucs/
```

Các thuật toán phải dùng cùng neighbor order hoặc ghi rõ cách tie-breaking để kết quả test có thể tái lập. Không so sánh hiệu năng nếu input graph, cost profile hoặc điều kiện dừng khác nhau.

