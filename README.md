# RescueRoute

RescueRoute là ứng dụng web mô phỏng tìm đường tối ưu cho xe cấp cứu trong bối cảnh giao thông đô thị Việt Nam. Hệ thống biểu diễn mạng lưới đường dưới dạng đồ thị, so sánh các thuật toán tìm kiếm AI và giải thích vì sao một tuyến đường được chọn dựa trên thời gian, ùn tắc và rủi ro.

> Trạng thái hiện tại: đã có FastAPI backend, dashboard Leaflet prototype,
> sáu thuật toán tìm đường có unified trace và API tối ưu nhiều
> waypoint. Khung React/TypeScript vẫn là hướng phát triển tiếp theo.

## Mục tiêu chính

- Tìm tuyến giữa hai địa điểm bằng BFS, DFS, UCS và A*.
- Cài đặt và so sánh thêm Dijkstra, Hill Climbing, Simulated Annealing và Genetic Algorithm theo phân công hiện tại.
- Tối ưu thứ tự ghé nhiều địa điểm bằng ít nhất một thuật toán/heuristic phù hợp.
- Trực quan hóa từng bước: node đã duyệt, frontier/open list và tuyến cuối cùng.
- Báo cáo quãng đường, thời gian dự kiến, tổng chi phí, số node đã mở rộng và thời gian xử lý.
- Giải thích tuyến đường, ảnh hưởng của ùn tắc/rủi ro và tính tối ưu hoặc xấp xỉ của thuật toán.

## Kiến trúc hiện tại

```text
HTML/JavaScript + Leaflet/OpenStreetMap
          |
          | HTTP/JSON
          v
FastAPI API -> application services -> search/optimization algorithms
          |
          v
processed CSV -> graph dataset in RAM
```

- `frontend/`: dashboard Leaflet prototype, chọn thuật toán và mô phỏng
  search trace; `frontend/src/` giữ khung React/TypeScript cho giai đoạn sau.
- `backend/`: FastAPI, mô hình đồ thị, thuật toán, nghiệp vụ định tuyến và tích hợp ngoài.
- `data/`: dữ liệu gốc, dữ liệu đã chuẩn hóa và bộ dữ liệu mẫu dùng cho demo/test.
- `infra/`: cấu hình Render, Supabase và các tài nguyên triển khai.
- `docs/`: đề bài, kế hoạch nhóm, tài liệu kiến trúc, API và báo cáo.
- `scripts/`: script kiểm tra, chuyển đổi dữ liệu và tác vụ phát triển dùng chung.

Xem chỉ mục đầy đủ tại [`docs/README.md`](docs/README.md).

## Mô hình dữ liệu cốt lõi

Node tối thiểu gồm `node_id`, `name`, `latitude`, `longitude`, `type`. Edge có hướng tối thiểu gồm `edge_id`, `source`, `target`, `distance`, `speed_limit`, `congestion_level`, `road_type` và `risk_factor`.

Chi phí khởi điểm theo kế hoạch nhóm:

```text
estimated_time = distance / actual_speed
actual_speed   = speed_limit / congestion_factor
edge_cost      = alpha * estimated_time
               + beta  * congestion_penalty
               + gamma * risk_penalty
```

Các trọng số mặc định dự kiến là `alpha = 0.6`, `beta = 0.3`, `gamma = 0.1`. Giá trị cuối cùng phải được kiểm chứng bằng benchmark và ghi rõ giả định trong báo cáo.

## Dataset demo và test

- `data/samples/simulated_vietnamese_traffic/`: fixture nhỏ 40 node/60 edge,
  dùng cho unit test deterministic.
- `data/samples/HCMUS_surrounding_filter/Minimap_ouput/`: minimap thực tế quanh
  HCMUS, gồm 3.364 node/4.918 edge. File `edges.csv` đã gom distance,
  estimated time, congestion level và road type theo contract của đề.
- `data/processed/`: graph hiện được FastAPI dashboard nạp vào RAM.

Xem data dictionary, nguồn và chính sách fallback tại
[`data/README.md`](data/README.md).

## Cấu trúc repository

```text
RescueRoute/
├── .github/                 # Pull request template
├── backend/
│   ├── app/
│   │   ├── api/routes/      # HTTP/WebSocket endpoints
│   │   ├── algorithms/      # Mỗi thuật toán có một folder riêng
│   │   │   ├── graph_search/
│   │   │   │   ├── astar/
│   │   │   │   ├── bfs/
│   │   │   │   ├── dfs/
│   │   │   │   ├── dijkstra/
│   │   │   │   └── ucs/
│   │   │   └── optimization/
│   │   │       ├── genetic_algorithm/
│   │   │       ├── held_karp/
│   │   │       ├── hill_climbing/
│   │   │       ├── nearest_neighbor/
│   │   │       └── simulated_annealing/
│   │   ├── core/            # Config, logging, constants
│   │   ├── domain/          # Node, Edge, Graph, Route và luật nghiệp vụ
│   │   ├── integrations/    # Map, Supabase và dịch vụ ngoài
│   │   ├── repositories/    # Truy cập dữ liệu
│   │   ├── schemas/         # Request/response schemas
│   │   ├── services/        # Điều phối use case
│   │   └── utils/
│   └── tests/
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/
├── docs/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── lib/api/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   ├── styles/
│   │   └── types/
│   └── tests/
├── infra/
└── scripts/
```

## Quy trình Git cho nhóm

Repo dùng mô hình gọn:

1. `main`: bản ổn định/demo được; không push trực tiếp.
2. `dev`: nhánh tích hợp cho sprint; mọi feature merge vào đây qua pull request.
3. `feature/<ten-ngan>`: tính năng mới, tạo từ `dev`.
4. `fix/<ten-ngan>`: sửa lỗi, tạo từ `dev`.
5. `docs/<ten-ngan>` và `experiment/<ten-ngan>`: tài liệu hoặc thử nghiệm có giới hạn.

Ví dụ:

```bash
git switch dev
git pull --ff-only origin dev
git switch -c feature/astar-search

# Sau khi code và test
git add backend/app/algorithms backend/tests
git commit -m "feat(algorithm): implement A* route search"
git push -u origin feature/astar-search
```

Mở pull request vào `dev`, cần ít nhất một người khác review. Chỉ merge `dev` vào `main` khi sprint đã chạy test và demo ổn định. Chi tiết nằm trong [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Bắt đầu một task thuật toán

Đọc [`backend/app/algorithms/README.md`](backend/app/algorithms/README.md), sau đó mở README trong folder thuật toán được phân công. Mỗi folder đã ghi owner, branch đề xuất, vị trí test, tài liệu và checklist riêng.

Thứ tự chung:

1. Chờ contract `Node`, `Edge`, `Graph`, cost và `SearchResult` dùng chung được merge vào `dev`.
2. Tạo branch thuật toán từ `dev`, ví dụ `feature/astar-search`.
3. Thêm `algorithm.py` và `__init__.py` trong đúng folder của thuật toán.
4. Viết test trong folder đối xứng dưới `backend/tests/unit/algorithms/`.
5. Viết design, pseudocode, flowchart và benchmark trong `docs/algorithms/`.
6. Mở pull request vào `dev`.

Không đặt FastAPI route, database query hoặc API call trong folder thuật toán.

## Bắt đầu phát triển

- Cài dependency: `python -m pip install -r backend/requirements.txt`.
- Chạy API/dashboard từ root: `python -m uvicorn backend.main:app --reload`.
- Chạy backend tests: `python -m pytest backend/tests -q`.
- Tái tạo HCMUS normalized edges:
  `python scripts/build_hcmus_minimap_edges.py`.

Khung React + TypeScript trong `frontend/src/` chưa thay thế dashboard HTML/JS
prototype. Không commit `.env`, virtual environment hoặc GPS người dùng.

Đọc [`backend/README.md`](backend/README.md) và [`CODING_RULES.md`](CODING_RULES.md) trước khi viết code.

## Tài liệu nguồn

PDF/DOCX của đề bài và kế hoạch ban đầu chỉ được giữ local trong `docs/` và bị
Git bỏ qua. Khi yêu cầu thay đổi, cập nhật chỉ mục Markdown và ghi quyết định
kỹ thuật mới trong `docs/architecture/` thay vì commit lại tài liệu nhị phân.

## Nhóm thực hiện

Team 5 - môn Introduction to Artificial Intelligence. Phân công hiện tại được ghi trong tài liệu họp; mọi thay đổi owner nên được cập nhật qua issue/project board và pull request.
