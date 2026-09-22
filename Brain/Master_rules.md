# Master Rules

**Project:** SIH 26151 — Dark Web Threat Actor De-anonymization
**Organization:** NTRO | **Theme:** Blockchain & Cybersecurity

This is the single source of truth for how the team (human and AI-assisted) works
in this repo. Every other `.md` file is subordinate to this one. If something
conflicts, this file wins.

## 1. Team & Folder Ownership

| Folder      | Owner role                     | Tech stack                              |
|-------------|---------------------------------|------------------------------------------|
| `/frontend` | Dashboard / GUI                 | (owned by frontend teammate)             |
| `/backend`  | API, orchestration, export      | (owned by backend teammate)              |
| `/scraper`  | Tor collection, infra fingerprinting | (owned by scraper teammate)         |
| `/ai-graph` | Stylometry, embeddings, Neo4j   | Python, Ollama, NLTK/spaCy, Neo4j, Docker |

## 2. Golden Rules (non-negotiable)

1. **Work only inside your own folder.** Never edit another folder's code. If you
   need something to change there, open an issue / ping the owner — don't do it
   yourself, even "just this once."
2. **The contract is the schema, not the code.** Cross-folder integration happens
   through documented interfaces (`API_Contracts.md`, `Data_model.md`). Changing
   a schema requires updating that doc *in the same PR*.
3. **No real dark web access without explicit authorization.** All development
   and testing uses sample/synthetic data (`Data_sources.md`). This is an
   NTRO-context OSINT tool — treat it with the same care as any lawful
   investigative system.
4. **Never commit secrets.** `.env` files are gitignored everywhere. See
   `Security.md`.
5. **Every AI-assisted coding session updates `Memory.md`** in the folder it
   worked in, before ending.

## 3. Branching Strategy

- `main` — always demo-able.
- `dev/<folder>` — long-lived per-folder integration branch (e.g. `dev/ai-graph`).
- `feature/<folder>/<short-desc>` — short-lived, PR'd into `dev/<folder>`.
- `dev/<folder>` → `main` only after the folder's tests pass in CI
  (see `Github_Actions.md`) and a teammate reviews the contract-facing changes.

## 4. Commit Convention

```
<folder>: <type>: <short summary>

type = feat | fix | docs | test | chore | refactor
```
Example: `ai-graph: feat: add cosine similarity threshold tuning`

## 5. Definition of Done

A task is "done" only when:
- Code is in the owning folder, tested (`Testing.md`).
- Any schema/contract touched is updated in the matching doc.
- `Memory.md` for that folder reflects the new state.
- `Changelog.md` has an entry under `Unreleased`.

## 6. AI Coding Agent Boundaries

See `Rules.md` §"Boundaries for AI" for the full list. Summary: agents may only
touch their assigned folder, must never fabricate demo data or results, must
ask before adding a new top-level dependency, and must leave `Memory.md`
updated for the next session (human or AI) to pick up cleanly.
