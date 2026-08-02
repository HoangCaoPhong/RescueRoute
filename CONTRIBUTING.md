# Contributing to RescueRoute

## Branch strategy

| Branch | Mục đích | Nguồn tạo | Merge vào |
|---|---|---|---|
| `main` | Bản ổn định, có thể demo/release | `dev` | - |
| `dev` | Tích hợp công việc trong sprint | `main` lúc khởi tạo | `main` |
| `feature/<slug>` | Tính năng hoặc thuật toán mới | `dev` | `dev` |
| `fix/<slug>` | Sửa lỗi thông thường | `dev` | `dev` |
| `docs/<slug>` | Tài liệu | `dev` | `dev` |
| `experiment/<slug>` | Thử nghiệm chưa cam kết | `dev` | thường không merge trực tiếp |
| `hotfix/<slug>` | Lỗi khẩn cấp trên bản ổn định | `main` | `main`, sau đó đồng bộ `dev` |

Tên branch viết thường, dùng dấu gạch ngang, không dùng tên cá nhân. Ví dụ: `feature/bfs-search-events`, `feature/gps-location-api`, `fix/one-way-edge-cost`.

## Khởi tạo `dev` lần đầu

Sau khi commit khung repository lên `main`, Tech Lead tạo nhánh tích hợp:

```bash
git switch main
git pull --ff-only origin main
git switch -c dev
git push -u origin dev
```

Trên GitHub, bật branch protection cho `main` và `dev`: yêu cầu pull request, ít nhất một approval, conversation đã resolve và status checks chạy thành công.

## Luồng làm việc cho một task

```bash
git switch dev
git pull --ff-only origin dev
git switch -c feature/short-description

# Code và kiểm tra
git status
git add <cac-file-dung-pham-vi>
git commit -m "feat(scope): short description"
git push -u origin feature/short-description
```

Sau đó mở pull request vào `dev`, điền đủ template và gán reviewer không phải chính tác giả.

## Commit convention

Định dạng:

```text
<type>(<scope>): <imperative summary>
```

Ví dụ:

- `feat(algorithm): implement uniform cost search`
- `feat(map): visualize visited and frontier nodes`
- `fix(graph): respect one-way road direction`
- `test(astar): compare optimal cost with UCS`
- `docs(api): describe route search response`

Mỗi commit phải có ý nghĩa độc lập. Không dùng thông điệp như `update`, `fix code`, `done` hoặc tên thành viên.

## Pull request rules

- Giữ PR nhỏ và chỉ giải quyết một mục tiêu. Nếu đổi API và UI lớn, ưu tiên tách thành các PR có thứ tự rõ.
- PR thuật toán phải có unit test và kết quả trên dataset mẫu.
- PR API phải cập nhật contract trong `docs/api/`.
- PR thay đổi dataset phải nêu nguồn, schema và ảnh hưởng benchmark.
- PR giao diện phải kèm ảnh/video trước-sau hoặc các bước kiểm tra thủ công.
- Tác giả tự review diff, xóa debug code và giải quyết conflict trước khi yêu cầu review.

## Gợi ý chia branch ban đầu

- `feature/astar-search` và `feature/hill-climbing`
- `feature/ucs-search` và `feature/simulated-annealing`
- `feature/dijkstra-search` và `feature/genetic-algorithm`
- `feature/dfs-search` và `feature/fastapi-foundation`
- `feature/bfs-search` và `feature/react-map-foundation`
- `feature/graph-dataset-schema` cho contract dữ liệu dùng chung

Không phát triển các thuật toán song song trước khi merge contract `Graph` và `SearchResult` dùng chung vào `dev`; nếu không, chi phí tích hợp sẽ rất cao.

Khi nhận task thuật toán, xem bảng owner và checklist tại [`backend/app/algorithms/README.md`](backend/app/algorithms/README.md). Source, test và tài liệu phải dùng cùng tên folder để reviewer tìm được ngay.
