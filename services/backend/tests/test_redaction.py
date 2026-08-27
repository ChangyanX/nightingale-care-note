import pytest

from app.domain.redaction import RedactionError, redact_for_llm, verify_redacted_text


def test_redacts_supported_identifiers_without_retaining_values() -> None:
    source = """Patient Name: Parker Patient
DOB: 03/04/1988
NRIC: S1234567D
Phone: +65 9123 4567
Email: parker.patient@example.com
Address: 12 Orchard Road, Singapore 238823
Persistent nocturnal cough; inhaler technique needs review."""

    result = redact_for_llm(source)

    for sensitive_value in (
        "Parker Patient",
        "03/04/1988",
        "S1234567D",
        "+65 9123 4567",
        "parker.patient@example.com",
        "12 Orchard Road",
    ):
        assert sensitive_value not in result.text
        assert sensitive_value not in repr(result)
        assert sensitive_value not in repr(result.safe_metadata())
    assert "Persistent nocturnal cough" in result.text
    assert result.safe_metadata() == {
        "verified": True,
        "name": 1,
        "identity_number": 1,
        "phone": 1,
        "email": 1,
        "date_of_birth": 1,
        "address": 1,
    }


def test_known_names_and_honorific_names_are_redacted_case_insensitively() -> None:
    result = redact_for_llm(
        "parker patient spoke with Dr Alice Tan about the cough.",
        known_names=["Parker Patient"],
    )

    assert result.text == ("[REDACTED_NAME] spoke with [REDACTED_NAME] about the cough.")
    assert result.safe_metadata()["name"] == 2


def test_unicode_clinical_content_is_normalized_and_preserved() -> None:
    result = redact_for_llm(
        "Parker Patient reports cafe\u0301 exposure and 夜间咳嗽.",
        known_names=["Parker Patient"],
    )

    assert "café exposure" in result.text
    assert "夜间咳嗽" in result.text
    assert "Parker Patient" not in result.text


@pytest.mark.parametrize("source", ["", "  \n "])
def test_empty_input_fails_closed(source: str) -> None:
    with pytest.raises(RedactionError, match="must not be empty"):
        redact_for_llm(source)


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "Contact patient@example.com",
        "NRIC S1234567D",
        "Call +65 9123 4567",
        "DOB: 1988-04-03",
        "Address: 12 Orchard Road",
        "Dr Alice Tan reviewed the patient",
    ],
)
def test_verifier_rejects_supported_residual_patterns(unsafe_text: str) -> None:
    with pytest.raises(RedactionError, match="Redaction verification failed"):
        verify_redacted_text(unsafe_text)


def test_verifier_rejects_residual_known_name_without_echoing_it() -> None:
    known_name = "Parker Patient"

    with pytest.raises(RedactionError) as raised:
        verify_redacted_text(f"Follow up with {known_name}", known_names=[known_name])

    assert known_name not in str(raised.value)
