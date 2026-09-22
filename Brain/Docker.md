# Docker — `/ai-graph` Local Stack

## 1. Why

Your module depends on two stateful services (Neo4j, Ollama) that are painful
to install natively and vary by OS. Containerizing them means:
- Reproducible on any teammate's/judge's machine — `docker compose up`, no
  manual Neo4j/Ollama install.
- Matches the rest of the team's compose-based setup (`Architecture.md` §4),
  so full-system integration (Phase 6) is just adding your services to the
  shared `docker-compose.yml`.
- Fully offline after model pull — no API keys, no per-call cost, works in a
  venue with bad wifi.

## 2. Services

```yaml
# docker-compose.yml (ai-graph-relevant excerpt)
services:
  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: ${NEO4J_USER}/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'      # optional, useful for graph algorithms
    ports:
      - "7474:7474"   # browser UI
      - "7687:7687"   # bolt
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
      interval: 10s
      retries: 5

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    # GPU (optional, big speedup if available):
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  ai-graph:
    build: ./ai-graph
    depends_on:
      neo4j:
        condition: service_healthy
      ollama:
        condition: service_started
    env_file: ./ai-graph/.env
    volumes:
      - ./ai-graph:/app

volumes:
  neo4j_data:
  ollama_data:
```

## 3. Pulling the Model

The `ollama` image starts empty — pull a model once after first `up`:

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3
# or: docker compose exec ollama ollama pull qwen2.5
```

Log the chosen model in `Memory.md` (Decisions table) so the whole team
knows which one the pipeline expects.

## 4. Local Dev Workflow

```bash
docker compose up -d neo4j ollama
cd ai-graph
python -m src.pipeline --input data/sample_texts.json
```

Scripts talk to `bolt://localhost:7687` (Neo4j) and `http://localhost:11434`
(Ollama) directly when run outside the `ai-graph` container, or to the
service names (`neo4j`, `ollama`) when run inside it — set via `.env`
(`NEO4J_URI`, `OLLAMA_HOST`).

## 5. GPU Note

CPU-only inference is fine at hackathon data scale (hundreds–low thousands of
records). If a GPU is available on the dev/demo machine, uncomment the
`deploy.resources` block above for a meaningful speedup on embedding
generation — not required to hit the demo goals.

## 6. `.env.example` (ai-graph folder)

```
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3
SIMILARITY_THRESHOLD=0.82
```
