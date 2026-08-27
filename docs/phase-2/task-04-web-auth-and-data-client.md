# P2-T04 — Web Authentication and Data Client

**Status:** Implemented; hosted Auth verification pending  
**Full estimate:** 1 hour  
**16-hour path:** 20 minutes  
**Dependencies:** Phase 1 hosted Auth, P2-T03 response contracts

## Objective

Connect Next.js to a real Supabase session and send the caller's short-lived
access token to FastAPI through one typed client boundary.

## Required work, in order

1. Add browser and server Supabase client helpers appropriate to App Router.
2. Add a compact demo sign-in route using the hosted synthetic accounts.
3. Add session-aware navigation and sign-out.
4. Create a typed API client that attaches `Authorization: Bearer`.
5. Handle expired sessions and redirect to sign-in without exposing token text.
6. Add local/deployment API base URL configuration.
7. Test token attachment, authentication failures, and redirection.

## Must be done

- A role switch must obtain a real Supabase session; it cannot alter only local state.
- Tokens must not be logged, rendered, or placed in URLs.
- The browser must never receive the service-role key.
- API parsing must reject unexpected response shapes safely.

## Optional

- Passwordless sign-in.
- Development-only one-click account labels.
- TanStack Query if installation and setup time remains justified.

## Acceptance criteria

- [ ] Staff, clinician, patient, and admin can establish real sessions.
- [ ] FastAPI receives the user's access token on authenticated requests.
- [ ] Sign-out removes the usable browser session.
- [ ] An expired or absent session reaches an understandable sign-in state.
- [ ] No privileged credential is present in the client bundle.
- [ ] API error handling distinguishes forbidden, not found, and unavailable states.

## Evidence

- Auth route/components
- Supabase session helpers
- Typed API client tests
- Browser network verification against the hosted environment

## Done when

The web application can exercise the same caller-scoped path proven by the
backend and RLS tests.
