# P1-T01 — Repository Baseline

**Status:** Implemented  
**Full estimate:** 30 minutes  
**16-hour path:** 15 minutes  
**Dependencies:** None

## Objective

Establish root-level conventions so every later task writes to a predictable location and generated files do not pollute Git history.

## Required work

1. Confirm the outer folder is the Git root.
2. Use `apps/web`, `services/backend`, `supabase`, and `docs` as root-level product directories.
3. Add a root `.gitignore` covering Node, Python, Supabase-local, environment, editor, OS, test, and build artifacts.
4. Add `.env.example` with names only and safe local defaults where appropriate.
5. Add root scripts or a `Makefile` for web, API, tests, lint, and database setup.
6. Add or update the root README with architecture and quick-start placeholders.
7. Preserve the staged nested Spec Kit scaffold until the user explicitly approves flattening or deletion.

## Optional work

- Add EditorConfig.
- Add pre-commit hooks.
- Add a dev-container definition.

## Acceptance criteria

- [ ] Product code is targeted at the Git root, not a second nested repository folder.
- [ ] Secrets, `.DS_Store`, `node_modules`, virtual environments, caches, and local database files are ignored.
- [ ] `.env.example` contains no usable secret.
- [ ] Root commands are named consistently and documented.
- [ ] Existing staged user files have not been overwritten or unstaged.

## Evidence

- `git status --short`
- Root directory listing
- `.gitignore`, `.env.example`, `Makefile`, and README review
