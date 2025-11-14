#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from common import pick_first, pretty_print, request_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a new student via /api/v1/users/students/add.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--full-name", required=True, help="Student full name.")
    parser.add_argument("--city", required=True, help="City of residence.")
    parser.add_argument("--student-card", required=True, help="Student card number.")
    parser.add_argument("--university-id", help="University UUID (optional, auto-selected if omitted).")
    parser.add_argument("--faculty-id", help="Faculty UUID (optional, auto-selected if omitted).")
    parser.add_argument("--group-id", help="Group UUID (optional, auto-selected if omitted).")
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Do not call the API, only show the payload (useful for rehearsing values).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    university_id = args.university_id
    faculty_id = args.faculty_id
    group_id = args.group_id

    chosen_university = None
    chosen_faculty = None
    chosen_group = None

    if not university_id:
        universities = request_json("GET", "/universities")
        chosen_university = pick_first(universities, "universities")
        university_id = chosen_university["id"]

    if not faculty_id:
        faculties = request_json("GET", f"/universities/{university_id}/faculties")
        chosen_faculty = pick_first(faculties, "faculties")
        faculty_id = chosen_faculty["id"]

    if not group_id:
        groups = request_json(
            "GET", f"/universities/{university_id}/faculties/{faculty_id}/groups"
        )
        chosen_group = pick_first(groups, "groups")
        group_id = chosen_group["id"]

    payload = {
        "full_name": args.full_name,
        "city": args.city,
        "student_card": args.student_card,
        "university_id": university_id,
        "faculty_id": faculty_id,
        "group_id": group_id,
    }

    print("ℹ️ Using the following context:")
    if chosen_university:
        print(f"  university: {chosen_university['name']} ({university_id})")
    if chosen_faculty:
        print(f"  faculty: {chosen_faculty['title']} ({faculty_id})")
    if chosen_group:
        label = chosen_group.get("name") or chosen_group.get("code")
        print(f"  group: {label} ({group_id})")

    if args.print_only:
        print("\nRequest payload:")
        pretty_print(payload)
        return

    result = request_json("POST", "/users/students/add", payload=payload)
    print("✅ Student created:")
    pretty_print(result)


if __name__ == "__main__":
    main()
