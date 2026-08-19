# Scripts

## English

This directory contains data-processing scripts, graph builders, benchmark
plot utilities, and notebooks for exploratory work.

Run commands from the repository root so internal imports resolve consistently:

```bash
python -m scripts.dataset_2_graph
python scripts/build_hcmus_minimap_edges.py
python scripts/generate_benchmark_plots.py
```

| File | Purpose |
| --- | --- |
| `dataset_2_graph.py` | Load processed data and build the adjacency graph |
| `enrich_data.py` | Derive traffic-related fields |
| `build_hcmus_minimap_edges.py` | Normalize the HCMUS minimap into `edges.csv` |
| `generate_benchmark_plots.py` | Generate plots from benchmark artifacts |
| `EDA.ipynb` | Explore and clean data |
| `benchmark_algorithms.ipynb` | Compare algorithm behavior |
| `visualize.ipynb` | Inspect graphs and datasets visually |

Data builders must be reproducible and must not modify `data/raw/` in place.
Additional notebook/script dependencies are listed in
`scripts/requirements.txt`.

---

## Tiếng Việt

Thư mục này chứa script xử lý dữ liệu, dựng graph và tạo biểu đồ benchmark.
Notebook dùng cho EDA và thử nghiệm thủ công.

## Chạy đúng thư mục

Chạy lệnh từ thư mục gốc repository để import nội bộ hoạt động ổn định:

```bash
python -m scripts.dataset_2_graph
python scripts/build_hcmus_minimap_edges.py
python scripts/generate_benchmark_plots.py
```

## Nội dung chính

| File | Mục đích |
| --- | --- |
| `dataset_2_graph.py` | Đọc dữ liệu processed và dựng adjacency graph |
| `enrich_data.py` | Tạo các trường dẫn xuất cho dữ liệu giao thông |
| `build_hcmus_minimap_edges.py` | Chuẩn hóa minimap HCMUS thành `edges.csv` |
| `generate_benchmark_plots.py` | Tạo hình từ artifact benchmark |
| `EDA.ipynb` | Khám phá và làm sạch dữ liệu |
| `benchmark_algorithms.ipynb` | Thử nghiệm so sánh thuật toán |
| `visualize.ipynb` | Kiểm tra trực quan graph/dữ liệu |

Script sinh dữ liệu phải cho kết quả tái lập được và không sửa trực tiếp file
trong `data/raw/`. Dependency riêng cho notebook/script nằm trong
`scripts/requirements.txt`.
