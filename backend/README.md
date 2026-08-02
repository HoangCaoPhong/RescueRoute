# Backend workspace

Thư mục này sẽ chứa FastAPI API, domain model, thuật toán tìm đường và test backend. Hiện tại repository chỉ dựng khung để các thành viên phát triển song song; chưa có ứng dụng backend chạy được và chưa khóa dependency.

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
│   ├── domain/              # Node, Edge, Graph, Route, cost
│   ├── integrations/        # Supabase, map/routing services
│   ├── repositories/        # Đọc/ghi dữ liệu
│   ├── schemas/             # API request/response
│   └── services/            # Điều phối use case
└── tests/
    ├── fixtures/
    ├── integration/
    └── unit/
```

## Thứ tự triển khai đề xuất

1. Merge `feature/graph-search-contract`: Node, Edge, Graph, CostProfile, SearchRequest và SearchResult.
2. Merge dataset mẫu ổn định vào `data/samples/`.
3. Các thành viên tạo branch thuật toán từ `dev` và chỉ làm trong folder được giao cùng folder test tương ứng.
4. Merge route service để chọn/chạy thuật toán.
5. Sau cùng mới nối FastAPI, frontend và dịch vụ ngoài.

Không để mỗi thuật toán tự định nghĩa một Graph hoặc kiểu kết quả riêng. Nếu contract chung chưa tồn tại, ưu tiên hoàn thành contract trước thay vì viết tạm rồi sửa hàng loạt.

## Môi trường Python

Backend dự kiến dùng Python 3.10+. Khi branch nền tảng thêm manifest dependency, thành viên sẽ cài theo lệnh được ghi trong README này. Trước thời điểm đó không tự tạo và commit `venv`, `.venv` hoặc dependency manifest riêng trong từng folder thuật toán.

