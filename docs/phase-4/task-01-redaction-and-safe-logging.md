# P4-T01 — Redaction and Safe Logging

**Status:** Implemented locally  
**Full estimate:** 1.25 hours  
**16-hour path:** 30 minutes  
**Dependencies:** Backend foundation

## Objective

Create one deterministic guard that every LLM-bound text path must use, with
safe diagnostics that reveal categories and counts but never original values.

## Required work, in order

1. Normalize input to Unicode NFC.
2. Replace email addresses, Singapore IC/FIN-style identifiers, labelled IDs,
   phone numbers, dates of birth, labelled addresses, and identifiable names.
3. Accept known patient/participant names from authorized application context.
4. Return redacted text plus category counts containing no raw matches.
5. Rescan the redacted result and fail closed when a supported sensitive pattern remains.
6. Define safe log fields: request/job ID, category counts, duration, and outcome only.
7. Add focused unit tests, including Unicode and overlapping patterns.

## Must be done

- Raw input and matched values do not appear in result metadata or exceptions.
- Known-name matching is case-insensitive and does not require sending names elsewhere.
- Provider code cannot accept an unverified redaction result.
- Empty input and residual supported identifiers fail before provider invocation.
- Documentation states that regex redaction is prototype protection, not production de-identification.

## Optional

- Medical NER for free-form names and locations.
- Organization-specific identifier dictionaries.
- Reversible pseudonyms in a separate encrypted mapping store.

## Acceptance criteria

- [x] Names, IC/FIN numbers, labelled IDs, phones, emails, DOBs, and addresses are covered.
- [x] Redacted text preserves useful clinical wording and Unicode text.
- [x] Results expose only replacement category/count metadata.
- [x] A supported residual pattern causes a fail-closed result.
- [x] `test_redaction.py` passes without network or credentials.
- [ ] A log-review walkthrough confirms that live worker logs contain no raw bodies.

## Done when

Later provider adapters can receive only a verified redaction result and cannot
accidentally log the original transcript through the redaction API.
