"""Optional JSON export for saved demos, reports, and offline playback."""

from __future__ import annotations

import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def export_trace_json(
    payload: dict[str, Any],
    output_dir: str | Path = "output/traces",
    *,
    compress: bool = False,
) -> Path:
    """Persist one API-compatible payload and return its generated path."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = ".json.gz" if compress else ".json"
    path = destination / f"trace-{timestamp}-{uuid4().hex[:12]}{suffix}"
    document = {
        "export_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    serialized = json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )
    if compress:
        with gzip.open(path, "wt", encoding="utf-8") as stream:
            stream.write(serialized)
    else:
        path.write_text(serialized, encoding="utf-8")
    return path
