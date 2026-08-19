# Processed data

## English

This directory contains derived tables used by the runtime and experiments.
They originate from `data/raw/` and should not be edited row by row.

| File | Role |
| --- | --- |
| `base_segments.csv` | Base edges with `length`, `base_time`, and `base_cost` |
| `processed_train.csv` | Speed, time, LOS, congestion, and risk by period |
| `nodes_with_poi_labels.csv` | Nodes with POI labels and matching distance |
| `train_with_cost.csv` | Legacy snapshot with a `cost` column for comparison |
| `cost_parameters.json` | Current cost weights and settings |

`backend/main.py` loads the required tables through
`scripts/dataset_2_graph.py`. Any schema change must update the loader, data
tests, and related API documentation in the same change.

---

## Tiếng Việt

Thư mục này chứa các bảng dẫn xuất dùng cho runtime và thử nghiệm. Dữ liệu được
tạo từ `data/raw/` và không nên được sửa thủ công từng dòng.

| File | Vai trò |
| --- | --- |
| `base_segments.csv` | Cạnh cơ sở với `length`, `base_time`, `base_cost` |
| `processed_train.csv` | Vận tốc, thời gian, LOS, congestion và risk theo kỳ |
| `nodes_with_poi_labels.csv` | Node kèm nhãn POI và khoảng cách ghép nhãn |
| `train_with_cost.csv` | Snapshot cũ có cột `cost`, chỉ dùng để đối chiếu |
| `cost_parameters.json` | Trọng số và cấu hình cost hiện tại |

`backend/main.py` nạp các bảng cần thiết thông qua
`scripts/dataset_2_graph.py`. Nếu thay đổi schema, cần cập nhật loader, test dữ
liệu và tài liệu API liên quan trong cùng thay đổi.
