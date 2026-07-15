#!/usr/bin/env python
from __future__ import annotations

import concurrent.futures
import io
import json
import time
from dataclasses import dataclass, asdict

from fastapi.testclient import TestClient

from validex.config import DEFAULT_CONFIG
from validex.server import create_app


@dataclass(frozen=True)
class Probe:
    name: str
    status_code: int
    seconds: float
    response_bytes: int
    error_code: str | None = None


def _csv(rows: int, cols: int = 5, invalid: bool = False, duplicate: bool = False) -> bytes:
    headers = ["compound_id", "logFC", "p_value", "FDR", "Annotation"]
    if duplicate:
        headers = ["compound_id", "compound_id", "p_value", "FDR", "Annotation"]
    while len(headers) < cols:
        headers.append(f"extra_{len(headers)}")
    lines = [",".join(headers[:cols])]
    for idx in range(rows):
        p_value = "not-a-number" if invalid and idx % 2 == 0 else "0.01"
        lines.append(f"C{idx},1.2,{p_value},0.02,Known" + ",x" * max(0, cols - 5))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _post(client: TestClient, name: str, content: bytes) -> Probe:
    start = time.perf_counter()
    response = client.post(
        "/audit",
        files={"file": (f"{name}.csv", io.BytesIO(content), "text/csv")},
    )
    elapsed = time.perf_counter() - start
    error_code = None
    try:
        body = response.json()
        error_code = body.get("error_code") if isinstance(body, dict) else None
    except Exception:
        body = response.text
    return Probe(
        name=name,
        status_code=response.status_code,
        seconds=round(elapsed, 4),
        response_bytes=len(response.content),
        error_code=error_code,
    )


def run() -> dict[str, object]:
    config = {
        **DEFAULT_CONFIG,
        "ai_enabled": False,
        "max_rows": 1000,
        "max_columns": 50,
        "max_total_cells": 20000,
        "max_upload_bytes": 2_000_000,
    }
    client = TestClient(create_app(config))
    probes = [
        _post(client, "small-valid", _csv(5)),
        _post(client, "typical-valid", _csv(500)),
        _post(client, "near-row-limit", _csv(1000)),
        _post(client, "near-column-limit", _csv(10, cols=50)),
        _post(client, "invalid-heavy", _csv(100, invalid=True)),
        _post(client, "duplicate-heavy", _csv(20, duplicate=True)),
        _post(client, "malformed", b"\x00\x00not,csv"),
        _post(client, "over-row-limit", _csv(1001)),
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        concurrent_results = list(
            executor.map(lambda _: _post(client, "concurrent-valid", _csv(50)), range(4))
        )
    probes.extend(concurrent_results)
    summary = {
        "status": "completed",
        "note": "Single-machine smoke evidence only; not a performance guarantee.",
        "probes": [asdict(probe) for probe in probes],
    }
    failures = [
        probe
        for probe in probes
        if probe.name != "over-row-limit" and probe.status_code >= 500
    ]
    if failures:
        summary["status"] = "failed"
        summary["failures"] = [asdict(probe) for probe in failures]
    return summary


def main() -> int:
    summary = run()
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
