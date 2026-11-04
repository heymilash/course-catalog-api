# Защита Lab 6 и Lab 7: что открыть и что сказать

## Начать коротко

**RU:** «В Lab 6 я создала схему базы PostgreSQL и проверила её через SQL.
В Lab 7 подключила эту базу к FastAPI через SQLAlchemy и добавила миграции Alembic».

**EN:** “In Lab 6, I designed a PostgreSQL database. In Lab 7, I connected it to
FastAPI with SQLAlchemy and added Alembic migrations.”

Это одна тема в двух этапах. Можно предложить показать их подряд, а порядок сдачи
согласовать с преподавателем.

## Сначала Lab 6 (примерно 5 минут)

Открой папку **course-catalog-db**. В PowerShell:

```powershell
cd "C:\Users\77712\Desktop\4 course\WEB\course-catalog-db"
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-Lab6.ps1
```

Теперь ты в psql, в базе Lab 6 на порту **5436**. Вводи:

```text
\dt
\d enrollments
```

Покажи три таблицы: **courses, students, enrollments**. В редакторе открой
**schema.sql**: PRIMARY KEY, FOREIGN KEY, NOT NULL, CHECK, UNIQUE, DEFAULT.

**RU:** «Записи на курсы связывают студентов и курсы: многие ко многим».

**EN:** “Enrollments connect students and courses in a many-to-many relationship.”

Затем покажи **seed.sql** и количество строк:

```sql
SELECT (SELECT count(*) FROM courses) AS courses,
       (SELECT count(*) FROM students) AS students,
       (SELECT count(*) FROM enrollments) AS enrollments;
```

Ожидается **6 / 3 / 6**. Покажи **queries.sql**, выполни `\i queries.sql`.
`WHERE` фильтрует, `ORDER BY` сортирует, `LIMIT/OFFSET` задают страницу,
`JOIN` соединяет таблицы. `LEFT JOIN` сохраняет курсы без записей.

Для одной ошибки:

```text
\set VERBOSITY verbose
```

```sql
INSERT INTO students (name, email) VALUES ('A', 'a@example.com');
```

Покажи **23514** и **students_name_check**. Это код PostgreSQL, не HTTP.
В API такая проверка входных данных соответствует **422**.

**RU:** «База сама защищает данные, даже если запись сделана в обход API».

**EN:** “Database constraints protect the data even outside the API.”

Открой README Lab 6:

1. **Constraint violation log** — все 10 ошибок и CASCADE.
2. **Index: EXPLAIN before and after** — Seq Scan до индекса, Bitmap Scan после.
3. **Transaction** — обе вставки откатываются вместе; другое окно видит изменения после COMMIT.
4. **Schema** — ER-диаграмма.

Подробный порядок с SQL-командами находится в **course-catalog-db/DEFENSE.md**.

## Затем Lab 7: запустить API

Открой **новый терминал PowerShell**. Если осталась в psql, сначала выйди через
`\q`. Команды `cd`, `powershell`, `python`, `alembic` вводятся в PowerShell,
а не после приглашения `course_catalog=>`.

```powershell
cd "C:\Users\77712\Desktop\4 course\WEB\course-catalog-api"
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-Lab7.ps1
```

Оставь сервер работать. В Chrome открой **http://localhost:8007/docs**.
У Lab 7 отдельная копия базы на порту **5437**; Lab 6 остаётся на 5436.

**RU:** «Теперь маршруты выполняют SQL-запросы, а данные сохраняются после перезапуска API».

**EN:** “The API now queries PostgreSQL. The data survives an API restart.”

## Lab 7: что показывать в Swagger по очереди

Во всех маршрутах сначала нажимай **Try it out**, затем **Execute**.

1. **GET /courses** — **200**, шесть курсов; в ответе есть `level` и `isElective`.
2. В этом же маршруте укажи **level = beginner** — два курса:
   `ai-integration` и `api-design`.
3. Очисти level, укажи **is_elective = false**, **page_size = 3**, **page = 2** —
   останется `databases-postgresql`.
4. **GET /courses/{course_id}**, id **nope** — **404 Course not found**.
5. **POST /courses/{course_id}/like**, id **api-design** — **200**, likes увеличился.
6. **POST /students** — сначала слишком короткое имя:

```json
{"name": "N", "email": "n@example.com"}
```

Ожидается **422**. Затем дублирующий email:

```json
{"name": "Aigerim Two", "email": "aigerim@example.com"}
```

Ожидается **409 Student with this email already exists**. Затем новый студент:

```json
{"name": "Nurlan Abenov", "email": "nurlan@example.com"}
```

Ожидается **201**. Запомни `id` из ответа. Если уже создавала такого студента,
получишь 409: используй другой email или сбрось учебные данные перед защитой.

7. **POST /enrollments** — используй **реальный id**, полученный выше:

```json
{"courseId": "web-security", "studentId": 4}
```

Первый запрос — **201**, повторный — **409**. Число 4 здесь только пример.
Замени courseId на `nope` — **404 Course not found**.

8. **GET /enrollments** — видны `studentName`, `courseTitle`, `enrolledAt`: это результат JOIN.
9. **GET /stats/courses** — статистика записей; курсы без записей имеют **0**.

Если нужно показать статусы в DevTools: **Network -> Fetch/XHR**, затем нажми
Execute в Swagger. Выбери запрос: **Headers -> Status Code**, **Response** — тело.

## Lab 7: какие файлы открыть по просьбе преподавателя

| Вопрос | Что открыть | Короткий ответ на английском |
|---|---|---|
| Где модель курса? | **models.py**, `class Course(Base)` | “This ORM model describes the courses table.” |
| Где проверяется JSON и имя? | **schemas.py**, `StudentIn` | “Pydantic validates the request before the database.” |
| Почему models и schemas отдельно? | Оба файла | “Models describe tables. Schemas describe API data.” |
| Где адрес базы? | **config.py**, затем **.env.example** | “Settings read the database URL from the environment.” |
| Где соединение и Session? | **db.py**, `engine`, `SessionLocal`, `get_db` | “Each request gets its own session, which is closed afterward.” |
| Где фильтры и страницы? | **main.py**, `list_courses` | “WHERE filters rows; LIMIT and OFFSET select a page.” |
| Где 404 для курса? | **main.py**, `get_course` | “If db.get returns None, the API returns 404.” |
| Где лайк? | **main.py**, `like_course` | “The database increments likes in one UPDATE.” |
| Где обработка 409? | **main.py**, `CONSTRAINT_ERRORS`, `raise_http_error` | “The constraint name selects the HTTP response.” |
| Где JOIN? | **main.py**, `list_enrollments` | “JOIN adds the student name and course title.” |
| Почему count(Enrollment.id)? | **main.py**, `course_stats` | “It ignores NULL and returns zero for courses with no enrollments.” |
| Почему isElective в JSON? | **schemas.py**, `alias_generator=to_camel` | “The API uses camelCase names.” |
| Зачем from_attributes? | **schemas.py**, `CamelModel` | “It lets Pydantic read ORM object attributes.” |

## Lab 7: показать миграции

Во **втором PowerShell**, из папки `course-catalog-api`:

```powershell
.\.venv\Scripts\python.exe check_db.py
.\.venv\Scripts\python.exe check_models.py
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic history
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe try_errors.py --base-url http://localhost:8007
```

Покажи: подключение к course_catalog, отсутствие различий имён, **0002 (head)**,
две миграции, **No new upgrade operations detected**, **5 of 5 as expected**.
После ручного добавления студента/записи количества строк могут быть больше 6/3/6.

Открой **alembic/versions/0001_create_catalog_tables.py**:
создаёт таблицы, ограничения и индекс.

Затем **0002_add_course_level.py** и покажи три команды:

1. `add_column(... nullable=True)` — добавляем поле без требования значения.
2. `op.execute("UPDATE ...")` — заполняем существующие строки.
3. `alter_column(... nullable=False)` — теперь значение обязательно.

**RU:** «Если сразу добавить NOT NULL, у существующих строк будет NULL и миграция упадёт».

**EN:** “Existing rows need a value first. I add the column, fill it, then set NOT NULL.”

Если попросит выполнить откат: останови API через Ctrl+C, затем:

```powershell
.\.venv\Scripts\python.exe -m alembic downgrade -1
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic check
```

После downgrade будет **0001**, поле level исчезнет; upgrade вернёт **0002**.
Откат удаляет значения level. После опыта снова запусти API.

## Самые вероятные вопросы

**Что такое миграция?** Версионированное изменение схемы базы.
“A migration is a versioned database schema change.”

**Что такое stamp?** Только записывает версию, не создаёт таблицы.
“Stamp records a revision without running the migration.”

**Почему не делать SELECT перед INSERT для проверки email?** Другой запрос может
занять email между проверкой и вставкой. Надёжнее UNIQUE и обработка ошибки записи.
“Another request can insert the same email after the check. The unique constraint prevents duplicates.”

**Почему неизвестная ошибка базы даёт 500?** Она может означать ошибку нашего кода;
её нельзя скрывать как обычный конфликт пользователя.
“An unknown constraint error may be a bug in our code.”

**Зачем commit?** Сохраняет изменения. Без него закрытие Session откатит транзакцию.
“Commit saves changes. Without it, the session rolls them back.”

**Почему нельзя просто присвоить course.likes += 1?** Два запроса могут прочитать
одно значение и перезаписать результат друг друга. SQL `likes = likes + 1` избегает этого.
“An atomic SQL update prevents lost likes.”

**Чем Lab 6 отличается от Lab 7?** В Lab 6 схема и запросы были в SQL-файлах.
В Lab 7 SQLAlchemy выполняет запросы из API, а Alembic управляет историей схемы.

## Перед защитой

Покажи **README.md -> Experiment log**: восемь реальных опытов, причины и исправления.
При необходимости открой полный вывод по ссылке нужного эксперимента.
Пять дополнительных бонусов не входят в эту реализацию.

Если хочешь вернуть именно учебные 6/3/6 записей Lab 7, выйди из psql и в PowerShell
из папки API выполни (пароль учебной роли: `change-me`):

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5437 -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
```

Это удаляет добавленные тобой учебные записи и возвращает начальные данные.
Для Lab 6 используй её собственную папку и порт 5436.
