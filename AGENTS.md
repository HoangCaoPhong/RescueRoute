# Repository Instructions for Coding Agents

These instructions apply to the entire repository.

## Read first

Before changing code, read:

1. `README.md` for scope and architecture.
2. `CODING_RULES.md` for language, API, algorithm, data, and test contracts.
3. `CONTRIBUTING.md` for branch, commit, and pull request rules.
4. Relevant source documents indexed by `docs/README.md` when a requirement is unclear.

## Architecture boundaries

- Keep graph and routing logic independent from FastAPI, Supabase, Leaflet, and external APIs.
- Put each two-location algorithm in its own folder under `backend/app/algorithms/graph_search/`.
- Put each multi-location or stochastic algorithm in its own folder under `backend/app/algorithms/optimization/`.
- Mirror every algorithm folder under `backend/tests/unit/algorithms/` and follow its local README.
- Put use-case orchestration in `backend/app/services/`, not in route handlers.
- Access databases and files through repositories; access third-party services through integrations.
- Keep feature-specific frontend code under `frontend/src/features/` and shared primitives under `frontend/src/components/`.

## Change discipline

- Preserve source documents in `docs/`; record new decisions in Markdown files.
- Do not introduce a second graph, cost, or search-result contract for one algorithm.
- Do not add dependencies without explaining their purpose and updating the relevant manifest/lockfile.
- Never add credentials or real user GPS records.
- Make the smallest coherent change and do not rewrite unrelated files.

## Verification

- Add or update tests for behavior changes.
- Algorithm tests must be deterministic and must not call the network.
- Run the narrowest relevant checks first, then the broader suite if available.
- Report checks that could not run and why; do not claim unexecuted tests passed.
