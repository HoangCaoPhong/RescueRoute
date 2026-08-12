# Phương Án Triển Khai Hosting / Server (Render Web Service)

Hạ tầng Backend API (Python FastAPI / Uvicorn) được triển khai trên dịch vụ Hosting Cloud / Server:

## Dịch vụ lựa chọn: Render Web Service (Cloud Hosting / VPS Container)
* **Môi trường:** Python 3.10+ (FastAPI + Uvicorn ASGI Server).
* **Cấu hình deployment:**
  * **Build Command:** `pip install -r requirements.txt`
  * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
* **Giải pháp tối ưu hóa hiệu năng & No-Sleep:**
  * **Bộ đệm RAM Đồ thị (Stateful RAM Graph):** Tải toàn bộ cấu trúc đồ thị Nodes & Edges từ `nodes.csv` / `edges.csv` / Supabase vào RAM ngay khi Server khởi động. Nhờ đó các API xử lý dữ liệu đạt tốc độ dưới **5ms**.
  * **Cơ chế Ping giữ Server (No Cold Start):** Cấu hình Cronjob định kỳ gọi API `GET /` đánh thức server, khắc phục hoàn toàn độ trễ khôi phục (50s) của gói Free trên Render.
