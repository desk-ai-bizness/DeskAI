# Fix: Audio Chunk Accumulation

## Status
planned

## Problem

During a 15-second recording session, the e2e test sends ~60 `audio.chunk` WebSocket messages. CloudWatch shows all 60 Lambda invocations execute successfully (HTTP 200), but:

1. **No application-level logs appear** for audio chunks — because the handler logs at `logger.debug` level (line 75 of `audio_chunk_handler.py`), while Lambda Powertools defaults to `INFO`. Every chunk is silently processed.

2. **When `session.stop` fires, `elevenlabs_session_closed` reports `audio_bytes: 0`** — meaning the ElevenLabs provider's in-memory buffer (`_SessionEntry.audio_buffer`) was never populated.

## Root Cause

**The `ElevenLabsScribeProvider` accumulates audio in an in-memory `bytearray` (`_SessionEntry.audio_buffer`), but AWS Lambda is stateless across invocations — each `audio.chunk` invocation may run on a different execution environment, or even when the same warm container handles multiple invocations, the critical issue is the lifecycle mismatch.**

Here is the exact flow that fails:

### Flow Trace

1. **`session.init`** (Lambda invocation #1):
   - `router.py:128-140` — routes to `handle_session_init`
   - `session_init_handler.py:50-55` — calls `transcription_provider.start_realtime_session(session_id, "pt")`
   - `lazy_provider.py:40-41` — lazy-initializes the `ElevenLabsScribeProvider`, calls `start_realtime_session`
   - `elevenlabs_provider.py:70-91` — creates a `_SessionEntry` with empty `audio_buffer` in `self._sessions` dict
   - The `_sessions` dict lives **in the `ElevenLabsScribeProvider` instance**, which lives **in the `Container`**, which lives **in the module-level `_container` global** in `router.py:9`

2. **`audio.chunk`** (Lambda invocations #2 through #61):
   - `router.py:142-154` — routes to `handle_audio_chunk`
   - `audio_chunk_handler.py:65-66` — calls `transcription_provider.send_audio_chunk(session.session_id, audio_bytes)`
   - `elevenlabs_provider.py:93-102` — looks up `self._sessions[session_id]` and extends `audio_buffer`

   **THE BUG**: If the Lambda container for invocation #2+ is different from invocation #1 (cold start), the `_container` global is freshly built. The new `ElevenLabsScribeProvider` has an **empty `_sessions` dict** — `_require_session(session_id)` raises `ProviderSessionError("Unknown session 'xxx'")`.

   But looking at `audio_chunk_handler.py:65`:
   ```python
   if audio_bytes and transcription_provider is not None:
       transcription_provider.send_audio_chunk(session.session_id, audio_bytes)
   ```
   There is **no try/except** around this call. If `send_audio_chunk` raises `ProviderSessionError`, the exception propagates up and the handler returns a 500 error (Lambda unhandled exception), NOT a 200.

   **However**, if all invocations happen on the **same warm container** (likely for ~60 rapid invocations within 15 seconds), then `_container` is reused and `_sessions` persists. In that case, `send_audio_chunk` SUCCEEDS — audio bytes ARE accumulated in memory on the warm container.

3. **`session.stop`** (Lambda invocation #62):
   - `router.py:156-169` — routes to `handle_session_stop`
   - `session_stop_handler.py:39-49` — calls `transcription_provider.finish_realtime_session(session.session_id)`
   - `elevenlabs_provider.py:104-125` — logs `elevenlabs_session_closed` with `audio_bytes: len(entry.audio_buffer)`

   **IF `session.stop` lands on a DIFFERENT container** than the one that accumulated audio, the `_sessions` dict is empty (or was freshly initialized). `_require_session` raises `ProviderSessionError`, which IS caught by the try/except at `session_stop_handler.py:42-49` and logged as `ws_session_stop_provider_finish_failed`. But the log at line 113-118 (`elevenlabs_session_closed`) would never execute in that case.

### Most Likely Scenario

Given the evidence (we DO see `elevenlabs_session_closed` with `audio_bytes: 0`), the stop handler IS finding the session entry. This means:

1. **`session.init` and `session.stop` land on the same warm container** (the `_SessionEntry` was created and found).
2. **But `audio.chunk` invocations land on a DIFFERENT container** (or the same container but the `send_audio_chunk` call silently fails).

Wait — re-reading the handler more carefully: the `audio.chunk` handler at line 65 guards with `if audio_bytes and transcription_provider is not None`. If `audio_bytes` is empty (the base64 decodes to nothing), the send is skipped entirely. Let me check: the e2e test at line 204 sends `base64.b64encode(chunk.tobytes())` — this should always produce non-empty bytes for a real audio chunk.

**The actual most likely root cause is Lambda concurrency**: API Gateway WebSocket routes all go to the same Lambda function (`websocket_handler`), but Lambda can scale horizontally. With ~60 rapid invocations, Lambda spins up multiple concurrent execution environments. The `_container` (and its `ElevenLabsScribeProvider._sessions` dict) is **per-container**. Audio chunks spread across N containers each accumulate partial buffers, but `session.stop` only finds the buffer on whichever container it lands on — which may have received 0 chunks.

### Summary

**Root cause: In-memory audio accumulation in `ElevenLabsScribeProvider._sessions` does not survive across Lambda execution environments. Audio chunks distributed across concurrent Lambda containers are lost when `session.stop` lands on a container that received none (or few) of the chunks.**

This is a fundamental architectural mismatch: the provider was designed for a long-running process (single instance accumulates all audio), but it runs inside stateless Lambda where each invocation may be a different instance.

## Fix

### Option A: Accumulate audio in DynamoDB/S3 (recommended for MVP)

Instead of buffering in-memory, persist each audio chunk to S3 (or DynamoDB if chunks are small enough) keyed by `session_id + chunk_index`, then reassemble at finalization time.

**Step-by-step:**

1. **`backend/src/deskai/adapters/transcription/elevenlabs_provider.py`**:
   - Remove in-memory `audio_buffer` from `_SessionEntry`
   - Add an `S3Client` or storage dependency to the provider
   - `send_audio_chunk`: write chunk to S3 at `audio-chunks/{session_id}/{chunk_index}.bin`
   - `finish_realtime_session`: read all chunks from S3, concatenate, report total bytes
   - `fetch_final_transcript`: read concatenated audio from S3, POST to ElevenLabs API

2. **`backend/src/deskai/handlers/websocket/audio_chunk_handler.py`**:
   - Line 65-66: add try/except around `send_audio_chunk` to handle `ProviderSessionError` when session not found on this container. Either:
     - (a) Re-initialize the session on-demand (call `start_realtime_session` if missing), OR
     - (b) Skip the provider call and just persist to S3 directly (if using Option A)
   - Line 75: change `logger.debug` to `logger.info` so chunk processing is visible in CloudWatch

3. **`backend/src/deskai/container.py`**:
   - Pass `s3_client` to `ElevenLabsScribeProvider` constructor

4. **`backend/src/deskai/adapters/transcription/elevenlabs_provider.py`**:
   - The `_require_session` pattern needs to be either:
     - Replaced with a stateless check (session state in DynamoDB), OR
     - Made resilient by auto-creating the session entry if it doesn't exist (since `session.init` already persisted the session to DynamoDB)

### Option B: Force Lambda concurrency = 1 for WebSocket handler (quick workaround)

Set `reserved_concurrent_executions=1` on the WebSocket Lambda. This guarantees all invocations hit the same container (sequential processing). Downsides: high latency under load, timeout risk for audio chunks.

**File:** `infra/stacks/compute_stack.py` — add `reserved_concurrent_executions=1` to the WebSocket Lambda definition.

### Recommended: Option A

Option A is the correct architectural fix. The MVP docstring in `elevenlabs_provider.py:53-59` already acknowledges this limitation:
> "For the MVP, audio chunks are buffered in-memory... This keeps the adapter stateless-friendly for Lambda while still supporting the port interface for future long-running process upgrades."

The assumption that "stateless-friendly" works is wrong when Lambda scales horizontally.

## Additional Fix: Logging Visibility

**`backend/src/deskai/handlers/websocket/audio_chunk_handler.py:75`**:
```python
# Change from:
logger.debug("ws_audio_chunk_processed", ...)
# To:
logger.info("ws_audio_chunk_processed", ...)
```

This ensures audio chunk processing is visible in CloudWatch at the default INFO level, making future debugging possible.

## Tests

### Unit Tests (TDD — write first)

1. **`test_audio_chunk_handler.py`**: Test that `send_audio_chunk` failure is caught and logged (not silently swallowed)
2. **`test_elevenlabs_provider.py`**: Test S3-backed chunk storage: write N chunks, read back concatenated
3. **`test_elevenlabs_provider.py`**: Test `finish_realtime_session` correctly reports total bytes from S3
4. **`test_elevenlabs_provider.py`**: Test `fetch_final_transcript` reassembles chunks before POSTing
5. **`test_audio_chunk_handler.py`**: Test that audio chunk logging is at INFO level

### Integration Tests

6. Test full flow across simulated separate Lambda invocations (fresh provider instances):
   - Invocation 1: `session.init` (container A)
   - Invocations 2-N: `audio.chunk` (container B — different provider instance)
   - Invocation N+1: `session.stop` (container A — finds all audio in S3)

## Verification

1. Deploy to dev environment
2. Run `scripts/e2e_voice_test.py` with 15-second recording
3. Check CloudWatch: `ws_audio_chunk_processed` logs should appear at INFO level for each chunk
4. Check CloudWatch: `elevenlabs_session_closed` should report `audio_bytes > 0`
5. Check S3: `audio-chunks/{session_id}/` should contain chunk files
6. Verify transcript is generated from the accumulated audio
