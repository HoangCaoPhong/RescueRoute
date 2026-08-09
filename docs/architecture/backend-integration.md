# Quyết Định Kỹ Thuật: Backend & Tích Hợp Hệ Thống

## 1. Phương Án Tiếp Nhận Dữ Liệu & Tích Hợp API Bản Đồ

Vì dữ liệu đồ thị giao thông đã được Data Engineer (Nhân) thu thập, chuẩn hóa và đóng gói sẵn dưới dạng file tĩnh CSV, Backend sẽ tiếp nhận dữ liệu và tích hợp dịch vụ bản đồ theo phương án sau:

### a. Nguồn Dữ Liệu Đồ Thị Đầu Vào (Dataset Input):
* Backend đọc trực tiếp các file CSV vào bộ nhớ đệm RAM / Supabase Database khi máy chủ khởi tạo.

### b. API Bản Đồ & Trực Quan Hoá (Map Tile API):
* **Lựa chọn:** **OpenStreetMap Tile API** (tích hợp qua Leaflet.js).
* **Lý do chọn:**
  * Hiển thị nền bản đồ giao thông đường phố Việt Nam mượt mà, trực quan.
  * Hoàn toàn miễn phí, không giới hạn request và không cần API Key hay thẻ tín dụng.

### c. API Routing Tham Chiếu Bên Ngoài (Tùy chọn - OpenRouteService API):
* Sử dụng **OpenRouteService (ORS) API** làm nguồn tham chiếu đối sánh quãng đường/thời gian di chuyển thực tế khi cần kiểm thử kết quả.

## 2. Cơ Chế An Toàn, Bảo Mật & Xử Lý Lỗi Hệ Thống (System Security & Resilience)

1. **Cấu hình CORS (Cross-Origin Resource Sharing):**
   * **Vấn đề:** Trình duyệt web mặc định chặn các request cross-domain từ Frontend (React/HTML trên domain khác) gọi tới Backend API trên Render.
   * **Giải pháp:** Cấu hình middleware `CORSMiddleware` với `allow_origins=["*"]` trong FastAPI, cho phép ứng dụng Web/Mobile truy cập gọi API an toàn không bị lỗi Cross-Origin.

2. **Kiểm thử Hiệu năng & Xử lý Ngoại lệ (Benchmarking & Errr Handling):**
   * **Kiểm soát độ trễ (< 10ms):** Tối ưu hóa các cấu trúc dữ liệu Dictionary (Hash Map) phía Backend, đảm bảo thời gian xử lý các API phản hồi tức thì dưới **10 mili-giây**. Tích hợp endpoint `GET /api/health` đo độ trễ thực tế.
   * **Xử lý các trường hợp biên:** Kiểm tra và bọc xử lý ngoại lệ đối với dữ liệu GPS nằm ngoài phạm vi bản đồ, hoặc dữ liệu đầu vào không hợp lệ (trả về lỗi HTTP Status 400 Bad Request / 404 Not Found kèm thông điệp JSON chi tiết).
