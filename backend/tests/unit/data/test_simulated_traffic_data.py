import csv
import unittest
from pathlib import Path


DATA_DIRECTORY = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "samples"
    / "simulated_vietnamese_traffic"
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIRECTORY / name).open(encoding="utf-8", newline="") as data_file:
        return list(csv.DictReader(data_file))


class SimulatedTrafficDataTest(unittest.TestCase):
    def test_graph_meets_size_and_timestamp_requirements(self) -> None:
        nodes = read_csv("nodes.csv")
        edges = read_csv("edges.csv")

        self.assertEqual(len(nodes), 40)
        self.assertEqual(len(edges), 60)
        self.assertEqual(len({node["node_id"] for node in nodes}), 40)
        self.assertEqual(len({edge["edge_id"] for edge in edges}), 60)
        self.assertEqual(len(nodes) * 3, len(edges) * 2)
        self.assertEqual({edge["date"] for edge in edges}, {"2020-08-02"})
        self.assertEqual({edge["time_period"] for edge in edges}, {"period_23_30"})
        self.assertEqual(len({edge["street_name"] for edge in edges}), 14)

    def test_edges_reference_nodes_and_have_required_traffic_fields(self) -> None:
        nodes = read_csv("nodes.csv")
        edges = read_csv("edges.csv")
        node_ids = {node["node_id"] for node in nodes}

        for edge in edges:
            self.assertIn(edge["source_node_id"], node_ids)
            self.assertIn(edge["target_node_id"], node_ids)
            self.assertGreater(float(edge["distance_m"]), 0)
            self.assertGreater(float(edge["estimated_time_s"]), 0)
            self.assertTrue(edge["congestion_level"])
            self.assertTrue(edge["road_type"])
            expected_time = float(edge["distance_m"]) / (
                float(edge["actual_speed_kph"]) / 3.6
            )
            self.assertAlmostEqual(
                float(edge["estimated_time_s"]), expected_time, places=2
            )

    def test_source_rows_are_traceable_and_graph_is_connected(self) -> None:
        nodes = read_csv("nodes.csv")
        source_rows = read_csv("source_slice.csv")
        edges = read_csv("edges.csv")
        self.assertEqual({row["date"] for row in source_rows}, {"2020-08-02"})
        self.assertEqual({row["period"] for row in source_rows}, {"period_23_30"})
        self.assertEqual(
            {edge["source_row_id"] for edge in edges},
            {row["_id"] for row in source_rows},
        )

        adjacency: dict[str, set[str]] = {}
        for edge in edges:
            source = edge["source_node_id"]
            target = edge["target_node_id"]
            adjacency.setdefault(source, set()).add(target)
            adjacency.setdefault(target, set()).add(source)
        pending = [next(iter(adjacency))]
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current not in visited:
                visited.add(current)
                pending.extend(adjacency[current] - visited)

        self.assertEqual(visited, {node["node_id"] for node in nodes})


if __name__ == "__main__":
    unittest.main()
