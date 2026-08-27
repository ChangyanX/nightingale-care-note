import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_TESTS = (
    "services/backend/tests/test_rbac_scope.py",
    "services/backend/tests/test_revision_history.py",
    "services/backend/tests/test_highlight_provenance.py",
    "services/backend/tests/test_concurrent_edits.py",
    "services/backend/tests/test_self_learning_importance.py",
)
REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "ATTRIBUTION.txt",
    "docs/technical-brief/technical-brief.pdf",
    "docs/submission-checklist.md",
    "docs/requirements-traceability.md",
)
FORBIDDEN_TRACKED_ENV_FILES = (
    ".env",
    ".env.hosted-demo",
    "apps/web/.env.local",
)

_SECRET_PATTERNS = {
    "groq_api_key": re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    "generic_api_key": re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "populated_llm_key": re.compile(
        r"(?m)^LLM_API_KEY[ \t]*=[ \t]*[^ \t\r\n<#][^ \t\r\n#]*[ \t]*$"
    ),
    "populated_service_role": re.compile(
        r"(?m)^SUPABASE_SERVICE_ROLE_KEY[ \t]*=[ \t]*"
        r"[^ \t\r\n<#][^ \t\r\n#]*[ \t]*$"
    ),
}


@dataclass(frozen=True, slots=True)
class AuditCheck:
    category: str
    name: str
    passed: bool
    detail: str


def secret_kinds_in_text(text: str) -> tuple[str, ...]:
    """Return category names only; never return the matching credential."""

    return tuple(name for name, pattern in _SECRET_PATTERNS.items() if pattern.search(text))


def tracked_files(repository_root: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    return tuple(path for path in result.stdout.decode().split("\0") if path)


def tracked_secret_findings(repository_root: Path) -> tuple[tuple[str, str], ...]:
    findings: list[tuple[str, str]] = []
    for relative_path in tracked_files(repository_root):
        path = repository_root / relative_path
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend((relative_path, kind) for kind in secret_kinds_in_text(text))
    return tuple(findings)


def run_audit(repository_root: Path = REPOSITORY_ROOT) -> list[AuditCheck]:
    tracked = set(tracked_files(repository_root))
    checks = [
        AuditCheck(
            "required_test",
            path,
            (repository_root / path).is_file(),
            "present" if (repository_root / path).is_file() else "missing",
        )
        for path in REQUIRED_TESTS
    ]
    checks.extend(
        AuditCheck(
            "required_artifact",
            path,
            (repository_root / path).is_file(),
            "present" if (repository_root / path).is_file() else "missing",
        )
        for path in REQUIRED_FILES
    )
    checks.extend(
        AuditCheck(
            "forbidden_tracked_file",
            path,
            path not in tracked,
            "not tracked" if path not in tracked else "tracked",
        )
        for path in FORBIDDEN_TRACKED_ENV_FILES
    )

    secret_findings = tracked_secret_findings(repository_root)
    checks.append(
        AuditCheck(
            "tracked_secrets",
            "tracked credential patterns",
            not secret_findings,
            (
                "none detected"
                if not secret_findings
                else ", ".join(f"{path} ({kind})" for path, kind in secret_findings)
            ),
        )
    )

    seed = repository_root / "supabase/seed.sql"
    seed_text = seed.read_text(encoding="utf-8") if seed.is_file() else ""
    synthetic_markers_present = "nightingale.local" in seed_text and '"synthetic":true' in seed_text
    checks.append(
        AuditCheck(
            "synthetic_data",
            "synthetic seed markers",
            synthetic_markers_present,
            "present" if synthetic_markers_present else "missing",
        )
    )

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    checks.append(
        AuditCheck(
            "repository_state",
            "clean working tree",
            not status.stdout.strip(),
            "clean" if not status.stdout.strip() else "uncommitted changes present",
        )
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Nightingale release evidence safely")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when any release check is incomplete",
    )
    arguments = parser.parse_args()
    checks = run_audit()
    for check in checks:
        status = "PASS" if check.passed else "OPEN"
        print(f"{status:4}  {check.category:24}  {check.name}: {check.detail}")
    open_count = sum(not check.passed for check in checks)
    print(f"\nRelease audit: {len(checks) - open_count} passed, {open_count} open")
    return 1 if arguments.strict and open_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
