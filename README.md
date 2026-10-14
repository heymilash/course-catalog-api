# Course Catalog API — Labs 4–5

Backend каталога курсов на FastAPI и Pydantic: список, фильтры, сортировка, пагинация, лайки и запись на курс.

## Запуск

Нужен Python 3.10+. Проверено с Python 3.14.2, FastAPI 0.142.2 и Pydantic 2.13.5. Для `validate_by_name` требуется Pydantic >= 2.11, ограничение записано в requirements.txt.

В PowerShell из папки `course-catalog-api`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\fastapi.exe dev main.py
```

При повторном запуске достаточно последней команды. Можно активировать окружение через `.\.venv\Scripts\Activate.ps1` и использовать короткую команду `fastapi dev main.py`. На macOS/Linux: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`, `fastapi dev main.py`.

Swagger: <http://localhost:8000/docs>. Также доступны `/redoc` и `/openapi.json`. Запускайте backend первым, затем Next.js на **http://localhost:3000**. Список и страницы курсов получают данные через сервер Next.js; фильтр, лайки и форма — напрямую из браузера.

## Структура

- `models.py`: `CamelModel`, `Course`, `EnrollmentIn`, `Enrollment`.
- `data.py`: шесть исходных курсов, `get_all_courses()` и `find_course()`; данные из Lab 1 сохранены.
- `main.py`: приложение, CORS, dependency `pagination`, шесть операций API.
- `requirements.txt`: зависимости; `.gitignore` исключает `.venv`, кэш и логи.

## What changed — Lab 5

### CORS

Добавлен `CORSMiddleware` с `allow_origins=["http://localhost:3000"]`, `allow_methods=["*"]`, `allow_headers=["*"]`. Разрешён ровно origin frontend: схема, хост и порт, без пути и завершающего `/`. Он нужен для чтения ответов JavaScript-кодом браузера. Серверные запросы Next.js не зависят от CORS.

CORS не является авторизацией: простой запрос от чужого origin может выполниться на сервере, но браузер не разрешит JavaScript прочитать ответ. Если нужен preflight, браузер сначала проверяет разрешение через OPTIONS и при отказе не отправляет основной запрос.

### camelCase JSON

`Course` и `EnrollmentIn` наследуются от `CamelModel`, `Enrollment` — от `EnrollmentIn`. Настройки: `alias_generator=to_camel`, `validate_by_name=True`, `validate_by_alias=True`. В Python используется `is_elective`, а в JSON — `isElective`. При создании объектов допускаются и Python-имена, и aliases. Поля записи в JSON: `courseId`, `studentName`, `id`.

Query-параметры сохраняют свои имена: `/courses?is_elective=true` возвращает два курса. `/courses?isElective=true` возвращает все шесть, потому что неизвестный query-параметр игнорируется. Эксперимент без `validate_by_name=True` выполнен: выборные курсы исчезают без ошибки; после восстановления настройки снова возвращаются два.

### Три новые операции

| Метод и путь | Назначение | Успешный статус |
| --- | --- | --- |
| `GET /` | Проверка сервера | 200 |
| `GET /courses` | Список, фильтрация, сортировка, пагинация | 200 |
| `GET /courses/{course_id}` | Один курс | 200 |
| `POST /courses/{course_id}/like` | Увеличить лайки и вернуть курс | 200 |
| `POST /enrollments` | Создать запись на курс | 201 |
| `GET /enrollments` | Посмотреть записи | 200 |

`POST /courses/web-security/like` после перезапуска возвращает:

```json
{
  "id": "web-security",
  "title": "Web Security Essentials",
  "description": "JWT/OAuth2, defending against XSS, CSRF, SQL injection.",
  "credits": 4,
  "isElective": false,
  "likes": 22
}
```

`POST /enrollments`, тело запроса:

```json
{"courseId": "web-security", "studentName": "Aigerim"}
```

Первый успешный ответ, статус 201:

```json
{"courseId": "web-security", "studentName": "Aigerim", "id": 1}
```

После него `GET /enrollments` возвращает:

```json
[{"courseId": "web-security", "studentName": "Aigerim", "id": 1}]
```

`EnrollmentIn.student_name` имеет `Field(min_length=2)`. Имя `A` получает 422 с `loc: ["body", "studentName"]` и сообщением `String should have at least 2 characters`. Неизвестный курс в записи или лайке получает 404 с `{"detail":"Course not found"}`.

Лайки и записи находятся в памяти: переживают обновление страницы браузера, но сбрасываются при перезапуске процесса backend. Повторная запись создаёт новую запись; авторизация, база данных и защита от повторных лайков в этой лабораторной не предусмотрены.

## What was verified

Проверено 14 октября 2026 через HTTP и реальные действия в Microsoft Edge. Swagger содержит шесть операций (пять разных путей, потому что `/enrollments` поддерживает GET и POST).

| Проверка | Результат |
| --- | --- |
| `GET /courses` | 6 курсов, `ai-integration` первый, `api-design` последний |
| `is_elective=true` / `false` | 2 выборных / 4 обязательных |
| `sort=title` | Названия по алфавиту |
| `page=2&page_size=2` | `web-security`, `backend-fastapi` |
| `page=4&page_size=2` | `[]` |
| `q=react` / `q=API` | Один / два курса, поиск без учёта регистра |
| `sort=banana`, `page=0`, `page_size=1000` | 422 — бонусная валидация Lab 4 сохранена |
| GET и POST лайка для `nope` | 404, `Course not found` |
| Два POST лайка `web-security` | 21 → 22 → 23; после обновления страницы остаётся 23 |
| POST записи с `Aigerim` | 201, назначен ID, запись доступна через GET |
| POST записи с `A` | 422, ошибка поля `studentName` |
| POST записи для `nope` | 404 |
| Origin `http://localhost:3000` | 200 и `access-control-allow-origin: http://localhost:3000` |
| Origin `http://evil.example` | 200 без `access-control-allow-origin` |
| OPTIONS записи | 200, разрешены POST и content-type, max-age 600 |
| JSON и OpenAPI | camelCase: `isElective`, `courseId`, `studentName` |
| `pip check` | Конфликтов зависимостей нет |

Команды для проверки CORS в PowerShell:

```powershell
curl.exe -i -H "Origin: http://localhost:3000" http://localhost:8000/
curl.exe -i -H "Origin: http://evil.example" http://localhost:8000/
curl.exe -i -X OPTIONS http://localhost:8000/enrollments -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type"
```

Пять обязательных поломок CORS/Python воспроизведены и исправлены. Журнал фактических Console/Network-наблюдений находится в `course-catalog/README.md` (frontend).

## Lab 4 — версия для отдельной защиты

Исходная версия сохранена в ветке `lab4-defense` и локальной рабочей папке `../course-catalog-api-lab4`. Это состояние коммита `8301b33`: три GET-маршрута, `is_elective` в JSON, README и девять коммитов Lab 4. В сохранённой папке подготовлено собственное виртуальное окружение.

```powershell
cd ..\course-catalog-api-lab4
.\.venv\Scripts\fastapi.exe dev main.py --port 8004
```

Откройте <http://localhost:8004/docs>. Отдельный порт позволяет показывать Lab 4 одновременно с Lab 5 на порту 8000. Копия проверена: три маршрута, snake_case и два выборных курса.

## Сдача

Для backend пока не настроен GitHub remote. Создайте пустой репозиторий `course-catalog-api`, затем замените YOUR_USERNAME в командах:

```bash
git remote add origin https://github.com/YOUR_USERNAME/course-catalog-api.git
git push -u origin main
git push origin lab4-defense
```

Последняя команда публикует сохранённую ветку для защиты Lab 4. В репозиторий не включаются `.venv`, кэш и логи. Для Lab 5 нужны ссылки на этот backend и существующий frontend `course-catalog`. Подробный сценарий защиты на русском и простом английском — `course-catalog/LAB5_DEFENSE.md`.
