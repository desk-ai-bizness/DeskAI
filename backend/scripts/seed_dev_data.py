#!/usr/bin/env python3
"""Seed the DynamoDB dev table with test doctor profiles.

Uses ``DoctorProfileFields.build_item`` as the single source of truth so
that field names in the database always match what the application code
reads.  Run after deploying the dev stack or whenever the schema changes.

Usage:
    python -m scripts.seed_dev_data          # dry-run (prints items)
    python -m scripts.seed_dev_data --apply  # writes to DynamoDB
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import boto3  # noqa: E402

from deskai.adapters.persistence.schema import DoctorProfileFields as F  # noqa: E402

TABLE_NAME = "deskai-dev-consultation-records"
REGION = "us-east-1"

# ── Test doctor profiles ─────────────────────────────────────────────
# Each dict maps to ``DoctorProfileFields.build_item`` kwargs.

SEED_PROFILES = [
    dict(
        identity_provider_id="f458e418-1071-7016-8437-452d7cd811e7",
        doctor_id="f458e418-1071-7016-8437-452d7cd811e7",
        email="danielportotoni@gmail.com",
        full_name="Dr. Daniel Toni",
        clinic_id="clinic-dev-001",
        clinic_name="Clinica Dev",
        plan_type="pro",
        created_at="2026-04-02T21:05:47+00:00",
    ),
    dict(
        identity_provider_id="64f87458-5001-70f0-f546-1a1eec028174",
        doctor_id="64f87458-5001-70f0-f546-1a1eec028174",
        email="daniel@deskai.com.br",
        full_name="Dr. Daniel (DeskAI)",
        clinic_id="clinic-dev-001",
        clinic_name="Clinica Dev",
        plan_type="plus",
        created_at="2026-04-02T21:05:47+00:00",
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed dev DynamoDB data")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write to DynamoDB (default is dry-run)",
    )
    args = parser.parse_args()

    items = [F.build_item(**profile) for profile in SEED_PROFILES]

    if not args.apply:
        print("DRY RUN — these items would be written:\n")
        for item in items:
            print(json.dumps(item, indent=2))
            print()
        print(f"Pass --apply to write {len(items)} items to {TABLE_NAME}")
        return

    table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE_NAME)

    for item in items:
        table.put_item(Item=item)
        print(f"  Seeded {item[F.PK]} / {item[F.SK]}")

    print(f"\nDone. {len(items)} profiles written to {TABLE_NAME}.")


if __name__ == "__main__":
    main()
