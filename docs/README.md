# Chỉ mục tài liệu

## Tài liệu nguồn được giữ nguyên

- `Lab 1 - Searching.pdf`: đề bài chính thức, yêu cầu chức năng và thang điểm.
- `Họp Project 1-AI.docx`: ý tưởng, sprint, vai trò và phân công ban đầu.
- `Lab1_KeHoach_TrienKhai_Team5.docx`: mô hình Node/Edge và cost function ban đầu.
- `KẾ HOẠCH TRIỂN KHAI BACKEND VÀ TÍCH HỢP HỆ THỐNG.docx`: kế hoạch FastAPI, Render, GPS, Supabase và bản đồ.

Không chỉnh sửa các file nguồn để ghi quyết định mới. Thêm tài liệu Markdown vào đúng thư mục dưới đây để Git review được thay đổi.

## Tài liệu sẽ phát triển

- `architecture/`: sơ đồ hệ thống, ADR và quyết định kỹ thuật.
  - `architecture/search-trace-history-contract.md`: contract trace history
    dùng chung cho thuật toán tìm kiếm và UI monitoring.
- `algorithms/`: design, pseudocode, flowchart và benchmark của từng thuật toán.
- `api/`: API contracts, schema và ví dụ request/response.
- `development/`: hướng dẫn môi trường, test, benchmark và release.
- `diagrams/`: source của flowchart, sequence diagram và hình dùng trong báo cáo.
- `meeting-notes/`: biên bản họp mới theo ngày `YYYY-MM-DD-topic.md`.
- `report/`: nội dung, số liệu và tài nguyên cho technical report.

## Checklist bám đề bài

- [ ] Graph có ít nhất 20 node, 30 edge với ngữ cảnh giao thông Việt Nam.
- [ ] Hỗ trợ tìm đường hai điểm và tối ưu nhiều điểm.
- [ ] BFS, DFS, UCS và A* chạy đúng và được so sánh.
- [ ] Có ít nhất hai thuật toán bổ sung.
- [ ] Cost không chỉ dựa vào khoảng cách; có giải thích trọng số.
- [ ] Heuristic được phân tích admissible/consistent hoặc practical-only.
- [ ] GUI cho chọn điểm, thuật toán, tiêu chí tối ưu và điểm trung gian.
- [ ] GUI mô phỏng visited nodes, frontier và final route từng bước.
- [ ] Kết quả có path, visiting order, explored nodes, distance, time, cost và processing time.
- [ ] Có giải thích route, tuyến thay thế, ùn tắc và bảo đảm tối ưu.
- [ ] Benchmark các thuật toán trên cùng điều kiện.
- [ ] Technical report, slide, demo video và dataset đúng định dạng nộp bài.
