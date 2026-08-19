# Backend tests

## English

Tests mirror the source layout so ownership and review paths remain clear:

```text
backend/tests/
├── fixtures/          # Shared graphs and datasets
├── integration/       # Flows spanning multiple modules
└── unit/
    ├── algorithms/
    │   ├── graph_search/
    │   └── optimization/
    ├── data/
    └── services/
```

Run the full backend suite from the repository root:

```bash
python -m pytest backend/tests -q
```

Focused examples:

```bash
python -m pytest backend/tests/unit/algorithms/graph_search -q
python -m pytest backend/tests/unit/services/test_routing_service.py -q
```

Algorithm tests must be deterministic and must not call the Internet, a real
database, or a map API. Cover success, no-route, `start == goal`, directed
graphs, and invalid input. Benchmarks complement correctness assertions but do
not replace them.

---

## Tiếng Việt

Test được bố trí gần với cấu trúc source để dễ tìm và review:

```text
backend/tests/
├── fixtures/          # Graph và dữ liệu dùng chung
├── integration/       # Luồng kết hợp nhiều module
└── unit/
    ├── algorithms/
    │   ├── graph_search/
    │   └── optimization/
    ├── data/
    └── services/
```

## Chạy test

Từ thư mục gốc repository:

```bash
python -m pytest backend/tests -q
```

Chạy một nhóm nhỏ khi đang phát triển:

```bash
python -m pytest backend/tests/unit/algorithms/graph_search -q
python -m pytest backend/tests/unit/services/test_routing_service.py -q
```

## Quy ước

- Test thuật toán phải xác định và không gọi Internet, database hoặc API bản đồ.
- Dùng fixture chung khi nhiều test cần cùng một graph.
- Bao phủ đường hợp lệ, không có đường, `start == goal`, đồ thị có hướng và
  input không hợp lệ.
- Benchmark bổ sung số liệu hiệu năng nhưng không thay thế assertion đúng/sai.
