"""Measure the same student screen over REST and GraphQL, without response caching."""
import argparse
import asyncio
import json
from pathlib import Path

import httpx

MY_COURSES = """
query MyCourses($id: ID!) {
  student(id: $id) {
    name
    enrollments { id course { title credits level } }
  }
}
"""


async def rest(client: httpx.AsyncClient, student: int):
    first = await asyncio.gather(
        client.get(f"/students/{student}"),
        client.get(f"/students/{student}/enrollments"),
    )
    for response in first:
        response.raise_for_status()
    codes = [item["courseId"] for item in first[1].json()]
    second = await asyncio.gather(*(client.get(f"/courses/{code}") for code in codes))
    for response in second:
        response.raise_for_status()
    screen = {"name": first[0].json()["name"], "courses": [
        {key: response.json()[key] for key in ("title", "credits", "level")}
        for response in second
    ]}
    return [*first, *second], 2, screen


async def graphql(client: httpx.AsyncClient, student: int):
    response = await client.post("/graphql", json={
        "query": MY_COURSES, "variables": {"id": str(student)}
    })
    response.raise_for_status()
    body = response.json()
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    person = body["data"]["student"]
    if person is None:
        raise RuntimeError("Student not found")
    screen = {"name": person["name"], "courses": [e["course"] for e in person["enrollments"]]}
    return [response], 1, screen


async def main(args):
    print(f"{'':<8} {'requests':<9} {'rounds':<7} {'bytes':<7} SQL queries")
    results = []
    screens = []
    async with httpx.AsyncClient(base_url=args.base_url, timeout=20, trust_env=False) as client:
        for name, run in (("REST", rest), ("GraphQL", graphql)):
            responses, rounds, screen = await run(client, args.student)
            screens.append(screen)
            result = {"api": name, "requests": len(responses), "rounds": rounds,
                      "bytes": sum(len(r.content) for r in responses),
                      "sql_queries": sum(int(r.headers["x-sql-queries"]) for r in responses)}
            results.append(result)
            print(f"{name:<8} {result['requests']:<9} {rounds:<7} {result['bytes']:<7} {result['sql_queries']}")
    if screens[0] != screens[1]:
        raise RuntimeError("REST and GraphQL screens differ")
    if args.json_output:
        Path(args.json_output).write_text(json.dumps({"student": args.student, "measurements": results,
            "same_screen": True, "screen": screens[0]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--student", type=int, default=2)
    parser.add_argument("--json-output")
    asyncio.run(main(parser.parse_args()))
