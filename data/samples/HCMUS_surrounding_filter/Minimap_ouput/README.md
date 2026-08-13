# HCMUS surrounding minimap dataset

Bộ dữ liệu này mô tả mạng đường thật quanh Trường Đại học Khoa học Tự nhiên,
ĐHQG-HCM (cơ sở Nguyễn Văn Cừ) và các bệnh viện lân cận. Dữ liệu được merge từ
nhánh `feature/mini-Q5-sample`, commits `8dfb9aa` và `3357eeb`.

Tên folder `Minimap_ouput` giữ nguyên chính tả từ nhánh nguồn để không làm gãy
đường dẫn đã được chia sẻ trong nhóm.

## Quy mô và phạm vi

- `3.364` node duy nhất.
- `4.918` segment/cạnh có hướng duy nhất.
- Tọa độ nằm trong khoảng `10.7437–10.7825` vĩ độ và
  `106.6627–106.7028` kinh độ, thuộc khu vực trung tâm TP.HCM.
- `graph_clean.png` là ảnh kiểm tra trực quan phạm vi graph.

Dataset vượt yêu cầu tối thiểu của đề là 20 node và 30 edge. Tọa độ là địa
điểm bản đồ, không phải GPS người dùng. Nhánh nguồn chưa kèm thông tin giấy
phép; nhóm cần xác nhận quyền phân phối trước khi đưa dữ liệu ra ngoài phạm vi
đồ án.

## Các file nguồn

| File | Nội dung |
|---|---|
| `nodes.csv` | Node gốc: `_id`, `long`, `lat` |
| `segments.csv` | Cạnh đường: hai đầu, chiều dài, tên và loại đường |
| `train.csv` | Quan sát giao thông theo ngày/khung giờ, gồm LOS A–F |
| `segment_status.csv` | Quan sát vận tốc segment theo thời điểm |
| `graph_clean.png` | Ảnh trực quan graph và các điểm quan trọng |

Các thuộc tính mà đề yêu cầu ban đầu nằm rải ở nhiều bảng. Chỉ `1.667/4.918`
segment có bản ghi LOS và velocity tương ứng; vì vậy không nên đưa trực tiếp
`segments.csv` cho thuật toán rồi tuyên bố mọi cạnh đã đủ traffic data.

## Graph chuẩn hóa dùng cho thuật toán

`edges.csv` được tạo bởi
[`scripts/build_hcmus_minimap_edges.py`](../../../../scripts/build_hcmus_minimap_edges.py)
và có đúng một dòng cho mỗi segment:

| Field | Đơn vị/ý nghĩa |
|---|---|
| `edge_id` | ID segment nguồn |
| `source_node_id`, `target_node_id` | Hướng đi của cạnh |
| `distance_m` | Mét; dùng `length`, hoặc Haversine cho 22 dòng có length bằng 0 |
| `estimated_time_s` | Giây, tính từ distance và actual speed |
| `congestion_level`, `los`, `congestion_factor` | Trạng thái giao thông chuẩn hóa từ LOS A–F |
| `free_flow_speed_kph` | `max_velocity`, hoặc mặc định theo `road_type` |
| `actual_speed_kph` | Vận tốc quan sát mới nhất; thiếu thì dùng vận tốc mô hình |
| `road_type`, `street_name`, `street_level` | Thuộc tính đường nguồn |
| `traffic_date`, `time_period` | Snapshot LOS nếu segment có quan sát |
| `traffic_source` | Cho biết field traffic đến từ quan sát hay fallback |

```text
estimated_time_s = distance_m / (actual_speed_kph / 3.6)
```

Fallback được ghi minh bạch trong `traffic_source`:

- Có LOS và velocity: `train_los+latest_segment_status`.
- Chỉ có một nguồn quan sát: kết hợp nguồn đó với speed/LOS mô hình.
- Không có quan sát: `road_type_defaults`, mặc định LOS A/free-flow.

Tái tạo file chuẩn hóa từ thư mục gốc project:

```bash
python scripts/build_hcmus_minimap_edges.py
```

`../filter_version3.py` là pipeline tạo lại bộ minimap từ `data/raw/`.
Script đọc bốn bảng raw hiện có, ghi vào chính folder này và không còn
phụ thuộc `streets.csv` bị thiếu trên nhánh nguồn:

```bash
python data/samples/HCMUS_surrounding_filter/filter_version3.py
python scripts/build_hcmus_minimap_edges.py
```

Test nghiệm thu nằm tại
`backend/tests/unit/data/test_hcmus_minimap_data.py` và kiểm tra số lượng,
tọa độ, tham chiếu node, bốn field bắt buộc và công thức estimated time.
