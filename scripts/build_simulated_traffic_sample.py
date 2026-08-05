"""Build a deterministic Vietnamese traffic graph from the EDA train dataset."""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Iterable

SOURCE_PATH = "data/raw/train.csv"
SELECTED_DATE = "2020-08-02"
SELECTED_PERIOD = "period_23_30"
NODE_COUNT = 40
EDGE_COUNT = 60
OUTPUT_DIRECTORY = Path("data/samples/simulated_vietnamese_traffic")

LOS_DETAILS = {
    "A": ("free_flow", 1.0),
    "B": ("light", 1.0),
    "C": ("moderate", 2.0),
    "D": ("heavy", 3.0),
    "E": ("severe", 5.0),
    "F": ("gridlock", 8.0),
}
DEFAULT_SPEED_KPH = 70.0

EDGE_FIELDS = (
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
    "date",
    "time_period",
    "source_row_id",
)

NODE_FIELDS = (
    "node_id",
    "name",
    "latitude",
    "longitude",
    "node_type",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--input",
        type=Path,
        help="Local train.csv path. If omitted, read it from a Git ref.",
    )
    source.add_argument(
        "--source-ref",
        default="feature/EDA_data",
        help="Git ref containing data/raw/train.csv (default: %(default)s).",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_DIRECTORY)
    return parser.parse_args()


def load_rows(input_path: Path | None, source_ref: str) -> list[dict[str, str]]:
    if input_path is not None:
        source_text = input_path.read_text(encoding="utf-8")
    else:
        try:
            source_text = subprocess.run(
                ["git", "show", f"{source_ref}:{SOURCE_PATH}"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            ).stdout
        except subprocess.CalledProcessError as exc:
            raise SystemExit(
                f"Cannot read {SOURCE_PATH!r} from Git ref {source_ref!r}. "
                "Fetch the branch or pass --input."
            ) from exc
    return list(csv.DictReader(io.StringIO(source_text)))


def select_connected_slice(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    timestamp_rows = [
        row
        for row in rows
        if row["date"] == SELECTED_DATE and row["period"] == SELECTED_PERIOD
    ]
    if len(timestamp_rows) < EDGE_COUNT:
        raise ValueError("the selected date and period do not contain enough edges")

    incident_edges: dict[str, list[int]] = defaultdict(list)
    neighbors: dict[str, set[str]] = defaultdict(set)
    for index, row in enumerate(timestamp_rows):
        source = row["s_node_id"]
        target = row["e_node_id"]
        incident_edges[source].append(index)
        incident_edges[target].append(index)
        neighbors[source].add(target)
        neighbors[target].add(source)

    best_rows: list[dict[str, str]] | None = None
    best_key: tuple[int, int, int] | None = None
    for seed_node in sorted(incident_edges, key=int):
        selected_nodes = {seed_node}
        selected_streets: set[str] = set()

        while len(selected_nodes) < NODE_COUNT:
            candidates = {
                neighbor
                for node_id in selected_nodes
                for neighbor in neighbors[node_id]
                if neighbor not in selected_nodes
            }
            if not candidates:
                break

            def priority(node_id: str) -> tuple[int, int, int, int]:
                connecting_indexes = {
                    index
                    for index in incident_edges[node_id]
                    if timestamp_rows[index]["s_node_id"] in selected_nodes
                    or timestamp_rows[index]["e_node_id"] in selected_nodes
                }
                connecting_streets = {
                    timestamp_rows[index]["street_name"] for index in connecting_indexes
                }
                new_street_count = len(connecting_streets - selected_streets)
                return (
                    len(connecting_indexes) + 10 * new_street_count,
                    new_street_count,
                    len(incident_edges[node_id]),
                    -int(node_id),
                )

            next_node = max(candidates, key=priority)
            for index in incident_edges[next_node]:
                row = timestamp_rows[index]
                if (
                    row["s_node_id"] in selected_nodes
                    or row["e_node_id"] in selected_nodes
                ):
                    selected_streets.add(row["street_name"])
            selected_nodes.add(next_node)

        if len(selected_nodes) != NODE_COUNT:
            continue
        internal_rows = [
            row
            for row in timestamp_rows
            if row["s_node_id"] in selected_nodes and row["e_node_id"] in selected_nodes
        ]
        if len(internal_rows) < EDGE_COUNT:
            continue
        street_count = len({row["street_name"] for row in internal_rows})
        candidate_key = (street_count, len(internal_rows), -int(seed_node))
        if best_key is None or candidate_key > best_key:
            best_rows = internal_rows
            best_key = candidate_key

    if best_rows is None:
        raise ValueError(
            f"no connected {NODE_COUNT}-node subgraph has at least {EDGE_COUNT} edges"
        )
    return _keep_connected_edges(best_rows)


def _keep_connected_edges(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep exactly EDGE_COUNT rows while preserving every node and connectivity."""

    parent: dict[str, str] = {}

    def find(node_id: str) -> str:
        parent.setdefault(node_id, node_id)
        if parent[node_id] != node_id:
            parent[node_id] = find(parent[node_id])
        return parent[node_id]

    def union(left: str, right: str) -> bool:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return False
        parent[right_root] = left_root
        return True

    street_frequency: dict[str, int] = defaultdict(int)
    for row in rows:
        street_frequency[row["street_name"]] += 1
    ordered_rows = sorted(
        rows,
        key=lambda row: (
            street_frequency[row["street_name"]],
            row["street_name"],
            int(row["segment_id"]),
        ),
    )

    selected: list[dict[str, str]] = []
    selected_ids: set[str] = set()
    selected_streets: set[str] = set()
    for row in ordered_rows:
        if union(row["s_node_id"], row["e_node_id"]):
            selected.append(row)
            selected_ids.add(row["segment_id"])
            selected_streets.add(row["street_name"])

    remaining_rows = [
        row for row in ordered_rows if row["segment_id"] not in selected_ids
    ]
    remaining_rows.sort(
        key=lambda row: (
            row["street_name"] in selected_streets,
            street_frequency[row["street_name"]],
            row["street_name"],
            int(row["segment_id"]),
        )
    )
    selected.extend(remaining_rows[: EDGE_COUNT - len(selected)])
    if len(selected) != EDGE_COUNT:
        raise ValueError("could not retain the requested number of connected edges")
    return sorted(selected, key=lambda row: int(row["segment_id"]))


def build_edges(source_rows: Iterable[dict[str, str]]) -> list[dict[str, object]]:
    edges: list[dict[str, object]] = []
    for row in source_rows:
        congestion_level, congestion_factor = LOS_DETAILS[row["LOS"]]
        free_flow_speed_kph = (
            float(row["max_velocity"])
            if row["max_velocity"].strip()
            else DEFAULT_SPEED_KPH
        )
        actual_speed_kph = free_flow_speed_kph / congestion_factor
        distance_m = float(row["length"])
        estimated_time_s = distance_m / (actual_speed_kph / 3.6)
        edges.append(
            {
                "edge_id": row["segment_id"],
                "source_node_id": row["s_node_id"],
                "target_node_id": row["e_node_id"],
                "distance_m": _number(distance_m),
                "estimated_time_s": round(estimated_time_s, 3),
                "congestion_level": congestion_level,
                "los": row["LOS"],
                "congestion_factor": _number(congestion_factor),
                "free_flow_speed_kph": _number(free_flow_speed_kph),
                "actual_speed_kph": round(actual_speed_kph, 3),
                "road_type": row["street_type"] or "unknown",
                "street_name": row["street_name"],
                "street_level": row["street_level"],
                "date": row["date"],
                "time_period": row["period"],
                "source_row_id": row["_id"],
            }
        )
    return edges


def build_nodes(source_rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    node_coordinates: dict[str, tuple[str, str]] = {}
    node_streets: dict[str, set[str]] = defaultdict(set)
    for row in source_rows:
        node_coordinates[row["s_node_id"]] = (row["lat_snode"], row["long_snode"])
        node_coordinates[row["e_node_id"]] = (row["lat_enode"], row["long_enode"])
        node_streets[row["s_node_id"]].add(row["street_name"])
        node_streets[row["e_node_id"]].add(row["street_name"])

    nodes: list[dict[str, str]] = []
    for node_id in sorted(node_coordinates, key=int):
        street_names = sorted(node_streets[node_id])
        if len(street_names) > 1:
            name = f"Nút giao {street_names[0]} - {street_names[1]}"
            node_type = "intersection"
        else:
            name = f"Điểm trên đường {street_names[0]}"
            node_type = "road_point"
        latitude, longitude = node_coordinates[node_id]
        nodes.append(
            {
                "node_id": node_id,
                "name": name,
                "latitude": latitude,
                "longitude": longitude,
                "node_type": node_type,
            }
        )
    return nodes


def write_csv(path: Path, rows: list[dict[str, object]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _number(value: float) -> int | float:
    return int(value) if value.is_integer() else value


def main() -> None:
    args = parse_args()
    all_rows = load_rows(args.input, args.source_ref)
    source_slice = select_connected_slice(all_rows)
    nodes = build_nodes(source_slice)
    edges = build_edges(source_slice)

    write_csv(args.output / "source_slice.csv", source_slice, source_slice[0].keys())
    write_csv(args.output / "nodes.csv", nodes, NODE_FIELDS)
    write_csv(args.output / "edges.csv", edges, EDGE_FIELDS)
    print(
        f"Created {len(nodes)} nodes and {len(edges)} edges from "
        f"{SELECTED_DATE} {SELECTED_PERIOD} in {args.output}"
    )


if __name__ == "__main__":
    main()
