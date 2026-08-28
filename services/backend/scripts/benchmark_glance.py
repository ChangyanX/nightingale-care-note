"""Measure the authenticated warm Glance endpoint without exposing its token."""

from __future__ import annotations

import argparse
import getpass
import json
import math
import os
import time
from typing import Any
from uuid import UUID

import httpx


def percentile(values: list[float], requested: float) -> float:
    """Return the deterministic nearest-rank percentile for non-empty values."""
    if not values:
        raise ValueError("At least one timing is required")
    if requested <= 0 or requested > 100:
        raise ValueError("Percentile must be in (0, 100]")
    ordered = sorted(values)
    index = max(0, math.ceil((requested / 100) * len(ordered)) - 1)
    return ordered[index]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patient-id", type=UUID, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--warmups", type=int, default=10)
    parser.add_argument("--requests", type=int, default=120)
    parser.add_argument("--target-ms", type=float, default=300.0)
    parser.add_argument("--enforce-target", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.warmups < 0 or args.requests < 100:
        raise SystemExit("Use at least 0 warmups and 100 measured requests")
    token = os.getenv("NIGHTINGALE_BENCHMARK_TOKEN") or getpass.getpass(
        "Paste a short-lived clinician/staff access token (hidden): "
    )
    if not token.strip():
        raise SystemExit("An access token is required")

    endpoint = f"{args.base_url.rstrip('/')}/patients/{args.patient_id}/glance"
    timings: list[float] = []
    errors: list[dict[str, Any]] = []
    with httpx.Client(
        headers={"authorization": f"Bearer {token.strip()}"},
        timeout=10.0,
    ) as client:
        for _ in range(args.warmups):
            response = client.get(endpoint)
            if response.status_code != 200:
                raise SystemExit(f"Warm-up failed with sanitized HTTP {response.status_code}")
        for index in range(args.requests):
            started = time.perf_counter_ns()
            try:
                response = client.get(endpoint)
                elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
                if response.status_code == 200:
                    timings.append(elapsed_ms)
                else:
                    errors.append({"request": index + 1, "status": response.status_code})
            except httpx.HTTPError:
                errors.append({"request": index + 1, "status": "transport_error"})

    report = {
        "endpoint_path": f"/patients/{args.patient_id}/glance",
        "warmups": args.warmups,
        "measured_requests": args.requests,
        "successful_requests": len(timings),
        "errors": errors,
        "concurrency": 1,
        "includes": (
            "FastAPI, caller authentication, network, Supabase Data API, "
            "RLS, serialization"
        ),
        "min_ms": round(min(timings), 2) if timings else None,
        "p50_ms": round(percentile(timings, 50), 2) if timings else None,
        "p95_ms": round(percentile(timings, 95), 2) if timings else None,
        "p99_ms": round(percentile(timings, 99), 2) if timings else None,
        "max_ms": round(max(timings), 2) if timings else None,
        "target_ms": args.target_ms,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors or not timings:
        raise SystemExit(2)
    if args.enforce_target and percentile(timings, 95) > args.target_ms:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
