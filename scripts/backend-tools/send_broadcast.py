#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from common import login_by_max_id, pretty_print, request_json, require_max_id  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a broadcast via /api/v1/broadcasts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--title", required=True, help="Broadcast title.")
    parser.add_argument("--message", required=True, help="Broadcast body.")
    parser.add_argument(
        "--faculty-id",
        help="UUID of the faculty to target (optional). If omitted, message goes to all users or the chosen group.",
    )
    parser.add_argument(
        "--group-id",
        help="UUID of the student group to target (optional). Overrides faculty if provided.",
    )
    parser.add_argument(
        "--max-id",
        type=int,
        help="MAX ID of staff/admin account used to authenticate (defaults to ADMIN_MAX_ID env var).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    max_id = require_max_id(args.max_id)
    token = login_by_max_id(max_id)

    payload = {
        "title": args.title,
        "message": args.message,
    }
    if args.group_id:
        payload["group_id"] = args.group_id
    if args.faculty_id:
        payload["faculty_id"] = args.faculty_id

    result = request_json("POST", "/broadcasts", token=token, payload=payload)
    print("✅ Broadcast created:")
    pretty_print(result)


if __name__ == "__main__":
    main()
