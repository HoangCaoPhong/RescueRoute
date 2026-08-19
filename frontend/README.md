# Frontend

## English

The current frontend is a Leaflet dashboard prototype written in plain HTML,
CSS, and JavaScript. The folders under `src/` are placeholders for a future
React/TypeScript application and are not yet an independently buildable app.

### Run the dashboard

The recommended approach is to let FastAPI serve both the UI and API:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000/`. For static-only development, run
`python -m http.server 5500` inside `frontend/`; this requires a compatible
backend URL and CORS configuration.

```text
frontend/
├── dashboard.html       # Page structure
├── dashboard.css        # Styling and display states
├── dashboard.js         # Leaflet, API calls, and trace playback
├── tests/               # JavaScript logic tests
├── public/              # Future static assets
└── src/                 # Future React/TypeScript structure
```

The dashboard receives a route and its `search_trace` in one response, then
replays that trace locally. Run tests with:

```bash
node --test frontend/tests/dashboard.logic.test.js
```

Keep frontend fields and endpoints synchronized with the backend contract, and
never place secrets or access tokens in client-side code.

---

## Tiếng Việt

Frontend hiện là dashboard prototype dùng HTML, CSS, JavaScript thuần và
Leaflet. Các thư mục trong `src/` mới là khung dành cho React/TypeScript trong
giai đoạn sau, chưa phải ứng dụng có thể build độc lập.

## Chạy dashboard

Cách đơn giản nhất là để FastAPI phục vụ cả giao diện và API:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Sau đó mở `http://127.0.0.1:8000/`.

Nếu chỉ cần xem static frontend, có thể chạy server riêng:

```bash
cd frontend
python -m http.server 5500
```

Cách này cần cấu hình backend URL/CORS phù hợp vì dashboard gọi các endpoint
`/api/...`.

## Cấu trúc

```text
frontend/
├── dashboard.html       # Bố cục giao diện
├── dashboard.css        # Style và trạng thái hiển thị
├── dashboard.js         # Leaflet, gọi API và phát search trace
├── tests/               # Test logic JavaScript
├── public/              # Static assets tương lai
└── src/                 # Khung React/TypeScript tương lai
```

Dashboard nhận route và `search_trace` trong cùng response, sau đó phát lại
trace ở phía client. Thuật toán không ghi file JSON trong lúc xử lý request.

## Kiểm tra

```bash
node --test frontend/tests/dashboard.logic.test.js
```

Khi đổi API field hoặc endpoint, cập nhật đồng thời backend, frontend và tài
liệu contract. Không đặt token hoặc secret trong mã frontend.
