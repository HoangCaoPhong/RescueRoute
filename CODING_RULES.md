# Coding Rules - RescueRoute

Tài liệu này là chuẩn chung cho mọi pull request. Nếu một quyết định mới mâu thuẫn với tài liệu này, nhóm phải ghi lại lý do trong `docs/architecture/` và cập nhật quy tắc trong cùng pull request.

## 1. Nguyên tắc chung

- Code, tên biến, tên hàm, API field và commit message dùng tiếng Anh; giải thích nghiệp vụ có thể dùng tiếng Việt.
- Một module chỉ nên có một trách nhiệm rõ ràng. API không chứa trực tiếp logic thuật toán.
- Thuật toán trong `backend/app/algorithms/` phải là code thuần, không import FastAPI, Supabase hoặc framework UI.
- Không hard-code secret, URL môi trường, API key hay mật khẩu. Đọc từ cấu hình môi trường.
- Không commit file sinh ra, cache, virtual environment, `node_modules`, log hoặc dữ liệu nhạy cảm.
- Không tự ý đổi schema dữ liệu/API dùng chung mà không cập nhật test, docs và báo cho frontend/backend liên quan.

## 2. Python / FastAPI

- Hỗ trợ Python 3.10+; dùng type hints cho public function và data model.
- Format/lint dự kiến bằng Ruff; kiểm tra kiểu bằng mypy khi cấu hình được thêm.
- Tên file, hàm và biến dùng `snake_case`; class dùng `PascalCase`; constant dùng `UPPER_SNAKE_CASE`.
- Route handler chỉ validate input, gọi service và chuyển kết quả thành response.
- Domain exception không trả trực tiếp stack trace cho client; map sang HTTP error có thông điệp rõ ràng.
- I/O chậm dùng `async` khi thư viện hỗ trợ; không biến hàm CPU-bound thành `async` giả.
- Mọi endpoint mới phải có request/response schema, status code, ví dụ lỗi và test tương ứng.

## 3. React / TypeScript

- Bật TypeScript strict mode khi scaffold frontend; tránh `any`, nếu bắt buộc phải ghi lý do.
- Component và file component dùng `PascalCase`; hook bắt đầu bằng `use`; biến/hàm dùng `camelCase`.
- Component hiển thị không gọi API trực tiếp. Đặt HTTP client trong `src/lib/api` hoặc `src/services`.
- Logic theo tính năng đặt trong `src/features/<feature-name>`; component dùng chung mới đặt trong `src/components`.
- Mọi trạng thái loading, empty và error phải có UI rõ ràng.
- Dữ liệu map dùng thứ tự tọa độ nhất quán và ghi rõ: domain/API dùng `latitude`, `longitude`; adapter Leaflet mới chuyển sang `[lat, lng]`.

## 4. Contract cho thuật toán

Mỗi thuật toán nằm trong một folder riêng:

- Tìm đường hai điểm: `backend/app/algorithms/graph_search/<algorithm>/`.
- Tối ưu nhiều điểm/xấp xỉ: `backend/app/algorithms/optimization/<algorithm>/`.
- Entry point chính đặt trong `algorithm.py`; chỉ tách helper khi có trách nhiệm rõ ràng.
- Không đặt bản sao của Graph, cost function hoặc SearchResult trong folder riêng.
- Test đặt đối xứng tại `backend/tests/unit/algorithms/<group>/<algorithm>/`.

Tất cả thuật toán tìm đường hai điểm phải nhận cùng một graph abstraction và trả cùng một dạng kết quả logic, tối thiểu gồm:

- `path`: danh sách node theo đúng thứ tự.
- `visited_order`: thứ tự node đã mở rộng để frontend mô phỏng.
- `trace_history.events` cho diễn tiến tìm kiếm.
- `total_distance`, `estimated_time`, `total_cost`.
- `explored_nodes`, `processing_time_ms`.
- `is_optimal` và mô tả điều kiện đảm bảo tối ưu.
- `explanation`: dữ liệu có cấu trúc để tạo giải thích cho người dùng.

Quy tắc bắt buộc:

- Không sửa đổi graph đầu vào trong lúc chạy thuật toán.
- Với cùng input và seed, kết quả phải tái lập được.
- Thuật toán ngẫu nhiên phải nhận `seed` từ caller.
- Trường hợp không có đường đi phải trả kết quả/exception domain thống nhất, không trả `None` tùy tiện.
- Mỗi thuật toán có test cho đường đi hợp lệ, không có đường, start bằng goal, đồ thị có hướng và cạnh rủi ro cao.

## 5. Graph, cost và heuristic

- Dùng ID duy nhất, ổn định cho node và edge; không dựa vào tên hiển thị làm khóa.
- Đơn vị chuẩn phải được ghi trong schema: khoảng cách (m), thời gian (s), tốc độ (km/h hoặc m/s, chọn một và chuyển đổi tại biên).
- Edge một chiều chỉ tồn tại theo hướng hợp lệ; đường hai chiều được biểu diễn rõ thành hai hướng hoặc bằng adapter nhất quán.
- Cost function nằm ở domain/service dùng chung, không sao chép công thức vào từng thuật toán.
- A* phải ghi rõ heuristic, đơn vị, điều kiện admissible/consistent và test đối chiếu với UCS/Dijkstra.
- Cạnh không thể đi qua phải được đánh dấu blocked/constraint; tránh dùng số “gần vô cực” rải rác trong code.

## 6. Dữ liệu

- `data/raw/`: dữ liệu nguồn, không chỉnh sửa thủ công sau khi nhập.
- `data/processed/`: dữ liệu chuẩn hóa dùng cho ứng dụng.
- `data/samples/`: bộ nhỏ, ổn định để demo và unit/integration test.
- Script chuyển đổi phải nằm trong `scripts/` và tạo kết quả tái lập được.
- Mọi dataset cần README/data dictionary nêu nguồn, giấy phép, schema, đơn vị và giả định.
- Không commit tọa độ GPS người dùng thật, token hoặc dữ liệu định danh cá nhân.

## 7. Test và chất lượng

- Sửa bug phải thêm regression test trước hoặc trong cùng pull request.
- Unit test thuật toán không gọi mạng, database hoặc API bản đồ.
- Integration test được phép dùng fixture/fake; test gọi dịch vụ thật phải được đánh dấu riêng và không là mặc định.
- So sánh thuật toán phải chạy trên cùng graph, cùng cost profile và cùng điều kiện.
- Không merge code bị bỏ qua test bằng comment hoặc `skip` mà không có issue/lý do.

## 8. API và tích hợp

- API public đặt dưới `/api/v1` khi bắt đầu triển khai; endpoint health check có thể ở `/health`.
- JSON dùng `snake_case` để đồng nhất với backend; frontend map sang kiểu TypeScript tại client boundary nếu cần.
- Tích hợp OpenStreetMap/Leaflet, OpenRouteService và Supabase phải qua adapter trong `integrations/`.
- OpenStreetMap tiles chỉ dùng để hiển thị nền; không xem tile server là routing API.
- Luôn kiểm tra điều khoản/usage policy, timeout, retry có giới hạn và lỗi dịch vụ ngoài.
- CORS dùng allowlist theo môi trường, không dùng wildcard trong production khi có credential.

## 9. Git và review

- Không push trực tiếp lên `main` hoặc `dev`.
- Branch nhỏ, tập trung một mục tiêu; rebase/merge `dev` thường xuyên để giảm conflict.
- Commit theo Conventional Commits: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.
- Pull request phải mô tả thay đổi, cách test, ảnh/video nếu đổi UI và ảnh hưởng API/data.
- Không approve pull request khi chưa đọc code hoặc chưa chạy kiểm tra phù hợp.
- Không force-push lên branch của người khác nếu chưa thống nhất.

## 10. Definition of Done

Một task chỉ hoàn tất khi:

- Acceptance criteria đã đạt.
- Code đã format/lint và test liên quan chạy qua.
- Không có secret hoặc file sinh ra bị commit.
- API/schema/data change đã cập nhật tài liệu.
- UI change có trạng thái loading/error và bằng chứng kiểm tra.
- Pull request được ít nhất một thành viên khác review và merge vào đúng nhánh.
