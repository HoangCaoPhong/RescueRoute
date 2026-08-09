flowchart TD
    Start([Bắt đầu]) --> Init["Khởi tạo: <br/>Stack = [(start_node, [start_node])]<br/>explored_set = {}<br/>visited_order = []<br/>frontier_steps = []"]
    Init --> LoopCheck{"Stack rỗng?"}
    
    LoopCheck -- Có --> NoPath["Ném ngoại lệ: NoRouteFoundException"]
    LoopCheck -- Không --> RecordFrontier["Ghi nhận trạng thái Stack vào frontier_steps"]
    
    RecordFrontier --> PopStack["Pop (current_node, path) từ Stack"]
    PopStack --> VisitedCheck{"current_node in explored_set?"}
    
    VisitedCheck -- Có --> LoopCheck
    VisitedCheck -- Không --> MarkVisited["Thêm current_node vào explored_set<br/>Thêm current_node vào visited_order"]
    
    MarkVisited --> GoalCheck{"current_node == goal_node_id?"}
    
    GoalCheck -- Có --> CalcMetrics["Tính toán metrics: total_distance, estimated_time, total_cost"]
    CalcMetrics --> ReturnResult(["Trả về SearchResult (is_optimal = False)"])
    
    GoalCheck -- Không --> GetNeighbors["Lấy các node lân cận (neighbors)"]
    GetNeighbors --> SortNeighbors["Sắp xếp neighbors theo ID giảm dần<br/>(Để khi Pop LIFO ra thứ tự ID tăng dần)"]
    SortNeighbors --> PushStack["Push (neighbor, path + [neighbor])<br/>chưa có trong explored_set vào Stack"]
    PushStack --> LoopCheck
