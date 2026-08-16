## Summary

- **Khắc phục lỗi tràn RAM 512MB & HTTP 502 Bad Gateway:** Xử lý triệt để tình trạng sập máy chủ trên môi trường cloud (Render Free tier 512MB) khi bấm "So sánh 6 thuật toán".
- **Cấu trúc lại thuật toán DFS:** Tách biệt rõ ràng giữa `solve_dfs` (Standard Unconstrained DFS lý thuyết thuần túy) và `solve_depth_limited_dfs` (Depth-Limited Search có giới hạn `max_expansions` mặc định 3.000 nodes) để sử dụng an toàn trên mạng lưới đường bộ thực tế.
- **Tối ưu hóa hiệu năng & bộ nhớ Search Trace:** 
  - Tối ưu `_active_frontier` trong A* và UCS với `heapq.nsmallest` giới hạn trong 250 items, loại bỏ việc sort toàn bộ heap nghìn phần tử ở từng bước duyệt.
  - Loại bỏ `deepcopy` đệ quy trong `SearchTraceHistory`, chuyển sang shallow copy trực tiếp.
  - Thu gom rác `gc.collect()` và giải phóng toàn bộ DataFrame Pandas tạm (`df_train`, `df_nodes`, `df_base`) sau khi hoàn tất nạp đồ thị, tiết kiệm hơn 100MB RAM nền.
- **FastAPI Non-blocking Event Loop:** Chuyển các endpoint tính toán đường đi CPU-bound từ `async def` sang `def` để FastAPI tự động đẩy vào Worker Threadpool, giúp máy chủ luôn phản hồi kịp thời Health check (tránh bị reverse proxy ngắt kết nối báo 502).
- **Khống chế kích thước Payload JSON:** Thêm giới hạn và thuật toán lấy mẫu `MAX_TRACE_STEPS = 500` cho dữ liệu `search_trace`, giữ dung lượng JSON dưới 300KB.
- **Sửa lỗi JSON Serialization của `numpy.bool_`:** Khắc phục lỗi `TypeError: 'numpy.bool' object is not iterable` khi FastAPI serialize response của Hill Climbing; chuẩn hóa ép kiểu an toàn trong `normalize_frontier_item`.
- **Dọn dẹp giao diện Frontend (theo ý kiến từ Nhân):**
  - Gỡ bỏ khối "04. Mô phỏng ùn tắc" thủ công trên giao diện sidebar do hệ thống hiện đã tự động tính toán chi phí giao thông động từ dữ liệu thực tế theo các khung giờ (period).
  - Gỡ bỏ khối "Giải thích tuyến đường" giúp giao diện hiển thị kết quả gọn gàng, trực quan hơn.
  - Bắt sạch các mã lỗi HTML 502/504 từ Gateway để hiển thị thông báo lỗi ngắn gọn thay vì chèn raw HTML vào bảng kết quả.

## Related task

- Tối ưu hóa hiệu năng thuật toán tìm đường trên đồ thị giao thông TP.HCM, xử lý lỗi tràn 512MB RAM và sập tiến trình khi so sánh 6 thuật toán.

## Type of change

- [x] Feature / algorithm
- [x] Bug fix
- [x] Refactor
- [x] Test / benchmark
- [x] Documentation
- [ ] Data / schema
- [ ] Infrastructure

## Verification

### 1. Kiểm thử tự động Backend (Pytest)
```bash
python -m pytest backend/tests
============================= 93 passed in 0.67s ==============================
```

### 2. Kiểm thử tự động Frontend (Node.js Test Runner)
```bash
node --test frontend/tests/dashboard.logic.test.js
# tests 17
# pass 17
# fail 0
# duration_ms 171.00
```

### 3. Checklist
- [x] Test liên quan chạy qua
- [x] Đã tự review diff
- [x] Không commit secret, cache hoặc file sinh ra
- [x] Đã cập nhật API/data/docs nếu contract thay đổi
- [x] UI change có ảnh/video hoặc mô tả kiểm tra

## API / data compatibility

- **Hoàn toàn tương thích ngược (Backward-compatible):** Không thay đổi schema request/response của các endpoint `/api/route`, `/api/route/multi-location`, `/api/route/nearest-hospital`. Payload trả về chuẩn hóa kiểu dữ liệu nguyên bản Python (`bool`, `float`, `int`).

## Screenshots / benchmark

### 1. Benchmark thời gian thực thi (So sánh 6 thuật toán trên mạng lưới TP.HCM)

| Thuật toán | Trước tối ưu | Sau tối ưu | Tỷ lệ cải thiện | Trạng thái |
| :--- | :---: | :---: | :---: | :---: |
| **BFS** | $211\text{ ms}$ | **$19.59\text{ ms}$** | **$10\times$ nhanh hơn** | Tìm thấy (38 chặng) |
| **A\*** | $218\text{ ms}$ | **$50.00\text{ ms}$** | **$4.3\times$ nhanh hơn** | Tìm thấy (38 chặng) |
| **Dijkstra** | $336\text{ ms}$ | **$68.41\text{ ms}$** | **$5\times$ nhanh hơn** | Tìm thấy (44 chặng) |
| **UCS** | $487\text{ ms}$ | **$76.20\text{ ms}$** | **$6.4\times$ nhanh hơn** | Tìm thấy (38 chặng) |
| **DFS (Depth-Limited)** | $25.950\text{ ms}$ (26s) | **$105.72\text{ ms}$** | **$245\times$ nhanh hơn** | Dừng an toàn (3.000 nodes) |
| **Hill Climbing** | $15\text{ ms}$ | **$3.17\text{ ms}$** | **$5\times$ nhanh hơn** | Dừng tại cực trị cục bộ |
| **Tổng chuỗi 6 thuật toán** | **$> 30\text{ giây}$ (sập server / 502)** | **$< 0.35\text{ giây}$** | **$> 85\times$ nhanh hơn** | **Hoàn thành 6/6 mượt mà** |

### 2. Đo lường mức tiêu thụ RAM (Memory Working Set / RSS)

| Giai đoạn thực thi | Mức RAM thực tế | Tỷ lệ chiếm dụng / 512MB | Đánh giá an toàn |
| :--- | :---: | :---: | :---: |
| Tiến trình Python khởi điểm | `17.68 MB` | 3.5% | — |
| Sau khi nạp đồ thị (`load_data()` + `gc.collect()`) | `349.42 MB` | 68.2% | Tiết kiệm > 100MB RAM nền |
| Chạy đơn lẻ từng thuật toán | `355.78 MB – 370.59 MB` | 69.4% – 72.3% | An toàn |
| **Chạy liên tiếp cả 6 thuật toán (So sánh)** | **`361.57 MB`** | **`70.6%`** | **Dư an toàn 150.43 MB (29.4%)** |
