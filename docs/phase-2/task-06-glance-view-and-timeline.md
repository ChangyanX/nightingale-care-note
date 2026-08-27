# P2-T06 — Glance View and Timeline

**Status:** Implemented; live visual QA pending  
**Full estimate:** 2 hours  
**16-hour path:** 50 minutes  
**Dependencies:** P2-T03 through P2-T05

## Objective

Render the core patient page so the current situation is understandable above
the fold and the longitudinal source story is easy to scan.

## Required work, in order

1. Build the patient header and compact Glance card skeleton.
2. Render current concern, material risk/recent change, and open action.
3. Attach importance reasons, states, dates, and source links to Glance items.
4. Build the time-ordered timeline with date grouping.
5. Show author, role, entry type, timestamp, visibility, source type, and source
   reference for each entry.
6. Give AI/system, patient, staff, and clinician entries distinct accessible labels.
7. Support deep links from Glance items to timeline entries.
8. Add loading, empty, forbidden, and error states for each major region.

## Must be done

- The first viewport answers what matters and what needs action.
- AI styling must say “AI generated”; color alone is insufficient.
- Patient-provided insight and AI-patient key question are visible in the timeline.
- Source links resolve to an actual rendered timeline item.
- Content remains readable at the target desktop viewport.

## Optional

- Role/type/date filters.
- Mobile layout optimization.
- Highlighting a source span in preparation for Phase 3 provenance controls.
- Skeleton animation and subtle transitions.

## Acceptance criteria

- [ ] The primary patient's concern, risk/change, and action appear without scrolling.
- [ ] Timeline spans multiple dates and required author/source types.
- [ ] Every entry shows author role, type, timestamp, and provenance metadata.
- [ ] AI, patient, staff, and clinician entries remain distinguishable without color.
- [ ] Deep-link navigation focuses or scrolls to the correct source entry.
- [ ] Long text wraps without overlap or horizontal clipping.
- [ ] A timed reviewer check can explain the record in under ten seconds.

## Evidence

- Glance and timeline components
- Component/visual tests
- Desktop screenshot and timed demo note

## Done when

The patient story is useful before note creation, collaboration, or genuine AI
generation is added.
