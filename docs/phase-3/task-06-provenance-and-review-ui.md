# P3-T06 — Provenance and Review UI

**Status:** Pending
**Full estimate:** 1 hour
**16-hour path:** 25 minutes
**Dependencies:** P3-T03 through P3-T05

## Objective

Make trust visible: reviewers can understand why a highlight matters, accept or
reject it quickly, and navigate to the exact historical source text.

## Required work, in order

1. Add suggested/accepted/rejected highlight cards with explicit text labels.
2. Show claim, risk level, reason, score explanation, generator, and review state.
3. Add clinician-only accept/reject controls requiring at most two actions.
4. Generate the entry/version/offset deep link from structured provenance.
5. Scroll/focus the timeline source and mark the exact quoted span.
6. Show historical source content when current content has changed.
7. Add missing/invalid-source and forbidden states.

## Must be done

- Status and risk cannot rely on color alone.
- The browser never invents or changes offsets.
- A failed source resolution cannot silently fall back to an entry-only link.
- Admin receives no review controls.

## Optional

- Keyboard shortcuts for review.
- Side-by-side current/historical source display.
- Animated source focus.

## Acceptance criteria

- [ ] Clinician accepts/rejects a suggestion in one or two actions.
- [ ] Highlight displays a concise importance/risk explanation.
- [ ] Source navigation selects the exact quote and historical version.
- [ ] Changed current content still resolves through version history.
- [ ] Invalid provenance is clearly unavailable and never shown as verified.
- [ ] Keyboard focus reaches review controls and source target.

## Evidence

- Highlight/review components
- Provenance resolver UI
- Component and browser tests

## Done when

A reviewer can verify a highlight's meaning and evidence without trusting a black box.
