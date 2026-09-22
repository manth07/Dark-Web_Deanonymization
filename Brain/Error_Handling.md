# Error Handling

## 1. Global Principles

- Fail **loud** in dev (raise, stack trace visible), fail **soft** in
  demo/prod (log, skip, continue pipeline).
- One bad record must never crash the batch. Isolate per-record processing in
  try/except with structured logging.
- Structured JSON logs: `{timestamp, module, level, record_id, message}`.
- Every module writes logs to `logs/<module>.log` locally (no external log
  shipping needed for the hackathon).

## 2. `/ai-graph` Specific Handling

| Failure | Handling |
|---|---|
| Ollama model unreachable / times out | Retry with exponential backoff (3 attempts). On final failure: log, mark record `status=deferred`, continue to next record — do not block the batch. |
| Text below minimum token threshold | Skip, log at `INFO` (expected/benign, not an error). |
| Malformed record (missing required field) | Reject, log at `WARNING` with `record_id`, write to `data/rejected/`. |
| Neo4j connection failure | Buffer writes in an in-memory/local queue, retry with backoff; if still failing after N attempts, flush queue to `data/pending_writes.jsonl` for replay on next run. |
| Cosine similarity edge case (zero-vector, NaN) | Treat as similarity `0.0`, log at `WARNING`, do not create a `SIMILAR_STYLE_TO` edge. |
| Duplicate MERGE conflict in Neo4j | Not an error — `MERGE` is idempotent by design (see `Data_model.md`); log at `DEBUG` only. |

## 3. Retry Policy (shared default)

```
attempts = 3
backoff = 2^attempt seconds (2s, 4s, 8s)
```

## 4. What Counts as a Blocking Error

Only these should stop a pipeline run entirely:
- Neo4j unreachable at startup (not mid-run).
- Ollama not running at startup and no cached embeddings available.
- Config/schema mismatch that would corrupt data (e.g. required constraint
  missing).

Everything else degrades gracefully and is visible in logs + a per-run
summary (`records_processed`, `records_skipped`, `records_deferred`,
`records_rejected`).

## 5. Demo-Day Note

Before a demo run, always check `data/pending_writes.jsonl` and
`data/rejected/` are empty/expected — a full pipeline run should leave a clean
summary.
