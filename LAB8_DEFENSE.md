# Lab 8: короткая инструкция для защиты

## Начать словами

«В Lab 8 я добавила GraphQL рядом с REST. Оба API используют одну базу и общие
сервисы. Я сравнила одинаковый экран через REST и GraphQL, устранила N+1
с помощью DataLoader и добавила защиту запросов».

Simple English: “REST and GraphQL use the same database and services. GraphQL
loads my courses in one request. DataLoaders reduce database queries.”

## Запуск на этом компьютере

Папка Lab 8: `course-catalog-api`. Сохранённая Lab 7: `course-catalog-api-lab7`.
В первом PowerShell, из папки Lab 8:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-Lab8.ps1
```

База: `localhost:5437/course_catalog_lab8`, роль `catalog_app`.
Учебный пароль для pgAdmin: `change-me`. Lab 7 использует на том же порту другую
базу `course_catalog`; Lab 6 находится на порту 5436.

- REST / Swagger: http://localhost:8008/docs
- GraphQL / GraphiQL: http://localhost:8008/graphql

Во втором PowerShell, в папке `course-catalog`:

```powershell
npm run dev
```

- GraphQL-страница: http://localhost:3000/my-courses
- REST-страница: http://localhost:3000/my-courses-rest

API_URL в `.env.local` должен указывать на http://127.0.0.1:8008.
Оставь оба сервера работающими; проверки выполняй в третьем терминале.
Если инструменты уже запущены на этих портах, второй раз их запускать не надо.

## По критериям преподавателя

| Баллы | Что открыть | Что сказать |
|---|---|---|
| 1 | services.py, problem.py; try_errors.py | «Правила общие. REST переводит ServiceError в Problem Details: type, title, status, detail, instance». |
| 1 | graphql_api.py: Context, CourseType, StudentType, EnrollmentType, Query | «Сессия и контекст создаются для каждого запроса. GraphQL возвращает выбранные поля». |
| 1 | Mutation, EnrollInput, EnrollPayload, LikePayload | «Ожидаемые ошибки возвращаются в userErrors, неожиданные — в errors». |
| 2 | counter.py, Context и batch_loader; try_n_plus_1.py | «Счётчик показывает SQL на HTTP-запрос. DataLoader собирает ключи и делает один IN-запрос». |
| 1 | check_limit, parse_id, should_mask, extensions | «Глубина 5, алиасы 10, limit 1–100, проверка ID, скрытие внутренних ошибок, настройка introspection». |
| 1 | обе страницы Next.js, lib/api.ts, lib/graphql.ts, measure.py | «Страницы одинаковые. REST: 5 запросов в 2 раунда; GraphQL: 1 в 1 раунд». |
| 2 | README: сравнение, Experiment log, Decisions | «Здесь реальные измерения, восемь опытов, причины и исправления». |
| 1 | README: How to run, What changed, Example queries; GitHub Commits | «Запуск с пустой базы проверен. По этапам сделаны отдельные коммиты». |

## GraphiQL: что вставлять

Открой /graphql. В редакторе слева вставь запрос, снизу открой Variables.
Нажми ▶ или Ctrl+Enter.

```graphql
query MyCourses($id: ID!) {
  student(id: $id) {
    name
    enrollments { id course { title credits level } }
  }
}
```

Variables:

```json
{"id":"2"}
```

Ожидается Daniyar Bekov и три курса. «Один POST получает весь экран, а не всё
содержимое таблиц». Поле `level` используется вместо instructor из лекции.

Для ожидаемой ошибки без изменения данных:

```graphql
mutation {
  enroll(input: {courseId: "ai-integration", studentId: "3"}) {
    enrollment { id }
    userErrors { code message }
  }
}
```

Ожидается `enrollment: null`, код `ALREADY_ENROLLED`, HTTP 200.
«Та же ошибка в REST даёт HTTP 409. Правило одно, формат ответа разный».

Для лайка:

```graphql
mutation {
  likeCourse(id: "api-design") {
    course { id likes }
    userErrors { code message }
  }
}
```

Каждый запуск добавляет один лайк. Перед сравнением нужны исходные данные.

## Команды проверки: третий PowerShell в папке Lab 8

```powershell
.\.venv\Scripts\python.exe try_errors.py --base-url http://localhost:8008
.\.venv\Scripts\python.exe try_graphql.py --base-url http://localhost:8008
.\.venv\Scripts\python.exe try_n_plus_1.py --base-url http://localhost:8008
.\.venv\Scripts\python.exe try_protection.py --base-url http://localhost:8008
.\.venv\Scripts\python.exe flood_likes.py --base-url http://localhost:8008
.\.venv\Scripts\python.exe measure.py --base-url http://localhost:8008
```

Ожидается 5/5, 8/8, SQL 3/3; защита отклоняет опасные запросы; flood даёт
`12 aliases found. Allowed: 10` и SQL 0. Сравнение: REST 5/2/1145/5,
GraphQL 1/1/339/3 (запросы / раунды / байты / SQL). Байты могут немного меняться.

Сброс **только Lab 8**, если были изменяющие демонстрации:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5437 -U catalog_app -d course_catalog_lab8 -v ON_ERROR_STOP=1 -f seed.sql
```

Это удаляет текущие учебные строки Lab 8 и возвращает 6/3/6.

## Что знать коротко

- **Query** читает; **Mutation** изменяет данные.
- **Схема** задаёт доступные типы, поля и аргументы.
- **!** означает «не может быть null». Нарушение поднимает null к родителю.
- **errors**: ошибка запроса/исполнения; **userErrors**: ожидаемый отказ правила.
- **HTTP 200** не гарантирует успех GraphQL: проверяем body.errors.
- **Problem Details** — единый формат ошибок REST, application/problem+json.
- **N+1** — отдельная SQL-загрузка связей для каждого объекта.
- **DataLoader** объединяет ключи; ответы должны совпадать с ключами по длине
  и порядку. Для отсутствующего ключа возвращается None или пустой список.
- **Контекст на запрос** предотвращает перенос кэша между запросами/пользователями.
- **X-SQL-Queries** — число обращений к БД, не число HTTP-запросов.
- **Алиас** позволяет запросить поле под другим именем; много алиасов может
  объединить много изменений в один HTTP-запрос.
- **Introspection** показывает схему. Её отключение не заменяет авторизацию.
- **no-store** заставляет страницы получать свежие данные.
- Серверные fetch-запросы Next.js видны в терминале API. Browser Network
  показывает запросы браузера к Next.js, а не внутренние вызовы Next.js к API.

## Восемь опытов одним предложением

1. Ошибочное поле или snake_case-аргумент: HTTP 200, но errors и data null.
2. Лишний !: несуществующий курс обнуляет весь ответ; nullable сохраняет другие поля.
3. Мутация через GET: 400, данные не меняются.
4. Больше студентов: SQL выросло с 7/7 до 27/24; после loaders осталось 3/3.
5. Неправильный batch: ошибка длины либо тихая подмена курсов из-за порядка строк.
6. Без защиты SQL и параметры утекали; после — безопасные сообщения и SQL 0 для flood.
7. Introspection выключена, но подсказки с именами полей остаются.
8. Ошибка GraphQL, отсутствие проверки errors и недоступный API дают разные сообщения.
