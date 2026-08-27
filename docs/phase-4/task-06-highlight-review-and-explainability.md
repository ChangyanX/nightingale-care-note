# P4-T06 — Highlight Review and Explainability

**Status:** Pending  
**Full estimate:** 1 hour  
**16-hour path:** 25 minutes  
**Dependencies:** P4-T05, Phase 3 highlights

## Objective

Map model-proposed quotes to immutable source spans and let clinicians accept or
reject suggestions quickly while keeping AI and confirmed states unmistakable.

## Required work, in order

1. Resolve each quote against the NFC-normalized historical source snapshot.
2. Accept only a unique exact match or an unambiguous validated occurrence hint.
3. Store entry, version, half-open offsets, quote, claim, risk reason, score, and AI generator.
4. Discard unmapped/ambiguous suggestions with a safe reason code.
5. Add bounded highlight list and clinician review endpoints.
6. Make review status transitions transactional and audited.
7. Add suggested/accepted/rejected UI with one- or two-action review.
8. Navigate from each visible highlight to the exact historical quote.

## Must be done

- A model quote never becomes a fuzzy or entry-only provenance link.
- Only clinicians can accept/reject; admin stays read-only.
- Suggested AI content is not rendered as clinician-confirmed information.
- Risk and status use text/icons in addition to color.
- Review response triggers authorized Glance/timeline refresh.

## Optional

- Bulk reject.
- Duplicate-suggestion grouping.
- Keyboard shortcuts.

## Acceptance criteria

- [ ] Exact quotes round-trip through Unicode offsets.
- [ ] Missing and ambiguous quotes are rejected.
- [ ] Clinician review takes no more than two interactions.
- [ ] A stale or repeated review cannot create contradictory state.
- [ ] Exact source navigation works after later source edits.
- [ ] `test_highlight_provenance.py` passes for manual and AI highlights.

## Done when

Every surfaced AI suggestion is visibly provisional, explainable, rapidly
reviewable, and resolvable to the exact historical words that support it.
