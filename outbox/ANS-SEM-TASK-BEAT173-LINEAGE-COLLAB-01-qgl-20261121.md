CLASSIFY: L2(qgl SI1语义应答·vinf代铸轨SEMANTIC-RESPONDER-01·覆写权归原线)
# outbox/ANS-SEM-TASK-BEAT173-LINEAGE-COLLAB-01-qgl-20261121.md

应卡: inbox/TASK-BEAT173-LINEAGE-COLLAB-01-qgl-20261121.md
引擎: DEEPSEEK_API_KEY/deepseek-chat usage={"prompt_tokens": 42, "completion_tokens": 695, "total_tokens": 737, "prompt_tokens_details": {"cached_tokens": 0}, "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 42}

I can't implement this because the request assumes a specific codebase, event model ("wake PUT", "HUB recovery", "required tree") that isn't provided in the message. To give you a correct, reviewable change I need the actual code.

Here's what I'd need, and how I'd approach it once I have it:

## What I need from you
1. **Repo access or the relevant files** — specifically:
   - The code path that issues the wake PUT (client + any wrapper/helper).
   - Where wake receipt / acknowledgment is (or should be) read back.
   - The HUB recovery entrypoint and the "required tree" availability check.
2. **Definition of "wake-receipt gap"** — is it:
   - PUT succeeds but status isn't persisted? Or
   - Status persisted only on success, not on failure/timeout? Or
   - Status persisted outside the same transaction/lock as the attempt?
3. **Persistence target** — DB table/row, KV, file, log? Schema and any constraints (idempotency key, attempt ID, timestamp).
4. **"Source and hosted evidence"** — which evidence sources must be recorded/verified (e.g., request ID from client, server-side receipt ID, hosted audit log)? What's the success criterion?
5. **Fail-closed semantics for HUB recovery** — what counts as "required tree unavailable" (specific paths, health check, lock file?), and what's the desired failure mode (refuse to start, return 503, abort recovery and roll back, alert)?
6. **Tests/CI expectations** — existing test harness, lint rules, PR template.

## Design sketch (to confirm, not to apply blindly)
- **Wrap the wake PUT attempt in a single unit of work** so that the persisted status covers all outcomes:
  - `attempt_id` generated before PUT.
  - Persist `pending` → perform PUT → persist `success | failure | timeout` with `attempt_id`, response code, receipt/source evidence ID, and hosted evidence reference.
  - Idempotent upsert keyed on `attempt_id` so retries don't erase the terminal state.
- **Evidence capture**: record both the client-side source (request ID it sent) and the hosted-side receipt (server-returned ID / audit-log ID) on the same record, so the gap is provably closed (no "attempted but no status" rows).
- **HUB recovery kept on a separate path** with an explicit precondition:
  - Check "required tree" availability first; if unavailable → fail closed (return error / refuse to proceed) and do **not** fall through to any best-effort recovery.
  - Recovery must not depend on the wake-receipt persistence path, and vice versa.

## What I'll produce once you share the code
- A minimal diff that persists wake PUT status after the attempt, with evidence fields.
- A separate guard in HUB recovery that fails closed when the required tree is unavailable.
- Tests covering: success, PUT failure, timeout, retry/idempotency, and recovery-blocked-when-tree-missing.

Please paste the relevant files (or point me at the repo/paths) and answer 2–5 above, and I'll write the change.

——qgl SI1语义轨·20261121T034132Z
