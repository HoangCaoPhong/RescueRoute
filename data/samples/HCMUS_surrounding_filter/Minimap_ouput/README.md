# HCMUS surrounding minimap

## English

This dataset represents roads around the University of Science, VNU-HCM
(Nguyen Van Cu campus), and nearby hospitals. The misspelled directory name
`Minimap_ouput` is preserved to avoid breaking existing project paths.

### Scale and normalized contract

- 3,364 nodes in `nodes.csv`.
- 4,918 directed edges in `edges.csv`.
- Coordinates span approximately 10.7437-10.7825 latitude and
  106.6627-106.7028 longitude.
- `graph_clean.png` provides a visual scope check.

`nodes.csv`, `segments.csv`, `train.csv`, and `segment_status.csv` are source
tables. The normalized `edges.csv` records directed endpoints, distance,
estimated time, congestion, speed, road attributes, and traffic provenance.

```text
estimated_time_s = distance_m / (actual_speed_kph / 3.6)
```

`traffic_source` distinguishes observations from road-type fallback values.
Rebuild and validate from the repository root:

```bash
python data/samples/HCMUS_surrounding_filter/filter_version3.py
python scripts/build_hcmus_minimap_edges.py
python -m pytest backend/tests/unit/data/test_hcmus_minimap_data.py -q
```

These are map coordinates, not user GPS records. Confirm the source license
before redistributing the dataset outside the project.

---

## Tiếng Việt

Bộ dữ liệu mô tả mạng đường quanh Trường Đại học Khoa học Tự nhiên,
ĐHQG-HCM (cơ sở Nguyễn Văn Cừ) và các bệnh viện lân cận. Tên thư mục
`Minimap_ouput` được giữ nguyên để không làm gãy các đường dẫn đã dùng trong
dự án.

## Quy mô

- 3.364 node trong `nodes.csv`.
- 4.918 cạnh có hướng trong `edges.csv`.
- Tọa độ nằm khoảng 10.7437–10.7825 vĩ độ và 106.6627–106.7028 kinh độ.
- `graph_clean.png` dùng để kiểm tra trực quan phạm vi graph.

Đây là tọa độ bản đồ, không phải GPS người dùng. Cần xác nhận giấy phép trước
khi phân phối dataset ra ngoài phạm vi đồ án.

## File nguồn và file chuẩn hóa

`nodes.csv`, `segments.csv`, `train.csv` và `segment_status.csv` là các bảng
nguồn của minimap. `edges.csv` là contract chuẩn hóa cho thuật toán:

| Trường | Ý nghĩa |
| --- | --- |
| `edge_id` | ID segment nguồn |
| `source_node_id`, `target_node_id` | Hướng của cạnh |
| `distance_m` | Khoảng cách theo mét |
| `estimated_time_s` | Thời gian ước tính theo giây |
| `congestion_level`, `los`, `congestion_factor` | Mức giao thông đã chuẩn hóa |
| `free_flow_speed_kph`, `actual_speed_kph` | Tốc độ km/h |
| `road_type`, `street_name`, `street_level` | Thuộc tính đường |
| `traffic_date`, `time_period`, `traffic_source` | Nguồn và thời điểm traffic |

```text
estimated_time_s = distance_m / (actual_speed_kph / 3.6)
```

`traffic_source` cho biết dữ liệu đến từ quan sát hay fallback. Các cạnh thiếu
quan sát dùng mặc định theo loại đường thay vì giả vờ có dữ liệu thực.

## Tái tạo

Từ thư mục gốc repository:

```bash
python data/samples/HCMUS_surrounding_filter/filter_version3.py
python scripts/build_hcmus_minimap_edges.py
python -m pytest backend/tests/unit/data/test_hcmus_minimap_data.py -q
```
