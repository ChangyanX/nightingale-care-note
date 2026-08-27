from datetime import UTC, datetime, timedelta

import pytest
from cryptography.fernet import Fernet

from app.domain.redaction import PseudonymCipher, PseudonymError, redact_for_llm


def test_contextual_ner_and_organization_dictionary_are_redacted() -> None:
    source = "Patient works in Marina Bay and uses Clinic Account ID HFC-9911. Review cough."
    result = redact_for_llm(
        source,
        known_locations=("Marina Bay",),
        organization_identifiers=("HFC-9911",),
    )
    assert "Marina Bay" not in result.text
    assert "HFC-9911" not in result.text
    assert result.safe_metadata()["location"] >= 1
    assert result.safe_metadata()["organization_identifier"] >= 1


def test_reversible_pseudonym_mapping_is_encrypted_expiring_and_versioned() -> None:
    now = datetime(2026, 8, 28, tzinfo=UTC)
    cipher = PseudonymCipher(Fernet.generate_key(), key_version=3)
    mapping = cipher.encrypt("[PSEUDONYM_NAME_1]", "Synthetic Person", now=now)

    assert b"Synthetic Person" not in mapping.ciphertext
    assert mapping.key_version == 3
    assert cipher.decrypt(mapping, now=now + timedelta(hours=1)) == "Synthetic Person"
    with pytest.raises(PseudonymError, match="unavailable"):
        cipher.decrypt(mapping, now=now + timedelta(days=8))
