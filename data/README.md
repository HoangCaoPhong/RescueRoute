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

