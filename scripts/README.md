# Dành cho các file .py

Thư mục này chứa các script python để chạy nghiệm thu graph từ cleaned dataset. 

## Hướng dẫn chạy Script

Để các module import hoạt động chính xác (đặc biệt là các script có gọi `from scripts import ...`), bạn **bắt buộc** phải chạy script từ thư mục gốc của toàn bộ dự án (`RescueRoute/`), **KHÔNG** chạy trực tiếp khi đang đứng bên trong thư mục `scripts/`.

### Ví dụ: Chạy test `dataset_2_graph.py`

Thay vì gõ `python dataset_2_graph.py` bên trong thư mục `scripts/`, hãy mở terminal, di chuyển ra thư mục ngoài cùng và chạy script dưới dạng module (`-m`):

```bash
# 1. Đảm bảo bạn đang đứng ở thư mục gốc RescueRoute
cd /path/to/RescueRoute

# 2. Chạy script dưới dạng module
python -m scripts.dataset_2_graph
```

Cách chạy này áp dụng cho mọi file python bên trong thư mục `scripts/`.

# Dành cho các file .ipynb

Thư mục này cũng chứa các notebook Jupyter để clean dữ liệu, trực quan hóa graph và thử nghiệm thuật toán. Các notebook này có thể được mở trực tiếp trong VSCode hoặc Jupyter Notebook.

## Cách chạy
Kết nối với kernel python/jupyter rồi chạy bình thường từ đầu đến cuối thôi.