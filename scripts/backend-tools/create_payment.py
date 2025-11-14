#!/usr/bin/env python3
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from common import login_by_max_id, pretty_print, request_json, require_max_id  # noqa: E402


def parse_amount(value: str) -> int:
    try:
        dec = Decimal(value)
    except InvalidOperation as exc:  # pragma: no cover - CLI validation
        raise argparse.ArgumentTypeError(f"Invalid amount '{value}'") from exc
    cents = int((dec * 100).to_integral_value())
    if cents <= 0:
        raise argparse.ArgumentTypeError("Amount must be positive")
    return cents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a payment for the authenticated user.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--max-id",
        type=int,
        help="MAX ID of the user who should receive the payment (defaults to STUDENT_MAX_ID env var).",
    )
    parser.add_argument(
        "--type",
        choices=["tuition", "dormitory", "event"],
        default="tuition",
        help="Payment type.",
    )
    parser.add_argument(
        "--amount",
        required=True,
        type=parse_amount,
        help="Amount in RUB (e.g. 1500 or 1500.50). Converted to kopeks automatically.",
    )
    parser.add_argument("--period", help="Optional period description for tuition/dormitory payments.")
    parser.add_argument("--description", help="Optional human-friendly description.")
    parser.add_argument("--event-id", help="Event UUID (required when --type=event).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    env_name = "STUDENT_MAX_ID" if args.type != "event" else "EVENT_USER_MAX_ID"
    max_id = require_max_id(args.max_id, env_name=env_name)
    token = login_by_max_id(max_id)

    if args.type == "event" and not args.event_id:
        raise SystemExit("--event-id is required when --type=event")
    if args.type != "event":
        payload = {
            "payment_type": args.type,
            "amount": args.amount,
            "period": args.period or "2024-2025 учебный год",
            "description": args.description or "Ручной тестовый платеж",
        }
    else:
        payload = {
            "payment_type": args.type,
            "amount": args.amount,
            "event_id": args.event_id,
        }
        if args.description:
            payload["description"] = args.description

    result = request_json("POST", "/payments", token=token, payload=payload)
    print("✅ Payment created:")
    pretty_print(result)


if __name__ == "__main__":
    main()
