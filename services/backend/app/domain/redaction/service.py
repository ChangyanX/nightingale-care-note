import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from re import Pattern
from typing import Final


class RedactionError(ValueError):
    """Fail-closed error whose message never contains source clinical text."""


class RedactionCategory(StrEnum):
    NAME = "name"
    IDENTITY_NUMBER = "identity_number"
    PHONE = "phone"
    EMAIL = "email"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "address"


@dataclass(frozen=True, slots=True)
class RedactionFinding:
    category: RedactionCategory
    count: int


@dataclass(frozen=True, slots=True)
class VerifiedRedaction:
    """Provider-safe text and non-sensitive diagnostic counts."""

    text: str
    findings: tuple[RedactionFinding, ...]
    verified: bool = True

    def safe_metadata(self) -> dict[str, int | bool]:
        return {
            "verified": self.verified,
            **{finding.category.value: finding.count for finding in self.findings},
        }


@dataclass(frozen=True, slots=True)
class _RedactionRule:
    category: RedactionCategory
    pattern: Pattern[str]


_FLAGS: Final = re.IGNORECASE | re.UNICODE
_RULES: Final = (
    _RedactionRule(
        RedactionCategory.EMAIL,
        re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])", _FLAGS),
    ),
    _RedactionRule(
        RedactionCategory.DATE_OF_BIRTH,
        re.compile(
            r"\b(?:DOB|Date\s+of\s+Birth)\s*[:#-]?\s*"
            r"(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
            r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})\b",
            _FLAGS,
        ),
    ),
    _RedactionRule(
        RedactionCategory.IDENTITY_NUMBER,
        re.compile(
            r"\b(?:Patient\s+ID|NRIC|FIN|IC|MRN|ID)\s*[:#-]?\s*"
            r"[A-Z0-9][A-Z0-9-]{4,19}\b",
            _FLAGS,
        ),
    ),
    _RedactionRule(
        RedactionCategory.IDENTITY_NUMBER,
        re.compile(r"(?<![A-Z0-9])[STFGM]\d{7}[A-Z](?![A-Z0-9])", _FLAGS),
    ),
    _RedactionRule(
        RedactionCategory.PHONE,
        re.compile(r"(?<!\d)(?:\+?65[\s-]?)?[689]\d{3}[\s-]?\d{4}(?!\d)", _FLAGS),
    ),
    _RedactionRule(
        RedactionCategory.ADDRESS,
        re.compile(r"\bAddress\s*:\s*[^\n;]{5,160}", _FLAGS),
    ),
    _RedactionRule(
        RedactionCategory.NAME,
        re.compile(r"\b(?:Patient\s+Name|Name)\s*:\s*[^\n;,]{2,80}", _FLAGS),
    ),
    _RedactionRule(
        RedactionCategory.NAME,
        re.compile(
            r"\b(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z][\w'’-]*"
            r"(?:\s+[A-Z][\w'’-]*){0,3}\b",
            re.UNICODE,
        ),
    ),
)


def _known_name_patterns(known_names: Iterable[str]) -> tuple[Pattern[str], ...]:
    patterns: list[Pattern[str]] = []
    for value in known_names:
        normalized = unicodedata.normalize("NFC", value).strip()
        if len(normalized) < 2:
            continue
        flexible_name = r"\s+".join(re.escape(part) for part in normalized.split())
        patterns.append(re.compile(rf"(?<!\w){flexible_name}(?!\w)", _FLAGS))
    return tuple(patterns)


def _placeholder(category: RedactionCategory) -> str:
    return f"[REDACTED_{category.value.upper()}]"


def verify_redacted_text(text: str, *, known_names: Iterable[str] = ()) -> None:
    """Reject supported sensitive patterns without returning the matching value."""

    for pattern in _known_name_patterns(known_names):
        if pattern.search(text):
            raise RedactionError("Redaction verification failed for category: name")
    for rule in _RULES:
        if rule.pattern.search(text):
            raise RedactionError(
                f"Redaction verification failed for category: {rule.category.value}"
            )


def redact_for_llm(text: str, *, known_names: Iterable[str] = ()) -> VerifiedRedaction:
    """Return verified provider-safe text; never retain raw matches in metadata."""

    normalized = unicodedata.normalize("NFC", text)
    if not normalized.strip():
        raise RedactionError("LLM-bound text must not be empty")

    counts = {category: 0 for category in RedactionCategory}
    redacted = normalized
    normalized_names = tuple(known_names)

    for pattern in _known_name_patterns(normalized_names):
        redacted, count = pattern.subn(_placeholder(RedactionCategory.NAME), redacted)
        counts[RedactionCategory.NAME] += count

    for rule in _RULES:
        redacted, count = rule.pattern.subn(_placeholder(rule.category), redacted)
        counts[rule.category] += count

    verify_redacted_text(redacted, known_names=normalized_names)
    findings = tuple(
        RedactionFinding(category=category, count=count)
        for category, count in counts.items()
        if count > 0
    )
    return VerifiedRedaction(text=redacted, findings=findings)
