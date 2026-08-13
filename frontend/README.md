# Frontend - RescueRoute

Frontend hiện tại gồm 2 phần:

- Dashboard prototype chạy bằng HTML/CSS/JS thuần (`dashboard.html`, `dashboard.css`, `dashboard.js`).
- Khung thư mục React/TypeScript trong `src/` (chưa scaffold project, đang giữ cấu trúc bằng `.gitkeep`).

## Mục tiêu

- Hiển thị bản đồ giao thông và vị trí xe cấp cứu.
- Gọi API backend để tìm tuyến đường tối ưu (A*, Dijkstra/UCS, BFS, DFS).
- Trực quan hóa kết quả route và từng bước tìm kiếm.

## Yêu cầu trước khi chạy

#### 1. Cài dependency backend bằng pip từ thư mục gốc dự án (`RescueRoute/`):

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

Nếu máy dùng launcher `py` trên Windows, có thể dùng:

```bash
py -m pip install --upgrade pip
py -m pip install -r backend/requirements.txt
```

#### 2. Chạy backend từ thư mục gốc dự án:

```bash
python -m uvicorn backend.main:app --reload
```

Đảm bảo backend mở tại `http://127.0.0.1:8000` (hoặc địa chỉ tương đương).

Dashboard đang gọi trực tiếp các endpoint như:

- `/api/health`
- `/api/nodes`
- `/api/edges`
- `/api/ambulance/location`
- `/api/route`

`POST /api/route` returns the completed route and its `search_trace` in one JSON
response. The dashboard uses that saved trace to animate the search locally; it
does not ask the backend to calculate each visualization step.

## Chạy Dashboard Prototype

Do dashboard dùng `fetch('/api/...')`, bạn nên mở dashboard qua HTTP server (không nên mở file trực tiếp bằng `file://`).

Từ thư mục `frontend/`, chạy:

```bash
python -m http.server 5500
```

Sau đó truy cập:

- `http://127.0.0.1:5500/dashboard.html`

> Nếu backend đang ở domain/port khác frontend, cần thêm proxy hoặc cấu hình CORS phù hợp ở backend.

## Cấu trúc thư mục frontend

```text
frontend/
├── dashboard.html            # Giao diện dashboard prototype
├── dashboard.css             # Style cho dashboard
├── dashboard.js              # Logic map, gọi API, hiển thị route
├── public/                   # Static assets cho app frontend tương lai
├── src/
│   ├── assets/
│   ├── components/
│   ├── features/
│   │   ├── map/
│   │   ├── route-planner/
│   │   └── search-visualizer/
│   ├── hooks/
│   ├── lib/api/
│   ├── pages/
│   ├── services/
│   ├── store/
│   ├── styles/
│   └── types/
└── tests/
```

## Lưu ý cho team

- Không commit secret hoặc token vào frontend.
- Giữ contract request/response đồng bộ với backend (`backend/app/schemas/`).
- Khi backend đổi endpoint hoặc field dữ liệu, cập nhật tài liệu này và UI tương ứng.
