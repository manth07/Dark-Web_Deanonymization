# Security

## 1. Sensitive Data Handling

This system stores investigative data (wallet addresses, PGP fingerprints,
handles, scraped text). Treat all of it as sensitive:
- Never log full raw text at `INFO` level — reference by `record_id`.
- Never commit sample/real identifiers into git history outside the
  designated `data/sample_texts.json` synthetic fixtures.
- `.onion` addresses and live source identifiers are never stored in plaintext
  in docs or logs — only as opaque hashes (`source_id`), per `Data_sources.md`.

## 2. Secrets Management

- All credentials (Neo4j password, any API keys) live in `.env` files,
  gitignored, with a checked-in `.env.example` per folder showing required
  keys with placeholder values.
- Docker Compose reads secrets from `.env` — never hardcode them in
  `docker-compose.yml`.
- CI secrets (if any) live in GitHub Actions repo secrets, not in workflow
  YAML.

## 3. Network Isolation

- Only the `scraper` container reaches the Tor proxy / dark web. No other
  service (`ai-graph`, `backend`, `frontend`) makes outbound dark-web calls —
  enforced by Docker network segmentation (scraper on its own network,
  everything else on an internal network that has no route to Tor).
- `ai-graph` and `backend` only talk to `neo4j`, `ollama`, and the raw-store
  — all on an internal Docker network, no exposed ports beyond what the
  frontend needs.

## 4. Data at Rest

- Neo4j runs with auth enabled (`NEO4J_AUTH` set from `.env`), never the
  default/no-auth mode, even for local dev.
- Docker volumes for Neo4j/Ollama data are not mounted world-readable.

## 5. Access Control

- Dashboard (`frontend`/`backend`) sits behind basic auth for the demo —
  sufficient for a hackathon prototype, explicitly noted as **not**
  production-grade (see `TRD.md` §7 Out of Scope).

## 6. Docker Hardening (baseline, not exhaustive)

- No `--privileged` containers.
- Pin image versions (`neo4j:5-community`, not `neo4j:latest`).
- Minimal base images for custom containers (`python:3.11-slim`).
- Ollama and Neo4j data volumes are named, not bind-mounted to arbitrary host
  paths.

## 7. Legal/Ethical Boundary (repeated from Data_sources.md deliberately)

This tool is designed for NTRO's lawful investigative mandate: passive
collection and correlation only. No active exploitation, no interaction with
threat actors, no purchases. Development/testing uses synthetic data only —
see `Data_sources.md` §5.
