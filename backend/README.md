# Backend workspace

Thư mục này chứa FastAPI demo, graph manager trong RAM, routing service,
các thuật toán tìm kiếm/tối ưu và test backend. Entry point hiện tại
là `backend.main:app`; dependency được khai báo trong `requirements.txt`.

## Đọc theo thứ tự

1. [`../CODING_RULES.md`](../CODING_RULES.md): quy tắc code, graph, cost, API và test.
2. [`app/algorithms/README.md`](app/algorithms/README.md): contract và cách thêm một thuật toán.
3. [`app/domain/README.md`](app/domain/README.md): phần dùng chung phải hoàn thành trước khi code thuật toán.
4. [`tests/README.md`](tests/README.md): vị trí và yêu cầu test.

## Cấu trúc

```text
backend/
├── app/
│   ├── api/routes/          # FastAPI endpoints
│   ├── algorithms/          # Thuật toán thuần Python
│   ├── core/                # Config, constants, logging
│   ├── schemas/             # API request/response
│   └── services/            # Điều phối use case
└── tests/
    ├── fixtures/
    ├── integration/
    └── unit/
```

## Luồng backend hiện tại

1. `GraphManager` nạp graph processed và các POI vào RAM.
2. FastAPI route validate request và gọi `app/services/routing_service.py`.
3. Service chọn BFS, DFS, UCS, A*, Dijkstra hoặc Hill Climbing.
4. Mọi thuật toán trả final path và unified search trace cho frontend.
5. Route nhiều điểm dùng Nearest Neighbor hoặc Held–Karp để sắp waypoint.

Thuật toán không tự đọc CSV, gọi FastAPI hoặc ghi JSON. Data adapter và
optional trace exporter nằm ngoài folder thuật toán.

## Môi trường Python

Backend dùng Python 3.10+. Cài package bằng
`python -m pip install -r backend/requirements.txt`. Không commit `venv`,
`.venv` hoặc dependency manifest riêng trong từng folder thuật toán.

## Cách chạy Server (Quan trọng)

> [!WARNING]
> Để tránh lỗi `ModuleNotFoundError`, bạn **bắt buộc** phải khởi chạy server từ thư mục gốc của toàn dự án (`RescueRoute/`), **KHÔNG** chạy từ bên trong thư mục `backend/`.

**Lệnh khởi chạy:**
```bash
# Đứng tại thư mục gốc RescueRoute
python -m uvicorn backend.main:app --reload
```
