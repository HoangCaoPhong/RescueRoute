## Summary

- **Xử lý triệt để lỗi tràn RAM 512MB & HTTP 502 Gateway Timeout trên tuyến đường dài:** Khắc phục tình trạng sập tiến trình hoặc timeout 30s của reverse proxy (Render Free Tier) khi so sánh 6 thuật toán trên các tuyến đường xuyên thành phố (ví dụ: từ Lê Văn Quới, Bình Tân $\to$ BV Nhân dân 115, Quận 10).
- **Tối ưu hóa tầng quan sát Search Trace (Frontier Snapshot):**
  - Giảm kích thước snapshot hàng đợi ưu tiên trong A*, Dijkstra, UCS từ 250 items xuống **24 items** (vừa vặn với thanh chip hiển thị trên UI).
  - Tự động bỏ qua bước trích xuất heap đắt đỏ (`heapq.nsmallest`) sau bước duyệt thứ 500, loại bỏ việc tạo hàng triệu dictionary trong RAM.
  - Tăng tốc Dijkstra từ $10.27\text{s} \to \mathbf{256\text{ms}}$ ($40\times$ nhanh hơn), UCS từ $3.22\text{s} \to \mathbf{115\text{ms}}$ ($28\times$ nhanh hơn), A* từ $1.35\text{s} \to \mathbf{129\text{ms}}$ ($10.5\times$ nhanh hơn) mà **không làm thay đổi bất kỳ logic cốt lõi hay tính đúng đắn nào của thuật toán**.
- **Cấu trúc lại thuật toán DFS:** Tách biệt rõ ràng giữa `solve_dfs` (Standard Unconstrained DFS lý thuyết thuần túy) và `solve_depth_limited_dfs` (Depth-Limited Search có giới hạn `max_expansions` mặc định 3.000 nodes) để sử dụng an toàn trên mạng lưới đường bộ thực tế.
- **Sửa lỗi JSON Serialization của `numpy.bool_`:** Khắc phục lỗi `TypeError: 'numpy.bool' object is not iterable` khi FastAPI serialize response của Hill Climbing; chuẩn hóa ép kiểu an toàn trong `normalize_frontier_item`.
- **FastAPI Non-blocking Event Loop:** Chuyển các endpoint tính toán đường đi CPU-bound từ `async def` sang `def` để FastAPI tự động đẩy vào Worker Threadpool, giúp máy chủ luôn phản hồi kịp thời Health check (tránh bị reverse proxy ngắt kết nối báo 502).
- **Thu dọn bộ nhớ nền:** Gọi `del df_nodes, df_train, df_base, ...` và `gc.collect()` ngay sau khi build xong đồ thị trong `GraphManager`, tiết kiệm hơn 100MB RAM nền.
- **Dọn dẹp giao diện Frontend (theo ý kiến từ Nhân):**
  - Gỡ bỏ khối "04. Mô phỏng ùn tắc" thủ công do hệ thống hiện đã tự động tính toán chi phí giao thông động từ dữ liệu thực tế theo các khung giờ (period).
  - Gỡ bỏ khối "Giải thích tuyến đường" giúp giao diện gọn gàng, trực quan hơn.
  - Bắt sạch các mã lỗi HTML 502/504 từ Gateway để hiển thị thông báo lỗi ngắn gọn thay vì chèn raw HTML vào bảng kết quả.

## Related task

- Tối ưu hóa hiệu năng thuật toán tìm đường trên đồ thị giao thông TP.HCM, xử lý lỗi tràn 512MB RAM và timeout HTTP 502 khi so sánh 6 thuật toán trên Render.

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
============================= 93 passed in 0.63s ==============================
```

### 2. Kiểm thử tự động Frontend (Node.js Test Runner)
```bash
node --test frontend/tests/dashboard.logic.test.js
# tests 17
# pass 17
# fail 0
# duration_ms 180.12
```

### 3. Checklist
- [x] Test liên quan chạy qua
- [x] Đã tự review diff
- [x] Không commit secret, cache hoặc file sinh ra
- [x] Đã cập nhật API/data/docs nếu contract thay đổi
- [x] UI change có ảnh/video hoặc mô tả kiểm tra

## API / data compatibility

- **Hoàn toàn tương thích ngược (Backward-compatible):** Logic tìm đường cốt lõi và tính tối ưu toán học của các thuật toán được giữ nguyên 100%. Không thay đổi schema request/response của các endpoint `/api/route`, `/api/route/multi-location`, `/api/route/nearest-hospital`. Payload trả về chuẩn hóa kiểu dữ liệu nguyên bản Python (`bool`, `float`, `int`).

## Screenshots / benchmark

### 1. Benchmark trên tuyến đường dài xuyên thành phố (Lê Văn Quới, Bình Tân $\to$ BV Nhân dân 115, Quận 10)

| Thuật toán | Số nodes duyệt | Trước tối ưu | Sau tối ưu | Tỷ lệ tăng tốc | Trạng thái |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **BFS** | $15.866$ | $557\text{ ms}$ | **$449\text{ ms}$** | $1.2\times$ | Tìm thấy (213 chặng) |
| **DFS (Depth-Limited)** | $3.000$ | $241\text{ ms}$ | **$198\text{ ms}$** | $1.2\times$ | Dừng an toàn (3.000 nodes) |
| **UCS** | $6.100$ | $3.220\text{ ms}$ (3.2s) | **$115\text{ ms}$** | **$28\times$ nhanh hơn** | Tìm thấy (246 chặng) |
| **A\*** | $2.061$ | $1.355\text{ ms}$ (1.3s) | **$129\text{ ms}$** | **$10.5\times$ nhanh hơn** | Tìm thấy (242 chặng) |
| **Dijkstra** | $11.176$ | $10.273\text{ ms}$ (10.3s) | **$256\text{ ms}$** | **$40\times$ nhanh hơn** | Tìm thấy (251 chặng) |
| **Hill Climbing** | $4$ | $46\text{ ms}$ | **$1.28\text{ ms}$** | $36\times$ | Dừng tại cực trị cục bộ |
| **Tổng cả 6 thuật toán** | — | **$> 16\text{ giây}$ (Timeout 502)** | **$\approx 1.1\text{ giây}$** | **$> 15\times$ nhanh hơn** | **Hoàn thành 6/6 mượt mà** |

### 2. Đo lường mức tiêu thụ RAM (Memory Working Set / RSS)

| Giai đoạn thực thi | Mức RAM thực tế | Tỷ lệ chiếm dụng / 512MB | Đánh giá an toàn |
| :--- | :---: | :---: | :---: |
| Tiến trình Python khởi điểm | `17.68 MB` | 3.5% | — |
| Sau khi nạp đồ thị (`load_data()` + `gc.collect()`) | `349.42 MB` | 68.2% | Tiết kiệm > 100MB RAM nền |
| Chạy đơn lẻ từng thuật toán | `355.78 MB – 370.59 MB` | 69.4% – 72.3% | An toàn |
| **Chạy liên tiếp cả 6 thuật toán (So sánh)** | **`361.57 MB`** | **`70.6%`** | **Dư an toàn 150.43 MB (29.4%)** |
