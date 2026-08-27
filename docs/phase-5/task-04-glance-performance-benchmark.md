# P5-T04 — Glance Performance Benchmark

**Status:** Pending
**Full estimate:** 0.75 hours
**16-hour path:** 25 minutes
**Dependencies:** Stable Glance API and seeded local or hosted dataset

## Objective

Measure the warm Glance API path reproducibly and report P50/P95/P99 against
the 300 ms target without hiding network or dataset assumptions.

## Required work, in order

1. Define environment, machine/region, dataset size, endpoint, and authenticated role.
2. Seed a realistic bounded history and open-task set.
3. Add a benchmark script that obtains or accepts a short-lived user token safely.
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

## Acceptance criteria

- [ ] At least 100 measured successful requests are reported.
- [ ] P50/P95/P99 calculation is deterministic and tested.
- [ ] Environment, dataset, warm-up, concurrency, and errors are documented.
- [ ] P95 is at or below 300 ms, or the limitation is stated precisely.

## Done when

A reviewer can reproduce and correctly interpret the Glance performance claim.
