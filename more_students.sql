-- Run once after seed.sql: add students 4-20, with one enrollment each.
BEGIN;
INSERT INTO students (name, email)
SELECT 'Student ' || n, 'student' || n || '@example.com'
FROM generate_series(4, 20) AS n;

INSERT INTO enrollments (course_id, student_id)
SELECT (ARRAY['modern-frontend', 'backend-fastapi', 'databases-postgresql',
              'api-design', 'web-security', 'ai-integration'])[1 + (s.id % 6)], s.id
FROM students s
WHERE s.id > 3;
COMMIT;
