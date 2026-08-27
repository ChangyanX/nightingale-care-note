# P2-T05 — Clinical Shell and Patient Selector

**Status:** Implemented; hosted role walkthrough pending  
**Full estimate:** 1 hour  
**16-hour path:** 20 minutes  
**Dependencies:** P2-T03, P2-T04

## Objective

Create an accessible clinical workspace that identifies the signed-in role and
lets staff, clinicians, and admins navigate only to patients returned by the API.

## Required work, in order

1. Add the authenticated clinical route group and shared navigation.
2. Show the active user's name, clinic membership, and role.
3. Fetch and render the clinic-scoped patient selector.
4. Navigate to `/patients/{patientId}` using stable patient IDs.
5. Add selector loading, empty, forbidden, and retry states.
6. Ensure the patient role reaches a separate patient-safe route.

## Must be done

- The selector uses the API result and never a hard-coded unrestricted patient list.
- The selected patient remains clear after navigation and refresh.
- Role labels and sign-out remain visible without crowding the patient content.
- Keyboard focus and form labels are usable.

## Optional

- Patient search for larger fixtures.
- Recently viewed patients.
- Responsive drawer navigation.

## Acceptance criteria

- [ ] Clinic A users never see Clinic B patients in the selector.
- [ ] Selecting a patient produces a stable, refreshable URL.
- [ ] Empty, forbidden, and API failure states are distinct.
- [ ] Admin is visibly read-only.
- [ ] Patient users cannot enter the clinical workspace.
- [ ] Desktop layout has no overlap or clipped navigation.

## Evidence

- Clinical route layout and selector components
- Component tests for response states
- Hosted cross-role browser check

## Done when

An authenticated reviewer can reliably reach the primary patient record with
their real role and clinic scope visible.
