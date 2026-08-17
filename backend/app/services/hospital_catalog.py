"""Helpers for building a unique, routable hospital catalog from POI data."""

import unicodedata
from typing import Any, Dict, Iterable, List, Mapping, Tuple


def normalize_hospital_name(name: str) -> str:
    """Return a comparison key that ignores case, accents, spacing, and punctuation."""
    normalized = unicodedata.normalize("NFKD", name.casefold()).replace("đ", "d")
    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    return " ".join(
        "".join(
            character if character.isalnum() else " "
            for character in without_accents
        ).split()
    )


def deduplicate_hospitals(
    hospitals: Iterable[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Keep one hospital per normalized name.

    ``nodes_with_poi_labels.csv`` may assign the same POI name to several
    nearby road nodes. The node with the shortest source POI distance is the
    representative kept for routing and map markers. ``source_distance_m`` is
    ingestion-only metadata and is never returned to API consumers.
    """
    unique_hospitals: Dict[str, Tuple[Tuple[float, int], Dict[str, Any]]] = {}

    for hospital in hospitals:
        candidate = dict(hospital)
        name_key = normalize_hospital_name(str(candidate["name"]))
        source_distance = float(candidate.pop("source_distance_m", float("inf")))
        rank = (source_distance, int(candidate["poi_node_id"]))
        existing = unique_hospitals.get(name_key)

        if existing is None or rank < existing[0]:
            unique_hospitals[name_key] = (rank, candidate)

    return [hospital for _rank, hospital in unique_hospitals.values()]
