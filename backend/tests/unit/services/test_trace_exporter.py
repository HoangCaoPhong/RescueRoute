import gzip
import json

from backend.app.services.trace_exporter import export_trace_json


def test_trace_exporter_writes_an_api_compatible_json_document(tmp_path):
    payload = {"found": True, "search_trace": {"schema_version": "1.0"}}

    path = export_trace_json(payload, tmp_path)
    document = json.loads(path.read_text(encoding="utf-8"))

    assert path.parent == tmp_path
    assert document["export_version"] == "1.0"
    assert document["payload"] == payload


def test_trace_exporter_can_write_gzip(tmp_path):
    path = export_trace_json({"found": False}, tmp_path, compress=True)

    with gzip.open(path, "rt", encoding="utf-8") as stream:
        assert json.load(stream)["payload"] == {"found": False}
