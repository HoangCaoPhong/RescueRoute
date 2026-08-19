import type {
  Algorithm,
  AmbulanceLocation,
  Criterion,
  DashboardData,
  HealthStatus,
  OptimizationMethod,
  PointOfInterest,
  RoadEdge,
  RouteResponse,
} from "../../types/api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload: unknown = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? String(payload.detail)
        : typeof payload === "string"
          ? payload
          : `HTTP ${response.status}`;
    throw new Error(detail || "Không thể kết nối tới máy chủ.");
  }

  return payload as T;
}

export async function getDashboardData(): Promise<DashboardData> {
  const [health, points, edges, ambulance] = await Promise.all([
    requestJson<HealthStatus>("/health"),
    requestJson<PointOfInterest[]>("/nodes?poi_type=all&limit=30000"),
    requestJson<RoadEdge[]>("/edges?limit=24000"),
    requestJson<AmbulanceLocation>("/ambulance/location"),
  ]);

  return { health, points, edges, ambulance };
}

export async function updateAmbulanceLocation(
  lat: number,
  lng: number,
): Promise<AmbulanceLocation> {
  const response = await requestJson<{
    current_gps: AmbulanceLocation;
  }>("/ambulance/location", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lng }),
  });

  return response.current_gps;
}

export function calculateDirectRoute(
  startNodeId: number,
  goalNodeId: number,
  algorithm: Algorithm,
): Promise<RouteResponse> {
  return requestJson<RouteResponse>("/route", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      start_node_id: startNodeId,
      goal_node_id: goalNodeId,
      algorithm,
    }),
  });
}

export function calculateOptimizedRoute(input: {
  startNodeId: number;
  waypointIds: number[];
  goalNodeId: number;
  algorithm: Algorithm;
  method: Exclude<OptimizationMethod, "input">;
  criterion: Criterion;
}): Promise<RouteResponse> {
  return requestJson<RouteResponse>("/route/multi-location", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      start_node_id: input.startNodeId,
      waypoint_ids: input.waypointIds,
      goal_node_id: input.goalNodeId,
      route_algorithm: input.algorithm,
      optimization_method: input.method,
      criterion: input.criterion,
    }),
  });
}
