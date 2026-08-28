# P5-T04 — Glance Performance Benchmark

**Status:** Implemented locally; hosted measurement pending
**Full estimate:** 0.75 hours
**16-hour path:** 25 minutes
**Dependencies:** Stable Glance API and seeded local or hosted dataset

## Objective

Measure the warm Glance API path reproducibly and report P50/P95/P99 against
the 300 ms target without hiding network or dataset assumptions.

## Required work, in order

1. Define environment, machine/region, dataset size, endpoint, and authenticated role.
2. Seed a realistic bounded history and open-task set. **Done:** five coherent
   patients across two clinics.
3. Add a benchmark script that obtains or accepts a short-lived user token safely.
   **Done:** `scripts.benchmark_glance` reads a hidden prompt or
   `NIGHTINGALE_BENCHMARK_TOKEN`, never a token argument.
4. Perform at least 10 unrecorded warm-up requests.
5. Record at least 100 sequential or deliberately configured concurrent requests.
6. Calculate P50/P95/P99, min/max, errors, and request count.
7. Repeat once and retain the representative raw timing file outside Git if it contains tokens.
8. Document whether measurement includes network and authentication overhead.

## Must be done

- Tokens never appear in command arguments, output, URLs, or committed results.
- Errors are counted and cannot be omitted from percentile reporting.
- Dataset size and warm/cold conditions are explicit.
- If P95 exceeds 300 ms, report it honestly and identify the dominant calls/query plan.

## Optional

- Cold-start measurement.
- Database `EXPLAIN (ANALYZE, BUFFERS)` for slow paths.

## Measurement layers

The standard automated suite performs 10 warm-ups and 120 in-process FastAPI
requests. It guards routing, auth dependency, ranking, DTO validation, and
serialization under the 300 ms P95 budget with deterministic fake Data API
responses. This is an approximation and explicitly excludes network and real
database/RLS latency.

The live script performs 10 warm-ups and 120 sequential requests through the
actual FastAPI URL. It includes caller authentication, network, Supabase Data
API, RLS, source lookups, tasks, ranking, and serialization. Timeline/source
loading and open-task loading run concurrently after the patient scope check.

```bash
make benchmark-glance PATIENT_ID=40000000-0000-0000-0000-000000000001
```

Use a short-lived staff or clinician token at the hidden prompt. The JSON output
contains path, counts, errors, min/max, P50/P95/P99, concurrency, and included
layers; it never contains the token or response body. Run it on the final hosted
environment before claiming hosted P95 compliance.

## Acceptance criteria

- [x] Automated approximation covers 120 measured successful requests.
- [x] P50/P95/P99 calculation is deterministic and tested.
- [x] Dataset, warm-up, concurrency, included layers, and errors are documented.
- [x] Approximation enforces P95 at or below 300 ms.
- [ ] Record and retain a final hosted 120-request result before making a hosted
  latency claim.

## Done when

A reviewer can reproduce and correctly interpret the Glance performance claim.
