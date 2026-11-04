# Course Catalog API

FastAPI backend with SQLAlchemy 2.1, PostgreSQL and Alembic migrations (Labs 4-7).
The original Lab 5 state is retained in the Git tag `before-lab7`; Lab 4 is on
the `lab4-defense` branch. Lab 7 continues this repository, not the frontend.

Repository: [course-catalog-api](https://github.com/heymilash/course-catalog-api).
Lab 6 SQL project: [course-catalog-db](https://github.com/heymilash/course-catalog-db).

## How to run

Requires Python **3.11+**, PostgreSQL **16+** and the `psql` client.
Verified with Python **3.14.2**, PostgreSQL **17.4**, SQLAlchemy **2.1.8**,
Alembic **1.20.1** and psycopg **3.3.8**.

On an empty PostgreSQL server, connect to database `postgres` as an administrator
and create the application role and database once:

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

`change-me` is a public classroom password. Real credentials belong in `.env`,
which is ignored by Git. `.env.example` contains only the teaching address.

From this project folder, in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit DATABASE_URL in .env for your PostgreSQL host, port and credentials.
python check_db.py
alembic upgrade head
psql -h localhost -p 5432 -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
python check_models.py
alembic check
fastapi dev main.py
```

For macOS/Linux, activate with `source .venv/bin/activate` and copy the example
with `cp .env.example .env`; the other commands are the same. The psql port must
match `.env`. Settings read environment variables before `.env`, so remove a
temporary `DATABASE_URL` override after experimenting with another database.

Swagger: **http://localhost:8000/docs**. In another terminal with the environment
activated, run `python try_errors.py` (expect **5 of 5 as expected**).
`seed.sql` deletes the lab rows and resets identity counters inside a transaction.
It is repeatable, but is only for a disposable teaching database.

### Prepared Windows workspace: Lab 6 and Lab 7 together

There are two independent local PostgreSQL clusters, both with a database named
`course_catalog`. This keeps the Lab 6 schema available for its separate defense.

| Lab | Project | Database port | What to open |
|---|---|---|---|
| 6 | `course-catalog-db` | 5436 | psql; SQL files; no `level` or Alembic table |
| 7 | `course-catalog-api` | 5437 | Swagger at http://localhost:8007/docs; ORM and migrations |

Lab 7 began with a `pg_dump` copy of the Lab 6 schema and rows, then followed the
existing-database migration procedure. The local `.env` points to **5437** and
has `SQL_ECHO=true` so SQL is visible during the defense. The example retains
the standard port **5432** for other computers.

Start the prepared Lab 7 database and API in PowerShell:

```powershell
cd "C:\Users\77712\Desktop\4 course\WEB\course-catalog-api"
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-Lab7.ps1
```

The script opens **http://localhost:8007/docs** as an address to visit; it keeps
the server running in this terminal. Ctrl+C stops the API. This process-only
execution policy does not change the user's permanent PowerShell policy.

In a second PowerShell terminal:

```powershell
cd "C:\Users\77712\Desktop\4 course\WEB\course-catalog-api"
.\.venv\Scripts\python.exe check_db.py
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe try_errors.py --base-url http://localhost:8007
```

To open the **Lab 7** database in psql using `.env`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-Lab7.ps1 -Database
```

Inside psql use `\dt`, `\d courses`, or `SELECT * FROM alembic_version;`.
Exit with `\q` before running PowerShell commands such as `cd` or `alembic`.
The startup helper can also be checked with `-CheckOnly`.

The Lab 7 cluster files are outside Git at `%LOCALAPPDATA%\CodexLab7Postgres\data`.
It listens only on localhost with password authentication. After reboot, the
helper starts it again. Database rows persist when the API is stopped.
For a local data reset, use the Lab 7 file and port:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5437 -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
```

Do not run Lab 6's `schema.sql` against the migrated Lab 7 database: it would
remove `level` while leaving an incorrect Alembic version marker.

### Verification from a clean database

The Lab 7 database was backed up locally, dropped and recreated on its isolated
server. Then `alembic upgrade head`, `seed.sql` (twice), `check_models.py`,
`alembic check`, the API and `try_errors.py` all passed. Actual outputs are in
[clean-start.txt](experiments/results/clean-start.txt),
[final-error-cases.txt](experiments/results/final-error-cases.txt) and
[acceptance.json](experiments/results/acceptance.json).

HTTP checks covered all eight operations, combined filters, sorting, pagination,
JSON aliases, JOIN results, zero-count statistics, 201/404/409/422 responses,
twelve concurrent likes, and persistence after restarting the API process.
The data was then reset to **6 courses, 3 students, 6 enrollments**. The separate
Lab 6 database was checked too: still 6/3/6 and no `level` column.

## What changed in the API

- PostgreSQL now stores courses, students and enrollments; API restarts do not
  erase them. The old `data.py` and in-memory `ENROLLMENTS` list are removed.
- `models.py` describes database tables; `schemas.py` describes JSON and input
  validation. `from_attributes=True` lets Pydantic read ORM attributes/SQL rows.
- `POST /enrollments` now accepts **courseId + studentId**. Create the student
  first using `POST /students` and use the returned id. Lab 5's frontend form
  sends `studentName` and therefore returns 422 against this API; the frontend
  is intentionally outside this lab's scope.
- `GET /enrollments` joins the three tables and adds `studentName`, `courseTitle`
  and the database-generated `enrolledAt` timestamp.
- Courses have a required `level`; `?level=beginner` returns two seeded elective
  courses, `intermediate` four, and `advanced` none. This core version stores level
  as required text without a default. Enforcing the three allowed labels with
  a CHECK is an optional bonus and is not claimed here.
- Constraint names map duplicate email/enrollment to 409 and missing referenced
  course/student to 404. Short names and invalid emails fail Pydantic with 422;
  unknown database constraint violations remain 500 errors.
- Prior query validation (`page >= 1`, `1 <= page_size <= 100`, sort values) and
  case-insensitive title search `q` are preserved. Search escapes `%` and `_` so
  they are literal substring characters, not unexpected SQL wildcards.

| Method | Route | Result |
|---|---|---|
| GET | `/` | Health message |
| GET | `/courses` | SQL filtering, sorting and pagination |
| GET | `/courses/{course_id}` | One course or 404 |
| POST | `/courses/{course_id}/like` | Atomic increment, 200 or 404 |
| POST | `/students` | Student, 201; duplicate email 409 |
| POST | `/enrollments` | Enrollment, 201; duplicate pair 409; missing FK 404 |
| GET | `/enrollments` | Enrollment details from two JOINs |
| GET | `/stats/courses` | LEFT JOIN counts, including zero |

Example request bodies:

```json
{"name": "Nurlan Abenov", "email": "nurlan@example.com"}
```

```json
{"courseId": "web-security", "studentId": 4}
```

Use the actual returned student id, which may differ after experiments.

## Migrations

Run Alembic from the project root, where `alembic.ini` is located.
The final chain has one head: **base -> 0001 -> 0002**.

| Command | What it does |
|---|---|
| `alembic upgrade head` | Applies missing migrations |
| `alembic downgrade -1` | Runs the latest downgrade; dropping a column loses its values |
| `alembic current` | Shows the database's recorded revision |
| `alembic history` | Shows the revision chain |
| `alembic heads` | Shows the latest revision(s) in the files |
| `alembic revision --autogenerate -m "text"` | Generates a draft from metadata vs. database; review before applying |
| `alembic check` | Fails if detectable model/schema differences remain |
| `alembic upgrade 0001:0002 --sql` | Prints migration SQL without running it |
| `alembic stamp head` | Changes only the version marker; never verifies or builds the schema |

`0001` creates the three tables, named constraints, identity columns and student
index. It was autogenerated against empty `scratch`, upgraded and checked there;
scratch was then removed. Applying it to the existing Lab 6 copy produced the
expected DuplicateTable error, without changing the data. We then used
**`alembic stamp 0001`** and checked the match.

When adopting a new Lab 6 database now, stamp **0001**, not `head`: the current
head is already 0002, which contains a column Lab 6 does not have. First verify
the original schema, stamp its matching revision, then run `upgrade head`.
For a genuinely empty database, use `upgrade head` directly; do not stamp it.

`0002` adds nullable `level`, fills existing rows (`beginner` for electives,
`intermediate` otherwise), then sets NOT NULL. Its downgrade drops only that
column. The SQL was reviewed and the upgrade/downgrade/upgrade cycle was run.
See [migration-cycle.txt](experiments/results/migration-cycle.txt) and
[migration-0002-sql.txt](experiments/results/migration-0002-sql.txt).

`alembic check` is not a complete proof of schema equivalence: some differences,
including CHECK changes under the default configuration, need manual review.
`check_models.py` additionally compares names and reads the mapped rows; it does
not prove that every named CHECK has the intended expression.

## Experiment log

These experiments were actually executed on the isolated Lab 7 setup. All
temporary source/schema changes were restored before the final checks.

| # | Experiment | What I saw | Cause | How I fixed it |
|---|---|---|---|---|
| 1 | Changed `uq` naming template | Model-only `students_email_unique`, `enrollments_course_id_unique`; original names database-only | Model names no longer matched PostgreSQL | Restored `%(table_name)s_%(column_0_N_name)s_key`; both differences `none` |
| 2 | Removed `Field(min_length=2)`, sent name N | HTTP 500; IntegrityError / CheckViolation for `students_name_check` | Invalid name reached the database; this unknown violation is treated as a code bug | Restored Pydantic validation; 422 again |
| 3 | Changed map key to `students_email_uniq` | HTTP 500; UniqueViolation actually named `students_email_key` | Error mapping requires the real constraint name | Restored key; duplicate email returns 409 |
| 4 | Removed title NOT NULL; then changed title to varchar(100) | `alembic check` failed with `modify_nullable`, then `modify_type` | Database differed from the ORM | Restored NOT NULL and text; check clean |
| 5 | Applied autogenerated required level column to six courses | NotNullViolation: level contains null values; revision stayed 0001 | Existing rows had no value for the new required column | Replaced draft with nullable -> fill -> NOT NULL; upgrade succeeded |
| 6 | Commented out `import models` in env.py | Draft 0003 proposed dropping all three tables and the index | Empty Base.metadata made existing tables appear unwanted | Inspected, **never applied**, deleted draft and restored import |
| 7 | Added optional Student.phone with no migration | Check failed with `add_column` for students.phone | Model was ahead of the database | Removed experimental field; check clean |
| 8 | Created two revision branches from 0002 | Heads 0003/0004; upgrade head failed with Multiple head revisions | No unique target head | Created 0005 merge, observed single head, then removed all three unapplied experiment files; final head 0002 |

Full observations: [1](experiments/results/01-naming.txt),
[2](experiments/results/02-no-pydantic-validation.txt),
[3](experiments/results/03-wrong-constraint-name.txt),
[4](experiments/results/04-schema-mismatch.txt),
[5](experiments/results/05-required-level.txt),
[6](experiments/results/06-missing-import.txt),
[7](experiments/results/07-missing-migration.txt),
[8](experiments/results/08-two-heads.txt).

The two branch revisions in experiment 8 were empty rehearsal templates, not
implemented phone/language features. They and the merge were never applied.
Extra checks reproduced connection failures for a wrong password/missing database
and the `count(*)` LEFT JOIN trap. Those were restored too.

## Decisions

1. **Constraint names and commit:** SQLSTATE identifies a category such as unique
   violation; the name identifies which rule needs which API message. We attempt
   the write and catch IntegrityError from `commit()` (which flushes the INSERT).
   A preliminary SELECT cannot prevent another request taking the same email
   before the insert. The handler explicitly rolls back and raises HTTPException;
   the request dependency closes the session in all cases.
2. **Atomic likes:** `UPDATE ... SET likes = likes + 1 ... RETURNING` lets
   PostgreSQL increment the current value under its row lock. Read/compute/write
   in Python can lose concurrent increments. Twelve parallel test requests all
   survived, and the value persisted after restarting the API.
3. **Three-step migration:** existing courses have no value for an immediately
   required column. Adding it nullable, backfilling with a deliberate rule, then
   enforcing NOT NULL protects those rows. PostgreSQL transactional DDL rolls
   back the whole migration if a step fails. Autogenerate compares schemas and
   cannot choose the correct data backfill for us.

## Migration 0002 self-check

| What to check | Result |
|---|---|
| Goal and steps | Yes: one change, required course level, implemented in three explicit steps. |
| Data | Yes: six pre-existing courses retained; two beginner and four intermediate; no NULLs. |
| Renames and drops | Yes: upgrade adds a column, not a disguised rename; downgrade drops level and its values. |
| Rollback | Yes: downgrade tested; custom level choices would be lost, so production rollback would need a separate data-preservation decision. |
| Verification | Yes: offline SQL read; upgrade/downgrade/upgrade passed on the Lab 6 copy; clean start also passed; alembic check clean. |
| History | Yes: only 0001 and 0002; one head; model, schema, filter, seed and migration 0002 committed together. |
| Application | Yes: CourseOut returns level, list accepts level filter, seed includes it; enrollment now requires studentId. |

The nine mandatory implementation stages are complete locally. The five optional
bonus tasks are not included. See [LAB6_LAB7_DEFENSE.md](LAB6_LAB7_DEFENSE.md)
for a short Russian walkthrough and simple English answers for both defenses.

Reference: [SQLAlchemy 2.1 mapped tables](https://docs.sqlalchemy.org/en/21/orm/declarative_tables.html)
and [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html).
