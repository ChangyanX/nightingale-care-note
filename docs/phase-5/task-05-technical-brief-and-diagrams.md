# P5-T05 — Technical Brief and Diagrams

**Status:** Pending
**Full estimate:** 1.5 hours
**16-hour path:** 40 minutes
**Dependencies:** P5-T01 through P5-T04 evidence

## Objective

Produce the required concise technical brief from verified implementation and
measurements rather than future-looking architecture alone.

## Required work, in order

1. Create a 2-3 page source document and rendered PDF.
2. Add the deployed/logical architecture diagram.
3. Add the complete relationship diagram linking entries, comments, versions,
   highlights, provenance/source records, AI jobs/entries, and adaptive feedback.
4. Explain JWT forwarding, RLS, security-invoker transactions, and worker-only service access.
5. Explain redaction, Groq structured output, exact quote resolution, and clinician review.
6. Include performance method/results and test evidence.
7. State assumptions, rejected alternatives, limitations, and Phase 6 deferral.
8. Render and visually inspect every page before delivery.

## Must be done

- Diagrams match actual migrations and modules.
- Seeded AI content is distinguished from the genuine run.
- Data retention, TLS, encryption, and provider responsibilities are accurate.
- No key, token, private URL, or real patient information appears.
- PDF remains legible at ordinary zoom and within 2-3 pages.

## Optional

- Appendix outside the page limit if explicitly allowed.
- Linked interactive schema.

## Acceptance criteria

- [ ] PDF is 2-3 pages and visually verified.
- [ ] Architecture and complete linked data schema are present.
- [ ] RBAC, revisions, provenance, AI pipeline, review, ranking, and performance are explained.
- [ ] Assumptions and trade-offs are honest and implementation-aligned.
- [ ] Every quantitative claim points to evidence.

## Done when

A technical reviewer can understand the system, security model, evidence, and limitations without opening every source file.
