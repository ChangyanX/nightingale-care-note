# Phase 1–4 Optional Deliverables Audit

**Rechecked:** August 28, 2026
**Result:** All optional deliverables have an implemented local code, schema,
test, UI, configuration, or documentation path. Hosted/provider checks remain
separate evidence gates and are never represented as locally proven.

## Phase 1

| Optional deliverable | Status | Evidence |
|---|---|---|
| EditorConfig | Complete | `.editorconfig` |
| Pre-commit hooks | Complete | `.pre-commit-config.yaml` runs hygiene, Ruff, mypy, and web types |
| Dev container | Complete | `.devcontainer/devcontainer.json`, `containers/workspace.Dockerfile`, `compose.yaml` |
| OpenAPI-generated TypeScript client | Complete | `make generate-api`, `docs/openapi.json`, generated `paths`, `generated-client.ts` |
| OpenAPI-generated frontend client (foundation API task) | Complete | Typed generated runtime client is exported by `apps/web/lib/api/generated-client.ts` for incremental endpoint adoption |
| Shared design-token package | Complete | `packages/design-tokens`, consumed by the web stylesheet |
| Container files | Complete | Separate backend/web/workspace Dockerfiles and Compose definition |
| Automatic audit-metadata trigger | Complete | `write_metadata_audit_event` excludes clinical bodies |
| Generated search columns | Complete | Stored patient/entry `tsvector` columns with GIN indexes |
| Database enum types | Complete | Foundation and optional migrations use PostgreSQL enums |
| Pagination beyond a bounded limit | Complete | Cursor timeline and before-version revision pagination |
| Structured access logs | Complete | Metadata-only JSON access middleware |

## Phase 2

| Optional deliverable | Status | Evidence |
|---|---|---|
| Second concern | Complete | Second ranked synthetic concern in local and hosted seeds plus demo story |
| Resolved historical task | Complete | Completed coaching task fixture |
| Mobile content-length guidance | Complete | `docs/demo-patient-story.md` |
| Task category enum | Complete | `care_task_category` and API/UI representation |
| Patient-visible task and acknowledgement | Complete | Columns, consistency constraint, guarded acknowledgement RPC/API |
| Task event history | Complete | `care_task_events` plus automatic change trigger |
| Timeline cursor pagination | Complete | Opaque stable cursor, bounded query, `X-Next-Cursor` |
| Glance ETag/cache headers | Complete | Private ETag and short revalidation cache policy |
| Timeline API filters for entry type, role, and date | Complete | Bounded server-side query parameters |
| Passwordless sign-in | Complete | Explicit user-triggered Supabase OTP flow; no email was sent during implementation |
| Development account labels | Complete | Development-only labels fill synthetic account email |
| TanStack Query | Complete | Shared query client with bounded stale/retry defaults |
| Patient search | Complete | Indexed server query and client search |
| Recently viewed patients | Complete | Five-item device-local history |
| Responsive drawer navigation | Complete | Keyboard-accessible mobile menu |
| Role/type/date filters in the Glance/timeline UI | Complete | Accessible filter toolbar |
| Mobile Glance/timeline layout | Complete | One-column responsive layouts and wrapping guidance |
| Source-span highlighting | Complete | Exact offset validation and `<mark>` rendering |
| Skeleton animation/transitions | Complete | Motion, skeleton, focus, and toast styles |
| Due-date editing | Complete | Optimistic task patch control |
| Task assignment UI | Complete | Unassigned/self assignment control |
| Optimistic UI | Complete | Task and highlight review rollback/error paths |
| Reconnect indicator | Complete | Realtime connecting/connected/offline state |
| Collaborator-change toast | Complete | Metadata-only Realtime change toast |
| Responsive/mobile/keyboard polish | Complete | Visual baselines and keyboard browser test |
| Timeline filters with URL-persisted state | Complete | Search parameters survive refresh/share navigation |

## Phase 3

| Optional deliverable | Status | Evidence |
|---|---|---|
| Inline comment source spans | Complete | Historical-version FK, exact quote trigger, API schema |
| Highlight categories beyond risk | Complete | Six-category taxonomy |
| Mention notification outbox | Complete | Durable idempotent outbox trigger |
| Three-way merge hints | Complete | Server merge-hint endpoint with explicit conflict markers |
| Batched multi-entry revert | Complete | Atomic bounded RPC and API |
| Word-level colored diff | Complete | Server token diff and accessible UI styling |
| Revision pagination | Complete | `before_version` cursor |
| Downloadable audit report | Complete | Metadata-only CSV endpoint |
| Notification delivery | Complete | RLS-protected in-app notification feed/dismissal; no email channel |
| Rich text, reactions, inline comments | Complete | Plain/Markdown format, bounded reactions, exact spans |
| Multiple assignments per thread | Complete | `comment_assignees` and transactional creation RPC |
| Bulk highlight review/reject | Complete | Bounded clinician-only RPC and UI |
| Duplicate/overlap consolidation | Complete | Stable normalized-claim grouping and group IDs |
| Risk-category taxonomy | Complete | API taxonomy plus risk/category UI labels |
| Review keyboard shortcuts | Complete | Arrow selection and `A`/`R` actions |
| Side-by-side historical/current source | Complete | Revision comparison viewer |
| Animated source focus | Complete | Exact-source `:target` focus animation |
| Collaborator activity toast | Complete | Authorized table events trigger refetch and toast |
| Durable mention notifications | Complete | Notification outbox survives disconnected clients |
| Reconnect status | Complete | Manual refresh remains available when disconnected |
| Property-based Unicode spans | Complete | Hypothesis normalization/offset round trips |
| Browser visual regression | Complete | Desktop/mobile Chromium snapshots and keyboard checks |
| Revision/highlight performance measurement | Complete | Bounded deterministic performance test |

## Phase 4

| Optional deliverable | Status | Evidence |
|---|---|---|
| Medical NER for names/locations | Complete | Contextual rules plus configured literal dictionaries |
| Organization identifier dictionaries | Complete | Per-invocation organization dictionary and category counts |
| Reversible encrypted pseudonyms | Complete | Versioned Fernet cipher, expiry, service-only mapping table |
| Queue position | Complete | Deterministic queue-position RPC/API |
| Cancellation before claim | Complete | Requester-only queued-job cancellation |
| Realtime job status | Complete | Job/event publication and patient job feed |
| Medication submodels | Complete | Dose/route/frequency/change/source/confidence contract |
| Model confidence separate from importance | Complete | Strict `model_confidence` independent of rank score |
| Multilingual source metadata | Complete | Strict BCP-47-like `source_language` field |
| Second provider adapter | Complete | Local Ollama OpenAI-compatible adapter and contract test |
| Streaming status stages | Complete | Generating, validating, persisting, completion/failure events plus bounded read API and live stage UI |
| Token-cost dashboard | Complete | Sanitized `GET /provider-usage` aggregation and visible provider/token/latency/cost panel |
| Reviewed patient-facing summary | Complete | Draft domain logic, review table, clinician review RPC/API |
| Encrypted provider request IDs | Complete | Ciphertext-only job column; raw IDs prohibited from browser/logs |
| Bulk reject | Complete | Clinician-only reject-all action uses bounded bulk RPC |
| Duplicate-suggestion grouping | Complete | Normalized-claim and overlapping-span groups |
| Review keyboard shortcuts | Complete | Same clinician-only `A`/`R` controls |
| Per-user preferences | Complete | Profile-isolated table, idempotent authenticated feedback RPC/API, reset, and UI controls |
| Embedding similarity | Complete | Deterministic local 16-dimensional topic embedding/cosine weighting persisted with each preference |
| Preference time decay | Complete | Documented 90-day half-life in domain and SQL decay function |
| Provider latency/cost table | Complete | `docs/provider-latency-and-cost.md` and runtime dashboard |
| Realtime completion animation | Complete | Live job feed and animated queued/processing indicator |
| Second genuine interaction type | Implementation complete | Doctor, nurse, and AI-patient synthetic smoke paths; genuine execution still requires a rotated Groq key or installed Ollama model and is tracked as an external evidence gate |

## Verification boundary

Local implementation completeness does not claim hosted RLS, live provider,
deployed TLS, or genuine-provider execution. Those checks require external
credentials/runtime state. The assistant did not submit, upload, change
repository visibility, or send email while completing this work.
