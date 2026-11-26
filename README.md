# Course Catalog API - Lab 8

FastAPI, SQLAlchemy 2.1, PostgreSQL, Alembic and Strawberry GraphQL: REST and
GraphQL are two entrances to the same database and application services.
Advanced Web Technologies, Labs 4-8.

Backend: [course-catalog-api](https://github.com/heymilash/course-catalog-api).
Frontend: [course-catalog](https://github.com/heymilash/course-catalog).
Lab 6 SQL: [course-catalog-db](https://github.com/heymilash/course-catalog-db).
The `before-lab8` tag and `lab7-defense` branch preserve Lab 7;
`before-lab7` preserves Lab 5 and `lab4-defense` preserves Lab 4.
Previous instructions: [Lab 7 README](docs/LAB7_README.md).
Russian walkthrough: [LAB8_DEFENSE.md](LAB8_DEFENSE.md).

## How to run

Python 3.11+, PostgreSQL 16+, Node.js and npm are required.
Verified on Windows with Python 3.14.2, PostgreSQL 17.4, SQLAlchemy 2.1.8,
Strawberry 0.341.3, GraphQL-core 3.3.2 and Next.js 16.3.5.

On an empty PostgreSQL server, run once as its administrator in database `postgres`:

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

The public classroom password `change-me` is only an example. Real credentials
belong in ignored local environment files. If this role already exists, reuse it.

From this backend repository, Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set DATABASE_URL to your actual server/database in .env.
python check_db.py
python -m alembic upgrade head
psql -h localhost -p 5432 -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
python check_models.py
python -m alembic check
fastapi dev main.py
```

On macOS/Linux, activate with `source .venv/bin/activate` and use
`cp .env.example .env`. The other commands are the same (your system may call
Python `python3`). Use the same PostgreSQL port and database as DATABASE_URL.
For an empty database, apply migrations directly: **do not stamp it**.
The unchanged chain is `base -> 0001 -> 0002`; no Lab 8 schema migration is needed.
`seed.sql` deletes existing teaching rows and resets identities; it is a deliberate reset.

Open REST docs at **http://localhost:8000/docs** and GraphiQL at
**http://localhost:8000/graphql**. GraphiQL is the interactive editor; ordinary
clients POST a JSON object containing `query` and `variables` to `/graphql`.
`python print_schema.py` prints the SDL without making an introspection request.

In another backend terminal, with .venv active:

```powershell
python try_errors.py
python try_graphql.py
python try_n_plus_1.py
python try_protection.py
python flood_likes.py
python measure.py
```

Expected: REST 5/5, GraphQL 8/8; nested queries 3 and 3 SQL statements;
five safe protection errors and permitted introspection; the flood is rejected
with 0 SQL statements. Measurement needs seed data: student 2 has three enrollments.
Each script accepts `--base-url http://localhost:8008` for another API port and
returns a nonzero process status when its checks fail.

In the **frontend repository**, `course-catalog`:

```powershell
npm ci
# Create .env.local with the API_URL line below.
npm run dev
```

```dotenv
API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

API_URL is used by the new server components. NEXT_PUBLIC_API_URL belongs to
older client components. Local environment files are ignored by Git.
Open **http://localhost:3000/my-courses-rest** and
**http://localhost:3000/my-courses**. They show the same name, three course
titles, credits and levels for student 2. Both use `cache: "no-store"`.
The REST page runs two independent requests in parallel, then three course
requests; the GraphQL page makes one POST. Browser Network sees Next.js page/RSC
requests; the server-to-API calls are in the API log, not browser Fetch/XHR.
`npm run lint` and `npm run build` pass; both pages have the dynamic `Ж’` marker.

### Prepared Windows workspace

| Work | Folder | PostgreSQL | API |
|---|---|---|---|
| Lab 6 | course-catalog-db | localhost:5436, course_catalog | SQL / pgAdmin |
| Preserved Lab 7 | course-catalog-api-lab7 | localhost:5437, course_catalog | 8007 |
| Lab 8 | course-catalog-api | localhost:5437, **course_catalog_lab8** | **8008** |

Lab 8 has a separate database on the prepared Lab 7 PostgreSQL cluster.
The local .env points to it; the portable .env.example retains 5432/course_catalog.
Start PostgreSQL and the Lab 8 API from this repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-Lab8.ps1
```

GraphiQL: http://localhost:8008/graphql. REST: http://localhost:8008/docs.
Leave the server terminal open. `-CheckOnly` checks the connection and Alembic;
`-Database` opens psql using .env. The helper uses the existing isolated local
cluster; fresh installations should follow the generic instructions above.
The frontend .env.local points to http://127.0.0.1:8008 on this computer.
Do not run Lab 6 schema.sql in either migrated database.

### Actual clean-start verification

Only the disposable **course_catalog_lab8** database was backed up, dropped and
recreated. The migrations ran 0001 then 0002; seed.sql restored 6/3/6; model names
and Alembic checks passed. All six scripts above and both frontend pages passed.
Lab 6 and Lab 7 databases were preserved. Actual output:
[clean-start.txt](experiments/lab8/09-clean-start.txt),
[comparison JSON](experiments/lab8/09-clean-comparison.json).
HTTP rendering and server logs were checked. Automated visual browser review
was unavailable because the Windows browser tool could not determine the URL.

## What changed in the API

- `services.py` owns enrollment, student creation, atomic likes and the four
  named constraint errors. It raises ServiceError(code, message) without any
  HTTP or GraphQL dependencies. There is no HTTPException or IntegrityError in main.py.
- `problem.py` translates service codes to RFC 9457 responses:
  `application/problem+json`, with type, title, status, detail and instance.
  Unknown routes and wrong methods use about:blank; the 405 Allow header survives.
  In the core version, Pydantic validation remains FastAPI's JSON 422 response.
- `/graphql` has Course, Student and Enrollment types; courses, course,
  students, student and enrollments queries. Nested fields return only requested data.
  IDs serialize as strings; Python names are converted to camelCase.
  `course` and `student` can return null for missing objects.
- `enroll(input: EnrollInput!)` and `likeCourse(id: ID!)` use the same services
  as REST. The like signature follows the detailed skeleton in step 4.
  Expected failures are in payload.userErrors (code/message), with the object null.
  Unexpected failures and query mistakes are in top-level errors.
- The SQL session and all four DataLoaders are created per request in Context.
  Batch functions group by key value and return one element per requested key,
  in that order: None or [] for a missing key. Related IDs are strawberry.Private
  and absent from Enrollment's public SDL. Successful writes clear relevant caches.
- X-SQL-Queries counts cursor executions for one HTTP request. A mutable
  ContextVar box is shared by that request's tasks/threads, not other requests.
  A cached SQLAlchemy statement is still a database call; this is not a result cache.
- Protection: depth <= 5; <= 10 aliases; list limit 1..100; numeric student IDs
  parsed before queries. Unexpected exception text becomes `Unexpected error.`;
  expected GraphQLError messages and schema validation hints remain visible.
  `GRAPHQL_INTROSPECTION=true` is the default. Set false and restart to reject
  introspection; GraphiQL documentation/autocomplete then cannot inspect the schema.
  This is not authentication, authorization, a rate limiter or a complete query-cost limit.
- GET /students/{student_id} returns a student or a Problem Details 404;
  GET /students/{student_id}/enrollments filters the reusable JOIN query.
  A missing student's enrollment list is empty; fetching the missing student is 404.
  Existing REST course filters, pagination, likes, JOIN lists and statistics remain.

| Event | REST | GraphQL |
|---|---|---|
| Duplicate email | 409, email-taken | Service code EMAIL_TAKEN (createStudent bonus) |
| Duplicate enrollment | 409, already-enrolled | 200, userErrors ALREADY_ENROLLED |
| Missing course/student on enrollment | 404, course-not-found / student-not-found | 200, userErrors COURSE_NOT_FOUND / STUDENT_NOT_FOUND |
| Bad field/argument in query | 404 unknown URL; 422 invalid REST parameter | 200, data null and top-level errors |
| Mutation via GET | Not applicable to REST mutation routes | 400 plain text; no write |

GraphQL's HTTP 200 alone is insufficient: gql checks response.ok **and** body.errors.
GET mutations and malformed protocol requests can return real HTTP 400 responses.
An oversized numeric ID deliberately reaches PostgreSQL in the required masking
experiment; the client gets only `Unexpected error.`, and the full traceback is
available to the developer. GraphQL resolvers use the lab's synchronous SQLAlchemy
session; slow SQL can block the worker event loop (see optional blocking experiment).

## Example queries

In GraphiQL, use the editor for queries and its Variables panel for JSON values.
The My courses query uses `level`, because this database has no instructor field.

```graphql
query MyCourses($id: ID!) {
  student(id: $id) {
    name
    enrollments { id course { title credits level } }
  }
}
```

```json
{"id": "2"}
```

The query returns Daniyar Bekov and three courses: Modern Frontend (5 credits,
intermediate), Backend Foundations (5, intermediate), AI/LLM Integration (5, beginner).

```graphql
mutation Enroll($input: EnrollInput!) {
  enroll(input: $input) {
    enrollment { id enrolledAt course { title } }
    userErrors { code message }
  }
}
```

```json
{"input": {"courseId": "web-security", "studentId": "3"}}
```

First execution creates an enrollment (the generated id and time vary):

```json
{"data":{"enroll":{"enrollment":{"id":"10","enrolledAt":"2026-11-26T08:00:00+05:00","course":{"title":"Web Security Essentials"}},"userErrors":[]}}}
```

This is an illustrative response shape; the actual recorded success is in
[04-successful-mutations.json](experiments/lab8/04-successful-mutations.json).
Repeating the mutation gives the following expected rule error:

```json
{"data":{"enroll":{"enrollment":null,"userErrors":[{"code":"ALREADY_ENROLLED","message":"Student is already enrolled in this course"}]}}}
```

```graphql
mutation {
  likeCourse(id: "api-design") {
    course { id likes }
    userErrors { code message }
  }
}
```

Reset seed data before reproducing the comparison and N+1 measurements. Do not
expect generated identities to be gap-free after failed/rolled-back inserts.

## REST vs GraphQL comparison

Student 2 on clean 6/3/6 seed data, measured locally on 2026-11-26.
Bytes are sums of UTF-8 response bodies, without HTTP headers, compression or TLS.
They are observations, not a claim about every possible REST or GraphQL design.

| Criterion | REST | GraphQL | Source |
|---|---|---|---|
| Requests and rounds per screen | 5 requests, 2 rounds | 1 request, 1 round | measure.py |
| Bytes in responses | 1145 | 339 | 09-clean-comparison.json |
| SQL queries per screen | 5 | 3 | measure.py, X-SQL-Queries |
| SQL growth with more students | Each known-shape JOIN endpoint remains 1 SQL; screen calls grow with course count | Before loaders: 7/7 (3 students), 27/24 (20 students); after: 3/3 in both | Experiments 4-5, try_n_plus_1.py |
| Error in query text | HTTP 404 / 422 | HTTP 200 with errors; client must inspect body | Experiments 1, 8 |
| Repeated enrollment | HTTP 409, application/problem+json | HTTP 200, data.enroll.userErrors | Steps 1, 4 |
| HTTP cache | GET resources can use ordinary HTTP cache semantics if configured | POST is not ordinarily cached by shared caches; persisted GET queries can be cached if configured | Conceptual; not measured; both personal pages use no-store |
| Expensive-query protection | Fixed query shape; bounded page_size | Depth 5, aliases 10, bounded limit, parsed IDs, masking; introspection switch | Experiments 6, 7 |

**Conclusion.** REST is suitable for simple resource reads and writes and existing
clients; it gives direct HTTP status semantics. For the nested My courses screen,
GraphQL reduced 5 requests to 1, 2 rounds to 1 and 1145 bytes to 339.
DataLoaders reduced SQL growth from 27/24 to 3/3 at 20 students.
This benefit requires batching, argument/query protections and correct client
error handling; another purpose-built REST endpoint could also combine data.

## Experiment log

Every row was executed, not copied from the expected output. Temporary changes
were restored; dangerous queries were run only against the local Lab 8 database.
Proofs are under [experiments/lab8](experiments/lab8).

| # | Experiment | What I saw | Cause | How I fixed it |
|---|---|---|---|---|
| 1 | `titel`, then snake_case `is_elective` | HTTP 200, data null, validation errors with Did you mean; REST missing course was 404 | Query checked against camelCase schema before execution | Restored title/isElective; [JSON](experiments/lab8/experiment-01-query-errors.json) |
| 2 | Removed nullable course return annotation | Missing course nulled all data; alias b error erased successful alias a too | Non-null failure propagates to nearest nullable parent | Restored CourseType or None; a survives, b null; [JSON](experiments/lab8/experiment-02-null-propagation.json) |
| 3 | Sent a mutation via GET | 400 plain text, likes unchanged | GET must be safe; mutations require POST | Sent mutation through POST; [JSON](experiments/lab8/experiment-03-get-mutation.json) |
| 4 | Increased 3 students to 20 | Before loaders: 7/7 SQL -> 27/24; after loaders: 3/3 at both sizes | Lazy relationships query per parent; identity map only reuses already-loaded objects | Per-request DataLoaders; reset seed after; [before 3](experiments/lab8/experiment-04-before-3.txt), [before 20](experiments/lab8/experiment-04-before-20.txt), [after 20](experiments/lab8/06-after-loaders-20.txt) |
| 5 | Returned descending raw batch rows | WrongNumberOfResultsReturned (3 keys, 6 rows); another query silently assigned wrong courses to 4 of 6 enrollments | DataLoader distributes by position, not key value | Restored grouping and key-ordered result; [JSON](experiments/lab8/experiment-05-broken-loader.json) |
| 6 | Six dangerous queries and a 12-like mutation, before/after protection | Before: depth/aliases executed, internal SQL leaked; likes 11 -> 23, 24 SQL. After: five safe errors; flood rejected, 0 SQL, likes unchanged | Query shape and arguments were unbounded; original exceptions were exposed | Added limits, checks, masking; [before](experiments/lab8/experiment-06-unprotected.txt), [after](experiments/lab8/experiment-06-protected.txt), [flood](experiments/lab8/experiment-06-flood-after.txt) |
| 7 | Disabled introspection and tried a misspelled field | __schema rejected; ordinary queries and 8/8 checks still worked; typo still disclosed field-name hints | Introspection controls schema discovery, not access to fields/data | Restored true and restarted; [JSON](experiments/lab8/experiment-07-introspection-off.json) |
| 8 | Typo in page query; removed errors check; stopped API | Three HTTP 500 pages: GraphQLRequestError naming titel; TypeError destructuring null; TypeError fetch failed | GraphQL error vs discarded error vs no network response | Restored query and errors check, restarted API; page 200 again; [JSON/log](experiments/lab8/experiment-08-client-errors.json) |

For experiment 4, the two formulas are `1 + N students + distinct courses`
(1+3+3, 1+20+6), and `1 + distinct courses + distinct students`
(1+3+3, 1+6+17). The second list defaults to 20 enrollments, not all 23.
One POST and a quick-looking editor do not reveal the extra database work.
SQL logs: [before](experiments/lab8/experiment-04-before-sql.txt),
[after](experiments/lab8/06-after-loaders-sql.txt).

In experiment 5, returning the wrong length fails loudly; returning the wrong
order can silently attach another course to an enrollment, which is more dangerous.

Experiment 6 exposed table/column names, SQL, parameter values and driver exception
classes for invalid limits/oversized IDs; a nonnumeric ID revealed Python's int()
conversion. Clear checks help clients correct inputs; masking alone would hide
even foreseeable mistakes behind Unexpected error. A depth limit of 2 would break
the legitimate MyCourses query (student -> enrollments -> course has depth 3).
Depth 4 and 5 queries were also tested successfully, and bad limits were rejected
before SQL. Alias limiting is not rate limiting; production needs per-client
limits and authorization as well.

In experiment 7, disabling introspection did not remove validation suggestions.
It cannot replace permissions. In experiment 8, checking only response.ok was
insufficient because the API returned HTTP 200 with errors and data null.

## Decisions

1. **One rules layer.** Enrollment, student creation, atomic likes and constraint
   translation are in services.py so transports cannot drift into different
   business rules. REST maps one code to a status and Problem Details; GraphQL
   maps the same code to userErrors. Unknown failures stay visible to developers.
2. **Per-request loaders and key matching.** Global loaders would cache stale
   objects across requests and could mix users' data. Batch results must be matched
   by key value, with placeholders for missing keys, because SQL row order is not
   input key order; experiment 5 showed both loud and silent failures. Session and
   loaders close/disappear with the request; mutations invalidate affected caches.
3. **Two protection layers.** check_limit and parse_id give actionable messages
   for expected bad arguments without unnecessary database work. MaskErrors hides
   unforeseen exceptions such as bigint overflow while logging their cause;
   replacing every error with a generic message would prevent clients fixing
   ordinary input mistakes. Depth/alias validators reject oversized shapes before SQL.

References: [Strawberry FastAPI integration](https://strawberry.rocks/docs/integrations/fastapi),
[DataLoaders](https://strawberry.rocks/docs/guides/dataloaders),
[Next.js fetch](https://nextjs.org/docs/app/api-reference/functions/fetch).


## Bonus

### 1. Validation errors as Problem Details

Implemented after the core README commit. RequestValidationError supplies
`exc.errors()`; the handler keeps only the location, field path and message.
All REST validation errors now use application/problem+json, status 422,
type `validation-error`, and an `errors` list with `in`, `field`, `detail`.
`errors` is an RFC 9457 extension, not one of its standard members.
With name N and email bad, both issues arrive together; no raw exception object
is serialized. Query validation such as page=0 uses the same format.
The core 422 JSON gap described above is therefore closed in the final version.
try_errors.py still passes 5/5 and now checks validation-error for the fifth case.
Proofs: [before](experiments/lab8/bonus-01-before.json),
[after](experiments/lab8/bonus-01-after.json).
