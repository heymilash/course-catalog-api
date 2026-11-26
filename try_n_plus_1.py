"""Measure SQL counts for the two nested GraphQL queries."""
import argparse

import httpx

QUERIES = [
    ("students -> enrollments -> course", "{ students { name enrollments { course { title } } } }"),
    ("enrollments -> course, student", "{ enrollments { id course { title } student { name } } }"),
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--expect-sql", nargs=2, type=int, default=[3, 3])
    args = parser.parse_args()
    failed = 0
    with httpx.Client(base_url=args.base_url, timeout=20, trust_env=False) as client:
        for (title, query), expected in zip(QUERIES, args.expect_sql):
            response = client.post("/graphql", json={"query": query})
            response.raise_for_status()
            body = response.json()
            if body.get("errors"):
                raise RuntimeError(body["errors"])
            rows = len(next(iter(body["data"].values())))
            count = int(response.headers["x-sql-queries"])
            failed += count != expected
            print(f"{title:<36} rows: {rows:<3} SQL queries: {count}")
    raise SystemExit(bool(failed))
