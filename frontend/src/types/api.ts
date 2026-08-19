export type Algorithm =
  | "astar"
  | "ucs"
  | "dijkstra"
  | "bfs"
  | "dfs"
  | "hill_climbing";

export type Criterion = "cost" | "time" | "distance" | "hops";

export type OptimizationMethod =
  | "input"
  | "nearest_neighbor"
  | "held_karp"
  | "genetic_algorithm"
  | "simulated_annealing";

export interface HealthStatus {
  status: string;
  latency_ms: number;
  nodes_count: number;
  edges_count: number;
  dynamic_edges_count: number;
}

export interface PointOfInterest {
  node_id: number;
  poi_node_id?: number;
  name?: string;
  type?: string;
  category?: string;
  lat: number;
  lng: number;
  is_hospital?: boolean;
  is_emergency?: boolean;
}

export interface RoadEdge {
  edge_id: string;
  name?: string;
  distance: number;
  congestion_level: number;
  current_cost: number;
  u_lat: number;
  u_lng: number;
  v_lat: number;
  v_lng: number;
}

export interface MappedRoadNode {
  nearest_node_id: number;
  nearest_node_name: string;
  distance_meters: number;
}

export interface AmbulanceLocation {
  lat: number;
  lng: number;
  mapped_nearest_node: Partial<MappedRoadNode>;
}

export interface SearchFrontierItem {
  node_id: number;
  g?: number;
  h?: number;
  f?: number;
  cost?: number;
  priority?: number;
  selected?: boolean;
}

export interface SearchStep {
  step: number;
  current_node: number | null;
  frontier: SearchFrontierItem[];
  frontier_size: number;
  frontier_truncated: boolean;
}

export interface SearchTrace {
  schema_version: string;
  algorithm: Algorithm;
  frontier_kind: string;
  visited_order: number[];
  steps: SearchStep[];
  node_coords: Record<string, [number, number]>;
}

export interface RouteResponse {
  found: boolean;
  message?: string;
  algorithm?: Algorithm;
  route_algorithm?: Algorithm;
  optimization_method?: Exclude<OptimizationMethod, "input">;
  criterion?: Criterion;
  is_optimal?: boolean;
  order_is_optimal?: boolean;
  total_cost?: number;
  total_distance_m?: number;
  nodes_expanded?: number;
  execution_time_ms?: number;
  hop_count?: number;
  path_nodes?: number[];
  path_coords?: [number, number][];
  visiting_order?: number[];
  ordered_waypoints?: number[];
  destination_hospital?: PointOfInterest;
  search_trace?: SearchTrace;
  segments?: RouteSegment[];
}

export interface RouteSegment {
  start: number;
  goal: number;
  result: RouteResponse;
}

export interface DashboardData {
  health: HealthStatus;
  points: PointOfInterest[];
  edges: RoadEdge[];
  ambulance: AmbulanceLocation;
}
