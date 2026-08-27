import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_every_phase_one_to_four_optional_has_an_evidence_row() -> None:
    optional_count = 0
    for phase in range(1, 5):
        for task in (ROOT / f"docs/phase-{phase}").glob("task-*.md"):
            match = re.search(
                r"^## Optional(?: work)?\s*$\n(.*?)(?=^## |\Z)",
                task.read_text(),
                re.MULTILINE | re.DOTALL,
            )
            if match:
                optional_count += sum(line.startswith("- ") for line in match.group(1).splitlines())

    matrix = (ROOT / "docs/phase-1-4-optional-deliverables.md").read_text()
    evidence_count = sum(
        line.startswith("| ") and not line.startswith("|---") and "Optional deliverable" not in line
        for line in matrix.splitlines()
    )

    assert optional_count == 84
    assert evidence_count == optional_count
