from backend.app.services.hospital_catalog import (
    deduplicate_hospitals,
    normalize_hospital_name,
)


def test_normalize_hospital_name_ignores_accents_case_and_punctuation():
    assert normalize_hospital_name("Bệnh viện - Đa Khoa") == "benh vien da khoa"
    assert normalize_hospital_name("benh vien da khoa") == "benh vien da khoa"


def test_deduplicate_hospitals_keeps_closest_point_for_the_same_name():
    hospitals = [
        {
            "name": "Bệnh viện Đa Khoa",
            "node_id": 10,
            "poi_node_id": 10,
            "source_distance_m": 35.0,
        },
        {
            "name": "benh vien da khoa",
            "node_id": 20,
            "poi_node_id": 20,
            "source_distance_m": 5.0,
        },
        {
            "name": "Phòng khám Khác",
            "node_id": 30,
            "poi_node_id": 30,
            "source_distance_m": 1.0,
        },
    ]

    unique_hospitals = deduplicate_hospitals(hospitals)

    assert [hospital["node_id"] for hospital in unique_hospitals] == [20, 30]
    assert all("source_distance_m" not in hospital for hospital in unique_hospitals)
