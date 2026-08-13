# Dataset workspace

```text
data/
├── raw/          # Dữ liệu nguồn, giữ nguyên sau khi nhập
├── processed/    # Dữ liệu đã clean/normalize dùng cho ứng dụng
└── samples/      # Bộ nhỏ, ổn định cho test và demo
```

Mọi dataset cần mô tả nguồn, schema, đơn vị và giả định. Không commit GPS thật của người dùng hoặc dữ liệu định danh cá nhân.

Dataset mẫu nên bao phủ tối thiểu:

- Đường một chiều và hai chiều.
- Nhiều tuyến hợp lệ giữa cùng hai node.
- Một node không thể đến được.
- Cạnh ùn tắc/rủi ro cao.
- Trường hợp tuyến ngắn nhất theo distance không tốt nhất theo total cost.
- Nhiều điểm cần tối ưu thứ tự ghé.

Tất cả thuật toán phải benchmark trên cùng phiên bản dataset và cost profile.

## Dataset mẫu hiện có

- [`samples/simulated_vietnamese_traffic/`](samples/simulated_vietnamese_traffic/README.md):
  graph giao thông TP.HCM gồm 40 node và 60 cạnh, cắt cùng ngày `2020-08-02`,
  cùng khung giờ `23:30`, dùng cho unit test nhỏ và đối chiếu đúng
  ngưỡng 20 node/30 edge của đề.
- [`samples/HCMUS_surrounding_filter/Minimap_ouput/`](samples/HCMUS_surrounding_filter/Minimap_ouput/README.md):
  graph khu vực HCMUS và các bệnh viện lân cận, gồm 3.364 node và
  4.918 cạnh có hướng. `edges.csv` là contract chuẩn hóa có distance,
  estimated time, congestion và road type cho demo/benchmark tích hợp.

Runtime dashboard hiện vẫn đọc graph từ `data/processed/` qua
`scripts/dataset_2_graph.py`. Hai folder sample là fixture ổn định; việc chuyển
runtime sang HCMUS minimap nên được thực hiện qua một data adapter riêng,
không hard-code schema CSV trong từng thuật toán.
