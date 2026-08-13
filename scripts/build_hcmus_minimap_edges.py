"""Normalize the HCMUS minimap source tables into one routing edge table."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "data/samples/HCMUS_surrounding_filter/Minimap_ouput"
)
LOS_DETAILS = {
    "A": ("free_flow", 1.0),
    "B": ("light", 1.25),
    "C": ("moderate", 1.75),
    "D": ("heavy", 2.5),
    "E": ("severe", 4.0),
    "F": ("gridlock", 8.0),
}
ROAD_SPEED_KPH = {
    "motorway": 80.0,
    "trunk": 60.0,
    "trunk_link": 50.0,
    "primary": 50.0,
    "primary_link": 40.0,
    "secondary": 40.0,
    "secondary_link": 35.0,
    "tertiary": 30.0,
    "tertiary_link": 25.0,
    "residential": 25.0,
    "service": 15.0,
}
OUTPUT_FIELDS = (
    "edge_id",
    "source_node_id",
    "target_node_id",
    "distance_m",
    "estimated_time_s",
    "congestion_level",
    "los",
    "congestion_factor",
    "free_flow_speed_kph",
    "actual_speed_kph",
    "road_type",
    "street_name",
    "street_level",
    "traffic_date",
    "time_period",
    "traffic_source",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def latest_rows(
    rows: list[dict[str, str]],
    *,
    id_field: str,
    timestamp_fields: tuple[str, ...],
) -> dict[str, dict[str, str]]:
    latest: dict[str, tuple[tuple[Any, ...], dict[str, str]]] = {}
    for row in rows:
        item_id = row.get(id_field, "")
        key = tuple(
            sortable_timestamp_value(field, row.get(field, ""))
            for field in timestamp_fields
        )
        if item_id and (item_id not in latest or key > latest[item_id][0]):
            latest[item_id] = (key, row)
    return {item_id: item[1] for item_id, item in latest.items()}


def sortable_timestamp_value(field: str, value: str) -> Any:
    if field == "period":
        try:
            _prefix, hour, minute = value.split("_")
            return int(hour) * 60 + int(minute)
        except (TypeError, ValueError):
            return -1
    if field == "_id":
        try:
            return int(value)
        except (TypeError, ValueError):
            return -1
    return value


def positive_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def haversine_meters(
    source: tuple[float, float],
    target: tuple[float, float],
) -> float:
    source_lat, source_lng = map(math.radians, source)
    target_lat, target_lng = map(math.radians, target)
    delta_lat = target_lat - source_lat
    delta_lng = target_lng - source_lng
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(source_lat)
        * math.cos(target_lat)
        * math.sin(delta_lng / 2) ** 2
    )
    return 6371000.0 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def build_edges(input_directory: Path) -> list[dict[str, Any]]:
    nodes = read_rows(input_directory / "nodes.csv")
    segments = read_rows(input_directory / "segments.csv")
    train = latest_rows(
        read_rows(input_directory / "train.csv"),
        id_field="segment_id",
        timestamp_fields=("date", "period", "_id"),
    )
    statuses = latest_rows(
        read_rows(input_directory / "segment_status.csv"),
        id_field="segment_id",
        timestamp_fields=("updated_at", "_id"),
    )
    coordinates = {
        row["_id"]: (float(row["lat"]), float(row["long"]))
        for row in nodes
    }

    edges = []
    for segment in segments:
        segment_id = segment["_id"]
        source_id = segment["s_node_id"]
        target_id = segment["e_node_id"]
        distance = positive_float(segment.get("length"))
        if distance is None:
            distance = haversine_meters(
                coordinates[source_id],
                coordinates[target_id],
            )

        road_type = segment.get("street_type") or "unknown"
        free_flow_speed = positive_float(segment.get("max_velocity"))
        if free_flow_speed is None:
            free_flow_speed = ROAD_SPEED_KPH.get(road_type, 30.0)

        traffic = train.get(segment_id)
        los = (traffic or {}).get("LOS") or "A"
        congestion_level, congestion_factor = LOS_DETAILS.get(
            los,
            ("unknown", 1.0),
        )
        status = statuses.get(segment_id)
        observed_speed = positive_float((status or {}).get("velocity"))
        actual_speed = observed_speed or free_flow_speed / congestion_factor
        estimated_time = distance / (actual_speed / 3.6)
        if traffic and status and observed_speed:
            traffic_source = "train_los+latest_segment_status"
        elif traffic:
            traffic_source = "train_los+modeled_speed"
        elif status and observed_speed:
            traffic_source = "latest_segment_status+default_los"
        else:
            traffic_source = "road_type_defaults"

        edges.append(
            {
                "edge_id": segment_id,
                "source_node_id": source_id,
                "target_node_id": target_id,
                "distance_m": f"{distance:.3f}",
                "estimated_time_s": f"{estimated_time:.3f}",
                "congestion_level": congestion_level,
                "los": los,
                "congestion_factor": f"{congestion_factor:.2f}",
                "free_flow_speed_kph": f"{free_flow_speed:.2f}",
                "actual_speed_kph": f"{actual_speed:.2f}",
                "road_type": road_type,
                "street_name": segment.get("street_name") or "Unknown road",
                "street_level": segment.get("street_level") or "",
                "traffic_date": (traffic or {}).get("date", ""),
                "time_period": (traffic or {}).get("period", ""),
                "traffic_source": traffic_source,
            }
        )
    return edges


def write_edges(edges: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(edges)


def main() -> None:
    args = parse_args()
    output_path = args.output or args.input / "edges.csv"
    edges = build_edges(args.input)
    write_edges(edges, output_path)
    print(f"Wrote {len(edges):,} normalized edges to {output_path}")


if __name__ == "__main__":
    main()
