# Fix: NormalizedTranscript JSON Serialization

## Status
planned

## Problem

CloudWatch error:
```
TypeError: Object of type NormalizedTranscript is not JSON serializable
```

Stack trace:
```
session_stop_handler.py:64 -> finalize_transcript.py:92 -> s3_transcript_repository.py:42 -> s3_client.py:26 -> json/encoder.py
```

The raw transcript (a plain `dict`) saves successfully. The normalized transcript (a frozen dataclass with nested frozen dataclasses) fails when `json.dumps()` is called in `S3Client.put_json`.

## Root Cause

There is a **type mismatch between the port interface and the adapter implementation**.

**The port** (`backend/src/deskai/ports/transcript_repository.py:28-33`) declares:
```python
def save_normalized_transcript(
    self,
    clinic_id: str,
    consultation_id: str,
    normalized: NormalizedTranscript,  # <-- expects a NormalizedTranscript entity
) -> None:
```

**The adapter** (`backend/src/deskai/adapters/storage/s3_transcript_repository.py:33-38`) declares:
```python
def save_normalized_transcript(
    self,
    clinic_id: str,
    consultation_id: str,
    normalized: dict,  # <-- type hint says dict, but actually receives a NormalizedTranscript
) -> None:
```

The adapter then passes `normalized` straight to `S3Client.put_json(key, data)` at line 42, which calls `json.dumps(data)` at `s3_client.py:26`. `json.dumps` cannot serialize:

1. **`NormalizedTranscript`** -- a frozen dataclass (not a dict)
2. **`SpeakerSegment`** -- nested frozen dataclass instances inside `speaker_segments: list[SpeakerSegment]`
3. **`CompletenessStatus`** -- a `StrEnum` (this one is actually JSON-safe since `StrEnum` serializes as a string, but it's worth noting)

The **caller** (`finalize_transcript.py:92-96`) passes the `NormalizedTranscript` entity directly:
```python
self.transcript_repo.save_normalized_transcript(
    clinic_id=clinic_id,
    consultation_id=consultation_id,
    normalized=normalized,  # <-- this is a NormalizedTranscript, not a dict
)
```

The existing **unit tests do not catch this** because:
- `test_s3_transcript_repository.py` passes plain `dict` objects as `normalized`, not actual `NormalizedTranscript` instances
- `test_finalize_transcript_use_case.py` uses a `MagicMock` for `transcript_repo`, so `save_normalized_transcript` is never actually called with a real S3Client underneath

## Fix

The fix must convert the `NormalizedTranscript` dataclass to a dict before passing it to `S3Client.put_json`. There are two options; Option A is the cleanest.

### Option A: Convert in the adapter (recommended)

The adapter is the right place to handle serialization -- it's an infrastructure concern, not a domain concern.

**File: `backend/src/deskai/adapters/storage/s3_transcript_repository.py`**

1. Fix the type hint on `save_normalized_transcript` to accept `NormalizedTranscript` (matching the port), not `dict` (lines 33-38)
2. Import `dataclasses.asdict`
3. Call `dataclasses.asdict(normalized)` before passing to `self._s3.put_json()`

The resulting method:
```python
from dataclasses import asdict

def save_normalized_transcript(
    self,
    clinic_id: str,
    consultation_id: str,
    normalized: NormalizedTranscript,
) -> None:
    key = build_artifact_key(
        clinic_id, consultation_id, ArtifactType.TRANSCRIPT_NORMALIZED
    )
    self._s3.put_json(key, asdict(normalized))
    ...
```

`dataclasses.asdict` recursively converts:
- `NormalizedTranscript` -> dict
- Each `SpeakerSegment` in `speaker_segments` -> dict
- `CompletenessStatus` (StrEnum) -> its string value

No custom encoder needed.

**File: `backend/src/deskai/adapters/storage/s3_transcript_repository.py`**

4. Similarly, `get_normalized_transcript` should return `dict | None` (it already does) -- the return type is fine since downstream consumers (AI pipeline) will work with the dict form. The port says it returns `NormalizedTranscript | None` but that's a separate concern (reconstruction from dict) for a future task if needed.

### What NOT to do

- Do NOT add a `.to_dict()` method to `NormalizedTranscript` -- that would leak infrastructure concerns into the domain entity.
- Do NOT add a custom JSON encoder to `S3Client` -- the client should remain generic.
- Do NOT convert in `finalize_transcript.py` -- the use case should not know about serialization.

## Tests

### 1. New test: adapter receives a real NormalizedTranscript and serializes it

**File: `backend/tests/unit/adapters/storage/test_s3_transcript_repository.py`**

Add a test that passes an actual `NormalizedTranscript` (with nested `SpeakerSegment` instances) to `save_normalized_transcript` and asserts that `put_json` receives a plain `dict` (not a dataclass).

```python
def test_save_normalized_transcript_converts_dataclass_to_dict(self) -> None:
    from deskai.domain.transcription.entities import NormalizedTranscript
    from deskai.domain.transcription.value_objects import SpeakerSegment

    normalized = NormalizedTranscript(
        consultation_id="cons-001",
        provider_name="elevenlabs",
        provider_session_id="sess-001",
        language="pt-BR",
        transcript_text="Paciente relata dor.",
        speaker_segments=[
            SpeakerSegment(
                speaker="speaker_0",
                text="Paciente relata dor.",
                start_time=0.0,
                end_time=2.0,
                confidence=0.9,
            )
        ],
        created_at="2026-04-02T12:00:00+00:00",
        updated_at="2026-04-02T12:00:00+00:00",
    )

    self.repo.save_normalized_transcript(
        clinic_id="clinic-01",
        consultation_id="cons-001",
        normalized=normalized,
    )

    call_args = self.mock_s3_client.put_json.call_args
    stored_data = call_args[0][1]
    assert isinstance(stored_data, dict)
    assert stored_data["consultation_id"] == "cons-001"
    assert isinstance(stored_data["speaker_segments"][0], dict)
    assert stored_data["speaker_segments"][0]["speaker"] == "speaker_0"
```

### 2. Update existing tests

The two existing `save_normalized_transcript` tests in `test_s3_transcript_repository.py` (lines 54-92) pass plain dicts. They should be updated to pass real `NormalizedTranscript` objects instead, since that's what the port and caller actually provide.

### 3. Integration-level: finalize use case test with real repo

Optionally, add or update `test_finalize_transcript_use_case.py` to use a non-mock `S3TranscriptRepository` (with a mocked `S3Client`) to verify the full flow doesn't raise `TypeError`. This would catch the bug at the use-case level.

## Verification

1. Run the updated unit tests -- they must pass
2. Run `json.dumps(dataclasses.asdict(normalized))` manually in a Python REPL with a real `NormalizedTranscript` to confirm no `TypeError`
3. Deploy to dev and trigger a real consultation session stop -- verify the normalized transcript appears in S3 as valid JSON
4. Check CloudWatch logs for `transcript_normalized_saved` without any `TypeError`
