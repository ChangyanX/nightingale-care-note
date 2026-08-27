import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.scribe import ScribeOutput

FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIRECTORY / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("fixture_name", "interaction_type"),
    [
        ("scribe_doctor_consult.json", "doctor_consult"),
        ("scribe_nurse_consult.json", "nurse_consult"),
        ("scribe_ai_patient_session.json", "ai_patient_session"),
    ],
)
def test_all_interaction_fixtures_share_one_contract(
    fixture_name: str,
    interaction_type: str,
) -> None:
    output = ScribeOutput.model_validate(load_fixture(fixture_name))

    assert output.schema_version == "1.0"
    assert output.interaction_type == interaction_type
    assert ScribeOutput.model_validate_json(output.model_dump_json()) == output


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("clinic_id", "10000000-0000-0000-0000-000000000001"),
        ("patient_id", "40000000-0000-0000-0000-000000000001"),
        ("author_role", "system"),
        ("visibility", "patient_facing"),
        ("status", "accepted"),
    ],
)
def test_model_cannot_supply_identity_authorization_or_review_fields(
    field: str,
    value: str,
) -> None:
    payload = load_fixture("scribe_doctor_consult.json")
    payload[field] = value

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ScribeOutput.model_validate(payload)


def test_duplicate_facts_and_highlights_are_rejected() -> None:
    payload = load_fixture("scribe_doctor_consult.json")
    payload["facts"].append(payload["facts"][0].copy())

    with pytest.raises(ValidationError, match="Duplicate extracted facts"):
        ScribeOutput.model_validate(payload)

    payload = load_fixture("scribe_doctor_consult.json")
    payload["highlights"].append(payload["highlights"][0].copy())
    with pytest.raises(ValidationError, match="Duplicate proposed highlights"):
        ScribeOutput.model_validate(payload)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("summary",), "x" * 4_001),
        (("highlights", 0, "score"), 100.1),
        (("highlights", 0, "risk_level"), "unknown"),
        (("highlights", 0, "risk_reason"), "   "),
    ],
)
def test_invalid_bounds_and_enums_are_rejected(
    path: tuple[str | int, ...],
    value: object,
) -> None:
    payload = load_fixture("scribe_doctor_consult.json")
    target: Any = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    with pytest.raises(ValidationError):
        ScribeOutput.model_validate(payload)


def test_json_schema_is_strict_and_provider_neutral() -> None:
    schema = ScribeOutput.model_json_schema()

    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == "1.0"
    assert "clinic_id" not in schema["properties"]
    assert "patient_id" not in schema["properties"]
    assert "offset" not in json.dumps(schema).lower()
    assert "occurrence_hint" in json.dumps(schema)
