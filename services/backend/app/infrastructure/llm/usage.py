from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    provider: str
    model: str
    calls: int
    input_tokens: int
    output_tokens: int
    latency_ms_total: float
    estimated_cost_usd: float

    @property
    def average_latency_ms(self) -> float:
        return round(self.latency_ms_total / self.calls, 2) if self.calls else 0.0


def aggregate_usage(rows: list[dict[str, object]]) -> list[ProviderUsage]:
    totals: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        key = (str(row.get("provider") or "unknown"), str(row.get("model") or "unknown"))
        bucket = totals.setdefault(key, [0, 0, 0, 0.0, 0.0])
        bucket[0] += 1
        bucket[1] += _number(row.get("input_tokens"))
        bucket[2] += _number(row.get("output_tokens"))
        bucket[3] += _number(row.get("latency_ms"))
        bucket[4] += _number(row.get("estimated_cost_usd"))
    return [
        ProviderUsage(
            provider=provider,
            model=model,
            calls=int(values[0]),
            input_tokens=int(values[1]),
            output_tokens=int(values[2]),
            latency_ms_total=round(values[3], 2),
            estimated_cost_usd=round(values[4], 6),
        )
        for (provider, model), values in sorted(totals.items())
    ]


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)
