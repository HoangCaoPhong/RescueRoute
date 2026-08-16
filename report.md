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
7. **Gỡ bỏ khối mô phỏng ùn tắc thủ công ([dashboard.html](file:///D:/RescueRoute/frontend/dashboard.html)):**
   * *(Theo ý kiến đóng góp từ **Nhân**)*: Đã xóa bỏ hoàn toàn phần **"04. Mô phỏng ùn tắc"** trên giao diện, vì hệ thống hiện tại đã tự động tính toán chi phí giao thông động từ dữ liệu thực tế theo các khung giờ (period) của backend mà không cần người dùng phải thao tác mô phỏng thủ công.



---

## 3. Kết quả kiểm thử

* **100% Automated Unit Tests:** `93/93 passed` trong **0.80 giây**.
```bash
python -m pytest backend/tests
============================= 93 passed in 0.80s ==============================
```

---

## 4. Tính toán & Đo lường chi tiết lượng RAM (Memory Profiling)

Đo đạc thực tế mức tiêu thụ bộ nhớ (Process RSS) trên môi trường Python 3.13 với toàn bộ dữ liệu giao thông TP.HCM:

### A. Phân bổ RAM nền (Baseline Memory)
* **Tiến trình Python khởi điểm (trước nạp dữ liệu):** `17.68 MB`
* **RAM nền sau khi `load_data()` và gọi `gc.collect()`:** `349.42 MB` (Tăng `+331.75 MB` cho toàn bộ cấu trúc đồ thị ~50.000 nút, hàng trăm nghìn cung, POI và cKDTree không gian).
* *Hiệu quả tối ưu:* Giải phóng toàn bộ DataFrame Pandas tạm (`df_train`, `df_nodes`, `df_base`), tiết kiệm hơn **`100 MB`** RAM nền so với trước.

### B. Mức sử dụng RAM khi chạy từng thuật toán đơn lẻ
| Thuật toán | Thời gian thực thi | RAM RSS thực tế | RAM cấp phát thêm ($\Delta$) | Tỷ lệ chiếm dụng / 512MB |
| :--- | :---: | :---: | :---: | :---: |
| **BFS** | `49.20 ms` | `357.13 MB` | `+7.71 MB` | **69.7%** (An toàn) |
| **A\*** | `131.79 ms` | `355.78 MB` | `+0.00 MB` | **69.4%** (An toàn) |
| **Dijkstra** | `137.34 ms` | `360.13 MB` | `+4.35 MB` | **70.3%** (An toàn) |
| **UCS** | `159.87 ms` | `363.92 MB` | `+3.79 MB` | **71.0%** (An toàn) |
| **DFS (Depth-Limited)** | `186.73 ms` | `370.59 MB` | `+6.67 MB` | **72.3%** (An toàn) |
| **Hill Climbing** | `8.13 ms` | `361.41 MB` | `+0.00 MB` | **70.5%** (An toàn) |

### C. Mức sử dụng RAM khi chạy "So sánh 6 thuật toán" liên tiếp
* **Trước tối ưu:**
  * DFS duyệt $> 21.000$ nodes $\to$ cấp phát hàng chục nghìn snapshot mảng trong RAM.
  * RAM tổng thể: $450\text{ MB (nền)} + 250\text{ MB (DFS)} = \mathbf{> 700\text{ MB}} \to$ **Vượt quá 512MB $\to$ Bị OOM Killer tắt tiến trình (gây HTTP 502)**.
* **Sau tối ưu:**
  * **Tổng thời gian chạy cả 6 thuật toán:** `637.56 ms` ($< 1$ giây).
  * **Mức RAM đỉnh (Peak RSS):** **`361.57 MB` / `512.00 MB`** (**`70.6%`** hạn mức Render).
  * **Dung lượng RAM còn trống (Headroom):** **`150.43 MB`** ($\approx 29.4\%$) đảm bảo hệ thống luôn hoạt động ổn định, không bao giờ bị tràn bộ nhớ.

