from time import perf_counter

from app.api.revisions import _word_diff


def test_revision_word_diff_stays_bounded_for_demo_sized_content() -> None:
    previous = " ".join(f"synthetic-token-{index}" for index in range(300))
    current = previous.replace("synthetic-token-175", "synthetic-token-updated", 1)
    started = perf_counter()
    for _ in range(100):
        parts = _word_diff(previous, current)
    elapsed_ms = (perf_counter() - started) * 1000
    assert parts
    assert elapsed_ms < 1_000
