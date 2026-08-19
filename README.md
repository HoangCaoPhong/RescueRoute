# RescueRoute

## English

### Project and team

RescueRoute is Team 4's Lab 01 project for the **Introduction to Artificial
Intelligence** course at the Faculty of Information Technology, University of
Science, Vietnam National University Ho Chi Minh City. Developed under the
guidance of instructors **Bùi Tiến Lên, Võ Nhật Tân, and Bùi Duy Đăng**, the
project investigates how classical and heuristic AI search methods can support
ambulance routing on the urban road network of Ho Chi Minh City.

The system addresses two related decisions: finding a feasible route between
two locations and optimizing the visit order of multiple locations. Its goal is
not only to return a path, but also to make the search process observable
through replayable traces and to explain the conditions under which a result is
optimal, approximate, or incomplete.

| Member | Student ID | Role | Primary responsibilities |
| --- | --- | --- | --- |
| Hoàng Cao Phong | 24127486 | Tech Lead / MLOps | A*, Hill Climbing, coordination, review, and integration |
| Võ Mỹ Ngọc | 24127294 | Frontend Developer | BFS, UCS, route visualization, and presentation slides |
| Nguyễn Trung Kiên | 24127068 | Backend Developer | DFS, FastAPI, routing services, and search-trace integration |
| Huỳnh Thái Hòa | 24127374 | Data Engineer | Dijkstra, Genetic Algorithm, cost model, benchmarking, and report editing |
| Lương Thiện Nhân | 24127475 | Data Engineer | Held-Karp, Simulated Annealing, data processing, and voice-over |

### Project overview

In urban emergency response, the shortest route by physical distance is not
always the fastest or most suitable. One-way streets, congestion, road class,
restricted segments, risk, and hospital accessibility can all affect the final
decision. RescueRoute models the road network as a directed graph and provides
both the selected route and a step-by-step view of how the algorithm reached
that result.

Current capabilities include:

- two-location search with BFS, DFS, UCS, Dijkstra, A*, and Hill Climbing;
- waypoint-order optimization with Nearest Neighbor, Held-Karp, Genetic
  Algorithm, and Simulated Annealing;
- visualization of expanded nodes, the frontier, and the final route;
- route metrics such as distance, cost, expanded-node count, and execution time;
- nearest-hospital lookup, ambulance-location updates, and congestion
  simulation;
- a FastAPI backend and an HTML/CSS/JavaScript Leaflet dashboard.

### Architecture

```text
Leaflet dashboard
      |
      | HTTP/JSON
      v
FastAPI routes -> routing services -> search/optimization algorithms
      |
      v
processed CSV -> in-memory directed graph
```

```text
RescueRoute/
├── backend/     # FastAPI, services, algorithms, and tests
├── data/        # Raw, processed, and sample datasets
├── docs/        # Architecture, API, and algorithm documentation
├── frontend/    # Leaflet dashboard prototype
└── scripts/     # Data processing and benchmark-plot utilities
```

### Quick start

Python 3.10 or later is required. Run from the repository root:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000/` for the dashboard or
`http://127.0.0.1:8000/docs` for the OpenAPI interface.

The backend loads its runtime graph from `data/processed/` at startup. If a
required derived file is missing, consult the [data guide](data/README.md) and
the [scripts guide](scripts/README.md).

### Main API endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Report application status and graph size |
| `GET /api/nodes` | Return hospitals or points of interest |
| `GET /api/edges` | Return road edges for map rendering |
| `POST /api/route` | Search for a route between two nodes |
| `POST /api/route/multi-location` | Optimize waypoint order and combine route segments |
| `POST /api/route/nearest-hospital` | Route to a suitable hospital |
| `GET/POST /api/ambulance/location` | Read or update the ambulance location |

These endpoints also have `/api/v1` variants.

### Verification

```bash
python -m pytest backend/tests -q
node --test frontend/tests/dashboard.logic.test.js
```

Algorithm tests are deterministic and do not call external services. See the
[backend test guide](backend/tests/README.md) for focused commands and test
conventions.

### Git workflow

- `main`: stable and demonstrable code.
- `dev`: sprint integration branch.
- `feature/<slug>` and `fix/<slug>`: short-lived branches created from `dev`.

Do not push directly to `main` or `dev`. See [CONTRIBUTING.md](CONTRIBUTING.md)
and [CODING_RULES.md](CODING_RULES.md) for the full workflow.

### Documentation map

- [Backend](backend/README.md)
- [Frontend](frontend/README.md)
- [Data](data/README.md)
- [Algorithms](backend/app/algorithms/README.md)
- [Documentation index](docs/README.md)

Binary assignment briefs and draft report artifacts are kept locally and are
not committed to Git history.

---

## Tiếng Việt

### Giới thiệu dự án và nhóm

RescueRoute là đồ án Lab 01 của **Nhóm 4** trong môn **Cơ sở Trí tuệ Nhân
tạo**, Khoa Công nghệ Thông tin, Trường Đại học Khoa học Tự nhiên, Đại học Quốc
gia Thành phố Hồ Chí Minh. Dưới sự hướng dẫn của các giảng viên **Bùi Tiến Lên,
Võ Nhật Tân và Bùi Duy Đăng**, nhóm nghiên cứu cách ứng dụng các thuật toán tìm
kiếm cổ điển và heuristic vào bài toán định tuyến xe cấp cứu trên mạng lưới giao
thông đô thị Thành phố Hồ Chí Minh.

Hệ thống giải quyết hai quyết định liên quan: tìm tuyến khả thi giữa hai địa
điểm và tối ưu thứ tự ghé nhiều địa điểm. Mục tiêu không chỉ là trả về một đường
đi, mà còn trực quan hóa quá trình tìm kiếm bằng trace có thể phát lại và giải
thích khi nào kết quả là tối ưu, xấp xỉ hoặc có thể không hoàn chỉnh.

| Thành viên | MSSV | Vai trò | Trách nhiệm chính |
| --- | --- | --- | --- |
| Hoàng Cao Phong | 24127486 | Tech Lead / MLOps | A*, Hill Climbing, điều phối, review và tích hợp |
| Võ Mỹ Ngọc | 24127294 | Frontend Developer | BFS, UCS, trực quan hóa tuyến đường và slide |
| Nguyễn Trung Kiên | 24127068 | Backend Developer | DFS, FastAPI, routing service và tích hợp search trace |
| Huỳnh Thái Hòa | 24127374 | Data Engineer | Dijkstra, Genetic Algorithm, cost model, benchmark và biên tập báo cáo |
| Lương Thiện Nhân | 24127475 | Data Engineer | Held-Karp, Simulated Annealing, xử lý dữ liệu và thu âm |

### Tổng quan dự án

Trong ứng cứu khẩn cấp đô thị, tuyến ngắn nhất theo khoảng cách chưa chắc là
tuyến nhanh nhất hoặc phù hợp nhất. Đường một chiều, ùn tắc, loại đường, đoạn bị
hạn chế, rủi ro và khả năng tiếp nhận của bệnh viện đều có thể ảnh hưởng đến
quyết định. RescueRoute mô hình hóa mạng đường bằng đồ thị có hướng, đồng thời
trả về tuyến được chọn và diễn tiến từng bước của thuật toán.

Các khả năng hiện có:

- tìm đường hai điểm bằng BFS, DFS, UCS, Dijkstra, A* và Hill Climbing;
- tối ưu thứ tự waypoint bằng Nearest Neighbor, Held-Karp, Genetic Algorithm và
  Simulated Annealing;
- hiển thị node đã mở rộng, frontier và tuyến cuối cùng;
- báo cáo khoảng cách, cost, số node mở rộng và thời gian thực thi;
- tìm bệnh viện gần nhất, cập nhật vị trí xe cấp cứu và mô phỏng ùn tắc;
- cung cấp FastAPI backend và dashboard Leaflet bằng HTML/CSS/JavaScript.

### Kiến trúc

```text
Leaflet dashboard
      |
      | HTTP/JSON
      v
FastAPI routes -> routing services -> search/optimization algorithms
      |
      v
processed CSV -> đồ thị có hướng trong bộ nhớ
```

```text
RescueRoute/
├── backend/     # FastAPI, services, thuật toán và test
├── data/        # Dữ liệu raw, processed và fixture mẫu
├── docs/        # Kiến trúc, API và tài liệu thuật toán
├── frontend/    # Dashboard Leaflet prototype
└── scripts/     # Xử lý dữ liệu và tạo biểu đồ benchmark
```

### Chạy nhanh

Yêu cầu Python 3.10 trở lên. Chạy từ thư mục gốc repository:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Mở `http://127.0.0.1:8000/` để dùng dashboard hoặc
`http://127.0.0.1:8000/docs` để xem OpenAPI.

Backend nạp graph runtime từ `data/processed/` khi khởi động. Nếu thiếu file
dẫn xuất, xem [hướng dẫn dữ liệu](data/README.md) và
[hướng dẫn scripts](scripts/README.md).

### API chính

| Endpoint | Mục đích |
| --- | --- |
| `GET /api/health` | Báo trạng thái ứng dụng và kích thước graph |
| `GET /api/nodes` | Lấy bệnh viện hoặc điểm quan tâm |
| `GET /api/edges` | Lấy cạnh đường để hiển thị bản đồ |
| `POST /api/route` | Tìm đường giữa hai node |
| `POST /api/route/multi-location` | Tối ưu waypoint và ghép các đoạn tuyến |
| `POST /api/route/nearest-hospital` | Tìm tuyến đến bệnh viện phù hợp |
| `GET/POST /api/ambulance/location` | Đọc hoặc cập nhật vị trí xe cấp cứu |

Các endpoint trên cũng có biến thể dưới `/api/v1`.

### Kiểm tra

```bash
python -m pytest backend/tests -q
node --test frontend/tests/dashboard.logic.test.js
```

Test thuật toán có tính xác định và không gọi dịch vụ bên ngoài. Xem
[hướng dẫn test backend](backend/tests/README.md) để chạy từng nhóm nhỏ.

### Quy trình Git

- `main`: mã nguồn ổn định, có thể demo.
- `dev`: nhánh tích hợp trong sprint.
- `feature/<slug>` và `fix/<slug>`: nhánh ngắn hạn tạo từ `dev`.

Không push trực tiếp lên `main` hoặc `dev`. Xem [CONTRIBUTING.md](CONTRIBUTING.md)
và [CODING_RULES.md](CODING_RULES.md) để biết quy trình đầy đủ.

### Chỉ mục tài liệu

- [Backend](backend/README.md)
- [Frontend](frontend/README.md)
- [Dữ liệu](data/README.md)
- [Thuật toán](backend/app/algorithms/README.md)
- [Chỉ mục tài liệu](docs/README.md)

Đề bài dạng nhị phân và các bản báo cáo đang soạn chỉ được giữ local, không đưa
vào lịch sử Git.
