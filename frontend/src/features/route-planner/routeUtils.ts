import type { RouteResponse, RouteSegment } from "../../types/api";

export function formatDistance(metres = 0): string {
  if (metres >= 1000) return `${(metres / 1000).toFixed(1)} km`;
  return `${Math.round(metres)} m`;
}

export function formatDuration(distanceMetres = 0): string {
  const totalMinutes = Math.max(1, Math.round(distanceMetres / 500));
  if (totalMinutes < 60) return `${totalMinutes} phút`;
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${hours} giờ${minutes ? ` ${minutes} phút` : ""}`;
}

export function aggregateRouteSegments(
  segments: RouteSegment[],
  visitingOrder: number[],
): RouteResponse {
  const pathNodes: number[] = [];
  const pathCoords: [number, number][] = [];

  segments.forEach(({ result }, index) => {
    pathNodes.push(...(index === 0 ? result.path_nodes ?? [] : result.path_nodes?.slice(1) ?? []));
    pathCoords.push(...(index === 0 ? result.path_coords ?? [] : result.path_coords?.slice(1) ?? []));
  });

  return {
    found: segments.every(({ result }) => result.found),
    path_nodes: pathNodes,
    path_coords: pathCoords,
    visiting_order: visitingOrder,
    segments,
    total_cost: segments.reduce((total, { result }) => total + (result.total_cost ?? 0), 0),
    total_distance_m: segments.reduce(
      (total, { result }) => total + (result.total_distance_m ?? 0),
      0,
    ),
    nodes_expanded: segments.reduce(
      (total, { result }) => total + (result.nodes_expanded ?? 0),
      0,
    ),
    execution_time_ms: segments.reduce(
      (total, { result }) => total + (result.execution_time_ms ?? 0),
      0,
    ),
    search_trace: segments.length === 1 ? segments[0].result.search_trace : undefined,
  };
}
