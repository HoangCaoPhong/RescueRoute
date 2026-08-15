import csv
import unittest
from pathlib import Path


DATA_DIRECTORY = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "samples"
    / "HCMUS_surrounding_filter"
    / "Minimap_ouput"
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIRECTORY / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class HcmusMinimapDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.nodes = read_csv("nodes.csv")
        cls.edges = read_csv("edges.csv")

    def test_graph_exceeds_assignment_size_and_uses_hcmus_coordinates(self) -> None:
        self.assertGreaterEqual(len(self.nodes), 20)
        self.assertGreaterEqual(len(self.edges), 30)
        self.assertEqual(len(self.nodes), 3364)
        self.assertEqual(len(self.edges), 4918)
        self.assertEqual(len({node["_id"] for node in self.nodes}), len(self.nodes))
        self.assertEqual(len({edge["edge_id"] for edge in self.edges}), len(self.edges))

        for node in self.nodes:
            self.assertGreaterEqual(float(node["lat"]), 10.74)
            self.assertLessEqual(float(node["lat"]), 10.79)
            self.assertGreaterEqual(float(node["long"]), 106.66)
            self.assertLessEqual(float(node["long"]), 106.71)

    def test_every_edge_has_the_fields_required_by_the_assignment(self) -> None:
        node_ids = {node["_id"] for node in self.nodes}
        traffic_sources = set()
        for edge in self.edges:
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
                float(edge["estimated_time_s"]),
                expected_time,
                places=2,
            )
            traffic_sources.add(edge["traffic_source"])

        self.assertIn("train_los+latest_segment_status", traffic_sources)
        self.assertIn("road_type_defaults", traffic_sources)


if __name__ == "__main__":
    unittest.main()
