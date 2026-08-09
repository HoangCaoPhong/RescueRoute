# API Định Vị GPS Xe Cấp Cứu

Backend chịu trách nhiệm tiếp nhận, xử lý và định vị vị trí xe cấp cứu theo thời gian thực thông qua các bước:

## 1. Thu thập dữ liệu GPS từ Client
* Sử dụng **Browser Geolocation API** (`navigator.geolocation.watchPosition`) trên thiết bị di động / máy tính của tài xế để tự động gửi tọa độ vĩ độ (Lat) và kinh độ (Lng) lên Backend.

## 2. Các API Endpoint GPS phía Backend

### API Cập nhật GPS (`POST /api/ambulance/location`)
* **Input Body:** `{ "lat": float, "lng": float }`
* **Xử lý:** Backend tiếp nhận tọa độ, tự động tính khoảng cách Euclidean/Haversine để **ánh xạ sang Node giao thông gần nhất (`mapped_nearest_node`)** trong dataset kèm khoảng cách tính theo mét.
* **Ghi nhật ký:** Đồng bộ tọa độ xe cấp cứu xuống bảng `ambulance_logs` trên Supabase.

### API Truy xuất GPS (`GET /api/ambulance/location`)
* Cung cấp vị trí GPS mới nhất cùng thông tin Node gần nhất cho màn hình bản đồ điều phối (Dispatcher Dashboard).
