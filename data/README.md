# Dữ liệu

## English

```text
data/
├── raw/          # Upstream data; never edited manually
├── processed/    # Cleaned data used by the runtime
└── samples/      # Stable fixtures for tests and demonstrations
```

### Available datasets

- [Simulated Vietnamese traffic](samples/simulated_vietnamese_traffic/README.md):
  a deterministic fixture with 40 nodes and 60 directed edges.
- [HCMUS surrounding minimap](samples/HCMUS_surrounding_filter/Minimap_ouput/README.md):
  a graph with 3,364 nodes and 4,918 directed edges around HCMUS and nearby
  hospitals.
- [Processed data](processed/README.md): the dataset currently loaded into
  memory by the dashboard backend.

Every dataset must document its source, schema, units, and fallback assumptions.
Node and edge IDs must remain stable, coordinates use WGS84, and real user GPS
or personally identifiable data must never be committed. Algorithm comparisons
must use the same dataset version and cost profile.

---

## Tiếng Việt

```text
data/
├── raw/          # Dữ liệu nguồn, không sửa thủ công
├── processed/    # Dữ liệu đã làm sạch dùng bởi runtime
└── samples/      # Fixture ổn định cho test và demo
```

## Bộ dữ liệu hiện có

- [Simulated Vietnamese traffic](samples/simulated_vietnamese_traffic/README.md):
  fixture 40 node, 60 cạnh để test xác định.
- [HCMUS surrounding minimap](samples/HCMUS_surrounding_filter/Minimap_ouput/README.md):
  graph 3.364 node, 4.918 cạnh quanh HCMUS và các bệnh viện lân cận.
- [Processed data](processed/README.md): dữ liệu mà dashboard hiện nạp vào RAM.

## Quy ước

- Mỗi dataset phải ghi nguồn, schema, đơn vị và giả định fallback.
- ID node/cạnh phải ổn định; tọa độ dùng WGS84.
- Không commit GPS người dùng thật hoặc dữ liệu định danh cá nhân.
- So sánh thuật toán phải dùng cùng phiên bản dữ liệu và cùng cost profile.
- `raw/` chỉ dùng làm nguồn; các biến đổi phải đi qua script có thể chạy lại.

Các fixture nên bao phủ đường một chiều, nhiều tuyến hợp lệ, node không thể tới,
cạnh ùn tắc/rủi ro cao và bài toán nhiều waypoint.
