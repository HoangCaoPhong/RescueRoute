import { describe, expect, it } from "vitest";
import type { RouteSegment } from "../../types/api";
import {
  aggregateRouteSegments,
  formatDistance,
  formatDuration,
} from "./routeUtils";

describe("route presentation utilities", () => {
  it("formats compact distance and duration labels", () => {
    expect(formatDistance(850)).toBe("850 m");
    expect(formatDistance(2_450)).toBe("2.5 km");
    expect(formatDuration(7_500)).toBe("15 phút");
  });

  it("joins segments without duplicating boundary nodes", () => {
    const segments: RouteSegment[] = [
      {
        start: 1,
        goal: 2,
        result: {
          found: true,
          path_nodes: [1, 8, 2],
          path_coords: [[10, 106], [10.1, 106.1], [10.2, 106.2]],
          total_cost: 5,
          total_distance_m: 1_000,
          nodes_expanded: 10,
          execution_time_ms: 2,
        },
      },
      {
        start: 2,
        goal: 3,
        result: {
          found: true,
          path_nodes: [2, 9, 3],
          path_coords: [[10.2, 106.2], [10.3, 106.3], [10.4, 106.4]],
          total_cost: 6,
          total_distance_m: 1_500,
          nodes_expanded: 12,
          execution_time_ms: 3,
        },
      },
    ];

    const aggregate = aggregateRouteSegments(segments, [1, 2, 3]);

    expect(aggregate.path_nodes).toEqual([1, 8, 2, 9, 3]);
    expect(aggregate.path_coords).toHaveLength(5);
    expect(aggregate.total_cost).toBe(11);
    expect(aggregate.total_distance_m).toBe(2_500);
    expect(aggregate.nodes_expanded).toBe(22);
  });
});
