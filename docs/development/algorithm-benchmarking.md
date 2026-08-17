# Benchmark thuật toán

Notebook chuẩn để đo và so sánh là
[`scripts/benchmark_algorithms.ipynb`](../../scripts/benchmark_algorithms.ipynb).
Nó chạy hai nhóm bài toán riêng: tìm đường hai điểm (BFS, DFS, UCS, Dijkstra,
A* và Hill Climbing) và tối ưu thứ tự nhiều điểm dừng (Nearest Neighbor,
Held-Karp, Simulated Annealing và Genetic Algorithm). Không so sánh trực tiếp
thời gian giữa hai nhóm vì không gian bài toán và contract đầu ra khác nhau.

Script sinh biểu đồ tự động:
[`scripts/generate_benchmark_plots.py`](../../scripts/generate_benchmark_plots.py).

---

## Mục tiêu và tiêu chí đo lường

Mỗi thuật toán được chạy trên **cùng graph, cùng cặp start/goal, cùng cost
`estimated_time_s`, cùng thứ tự láng giềng và cùng số lần lặp**. Với bài toán
nhiều điểm dừng, tất cả dùng cùng pairwise cost matrix và cùng start/goal.
Các thuật toán ngẫu nhiên nhận `seed` cố định (`20260817`).

| Tiêu chí | Cách đo | Lý do chọn |
| --- | --- | --- |
| **Thời gian (Latency)** | Median và p95 của wall-clock time (ms), sau warm-up (21 lần lặp) | Median ít bị lệch bởi tiến trình nền; p95 cho biết trường hợp chậm bất thường. Đo bên ngoài hàm thuật toán để gồm toàn bộ chi phí thực thi contract/trace. GC được tạm ngắt trong lượt đo timing. |
| **Bộ nhớ (Memory)** | Median và max của **peak Python heap** (MiB), đo độc lập bằng `tracemalloc` (7 lần lặp) | So sánh công bằng phần bộ nhớ Python được thuật toán cấp phát, gồm cả trace/frontier mà ứng dụng thực sự trả về. Graph đã được nạp trước khi đo nên không lẫn chi phí I/O/dataset. Đây không phải RSS của cả tiến trình OS. |
| **Độ tối ưu (Optimality)** | Điều kiện lý thuyết và `cost_gap_to_oracle_pct` | `is_optimal` của mỗi hàm chỉ có ý nghĩa theo mục tiêu riêng. Oracle Dijkstra (graph search) và Oracle Held-Karp (multi-stop) kiểm tra thực nghiệm khoảng cách chi phí so với nghiệm tối ưu toàn cục. |
| **Tính hoàn chỉnh (Completeness)** | Điều kiện lý thuyết và `completed_all_runs` | Phân biệt thuộc tính "bảo đảm luôn tìm được nghiệm nếu có" với việc một lần chạy cụ thể thành công. Thuật toán heuristic có thể chạy xong nhưng không complete. |
| **Tính tái lập (Reproducibility)** | Dataset hash, Git commit, Python/package/OS/CPU/GPU, seed và cấu hình được lưu JSON | Cho phép đối chiếu chính xác giữa hai lần chạy và phát hiện thay đổi code/dữ liệu/môi trường. |

> [!NOTE]
> `tracemalloc` được bật ở lượt đo bộ nhớ nhưng **không** bật ở lượt đo thời
> gian, vì tracer làm chậm Python và sẽ làm latency không còn đại diện. Số liệu
> memory do đó phải được ghi là "peak Python heap", không ghi là tổng RAM của máy.

---

## Cấu hình máy thử nghiệm (Baseline Snapshot)

Các thuật toán hiện tại là Python thuần và không gọi CUDA, PyTorch, CuPy hay
kernel GPU. Vì vậy đây là benchmark **CPU/RAM**; GPU được phát hiện và lưu chỉ
để công bố môi trường, không được dùng để diễn giải chênh lệch hiệu năng.

### Cấu hình máy tác giả

Các số liệu gốc trong dự án được thu thập trên môi trường chuẩn sau:

| Thành phần | Chi tiết |
| --- | --- |
| **CPU** | Intel(R) Core(TM) i5-9300H CPU @ 2.40GHz (4 cores / 8 threads, TDP 45 W, Turbo Boost lên 4.1 GHz) |
| **RAM** | 16 GB DDR4 (17,016,406,016 bytes) |
| **GPU** | NVIDIA GeForce GTX 1650 Ti with Max-Q Design (4 GB GDDR6, Driver 595.97) — *không dùng trong benchmark* |
| **Hệ điều hành** | Windows 11 (build 10.0.26200) |
| **Python** | 3.13.9 64-bit |
| **Packages** | `pandas 3.0.5`, `numpy 2.5.2`, `matplotlib 3.11.1` |
| **Dataset** | HCMUS surrounding filter (`edges.csv` SHA256: `1a609d...`, `nodes.csv` SHA256: `349459...`) |
| **Workload Graph** | 2,752 nodes, 6,104 directed edges; Largest SCC: 2,746 nodes |
| **Workload Run ID** | `20260817T100628Z` (`TIME_REPEATS = 21`, `MEMORY_REPEATS = 7`, `WARMUP_RUNS = 3`) |

---

## Bảng kết quả thực nghiệm chi tiết

### 1. Nhóm Tìm đường hai điểm (Graph Search)

Workload: Start node `1996655313`, Goal node `5500064102`, Cost metric: `estimated_time_s`.  
Oracle chi phí: Dijkstra (`89.048 s`).

| Thuật toán | Runtime Median (ms) | Runtime p95 (ms) | Peak Heap Median (MiB) | Peak Heap Max (MiB) | Cost (s) | Cost Gap vs Oracle (%) | Completed All Runs | Deterministic |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hill Climbing** | 0.09 | 0.12 | 0.015 | 0.015 | *N/A* | *N/A* | **False** (Dead end) | True |
| **BFS** | 1.25 | 1.63 | 0.178 | 0.318 | 89.05 | 0.00% | True | True |
| **A\*** | **2.43** | **3.33** | **0.147** | **0.287** | **89.05** | **0.00%** | **True** | **True** |
| **Dijkstra** | 6.19 | 7.94 | 0.397 | 0.537 | 89.05 | 0.00% (Oracle) | True | True |
| **UCS** | 6.80 | 8.91 | 0.370 | 0.370 | 89.05 | 0.00% | True | True |
| **DFS** | 22.71 | 48.19 | 1.641 | 1.781 | 4924.38 | **+5430.03%** | True | True |

---

### 2. Nhóm Tối ưu nhiều điểm dừng (Multi-Stop Optimization)

Workload: 6 Waypoints trung gian + Start + Goal (tổng 8 locations trên Strongly Connected Component).  
Pairwise Cost Matrix: Tính bằng Dijkstra trên graph thực tế.  
Oracle thứ tự dừng: Held-Karp (`1595.914 s`).

| Thuật toán | Runtime Median (ms) | Runtime p95 (ms) | Peak Heap Median (MiB) | Peak Heap Max (MiB) | Cost (s) | Cost Gap vs Oracle (%) | Completed All Runs | Tính chất nghiệm |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Nearest Neighbor** | **0.02** | **0.05** | **0.002** | 0.002 | 1751.93 | +9.78% | True | Tham lam (Greedy heuristic) |
| **Held-Karp** | **0.46** | **0.58** | **0.036** | 0.036 | **1595.91** | **0.00% (Oracle)** | True | **Tối ưu toàn cục (Exact DP)** |
| **Genetic Algorithm** | 4.86 | 7.75 | 0.016 | 0.157 | 1780.63 | +11.57% | True | Tiến hóa ($N_{pop}=20, G=30$) |
| **Simulated Annealing** | 21.32 | 25.48 | 0.009 | 0.150 | **1595.91** | **0.00%** | True | Tôi luyện kim loại ($T_0=1000$) |

---

## Phân tích chuyên sâu từng thuật toán

### Nhóm Tìm đường hai điểm (Graph Search)

```
Thời gian thực thi (ms) - Càng ngắn càng tốt:
[Hill Climbing] 0.09 ms  (Kẹt Dead End ❌)
[BFS]           1.25 ms  ██▌
[A*]            2.43 ms  █████
[Dijkstra]      6.19 ms  ████████████▍
[UCS]           6.80 ms  █████████████▋
[DFS]          22.71 ms  ██████████████████████████████████████████████
```

1. **A\* (A-Star)**:
   - **Hiệu năng vượt trội**: Đạt thời gian $2.43\text{ ms}$, **nhanh gấp ~2.55 lần Dijkstra** ($6.19\text{ ms}$) và nhanh gấp ~2.8 lần UCS ($6.80\text{ ms}$).
   - **Bộ nhớ tối ưu**: Peak heap $0.147\text{ MiB}$ (thấp nhất trong các thuật toán bảo đảm tối ưu), do hàm heuristic admissible ($h(n) = \text{Haversine}(n, goal) / v_{max}$) định hướng tìm kiếm trực diện về đích, cắt tỉa đáng kể số lượng node phải đưa vào priority queue / trace history.
   - **Nghiệm tối ưu**: Chi phí đạt $89.05\text{ s}$ (bằng chính xác Oracle Dijkstra).

2. **Dijkstra & UCS (Uniform Cost Search)**:
   - Cả hai đều tìm ra đường đi ngắn nhất về mặt thời gian di chuyển ($89.05\text{ s}$, `cost_gap = 0.0%`).
   - Dijkstra và UCS mở rộng không gian tìm kiếm đồng tâm (không có heuristic định hướng), dẫn đến số node mở rộng lớn hơn A*, thời gian xử lý khoảng $6.19 - 6.80\text{ ms}$ và bộ nhớ heap ~ $0.37 - 0.40\text{ MiB}$.
   - UCS và Dijkstra có độ phức tạp tương đồng $O((V + E) \log V)$ với Min-Heap.

3. **BFS (Breadth-First Search)**:
   - Rất nhanh ($1.25\text{ ms}$) do thao tác hàng đợi FIFO ($O(1)$) không tốn chi phí duy trì min-heap ($O(\log N)$).
   - **Cảnh báo bản chất**: BFS chỉ tối ưu **số cạnh đi qua (minimum hops)**. Trong trường hợp cụ thể này, đường đi ít chặng nhất trùng với đường có thời gian ngắn nhất, nhưng trên đồ thị có trọng số tổng quát (ví dụ đường cao tốc xa vs đường ngõ hẹp), BFS **không** bảo đảm tối ưu thời gian.

4. **DFS (Depth-First Search)**:
   - **Kém nhất về chất lượng đường đi**: Chi phí lên tới $4924.38\text{ s}$ (**chậm hơn 55 lần so với đường tối ưu**, độ lệch $+5430.03\%$).
   - **Latency và memory cao**: Mất $22.71\text{ ms}$ (p95 lên đến $48.19\text{ ms}$ do đào sâu nhánh không triển vọng) và tiêu thụ $1.641\text{ MiB}$ bộ nhớ đỉnh (gấp 11 lần A*).
   - **Kết luận**: DFS tuyệt đối không dùng để điều hướng cứu hộ khẩn cấp.

5. **Hill Climbing**:
   - Chạy cực nhanh ($0.09\text{ ms}$) do chỉ đi theo độ dốc heuristic tức thời và không lưu frontier.
   - **Thất bại (Incomplete)**: Bị kẹt tại ngõ cụt cục bộ (node `1996655226`) do đồ thị đường phố thực tế có đường một chiều và cấu trúc không lồi (non-convex). Thuật toán dừng mà không tới được đích (`completed_all_runs = False`).

---

### Nhóm Tối ưu thứ tự nhiều điểm dừng (Multi-Stop Optimization)

```
Thời gian thực thi (ms) - Càng ngắn càng tốt:
[Nearest Neighbor]   0.02 ms  ▏
[Held-Karp]          0.46 ms  █
[Genetic Algorithm]  4.86 ms  ██████████
[Simulated Anneal.] 21.32 ms  ████████████████████████████████████████████
```

1. **Held-Karp (Dynamic Programming)**:
   - **Chuẩn mực tối ưu (Oracle)**: Sử dụng quy hoạch động với bitmask ($O(2^n \cdot n^2)$), tìm ra thứ tự đi qua 6 điểm dừng với tổng thời gian ngắn nhất ($1595.914\text{ s}$).
   - **Thời gian ấn tượng ở $n \le 10$**: Chỉ mất $0.46\text{ ms}$ cho 8 điểm (Start + 6 Waypoints + Goal), bộ nhớ chỉ $0.036\text{ MiB}$.
   - **Giới hạn**: Số phép tính tăng theo hàm mũ $2^n$. Thuật toán bị chặn ở $n \le 10$ trong implementation để tránh tràn bộ nhớ/CPU.

2. **Nearest Neighbor (Tham lam)**:
   - **Tốc độ số một**: Hoàn thành trong **$0.02\text{ ms}$** ($22.8\ \mu\text{s}$), bộ nhớ gần như bằng 0 ($0.002\text{ MiB}$).
   - **Chất lượng nghiệm**: Độ lệch chi phí chỉ $+9.78\%$ ($1751.93\text{ s}$ vs $1595.91\text{ s}$).
   - Rất phù hợp khi cần tính toán tức thì phản hồi UI hoặc làm nghiệm khởi tạo ban đầu cho các thuật toán meta-heuristic.

3. **Simulated Annealing (Tôi luyện kim loại)**:
   - **Chất lượng nghiệm xuất sắc**: Với seed cố định và lịch giảm nhiệt phù hợp ($T_0=1000, \alpha=0.95$), SA đã tìm được **chính xác nghiệm tối ưu toàn cục** ($1595.914\text{ s}$, gap $0.00\%$).
   - **Thời gian**: Mất $21.32\text{ ms}$ do lặp qua nhiều mức nhiệt độ để tránh cực tiểu cục bộ.

4. **Genetic Algorithm (Giải thuật di truyền)**:
   - Đạt thời gian $4.86\text{ ms}$ với quần thể 20 cá thể, 30 thế hệ.
   - Cho nghiệm khả thi với độ lệch chi phí $+11.57\%$ ($1780.63\text{ s}$).

---

## Ma trận so sánh đặc tính & Độ phức tạp lý thuyết

| Thuật toán | Độ phức tạp thời gian | Độ phức tạp không gian | Yêu cầu bộ nhớ | Tính tối ưu (Optimality) | Tính hoàn chỉnh (Completeness) | Ứng dụng phù hợp |
| :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| **A\*** | $O(E)$ (trung bình) / $O(b^d)$ | $O(V)$ | Thấp (~0.15 MiB) | **Có** (khi $h$ admissible) | **Có** (trên đồ thị hữu hạn) | **Tìm đường cứu hộ khẩn cấp chuẩn** |
| **Dijkstra** | $O((V + E) \log V)$ | $O(V)$ | Trung bình (~0.40 MiB) | **Có** (cost $\ge 0$) | **Có** (cost $\ge 0$) | Tính ma trận khoảng cách / Baseline |
| **UCS** | $O(b^{1 + \lfloor C^* / \epsilon \rfloor})$ | $O(V)$ | Trung bình (~0.37 MiB) | **Có** (cost $\ge \epsilon > 0$) | **Có** (cost $\ge \epsilon > 0$) | Khám phá đồ thị chi phí tổng quát |
| **BFS** | $O(V + E)$ | $O(V)$ | Thấp (~0.18 MiB) | Chỉ tối ưu số cạnh (hops) | **Có** (trên đồ thị hữu hạn) | Phân tích topo, tìm trạm gần nhất theo hop |
| **DFS** | $O(V + E)$ | $O(V)$ | Cao (~1.64 MiB) | **Không** | **Có** (khi có visited set) | Duyệt cây, kiểm tra tính liên thông |
| **Hill Climbing** | $O(b \cdot m)$ | $O(1)$ | Rất thấp (~0.015 MiB)| **Không** | **Không** (kẹt local minima) | Demo bài giảng / Bài toán lồi |
| **Held-Karp** | $O(n^2 2^n)$ | $O(n 2^n)$ | Thấp ở $n \le 10$ (~0.04 MiB) | **Có** (Tối ưu toàn cục TSP) | **Có** ($n \le 10$) | **Tối ưu lịch trình $\le 10$ điểm dừng** |
| **Nearest Neighbor** | $O(n^2)$ | $O(n)$ | Cực thấp (~0.002 MiB) | Xấp xỉ (không bảo đảm) | Không trên ma trận thưa | Phản hồi siêu nhanh / Tạo seed cho SA |
| **Simulated Annealing** | $O(k \cdot n)$ | $O(n)$ | Thấp (~0.009 MiB) | Xấp xỉ (tiệm cận tối ưu) | Có trên ma trận đầy đủ | Tối ưu nhiều điểm dừng $n > 10$ |
| **Genetic Algorithm** | $O(G \cdot P \cdot n)$ | $O(P \cdot n)$ | Thấp (~0.016 MiB) | Xấp xỉ | Có trên ma trận đầy đủ | Tối ưu đa mục tiêu / Quần thể lớn |

---

## Biểu đồ trực quan hóa (Visualizations)

Các biểu đồ sau được sinh tự động bởi [`scripts/generate_benchmark_plots.py`](../../scripts/generate_benchmark_plots.py) và lưu tại thư mục `artifacts/benchmarks/`:

1. **Tổng hợp toàn diện (Summary Plot)**:  
   `artifacts/benchmarks/benchmark_summary.png`  
   *(Bao gồm 4 panel: Runtime & Memory của Graph Search, Runtime & Cost Gap của Multi-Stop)*

2. **Chi tiết Tìm đường 2 điểm**:  
   `artifacts/benchmarks/benchmark_graph_search.png`

3. **Chi tiết Tối ưu nhiều điểm dừng**:  
   `artifacts/benchmarks/benchmark_multi_stop.png`

---

## Khuyến nghị kiến trúc cho hệ thống RescueRoute

Dựa trên dữ liệu thực nghiệm trên hệ thống i5-9300H:

1. **Routing Engine 1-to-1 (Tìm đường khẩn cấp giữa 2 điểm)**:
   - **Ưu tiên mặc định**: **A\*** với heuristic Haversine / max_speed. Thuật toán đạt thời gian $2.43\text{ ms}$ (đáp ứng xuất sắc SLA < $50\text{ ms}$ cho real-time navigation) và bảo đảm đường đi ngắn nhất về thời gian.
   - **Xây dựng Distance Matrix**: Sử dụng **Dijkstra 1-to-All** để tạo pairwise matrix một lần phục vụ bài toán đa điểm dừng.

2. **Dispatching Engine (Điều phối xe cứu hộ nhiều điểm dừng)**:
   - **Số điểm dừng $\le 10$**: Sử dụng **Held-Karp**. Đem lại lộ trình tối ưu tuyệt đối với thời gian tính toán chỉ dưới $1\text{ ms}$.
   - **Số điểm dừng $> 10$ (Quy mô lớn)**: Kết hợp **Nearest Neighbor** (khởi tạo trong $0.02\text{ ms}$) + **Simulated Annealing** (tối ưu hóa cục bộ) để bảo đảm thời gian phản hồi dưới $100\text{ ms}$.

---

## Hướng dẫn tái lập kết quả (Reproducibility)

Để chạy lại benchmark và đối chiếu với baseline trên máy của bạn:

1. Đảm bảo môi trường ảo `.venv` đã cài đặt đầy đủ:
   ```bash
   pip install -r backend/requirements.txt
   pip install matplotlib
   ```
2. Mở notebook [`scripts/benchmark_algorithms.ipynb`](../../scripts/benchmark_algorithms.ipynb) bằng kernel `.venv`.
3. Chạy toàn bộ cell (**Run All**).
4. Kiểm tra các file kết quả được sinh trong `artifacts/benchmarks/`:
   - `graph-search-<timestamp>.csv`
   - `multi-stop-<timestamp>.csv`
   - `environment-<timestamp>.json`
   - `benchmark_summary.png`, `benchmark_graph_search.png`, `benchmark_multi_stop.png`
