# Frontend

## English

RescueRoute's frontend is a React and TypeScript single-page dashboard styled
with Tailwind CSS and rendered on Leaflet. The interface is intentionally
typography-led: the map remains the primary workspace, controls use plain text,
and symbols are reserved for map data or essential navigation.

### Technology

- React 18 and TypeScript in strict mode;
- Vite for development and production builds;
- Tailwind CSS for the restrained light/dark design system;
- React-Leaflet for road, hospital, ambulance, route, and search-trace layers.

### Development

Run the API and Vite in separate terminals from the repository root:

```bash
python -m uvicorn backend.main:app --reload
```

```bash
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api`, `/docs`, and
`/openapi.json` to FastAPI on port 8000.

### Production build

```bash
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn backend.main:app
```

FastAPI serves `frontend/dist/index.html` and its hashed assets at
`http://127.0.0.1:8000/`. The generated `dist/` directory is intentionally
ignored by Git and must be rebuilt for deployment.

### Structure

```text
frontend/
├── src/components/             # Shared interface primitives
├── src/features/map/           # Leaflet map and data layers
├── src/features/route-planner/ # Route controls, results, and utilities
├── src/features/search-visualizer/ # Search-trace playback
├── src/lib/api/                # HTTP boundary and API field mapping
├── src/pages/                  # Page composition
├── src/styles/                 # Tailwind entry point and Leaflet refinements
└── src/types/                  # Backend contract types
```

### Verification

```bash
npm test
npm run build
npm audit --audit-level=moderate
```

No credential, map token, or user GPS history is stored in frontend code.

---

## Tiếng Việt

Frontend của RescueRoute là dashboard một trang dùng React và TypeScript, tạo
style bằng Tailwind CSS và hiển thị bản đồ qua Leaflet. Giao diện ưu tiên hệ
thống chữ: bản đồ là không gian làm việc chính, các điều khiển dùng nhãn chữ rõ
ràng, còn ký hiệu chỉ dành cho dữ liệu bản đồ hoặc điều hướng bắt buộc.

### Công nghệ

- React 18 và TypeScript strict mode;
- Vite cho môi trường phát triển và production build;
- Tailwind CSS cho hệ thống giao diện sáng/tối tối giản;
- React-Leaflet cho lớp mạng đường, bệnh viện, xe cấp cứu, tuyến và search trace.

### Phát triển local

Chạy API và Vite trong hai terminal riêng từ thư mục gốc repository:

```bash
python -m uvicorn backend.main:app --reload
```

```bash
cd frontend
npm ci
npm run dev
```

Mở `http://127.0.0.1:5173`. Vite chuyển tiếp `/api`, `/docs` và
`/openapi.json` sang FastAPI ở cổng 8000.

### Build production

```bash
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn backend.main:app
```

FastAPI phục vụ `frontend/dist/index.html` cùng các asset có hash tại
`http://127.0.0.1:8000/`. Thư mục sinh `dist/` được Git bỏ qua và phải được
build lại khi triển khai.

### Cấu trúc

```text
frontend/
├── src/components/             # Component giao diện dùng chung
├── src/features/map/           # Bản đồ Leaflet và các lớp dữ liệu
├── src/features/route-planner/ # Điều khiển, kết quả và tiện ích định tuyến
├── src/features/search-visualizer/ # Phát lại search trace
├── src/lib/api/                # Biên HTTP và ánh xạ field API
├── src/pages/                  # Ghép bố cục trang
├── src/styles/                 # Tailwind entry point và tinh chỉnh Leaflet
└── src/types/                  # Kiểu dữ liệu theo contract backend
```

### Kiểm tra

```bash
npm test
npm run build
npm audit --audit-level=moderate
```

Không lưu credential, map token hoặc lịch sử GPS người dùng trong frontend.
