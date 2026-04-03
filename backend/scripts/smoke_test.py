#!/usr/bin/env python3
"""Post-deploy smoke test for the DeskAI dev environment.

Hits the live API Gateway endpoints to verify the deployment is healthy.
Exits 0 on success, 1 on any failure.

Usage:
    python scripts/smoke_test.py                        # uses default dev URL
    python scripts/smoke_test.py --api-url https://...  # custom URL
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib import request
from urllib.error import HTTPError, URLError

DEV_API_URL = "https://i0dueykjuc.execute-api.us-east-1.amazonaws.com/dev"

failures: list[str] = []


def _request(
    method: str,
    url: str,
    body: dict | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict]:
    """Make an HTTP request and return (status_code, parsed_body)."""
    data = json.dumps(body).encode() if body else None
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except HTTPError as e:
        raw = e.read().decode()
        return e.code, json.loads(raw) if raw else {}
    except URLError as e:
        return 0, {"error": str(e)}


def check(name: str, passed: bool, detail: str = "") -> None:
    """Record a check result."""
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    if not passed:
        failures.append(name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-deploy smoke test")
    parser.add_argument("--api-url", default=DEV_API_URL)
    args = parser.parse_args()
    base = args.api_url.rstrip("/")

    print(f"Smoke testing: {base}\n")

    # 1. Health check
    status, body = _request("GET", f"{base}/health")
    check("GET /health returns 200", status == 200)
    check(
        "GET /health body has status=healthy",
        body.get("status") == "healthy",
    )

    # 2. Login with bad credentials (should be 401, not 500)
    status, body = _request(
        "POST",
        f"{base}/v1/auth/session",
        body={"email": "smoke@test.com", "password": "FakePass123!"},
    )
    check(
        "POST /v1/auth/session with bad creds returns 401",
        status == 401,
        f"got {status}",
    )

    # 3. Login with missing body (should be 400, not 500)
    status, body = _request("POST", f"{base}/v1/auth/session")
    check(
        "POST /v1/auth/session with empty body returns 400",
        status == 400,
        f"got {status}",
    )

    # 4. Protected endpoint without token (should be 401 from API GW)
    status, body = _request("GET", f"{base}/v1/me")
    check(
        "GET /v1/me without token returns 401",
        status == 401,
        f"got {status}",
    )

    # 5. Forgot password (always 200 — never leaks user existence)
    status, body = _request(
        "POST",
        f"{base}/v1/auth/forgot-password",
        body={"email": "nonexistent@smoke.test"},
    )
    check(
        "POST /v1/auth/forgot-password returns 200",
        status == 200,
        f"got {status}",
    )

    # 6. Unknown route returns 404 (not 500)
    status, body = _request("GET", f"{base}/v1/does-not-exist")
    check(
        "GET /v1/does-not-exist returns 401 or 404",
        status in (401, 404),
        f"got {status}",
    )

    # Summary
    print()
    total = len(failures)
    if total:
        print(f"FAILED: {total} check(s) failed.")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
