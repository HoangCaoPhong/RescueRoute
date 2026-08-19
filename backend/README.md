# Backend

## English

The backend contains the FastAPI application, the in-memory road graph,
routing services, search and optimization algorithms, and automated tests. Its
entry point is `backend.main:app`.

### Structure

```text
backend/
├── main.py                 # FastAPI app, request schemas, and routes
├── requirements.txt
├── app/
│   ├── algorithms/         # Framework-free Python algorithms
│   ├── core/               # Application settings
│   └── services/           # Routing orchestration and trace normalization
└── tests/                  # Unit and integration tests
```

`GraphManager` loads data from `data/processed/`, builds the adjacency graph,
and creates spatial indexes. Route handlers validate requests before delegating
the computation to `backend/app/services/routing_service.py`.

### Install and run

Run from the repository root so Python can resolve internal packages:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

- Dashboard: `http://127.0.0.1:8000/`
- OpenAPI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

Keep algorithms independent of FastAPI, pandas, databases, and the UI. Put
use-case orchestration in `app/services/`, reuse the shared graph/cost/trace
contracts, and update tests whenever behavior changes.

Read the [coding rules](../CODING_RULES.md),
[algorithm guide](app/algorithms/README.md), and
[test guide](tests/README.md) before modifying the backend.

---

## Tiếng Việt

Backend gồm FastAPI app, graph trong bộ nhớ, service điều phối, các thuật toán
tìm kiếm/tối ưu và bộ test. Entry point là `backend.main:app`.

## Cấu trúc

```text
backend/
├── main.py                 # FastAPI app, request schema và route
├── requirements.txt
├── app/
│   ├── algorithms/         # Thuật toán thuần Python
│   ├── core/               # Cấu hình ứng dụng
│   └── services/           # Điều phối tìm đường và chuẩn hóa trace
└── tests/                  # Unit/integration tests
```

`GraphManager` trong `backend/main.py` nạp dữ liệu từ `data/processed/`, dựng
adjacency graph và các chỉ mục không gian. Route handler kiểm tra request rồi
chuyển việc tính toán cho `backend/app/services/routing_service.py`.

## Cài đặt và chạy

Luôn chạy từ thư mục gốc repository để Python tìm đúng package:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

- Dashboard: `http://127.0.0.1:8000/`
- OpenAPI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

## Nguyên tắc thay đổi

- Giữ thuật toán độc lập với FastAPI, pandas và giao diện.
- Đặt điều phối use case trong `app/services/`.
- Dùng chung graph, cost, result và trace contract; không tạo bản sao riêng cho
  từng thuật toán.
- Thêm hoặc cập nhật test khi thay đổi hành vi.

Đọc [quy tắc code](../CODING_RULES.md),
[hướng dẫn thuật toán](app/algorithms/README.md) và
[hướng dẫn test](tests/README.md) trước khi sửa backend.
