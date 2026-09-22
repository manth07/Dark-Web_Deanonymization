# GitHub Actions / CI

## 1. Principle

Four folders, four independent CI jobs. A change in `/ai-graph` never
triggers (or blocks on) `/frontend`'s tests, and vice versa — this is what
makes the isolated-folder strategy actually conflict-free at the CI level too.

## 2. Path-Filtered Workflow (example: `.github/workflows/ai-graph.yml`)

```yaml
name: ai-graph CI
on:
  pull_request:
    paths:
      - 'ai-graph/**'
  push:
    branches: [ dev/ai-graph, main ]
    paths:
      - 'ai-graph/**'

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      neo4j:
        image: neo4j:5-community
        env:
          NEO4J_AUTH: neo4j/testpassword
        ports: [ '7687:7687' ]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install -r ai-graph/requirements.txt
      - name: Lint
        run: ruff check ai-graph/
      - name: Unit + integration tests
        run: pytest ai-graph/tests/ -v
        env:
          NEO4J_URI: bolt://localhost:7687
          NEO4J_PASSWORD: testpassword
          OLLAMA_MOCK: "true"
```

Duplicate this pattern per folder: `frontend.yml`, `backend.yml`,
`scraper.yml`, each scoped with its own `paths:` filter.

## 3. Branch Protection

- `main`: require the matching folder's CI job green + 1 review before merge.
- `dev/<folder>`: require the folder's own CI green.

## 4. CODEOWNERS

```
/frontend/  @frontend-owner
/backend/   @backend-owner
/scraper/   @scraper-owner
/ai-graph/  @ai-graph-owner
```

This makes cross-folder PRs require the *owning* teammate's review even if
someone else opens them — enforces Master_rules.md §2 Rule 1 at the platform
level.

## 5. Docker Build Check (optional, recommended near demo day)

Add a `docker-build.yml` that runs `docker compose config` and
`docker compose build` on PRs touching `docker-compose.yml` or any
`Dockerfile`, so a broken container definition never reaches `main`
unnoticed.
