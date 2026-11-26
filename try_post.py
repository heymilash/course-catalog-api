"""Print the REST student-creation response, including error content type."""
import argparse

import httpx

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("email")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    with httpx.Client(base_url=args.base_url, timeout=10, trust_env=False) as client:
        response = client.post("/students", json={"name": args.name, "email": args.email})
    print(response.status_code, response.headers["content-type"])
    print(response.text)
