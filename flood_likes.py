"""Demonstrate that 12 aliased writes are rejected before SQL execution."""
import argparse

import httpx

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--observe", action="store_true", help="Allow the unprotected demonstration to mutate data.")
    args = parser.parse_args()
    operations = " ".join(
        f'a{i}: likeCourse(id: "api-design") {{ course {{ likes }} }}'
        for i in range(1, 13)
    )
    with httpx.Client(base_url=args.base_url, timeout=20, trust_env=False) as client:
        response = client.post("/graphql", json={"query": "mutation { " + operations + " }"})
    response.raise_for_status()
    body = response.json()
    print("HTTP status:", response.status_code)
    if body.get("errors"):
        message = body["errors"][0]["message"]
        print("error:", message)
    else:
        message = ""
        print("likes:", [body["data"][f"a{i}"]["course"]["likes"] for i in range(1, 13)])
    count = int(response.headers["x-sql-queries"])
    print("SQL queries:", count)
    ok = response.status_code == 200 and "12 aliases found. Allowed: 10" in message and count == 0
    raise SystemExit(not ok and not args.observe)
