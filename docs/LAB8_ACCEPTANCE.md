# Lab 8 acceptance audit

Verified on 2026-11-26. Every temporary experiment edit was restored.

| Requirement | Result and evidence |
|---|---|
| Strawberry dependency; introspection setting; local env ignored | requirements.txt, config.py, .env.example; Git file audit excludes .env/.env.local/.venv |
| Shared services, RFC 9457 REST errors | services.py, problem.py; try_errors.py 5/5, including validation bonus |
| GraphQL alongside REST; per-request session; 3 entity types and 5 root queries | graphql_api.py; docs/schema.graphql; HTTP /graphql and /docs both 200 |
| enroll and likeCourse; consistent userErrors | try_graphql.py 8/8; successful write, duplicate and missing-object tests archived |
| SQL counter and N+1 proof | Before: 7/7 -> 27/24. After: 3/3 on both datasets; experiments/lab8/experiment-04-*.txt and 06-after-loaders-*.txt |
| Per-request loaders, key alignment, missing placeholders | final-checks.json; both one/many loader contracts tested against actual database |
| Depth 5, aliases 10, argument checks, masking, introspection setting | try_protection.py; flood_likes.py rejects with 0 SQL; experiments 6 and 7 |
| Two additional REST student routes | main.py; original routes and new routes tested in final-checks.json |
| Two Next.js pages and request helpers | frontend app/my-courses, app/my-courses-rest, lib/api.ts, lib/graphql.ts; both HTTP 200, identical screen data |
| Actual comparison | REST 5 requests / 2 rounds / 1145 bytes / 5 SQL; GraphQL 1 / 1 / 339 / 3; 09-clean-comparison.json |
| Six README sections, eight experiments, three decisions | README.md; experiments/lab8 holds actual responses and logs |
| Clean database start | 09-clean-start.txt: both migrations, seed 6/3/6, Alembic check clean, scripts and frontend pass after bonuses |
| Commits by stage and publication | Nine core stage commits plus separate bonus commits; frontend pages committed separately; see Git history |
| Bonus 1 | REST validation errors use Problem Details; two simultaneous field errors and bad query tested |
| Bonus 2 | createStudent; shared trimmed-name rule; duplicate and success; missing REST mapping reproduced and restored |
| Bonus 3 | Four slow requests: REST 0.693 s, GraphQL sync 2.062 s, threadpool 0.529 s; temporary server stopped |
| Other verification | 12 concurrent requests kept isolated SQL counters; pip check, npm run lint and npm run build passed; both pages marked dynamic |

Visual browser automation was stopped by the Windows tool because it could not
determine the current URL. HTTP rendering, Next.js build and real API request logs
were verified; a browser screenshot review is not claimed.

Lab 6 and Lab 7 use their preserved databases. Lab 8 experiments/reset target only
localhost:5437/course_catalog_lab8. Local pre-task patches/env snapshots remain in
document-work/lab8, outside the published repositories.
