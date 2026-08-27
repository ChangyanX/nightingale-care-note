# Requirements Traceability Matrix

This matrix maps the Nightingale Candidate Brief to implementation phases, evidence, and tests. The brief remains the authoritative source if wording differs.

## Product requirements

| Brief requirement | Classification | Planned implementation | Evidence / acceptance |
|---|---|---|---|
| Single shared Care Note per patient | Required | One patient page backed by `care_notes`, versioned sections, entries, tasks, and comments | Phase 2 patient-page acceptance |
| Glance / Top Card readable and actionable in under 10 seconds | Required | Compact current concern, risks, open actions, recent change, and clinician-confirmed items | Timed demo plus Phase 2 acceptance |
| Time-ordered longitudinal timeline | Required | Clinic-scoped timeline across dates and roles | Phase 2 tests and Demo Scenario C |
| Patient and AI-session summaries/key questions | Required | `patient_insight` and `ai_patient_session_summary` entry types | Seed fixture and Phase 2 acceptance |
| Doctor-patient AI-scribed summary | Required | `ai_doctor_consult_summary`, system-authored | Phase 4 genuine AI flow |
| Nurse-patient AI-scribed summary | Required | `ai_nurse_consult_summary`, system-authored through the same ingestion contract | Phase 4 deterministic fixture and schema validation |
| AI-patient pre/post-session summary | Required | `ai_patient_session_summary`, system-authored through the same ingestion contract | Phase 4 deterministic fixture and schema validation |
| Entry metadata | Required | Author role/ID, timestamp, type, visibility, source record, offsets where applicable | Schema constraints and API tests |
| Original-source pointer for every AI-scribed note | Required | `source_records` plus `entries.source_record_id` | Source-resolution test |
| Lightweight real-time role collaboration | Required | Supabase Realtime updates for entries, comments, tasks, and highlight decisions | Two-session integration acceptance |
| Threaded comments with resolve/unresolve | Required project scope | Comment threads and resolution state | Phase 3 acceptance |
| Mentions and assignments | Optional in brief; included in MVP | Clinic-scoped mentions and care-task assignment | Phase 3 acceptance |
| Full revision history | Required | Immutable full snapshots for entries and sections | `test_revision_history.py` |
| View changes since selected version | Required | Compare current state with any selected historical snapshot | Phase 3 acceptance |
| Revert to any prior version | Required | Revert creates a new immutable version | `test_revision_history.py` |
| Smart prioritization | Required | Explainable risk, recency, task, entity, confirmation, and feedback factors | Ranking tests and Glance explanation |
| Fast highlight accept/reject | Required hard constraint | One- or two-action clinician review | Phase 4 acceptance |
| Highlight risk reason | Required hard constraint | Stored `risk_reason` and visible factors | Provenance and UI tests |
| Exact highlight provenance | Required hard constraint | Entry, historical version, offsets, and quoted-text match; invalid suggestions rejected | `test_highlight_provenance.py` |
| Clinician precedence or conflict review | Required | Clinician-confirmed facts outrank AI; unresolved contradictions are flagged | Conflict tests and demo |
| Self-learning importance logic | Bonus; committed | Bounded deterministic weight updates from explicit interactions; no RL | `test_self_learning_importance.py` |
| Hybrid storage / data decay | Bonus; separate milestone | Hot/warm/archive tiers, verified roll-ups, exact source restoration | Phase 6 and `test_data_decay.py` |
| Ambient patient voice capture | Bonus; out of current scope | Architecture note only | Explicit scope statement |
| Ambient clinical voice, diarization, noisy audio, multilingual support | Bonus; out of current scope | Architecture note only | Explicit scope statement |

## Authorization requirements

| Role | Required behavior | Planned policy |
|---|---|---|
| Patient | View own patient-facing summaries and instructions only; no internal comments or raw AI notes | Dedicated patient-safe query/response plus RLS |
| Staff | View/add staff notes; no cross-clinic access | Clinic-scoped read; staff-owned writes; cannot edit clinician sections |
| Clinician | View/edit clinician sections; view staff and all AI-scribed notes; clinic-scoped | Clinician-owned section writes plus clinic-scoped reads |
| Admin | Clinic-scoped oversight | Read-only clinical oversight and membership management; clinical edits require a separate clinician role |

Authorization is enforced in the frontend for usability, FastAPI for operation-level checks, and PostgreSQL RLS for row-level protection. Ordinary user requests preserve the caller's JWT; service-role access is restricted to the worker and setup.

## Technical constraints

| Constraint | Plan | Evidence |
|---|---|---|
| Staff and clinicians cannot overwrite each other's notes | Separate role-owned sections and optimistic concurrency | `test_rbac_scope.py`, `test_concurrent_edits.py` |
| Warm-path Glance P95 at or below 300 ms | Bounded read model, seeded benchmark, at least 100 warm requests | Benchmark report in technical brief |
| Synthetic data only | Deterministic synthetic seed fixtures | Repository audit and README |
| Redact names, IC/ID numbers, and phone numbers before LLM | Deterministic redaction and fail-closed verification implemented; provider boundary pending | `test_redaction.py` |
| Strict redaction for all LLM-bound data streams | One guarded LLM gateway used by all jobs | Integration tests and safe logs |
| TLS in transit | HTTPS/TLS for web, API, database, storage, and LLM connections | Deployment verification |
| Encryption at rest | Provider-managed database and private-object encryption | Technical brief documentation |
| Clean logs | No raw clinical bodies, secrets, or unredacted prompts | Log review test/checklist |

## Required tests

| Test | Required assertions |
|---|---|
| `test_rbac_scope.py` | Cross-role write denial; patient internal-comment and raw-AI denial; cross-clinic isolation |
| `test_revision_history.py` | Version increment; changes since X; revert; metadata-only audit identity/action |
| `test_highlight_provenance.py` | Manual and AI-scribed highlights; exact pointer resolves to entry/version/span |
| `test_concurrent_edits.py` | Different-section edits do not overwrite; same-section conflict is deterministic |
| `test_self_learning_importance.py` | Interaction increases similar future priority; bounded safety floor |
| `test_data_decay.py` | Bonus: safe eligibility, archive verification, restoration, and provenance preservation |

## Deliverables

| Deliverable | Planned location / evidence |
|---|---|
| Working Git repository and clear commits | Repository root and Git history |
| Automated tests and run instructions | Backend/frontend test folders and README |
| README setup, run, redaction, and RBAC explanation | `README.md` |
| 2-3 page technical brief | `docs/technical-brief/` |
| Architecture diagram and explanation | Technical brief |
| Comprehensive linked schema | Technical brief and `docs/blueprint.md` |
| Assumptions and trade-offs | Technical brief |
| `ATTRIBUTION.txt` with libraries, models, licenses | Repository root |
| Demo video | Submission link |
| Resume, WhatsApp number, WeChat ID | Prepared outside source code and included with submission |

## Demo coverage

| Recommended scenario | Planned demonstration |
|---|---|
| A — Glance View and AI Scribe | Staff opens patient, reads Top Card, clicks AI-derived highlight, lands on exact source span |
| B — Collaboration, audit, and learning | Staff note/comment/mention; clinician manual highlight and plan edit; diff and revert; preference-weight change |
| C — Longitudinal context | Multi-date manual/AI history, ranking explanation, and data-decay policy or Phase 6 demo |
| Security extension | Patient internal-access denial, read-only admin, and cross-clinic denial |

## Explicit scope decisions

- Implement one genuine LLM-generated AI-scribe flow.
- Treat lightweight live updates as required real-time behavior.
- Do not implement CRDT-style simultaneous character editing.
- Implement lightweight adaptive importance weighting; do not build a reinforcement-learning system.
- Implement hybrid storage/data decay as a separate Phase 6 milestone after the core submission is stable.
- Keep admin clinical access read-only unless the same user also holds a clinician membership.
- Keep ambient voice capture out of the current implementation scope.
