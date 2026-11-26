"""Send the six protection probes; default expectations match the protected server."""
import argparse

import httpx

CYCLE = """query Cycle {
  student(id: 2) {
    enrollments { student { enrollments { student { enrollments { id } } } } }
  }
}"""
ALIASES = "{ " + " ".join(
    f'a{i}: course(id: "api-design") {{ title }}' for i in range(1, 13)
) + " }"
CASES = [
    ("depth 6 (cycle)", CYCLE, "maximum operation depth of 5"),
    ("12 aliases", ALIASES, "12 aliases found. Allowed: 10"),
    ("limit -1", "{ courses(limit: -1) { id } }", "limit must be between 1 and 100"),
    ('id "abc"', '{ student(id: "abc") { name } }', "Invalid ID: 'abc'"),
    ("id of 20 digits", '{ student(id: "99999999999999999999") { name } }', "Unexpected error."),
    ("introspection", "{ __schema { queryType { name } } }", None),
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--observe", action="store_true", help="Print unprotected responses without checking protected expectations.")
    parser.add_argument("--introspection-off", action="store_true")
    args = parser.parse_args()
    failed = 0
    print(f"{'case':<18} {'status':<7} result")
    with httpx.Client(base_url=args.base_url, timeout=20, trust_env=False) as client:
        for title, query, expected in CASES:
            response = client.post("/graphql", json={"query": query})
            response.raise_for_status()
            errors = response.json().get("errors")
            message = errors[0]["message"].split("\n")[0] if errors else "data, no errors"
            if title == "introspection" and args.introspection_off:
                expected = "introspection has been disabled"
            ok = response.status_code == 200 and (
                (expected in message) if expected else not errors
            )
            failed += not ok
            print(f"{title:<18} {response.status_code:<7} {message}")
    raise SystemExit(bool(failed) and not args.observe)
