# Submission Checklist

> **Execution boundary:** This repository may prepare and verify artifacts, but
> the assistant must not submit or upload them, change repository visibility,
> or send email. Every final delivery action in this checklist is user-only.

## Deadline

- **Due:** Friday, August 28, 2026, 5:30 PM SGT/MYT
- The user must complete any desired upload and email before the deadline; do
  not use the deadline as the target time for rendering or uploading.

## Email

- **To:** irakumar@ntngale.com
- **CC:** frank.ng@ntu.edu.sg
- **CC:** carrene.teo@ntu.edu.sg
- **Subject:** `Nightingale 72HR Build — <Your Name>`

## Required attachments and links

- [ ] Repository link or repository zip
- [ ] Working application instructions and, if available, deployed demo link
- [ ] Automated tests with exact run command
- [ ] README with setup and run instructions
- [ ] README explanation of where redaction occurs
- [ ] README explanation of server-side RBAC/RLS enforcement
- [ ] 2-3 page technical brief
- [ ] Architecture diagram and explanation
- [ ] Comprehensive data schema and relationship diagram
- [ ] Assumptions, first-principles reasoning, and scope/trade-off discussion
- [ ] `ATTRIBUTION.txt` listing all external libraries, models, and licenses
- [ ] Demo video link
- [ ] Resume
- [ ] WhatsApp number
- [ ] WeChat ID

## Technical release gate

Run `make release-status` during development and `make release-check` from the
clean final commit. See [Release Status](release-status.md) for evidence that is
still local-only, hosted-only, live-provider, or manual.

- [ ] All required tests pass from documented commands.
- [ ] `test_rbac_scope.py` passes.
- [ ] `test_revision_history.py` passes.
- [ ] `test_highlight_provenance.py` passes with an AI-scribed source.
- [ ] `test_concurrent_edits.py` passes.
- [ ] `test_self_learning_importance.py` passes.
- [ ] `test_data_decay.py` passes if Phase 6 is claimed as implemented.
- [ ] Glance warm-path P95 is at or below 300 ms, or the approximation and limitation are stated precisely.
- [ ] Every Glance highlight resolves to an exact source entry, version, and span.
- [ ] Patient responses contain no internal comments or raw AI-scribed notes.
- [ ] Staff and clinician writes cannot overwrite each other's owned content.
- [ ] Admin clinical access is read-only.
- [ ] Cross-clinic access is denied.
- [ ] Every LLM-bound path applies and verifies redaction first.
- [ ] A genuine LLM-generated AI-scribe flow works in the demo environment.
- [ ] Timeline entries, comments, tasks, and highlight decisions update live for connected authorized users.
- [ ] TLS and encryption-at-rest controls are documented.
- [ ] Logs contain no raw clinical text, unredacted prompts, tokens, or secrets.
- [ ] Repository and demo contain synthetic data only.

## Repository audit

- [ ] No `.env` files or credentials are committed.
- [ ] No Supabase service-role key appears in browser code.
- [ ] No real patient data is present.
- [ ] `.DS_Store`, caches, generated recordings, and local database files are ignored.
- [ ] README links and setup commands work from a fresh clone.
- [ ] Commit history is clear and logically grouped.
- [ ] License and attribution information are complete.
- [ ] Demo accounts use replaceable synthetic credentials.

## Demo rehearsal

- [ ] Scenario A: Top Card is understood in under ten seconds.
- [ ] Scenario A: AI highlight jumps to the exact source span.
- [ ] Scenario B: Staff adds a note, comment, mention, and assignment.
- [ ] Scenario B: Clinician manually highlights an AI-scribed phrase and edits the plan.
- [ ] Scenario B: Revision diff and revert work.
- [ ] Scenario B: Adaptive importance changes after explicit feedback.
- [ ] Scenario C: Multi-date manual and AI history is clear.
- [ ] Scenario C: Ranking and data-decay behavior are explained.
- [ ] Security: patient, read-only admin, and second-clinic denials are demonstrated or covered by tests.
- [ ] A local recording fallback exists if the deployed environment becomes unavailable.

## Final send

- [ ] Replace `<Your Name>` in the subject.
- [ ] Confirm every link is accessible without an unintended private-account dependency.
- [ ] Confirm the repository visibility matches the instructions given to reviewers.
- [ ] Send the email and retain the sent-message timestamp.
