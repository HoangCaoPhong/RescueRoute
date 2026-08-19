# Thiết kế Hill Climbing

## English

### Objective

Hill Climbing constructs a route by repeatedly selecting the unvisited neighbor
with the lowest heuristic. It is a fast, memory-light local-search baseline and
does not guarantee an optimal route.

### Pseudocode

```text
current <- start
path <- [start]
visited <- {start}

until current is goal:
    rank unvisited neighbors by (heuristic, node ID)
    record candidates in the trace
    if no candidate exists: report a dead end

    next <- best candidate
    if next does not improve and sideways moves are disabled:
        report a local optimum
    append next and continue

return path and heuristic_steps
```

Hill Climbing is incomplete and not globally optimal. It may stop at a local
optimum, plateau, dead end, or step limit. Stable tie-breaking makes repeated
runs deterministic; visited nodes are not revisited.

---

## Tiếng Việt

## Mục tiêu

Hill Climbing xây dựng tuyến bằng cách chọn neighbor chưa thăm có heuristic nhỏ
nhất. Đây là local-search baseline nhanh và ít bộ nhớ, không phải thuật toán
đảm bảo đường đi tối ưu.

## Pseudocode

```text
current <- start
path <- [start]
visited <- {start}

đến khi current là goal:
    xếp các neighbor chưa thăm theo (heuristic, node ID)
    ghi danh sách ứng viên vào trace
    nếu không có ứng viên: báo dead end

    next <- ứng viên tốt nhất
    nếu next không cải thiện và không cho sideways: báo local optimum
    thêm next vào path và visited
    current <- next

trả path và heuristic_steps
```

## Thuộc tính

- Không complete và không tối ưu toàn cục.
- Có thể kẹt ở local optimum, plateau hoặc dead end.
- Tie-breaking xác định; không quay lại node đã thăm.
- `allow_sideways` và `max_steps` giúp caller kiểm soát hành vi.

Test bao phủ local optimum, sideways move, step limit, graph có hướng, heuristic
không hợp lệ, tie xác định và route metrics.
