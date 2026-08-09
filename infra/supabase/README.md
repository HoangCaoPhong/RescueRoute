# Phương Án Quản Lý Dữ Liệu & Tích Hợp Supabase (PostgreSQL)

Hệ thống sử dụng **Supabase (PostgreSQL)** làm nền tảng Cơ sở dữ liệu Cloud, Quản lý người dùng và Đồng bộ Real-time:

## 1. Cơ sở dữ liệu PostgreSQL (Database Storage)
* **Bảng `ambulance_logs`:** Lưu lịch sử tọa độ GPS của xe cấp cứu theo thời gian.
* **Bảng `route_histories`:** Lưu vết kết quả tìm đường và thông số hiệu năng hệ thống.

## 2. Xác thực & Phân quyền (Supabase Auth)
* Quản lý đăng nhập / đăng ký tài khoản phân quyền cho: **Tài xế xe cấp cứu**, **Bác sĩ điều phối**, và **Quản trị viên (Admin)**.

## 3. Đồng bộ Thời gian thực (Supabase Realtime WebSocket)
* Kết nối kênh Realtime để tự động push vị trí GPS xe cấp cứu 🚑 và biến động kẹt xe 🚦 tới tất cả các client đang mở ứng dụng mà không cần F5 / Polling.

## 4. Tiện ích PostGIS Spatial Extension
* Kích hoạt extension PostGIS trên Supabase để thực hiện các truy vấn tìm kiếm điểm cứu hộ theo vùng địa lý trực tiếp bằng SQL (`ST_DWithin`, `ST_Distance`).
