# Simulated Vietnamese traffic

## English

This deterministic fixture is a small slice of Ho Chi Minh City traffic data,
used for tests and demonstrations without loading the full dataset. All rows
share the date `2020-08-02` and time period `period_23_30`.

- `nodes.csv`: 40 normalized nodes.
- `edges.csv`: 60 directed edges across 14 street names.
- `source_slice.csv`: 60 upstream rows retained for traceability.

Nodes use `node_id`, `name`, `latitude`, `longitude`, and `node_type`. Edges
include endpoints, distance, estimated time, LOS, congestion, speed, road
attributes, and source metadata.

```text
estimated_time_s = distance_m / (actual_speed_kph / 3.6)
```

Run validation with:

```bash
python -m pytest backend/tests/unit/data/test_simulated_traffic_data.py -q
```

The repository does not yet record a separate redistribution license for this
slice; confirm permission before using it outside the assignment.

---

## Tiếng Việt

Fixture này là một lát cắt nhỏ từ dữ liệu giao thông TP.HCM, dùng để test và
demo mà không phải nạp toàn bộ dataset. Snapshot gồm cùng ngày `2020-08-02` và
khung giờ `period_23_30`.

## Quy mô và file

- `nodes.csv`: 40 node đã chuẩn hóa.
- `edges.csv`: 60 cạnh có hướng thuộc 14 tên đường.
- `source_slice.csv`: 60 dòng nguồn để truy vết.

## Schema chính

Node dùng `node_id`, `name`, `latitude`, `longitude`, `node_type`.

Edge dùng `edge_id`, hai node đầu cuối, `distance_m`, `estimated_time_s`, LOS,
congestion, tốc độ và thuộc tính đường. Công thức thời gian:

```text
estimated_time_s = distance_m / (actual_speed_kph / 3.6)
```

LOS A/B/C/D/E/F lần lượt được ánh xạ thành mức ùn tắc dùng trong fixture. Nếu
thiếu tốc độ tự do, dữ liệu dùng giả định 70 km/h và giữ lại trường nguồn để
đối chiếu.

## Kiểm tra

```bash
python -m pytest backend/tests/unit/data/test_simulated_traffic_data.py -q
```

Repository chưa ghi giấy phép riêng cho lát cắt này; cần xác nhận quyền phân
phối trước khi dùng ngoài phạm vi đồ án.
