# Simulated Vietnamese traffic graph

Bộ dữ liệu nhỏ này được cắt từ
[`feature/EDA_data/data/raw/train.csv`](https://github.com/HoangCaoPhong/RescueRoute/blob/feature/EDA_data/data/raw/train.csv)
để test và demo thuật toán tìm đường mà không phải nạp toàn bộ file nguồn.
Snapshot nguồn đã kiểm tra tại commit
`951258f5d475bcc8bd371d3844ba2bdefbcbb198`.

Repository nguồn chưa ghi giấy phép riêng cho `train.csv`. Cần xác nhận quyền
sử dụng/phân phối với chủ dataset trước khi phát hành bộ dữ liệu ra ngoài phạm
vi đồ án.

## Điều kiện cắt

- Ngày: `2020-08-02`.
- Khung giờ: `period_23_30` (23:30).
- Tất cả cạnh cùng ngày và cùng khung giờ; các cạnh thuộc nhiều đoạn/tên đường
  khác nhau.
- Chọn xác định một tiểu đồ thị liên thông vô hướng có đúng 40 node và ít nhất
  60 cạnh nội bộ, đồng thời ưu tiên số tên đường khác nhau lớn nhất.
- Giữ một cây khung để không làm mất node hoặc tính liên thông, sau đó bổ sung
  cạnh từ các đường chưa xuất hiện cho đến đúng 60 cạnh.
- Kết quả: 40 node, 60 cạnh có hướng và 14 tên đường thực tại TP.HCM.
- Tỷ lệ `node : edge = 40 : 60 = 2 : 3`.

`source_slice.csv` giữ nguyên 60 dòng và schema nguồn. `nodes.csv` và
`edges.csv` là graph đã chuẩn hóa dùng cho ứng dụng.

## Schema node

| Field | Ý nghĩa |
|---|---|
| `node_id` | ID node ổn định từ dữ liệu nguồn |
| `name` | Tên thực tế/giả lập từ các đường kề node |
| `latitude`, `longitude` | Tọa độ WGS84 từ nguồn |
| `node_type` | `intersection` hoặc `road_point` |

Tên dạng `Nút giao A - B` được dùng khi hai tên đường gặp nhau; node chỉ thuộc
một đường được đặt tên `Điểm trên đường A`. Đây không phải GPS người dùng.

## Schema edge

| Field | Đơn vị/ý nghĩa |
|---|---|
| `edge_id` | `segment_id` từ nguồn |
| `source_node_id`, `target_node_id` | Hướng đi của cạnh |
| `distance_m` | Mét, lấy từ cột `length` |
| `estimated_time_s` | Giây, tính từ khoảng cách và vận tốc thực tế |
| `congestion_level` | `free_flow`, `light`, `moderate`, `heavy`, `severe`, `gridlock` |
| `los` | Level of Service gốc A-F |
| `congestion_factor` | A/B=1, C=2, D=3, E=5, F=8 |
| `free_flow_speed_kph` | `max_velocity`; thiếu thì dùng giả định 70 km/h |
| `actual_speed_kph` | `free_flow_speed_kph / congestion_factor` |
| `road_type`, `street_name`, `street_level` | Thuộc tính đường từ nguồn |
| `date`, `time_period` | Mốc thời gian chung của snapshot |
| `source_row_id` | Cột `_id` để truy vết dòng nguồn |

```text
estimated_time_s = distance_m / (actual_speed_kph / 3.6)
```

Mapping LOS bám theo `scripts/dataset_2_graph.py` trên nhánh EDA.

## Tái tạo dữ liệu

Khi đã fetch nhánh nguồn:

```bash
python scripts/build_simulated_traffic_sample.py --source-ref origin/feature/EDA_data
```

Hoặc dùng file local:

```bash
python scripts/build_simulated_traffic_sample.py --input data/raw/train.csv
```

Script chỉ đọc dữ liệu nguồn và ghi vào folder sample này; không sửa file raw.
