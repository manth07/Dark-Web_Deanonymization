# Rules — What to Use, What to Avoid, AI Boundaries

## 1. `/ai-graph` — Approved Libraries

| Purpose | Use | Avoid |
|---|---|---|
| NLP feature extraction | spaCy | Rolling custom tokenizers from scratch |
| Embeddings | Ollama Python client against local Qwen 3 | Calling any cloud LLM API (breaks offline/no-cost requirement) |
| Similarity | numpy / scikit-learn cosine similarity | Reimplementing vector math by hand |
| Graph writes | official `neo4j` Python driver, parameterized Cypher | String-concatenated Cypher (injection risk — see §3) |
| Schema/validation | `pydantic` for record validation | Untyped dicts passed silently through the pipeline |
| Testing | `pytest` | — |
| Config | `.env` + `python-dotenv` | Hardcoded connection strings |

## 2. What to Avoid Project-Wide

- No hardcoded credentials, ever — including "just for testing," they get
  forgotten and committed.
- No synchronous, un-timeboxed calls to Ollama inside a hot loop — always set
  a timeout and a retry cap (`Error_Handling.md`).
- No raw string-built Cypher — always parameterized queries (`$param`), to
  avoid injection and to keep queries reusable/testable.
- No scraping real dark web sites "just to get real test data quickly" —
  use the synthetic dataset (`Data_sources.md` §5). This is a hard boundary,
  not a style preference.
- No new top-level dependency added without a one-line note in
  `Changelog.md` (keeps the requirements.txt reviewable).

## 3. Boundaries for AI Coding Assistants (Claude Code / Copilot / etc.)

- Only edit files inside the folder you were asked to work in
  (`Master_rules.md` §2 Rule 1). Do not "helpfully" fix something in another
  folder — flag it instead.
- Never fabricate results, sample outputs, or demo numbers. If a script
  hasn't been run, say so instead of inventing plausible-looking output.
- Never silently change the Neo4j schema — any node/relationship/property
  change must be reflected in `Data_model.md` in the same task.
- Always update `Memory.md` at the end of a working session: what was
  completed, what's in progress, what decision is pending.
- Ask before adding a new dependency, changing the Docker base image, or
  altering the record schema in `Scraping_spec.md` / `API_Contracts.md` —
  these ripple into other folders.
- When uncertain about a design choice affecting another module's contract,
  stop and ask rather than guessing and moving on.

## 4. Style

- Python: `black` formatting, `ruff` linting, type hints on public
  functions/methods.
- Docstrings on every pipeline stage function (`features/`, `embeddings/`,
  `resolution/`, `graph/`) explaining input/output shape — this doubles as
  onboarding material for teammates reading into `/ai-graph`.
