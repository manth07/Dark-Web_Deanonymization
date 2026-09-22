# Testing

## 1. Philosophy

Pragmatic, not exhaustive — this is a hackathon prototype. Cover the logic
that would silently produce *wrong attribution results* (worst possible
failure mode for this system), and skip coverage theater elsewhere.

## 2. `/ai-graph` Test Plan

### Unit tests — feature extraction
- `test_sentence_length()` — known input string → expected avg/variance.
- `test_punctuation_frequency()` — known input → expected frequency dict.
- `test_ngrams()` — known input → expected n-gram set for n=1,2,3.
- Edge cases: empty string, single word, unicode/emoji-heavy text.

### Unit tests — similarity
- `test_cosine_similarity_identical_vectors()` → 1.0
- `test_cosine_similarity_orthogonal_vectors()` → 0.0
- `test_cosine_similarity_zero_vector()` → handled per `Error_Handling.md`
  (returns 0.0, no exception).

### Integration tests — Ollama (mocked)
- Mock the Ollama client (`OLLAMA_MOCK=true` env, see `Github_Actions.md`) so
  CI doesn't need a live model.
- `test_embedding_pipeline_end_to_end()` — sample text → feature vector →
  mocked embedding → similarity score, assert shape/range.

### Integration tests — Neo4j
- Run against a disposable Neo4j test instance (Docker service in CI, or
  Testcontainers locally).
- `test_actor_merge_idempotent()` — writing the same handle twice produces
  one node, not two.
- `test_similarity_edge_written()` — after processing two similar sample
  texts, assert a `SIMILAR_STYLE_TO` edge exists with the expected
  approximate score.

### The core entity-resolution test (most important)
- Uses `data/sample_texts.json`, which contains deliberately-planted
  persona pairs (same writer, different handle).
- `test_entity_resolution_recovers_known_pairs()` — run the full pipeline,
  assert the planted pairs end up linked above the similarity threshold, and
  an unrelated pair does **not**.
- This is the test that proves capability 3 (PRD §5) actually works, and is
  the one to demo live if asked.

## 3. Running Tests

```bash
cd ai-graph
docker compose up -d neo4j        # if not already running
pytest tests/ -v --cov=src
```

## 4. Coverage Target

No hard percentage requirement — but feature extraction and entity
resolution logic (the two things a judge might ask "how do you know this
works?" about) should be fully covered.
