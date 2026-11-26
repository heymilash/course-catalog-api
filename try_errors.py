import argparse

import httpx

CASES = [
    ("email already taken", "/students",
     {"name": "Aigerim Two", "email": "aigerim@example.com"}, 409, "email-taken"),
    ("already enrolled", "/enrollments",
     {"courseId": "ai-integration", "studentId": 3}, 409, "already-enrolled"),
    ("unknown course", "/enrollments",
     {"courseId": "nope", "studentId": 3}, 404, "course-not-found"),
    ("unknown student", "/enrollments",
     {"courseId": "web-security", "studentId": 999}, 404, "student-not-found"),
    ("name too short", "/students",
     {"name": "N", "email": "n@example.com"}, 422, "validation-error"),
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check REST statuses, Problem Details types and content types on seed data.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    failed = 0
    with httpx.Client(base_url=args.base_url, timeout=10, trust_env=False) as client:
        for title, path, body, expected, slug in CASES:
            response = client.post(path, json=body)
            kind = response.json().get("type", "-").rsplit("/", 1)[-1]
            content_type = response.headers["content-type"].split(";")[0]
            expected_type = "application/problem+json" if slug else "application/json"
            ok = (response.status_code == expected and content_type == expected_type
                  and (slug is None or kind == slug))
            failed += not ok
            mark = "ok  " if ok else "FAIL"
            print(f"{mark} {title:<20} {response.status_code}  {content_type:<25} {kind}")
    print(f"{len(CASES) - failed} of {len(CASES)} as expected")
    raise SystemExit(bool(failed))
