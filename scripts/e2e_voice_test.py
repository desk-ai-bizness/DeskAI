#!/usr/bin/env python3
"""End-to-end voice-to-text test through the full DeskAI stack.

Flow: Auth → Create consultation → Start session → Record mic → Stream via WS → End session → Fetch transcript

Usage: python3 scripts/e2e_voice_test.py
"""

import base64
import argparse
import json
import os
import queue
import sys
import threading
import time

import requests
import sounddevice as sd
import websocket

# ─── Configuration ───────────────────────────────────────────────────────────

API_BASE = "https://i0dueykjuc.execute-api.us-east-1.amazonaws.com/dev"
WS_URL = "wss://dzy4cvrae2.execute-api.us-east-1.amazonaws.com/dev"

COGNITO_CLIENT_ID = "47d3uh68af2b4n10c261fkr68k"
COGNITO_REGION = "us-east-1"

SAMPLE_RATE = 16000  # 16kHz mono, optimal for speech recognition
CHANNELS = 1
CHUNK_DURATION_MS = 250  # Send audio every 250ms
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)
DEFAULT_MAX_POLL_ATTEMPTS = int(os.getenv("DESKAI_E2E_MAX_POLL_ATTEMPTS", "60"))
DEFAULT_POLL_INTERVAL_SECONDS = float(os.getenv("DESKAI_E2E_POLL_INTERVAL_SECONDS", "5"))
DEFAULT_INITIAL_WAIT_SECONDS = int(os.getenv("DESKAI_E2E_INITIAL_WAIT_SECONDS", "10"))
DEFAULT_RECORDING_SECONDS = int(os.getenv("DESKAI_E2E_RECORDING_SECONDS", "15"))
DEFAULT_EMAIL = os.getenv("DESKAI_E2E_EMAIL", "gabrielmssantiago@gmail.com")
DEFAULT_PATIENT_ID = os.getenv(
    "DESKAI_E2E_PATIENT_ID",
    "e582d101-90ac-464a-8f5e-c2f8d9076c45",
)

# ─── Step 1: Authenticate ────────────────────────────────────────────────────


def authenticate(email: str, password: str) -> dict:
    """Get tokens via the BFF login endpoint."""
    print(f"\n[1/7] Authenticating as {email}...")
    resp = requests.post(
        f"{API_BASE}/v1/auth/session",
        json={"email": email, "password": password},
    )
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code} - {resp.text}")
        sys.exit(1)
    tokens = resp.json()
    print(f"  OK - token expires in {tokens.get('expires_in', '?')}s")
    return tokens


# ─── Step 2: Create consultation ─────────────────────────────────────────────


def create_consultation(token: str, patient_id: str) -> dict:
    """Create a new consultation."""
    print("\n[2/7] Creating consultation...")
    resp = requests.post(
        f"{API_BASE}/v1/consultations",
        json={
            "patient_id": patient_id,
            "specialty": "general_practice",
            "scheduled_date": "2026-04-04",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 201:
        print(f"  ERROR: {resp.status_code} - {resp.text}")
        sys.exit(1)
    consultation = resp.json()
    cid = consultation["consultation_id"]
    print(f"  OK - consultation_id: {cid}")
    print(f"  Status: {consultation['status']}")
    return consultation


# ─── Step 3: Start session ───────────────────────────────────────────────────


def start_session(token: str, consultation_id: str) -> dict:
    """Start a real-time audio session."""
    print("\n[3/7] Starting session...")
    resp = requests.post(
        f"{API_BASE}/v1/consultations/{consultation_id}/session/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code} - {resp.text}")
        sys.exit(1)
    session = resp.json()
    print(f"  OK - session_id: {session['session_id']}")
    print(f"  WebSocket URL: {session.get('websocket_url', WS_URL)}")
    return session


# ─── Step 4: Connect WebSocket and stream audio ─────────────────────────────


def stream_audio(
    token: str, consultation_id: str, session_id: str, duration_seconds: int = 15
):
    """Record from microphone and stream via WebSocket."""
    print(f"\n[4/7] Recording from microphone ({duration_seconds}s)...")
    print("  Speak now! (pt-BR medical consultation)")
    print("  " + "=" * 50)

    audio_queue = queue.Queue()
    ws_messages = []
    ws_ready = threading.Event()
    chunk_count = [0]

    def on_ws_open(ws):
        # Send session.init
        init_msg = json.dumps(
            {
                "action": "session.init",
                "data": {
                    "consultation_id": consultation_id,
                    "session_id": session_id,
                },
            }
        )
        ws.send(init_msg)
        print("  WebSocket connected, session.init sent")
        ws_ready.set()

    def on_ws_message(ws, message):
        ws_messages.append(message)
        try:
            data = json.loads(message)
            event_type = data.get("event", "")
            if event_type == "transcript.partial":
                text = data.get("data", {}).get("text", "")
                if text:
                    print(f"  [partial] {text}")
            elif event_type == "transcript.final":
                text = data.get("data", {}).get("text", "")
                if text:
                    print(f"  [FINAL] {text}")
            elif event_type == "session.status":
                st = data.get("data", {}).get("status", "")
                print(f"  [status] {st}")
        except json.JSONDecodeError:
            pass

    def on_ws_error(ws, error):
        print(f"  WS ERROR: {error}")

    def on_ws_close(ws, close_status_code, close_msg):
        print(f"  WebSocket closed ({close_status_code})")

    # Connect WebSocket with auth token
    ws_url = f"{WS_URL}?token={token}"
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_ws_open,
        on_message=on_ws_message,
        on_error=on_ws_error,
        on_close=on_ws_close,
    )

    ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
    ws_thread.start()

    # Wait for WebSocket to be ready (Lambda cold start can take 15-20s)
    if not ws_ready.wait(timeout=30):
        print("  ERROR: WebSocket connection timed out after 30s")
        return ws_messages

    time.sleep(1)  # Let session.init process

    # Audio callback
    def audio_callback(indata, frames, time_info, cb_status):
        if cb_status:
            print(f"  Audio status: {cb_status}")
        audio_queue.put(indata.copy())

    # Start recording
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=CHUNK_SAMPLES,
        callback=audio_callback,
    )

    with stream:
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            try:
                chunk = audio_queue.get(timeout=0.5)
                # Convert to base64 and send
                audio_bytes = chunk.tobytes()
                b64_audio = base64.b64encode(audio_bytes).decode("ascii")

                msg = json.dumps(
                    {
                        "action": "audio.chunk",
                        "data": {
                            "chunk_index": chunk_count[0],
                            "audio": b64_audio,
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        },
                    }
                )
                try:
                    ws.send(msg)
                    chunk_count[0] += 1
                except Exception:
                    pass

                elapsed = int(time.time() - start_time)
                if chunk_count[0] % 20 == 0:
                    print(
                        f"  Streaming... {elapsed}s/{duration_seconds}s ({chunk_count[0]} chunks sent)"
                    )

            except queue.Empty:
                continue

    print(f"  Recording complete. Sent {chunk_count[0]} audio chunks.")

    # Send session.stop via WebSocket
    print("\n[5/7] Sending session.stop...")
    try:
        stop_msg = json.dumps(
            {
                "action": "session.stop",
                "data": {"consultation_id": consultation_id},
            }
        )
        ws.send(stop_msg)
        time.sleep(2)  # Wait for response
    except Exception as e:
        print(f"  WS send failed: {e}")

    ws.close()
    return ws_messages


# ─── Step 5: End session via HTTP (fallback) ─────────────────────────────────


def end_session(token: str, consultation_id: str):
    """End the session via HTTP endpoint (fallback to WebSocket stop)."""
    print("\n[6/7] Ending session via HTTP...")
    resp = requests.post(
        f"{API_BASE}/v1/consultations/{consultation_id}/session/end",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Session ended: {data.get('session_id', '?')}")
        print(f"  Duration: {data.get('duration_seconds', '?')}s")
        print(f"  Consultation status: {data.get('status', '?')}")
    else:
        print(f"  Response: {resp.text[:200]}")
    return resp


# ─── Step 6: Check consultation status and transcript ────────────────────────


def check_result(
    token: str,
    consultation_id: str,
    max_poll_attempts: int,
    poll_interval_seconds: float,
) -> bool:
    """Check the consultation status and see if transcript was generated.

    Returns True if processing completed successfully, False otherwise.
    """
    print("\n[7/7] Checking consultation result...")

    # Poll for status change (processing can take a few seconds)
    for attempt in range(max_poll_attempts):
        resp = requests.get(
            f"{API_BASE}/v1/consultations/{consultation_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            print(f"  ERROR: {resp.status_code} - {resp.text[:200]}")
            return False

        data = resp.json()
        current_status = data["status"]
        print(f"  Attempt {attempt + 1}: status = {current_status}")

        if current_status in ("draft_generated", "under_physician_review", "finalized"):
            print("\n  Processing complete!")
            print(f"  Has draft: {data.get('has_draft', False)}")
            print(
                f"  Processing completed at: {data.get('processing', {}).get('completed_at', 'N/A')}"
            )

            # Try to open review to see the generated content
            review_resp = requests.get(
                f"{API_BASE}/v1/consultations/{consultation_id}/review",
                headers={"Authorization": f"Bearer {token}"},
            )
            if review_resp.status_code == 200:
                review = review_resp.json()
                print("\n  === MEDICAL HISTORY ===")
                print(
                    f"  {json.dumps(review.get('medical_history', {}).get('content', {}), indent=2, ensure_ascii=False)[:500]}"
                )
                print("\n  === SUMMARY ===")
                print(
                    f"  {json.dumps(review.get('summary', {}).get('content', {}), indent=2, ensure_ascii=False)[:500]}"
                )
                print(f"\n  === INSIGHTS ({len(review.get('insights', []))}) ===")
                for insight in review.get("insights", [])[:3]:
                    print(
                        f"  - [{insight.get('category')}] {insight.get('description', '')[:100]}"
                    )
            return True

        if current_status == "processing_failed":
            print("\n  Processing FAILED.")
            print(f"  Error: {data.get('processing', {}).get('error_details', 'N/A')}")
            return False

        if current_status == "in_processing":
            print(f"  Still processing... waiting {poll_interval_seconds:.1f}s")
            time.sleep(poll_interval_seconds)
            continue

        # Status is started/recording — session didn't end properly
        if attempt < max_poll_attempts - 1:
            print(f"  Status still '{current_status}', waiting 3s...")
            time.sleep(3)

    print("  Timed out waiting for processing to complete.")
    return False


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="DeskAI end-to-end voice test")
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--patient-id", default=DEFAULT_PATIENT_ID)
    parser.add_argument("--recording-seconds", type=int, default=DEFAULT_RECORDING_SECONDS)
    parser.add_argument("--initial-wait-seconds", type=int, default=DEFAULT_INITIAL_WAIT_SECONDS)
    parser.add_argument("--max-poll-attempts", type=int, default=DEFAULT_MAX_POLL_ATTEMPTS)
    parser.add_argument("--poll-interval-seconds", type=float, default=DEFAULT_POLL_INTERVAL_SECONDS)
    args = parser.parse_args()

    if args.max_poll_attempts < 1:
        print("ERROR: --max-poll-attempts must be >= 1")
        sys.exit(2)
    if args.poll_interval_seconds <= 0:
        print("ERROR: --poll-interval-seconds must be > 0")
        sys.exit(2)
    if args.initial_wait_seconds < 0:
        print("ERROR: --initial-wait-seconds must be >= 0")
        sys.exit(2)
    if args.recording_seconds <= 0:
        print("ERROR: --recording-seconds must be > 0")
        sys.exit(2)

    print("=" * 60)
    print("  DeskAI E2E Voice-to-Text Test")
    print("=" * 60)

    # Get password
    import getpass

    email = args.email
    password = getpass.getpass(f"Password for {email}: ")

    # Step 1: Auth
    tokens = authenticate(email, password)
    access_token = tokens["access_token"]

    # Step 2: Create consultation (use existing patient)
    patient_id = args.patient_id
    consultation = create_consultation(access_token, patient_id)
    consultation_id = consultation["consultation_id"]

    # Step 3: Start session
    session = start_session(access_token, consultation_id)
    session_id = session["session_id"]

    # Step 4: Record and stream (15 seconds)
    print("\n" + "=" * 60)
    print("  RECORDING STARTS NOW — Speak in Portuguese!")
    print("  Simulate a doctor-patient conversation.")
    print("  Example: 'Bom dia, qual e a sua queixa principal?'")
    print("=" * 60)

    stream_audio(
        access_token,
        consultation_id,
        session_id,
        duration_seconds=args.recording_seconds,
    )

    # Step 5: End session via HTTP
    end_session(access_token, consultation_id)

    # Step 6: Wait and check result
    print(f"\n  Waiting {args.initial_wait_seconds}s for processing pipeline...")
    time.sleep(args.initial_wait_seconds)
    success = check_result(
        access_token,
        consultation_id,
        max_poll_attempts=args.max_poll_attempts,
        poll_interval_seconds=args.poll_interval_seconds,
    )

    print("\n" + "=" * 60)
    if success:
        print("  Test PASSED!")
    else:
        print("  Test FAILED!")
    print(f"  Consultation ID: {consultation_id}")
    print(f"  API: {API_BASE}/v1/consultations/{consultation_id}")
    print("=" * 60)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
