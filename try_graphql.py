"""Eight read-only/error-path checks. Run against seed.sql data."""
import argparse

import httpx


def enroll(course_id: str, student_id: str) -> str:
    return ('mutation { enroll(input: '
            f'{{courseId: "{course_id}", studentId: "{student_id}"}}) '
            '{ enrollment { id } userErrors { code } } }')


def first_error(body) -> str:
    return body["errors"][0]["message"].split(". Did you")[0]


CASES = [
    ("courses(limit: 2)", "{ courses(limit: 2) { id } }",
     lambda d: ",".join(c["id"] for c in d["data"]["courses"]), "ai-integration,modern-frontend"),
    ('course(id: "api-design")', '{ course(id: "api-design") { title } }',
     lambda d: d["data"]["course"]["title"], "API Design: REST vs GraphQL"),
    ('course(id: "nope")', '{ course(id: "nope") { title } }',
     lambda d: str(d["data"]["course"]), "None"),
    ("student(id: 2) -> courses", "{ student(id: 2) { enrollments { course { id } } } }",
     lambda d: str(len(d["data"]["student"]["enrollments"])), "3"),
    ("enroll twice", enroll("ai-integration", "3"),
     lambda d: d["data"]["enroll"]["userErrors"][0]["code"], "ALREADY_ENROLLED"),
    ("enroll: unknown course", enroll("nope", "3"),
     lambda d: d["data"]["enroll"]["userErrors"][0]["code"], "COURSE_NOT_FOUND"),
    ("enroll: unknown student", enroll("web-security", "999"),
     lambda d: d["data"]["enroll"]["userErrors"][0]["code"], "STUDENT_NOT_FOUND"),
    ("unknown field", '{ course(id: "api-design") { titel } }',
     first_error, "Cannot query field 'titel' on type 'Course'"),
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--expected-passes", type=int, default=8,
                        help="Intermediate stages have 4 or 5 implemented cases.")
    args = parser.parse_args()
    passed = 0
    with httpx.Client(base_url=args.base_url, timeout=10, trust_env=False) as client:
        for title, query, pick, expected in CASES:
            response = client.post("/graphql", json={"query": query})
            response.raise_for_status()
            try:
                actual = pick(response.json())
            except (KeyError, IndexError, TypeError):
                actual = "?"
            ok = response.status_code == 200 and actual == expected
            passed += ok
            print(f"{'ok  ' if ok else 'FAIL'} {title:<27} {actual}")
    print(f"{passed} of {len(CASES)} as expected")
    raise SystemExit(passed != args.expected_passes)
