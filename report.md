# Walkthrough - Search Algorithm Optimizations & 512MB RAM Efficiency

Đã tạo nhánh `feature/dfs_and_more_optimizations` và hoàn thành gói tối ưu toàn diện xử lý triệt để lỗi tràn bộ nhớ (512MB RAM), nghẽn hiệu năng và lỗi `HTTP 502 Bad Gateway`.

---

## 1. Cấu trúc Thuật toán DFS

1. **`solve_dfs` ([dfs.py](file:///D:/RescueRoute/backend/app/algorithms/graph_search/dfs/dfs.py)):**
   * Giữ nguyên bản chất **Standard Depth-First Search thuần túy**, không áp đặt giới hạn mở rộng (unconstrained), sử dụng LIFO stack.
   * Tối ưu hóa snapshot slice ngăn xếp ($\le 250$ phần tử) để tránh nhân bản mảng hàng chục nghìn phần tử trong RAM.
2. **`solve_depth_limited_dfs` / `solve_bounded_dfs` ([dfs.py](file:///D:/RescueRoute/backend/app/algorithms/graph_search/dfs/dfs.py)):**
   * Thuật toán **Depth-Limited Search (DLS)** hỗ trợ cả `max_depth` và `max_expansions` (mặc định 3.000 nodes).
   * Được sử dụng bởi `routing_service.py` khi tìm đường trên mạng lưới giao thông thực tế nhằm chống tràn RAM và ngăn ngừa chạy lan man.

---

## 2. Các tối ưu hóa khác

1. **A\* & UCS ([astar.py](file:///D:/RescueRoute/backend/app/algorithms/graph_search/astar/astar.py), [ucs.py](file:///D:/RescueRoute/backend/app/algorithms/graph_search/ucs/ucs.py)):**
   * Tối ưu `_active_frontier` với `heapq.nsmallest` giới hạn trong phạm vi 250 items, loại bỏ việc sort toàn bộ heap nghìn phần tử ở từng bước duyệt.
2. **SearchTraceHistory ([trace_history.py](file:///D:/RescueRoute/backend/app/algorithms/graph_search/trace_history.py)):**
   * Loại bỏ `deepcopy` đệ quy chậm chạp, thay bằng shallow copy trực tiếp các dict/list snapshot.
3. **Dataframe Cleanup ([main.py](file:///D:/RescueRoute/backend/main.py)):**
   * Gọi `del df_nodes, df_train, df_base, ...` và `gc.collect()` ngay sau khi build đồ thị xong, giải phóng hàng trăm MB RAM cho môi trường 512MB.
4. **FastAPI Event Loop Non-Blocking ([main.py](file:///D:/RescueRoute/backend/main.py)):**
   * Đổi endpoint tìm đường CPU-bound sang `def` để FastAPI tự động đưa vào Worker Threadpool, giúp Event loop luôn phản hồi kịp thời các request và health check (ngăn Render trả về 502 Bad Gateway).
5. **Giới hạn kích thước Search Trace ([search_trace.py](file:///D:/RescueRoute/backend/app/services/search_trace.py)):**
   * Lấy mẫu tối đa 500 bước (bảo toàn bước đầu và bước cuối), giữ JSON payload $< 300\text{ KB}$.
6. **Frontend Sanitization ([dashboard.js](file:///D:/RescueRoute/frontend/dashboard.js)):**
   * Bắt sạch các trang lỗi HTML 502/504 từ reverse proxy, tránh chèn mã HTML thô vào giao diện.

---

## 3. Kết quả kiểm thử

* **100% Automated Unit Tests:** `93/93 passed` trong **0.80 giây**.
```bash
python -m pytest backend/tests
============================= 93 passed in 0.80s ==============================
```
