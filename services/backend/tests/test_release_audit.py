from pathlib import Path

from scripts.release_audit import (
    REQUIRED_TESTS,
    run_audit,
    secret_kinds_in_text,
    tracked_secret_findings,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_secret_detector_returns_categories_without_values() -> None:
    groq_key = "gsk_" + "A" * 40
    service_key = "service-role-value-that-must-not-be-returned"
    text = f"LLM_API_KEY={groq_key}\nSUPABASE_SERVICE_ROLE_KEY={service_key}"

    findings = secret_kinds_in_text(text)

    assert "groq_api_key" in findings
    assert "populated_llm_key" in findings
    assert "populated_service_role" in findings
    assert groq_key not in repr(findings)
    assert service_key not in repr(findings)


def test_current_tracked_files_have_no_key_patterns() -> None:
    assert tracked_secret_findings(REPOSITORY_ROOT) == ()


def test_required_test_inventory_matches_brief_names() -> None:
    assert REQUIRED_TESTS == (
        "services/backend/tests/test_rbac_scope.py",
        "services/backend/tests/test_revision_history.py",
        "services/backend/tests/test_highlight_provenance.py",
        "services/backend/tests/test_concurrent_edits.py",
        "services/backend/tests/test_self_learning_importance.py",
    )


def test_audit_reports_checks_without_embedding_file_contents() -> None:
    checks = run_audit(REPOSITORY_ROOT)

    assert checks
    assert any(check.category == "tracked_secrets" and check.passed for check in checks)
    assert all("gsk_" not in check.detail for check in checks)
