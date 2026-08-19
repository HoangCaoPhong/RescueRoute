# Dữ liệu raw

## English

Files in this directory come from Thanh Nguyen's Kaggle dataset
[Traffic Flow Data in Ho Chi Minh City, Viet Nam](https://www.kaggle.com/datasets/thanhnguyen2612/traffic-flow-data-in-ho-chi-minh-city-viet-nam).
They are upstream source files and must not be edited manually after import.

| File | Main content |
| --- | --- |
| `nodes.csv` | Node IDs, longitude, and latitude |
| `segments.csv` | Segment endpoints, length, speed, and road attributes |
| `segment_status.csv` | Segment speed observations over time |
| `train.csv` | LOS and traffic observations by date and time period |

Inspect each CSV header for the complete schema. Cleaning and feature
engineering must be performed by reproducible scripts that write to
`data/processed/` or `data/samples/`.

---

## Tiếng Việt

Các file trong thư mục này lấy từ bộ Kaggle
[Traffic Flow Data in Ho Chi Minh City, Viet Nam](https://www.kaggle.com/datasets/thanhnguyen2612/traffic-flow-data-in-ho-chi-minh-city-viet-nam)
của Thanh Nguyen. Đây là dữ liệu nguồn; không chỉnh sửa thủ công sau khi nhập.

## Các file

| File | Nội dung chính |
| --- | --- |
| `nodes.csv` | ID node, kinh độ và vĩ độ |
| `segments.csv` | Hai đầu segment, chiều dài, tốc độ và thông tin đường |
| `segment_status.csv` | Vận tốc segment theo thời điểm |
| `train.csv` | Quan sát LOS và lưu lượng theo ngày/khung giờ |

Xem header CSV để biết schema đầy đủ. Mọi bước làm sạch hoặc bổ sung thuộc tính
phải được thực hiện bằng script và ghi kết quả sang `data/processed/` hoặc
`data/samples/`.
