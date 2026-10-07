# Course Catalog API — Lab 4

## 1. Что это

Самостоятельный backend каталога курсов на FastAPI с Pydantic-моделью, фильтрацией, сортировкой и пагинацией через `Depends`.

Данные шести курсов перенесены из `course-catalog/lib/courses.ts` первой лабораторной. Сохранены исходные названия, описания, кредиты и лайки. Python-поле `is_elective` соответствует TypeScript-полю `isElective`; в JSON используется `is_elective`.

```text
course-catalog-api/
├── .venv/             # локальное окружение, исключено из Git
├── .gitignore
├── README.md
├── requirements.txt
├── models.py          # Pydantic-модель Course
├── data.py            # шесть курсов и функции доступа
└── main.py            # приложение, маршруты, dependency пагинации
```

| Метод | Путь | Назначение |
| --- | --- | --- |
| GET | `/` | Проверка работы сервера |
| GET | `/courses` | Список курсов с параметрами |
| GET | `/courses/{course_id}` | Один курс или ошибка 404 |

Документация доступна на `/docs` (Swagger UI), `/redoc` и `/openapi.json`. В OpenAPI ровно три прикладных маршрута.

Как работает код:

- `Course(BaseModel)` проверяет поля во время выполнения. Обязательны `id`, `title`, `description`, `credits`; по умолчанию `is_elective=False`, `likes=0`.
- `get_all_courses()` возвращает копию списка; `find_course()` возвращает курс или `None`.
- `response_model` описывает и проверяет форму ответа, а также добавляет схему в документацию.
- Проверка `is_elective is not None` позволяет корректно обрабатывать и `true`, и `false`.
- Сначала выполняются фильтрация и поиск, затем сортировка, затем срез страницы.
- `pagination()` вычисляет `offset = (page - 1) * page_size` и `limit`. FastAPI передаёт результат в маршрут через `Depends(pagination)`.
- Для неизвестного ID выбрасывается `HTTPException(status_code=404, detail="Course not found")`.

Реализованы бонусы 1–3: `Literal["popular", "title"]`, ограничения пагинации через `Query` и поиск `q` по названию без учёта регистра. Необязательный `/stats` не добавлен: сохранены три маршрута из основного acceptance checklist.

Справка: [зависимости FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/).

## 2. Как запустить

Требования: Python 3.10+ и Git. Проверено на Windows с Python 3.14.2, FastAPI 0.142.2 и Pydantic 2.13.5.

Откройте терминал в папке `course-catalog-api`. При первом запуске создайте окружение и установите зависимости.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
fastapi dev main.py
```

Если окружение уже создано и зависимости установлены, достаточно активации и команды `fastapi dev main.py`.

Если PowerShell запрещает выполнение `Activate.ps1`, можно запускать через полные пути без изменения политики:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\fastapi.exe dev main.py
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
fastapi dev main.py
```

Откройте <http://127.0.0.1:8000/docs>. Оставьте терминал с сервером открытым. Изменения Python-файлов подхватываются автоматически. Остановка сервера в терминале: `Ctrl+C`. Если порт занят, используйте `fastapi dev main.py --port 8001` и адрес с портом `8001`.

Параметры `GET /courses`:

| Параметр | По умолчанию | Допустимые значения |
| --- | --- | --- |
| `is_elective` | не задан | `true` / `false`; без параметра — все курсы |
| `sort` | `popular` | `popular` — лайки по убыванию; `title` — название по алфавиту |
| `q` | не задан | Подстрока названия без учёта регистра |
| `page` | `1` | Целое число ≥ 1 |
| `page_size` | `20` | Целое число от 1 до 100 |

Для сдачи создайте на GitHub пустой репозиторий `course-catalog-api` без автоматически созданного README. Затем выполните, заменив `YOUR_USERNAME` своим логином:

```bash
git remote add origin https://github.com/YOUR_USERNAME/course-catalog-api.git
git push -u origin main
```

Репозиторий должен быть публичным либо доступным преподавателю. Отправьте ссылку через LMS или чат курса. Локальные коммиты уже созданы по этапам; `.venv`, кэш Python и логи исключены из Git. Публикация на GitHub не выполнена: удалённый репозиторий для этого проекта ещё не настроен.

## 3. What was verified — что проверено

Запросы ниже проверены на работающем сервере. В колонке результата списки обозначают ID курсов в порядке ответа; API возвращает полные объекты с шестью полями.

| Запрос | HTTP | Фактический результат |
| --- | --- | --- |
| `/` | 200 | `{"message":"Course Catalog API is running"}` |
| `/courses` | 200 | `ai-integration`, `modern-frontend`, `web-security`, `backend-fastapi`, `databases-postgresql`, `api-design` |
| `/courses/web-security` | 200 | Один объект `web-security` |
| `/courses/nope` | 404 | `{"detail":"Course not found"}` |
| `/courses?is_elective=true` | 200 | `ai-integration`, `api-design` |
| `/courses?is_elective=false` | 200 | `modern-frontend`, `web-security`, `backend-fastapi`, `databases-postgresql` |
| `/courses?sort=title` | 200 | `ai-integration`, `api-design`, `backend-fastapi`, `modern-frontend`, `databases-postgresql`, `web-security` |
| `/courses?page=1&page_size=2` | 200 | `ai-integration`, `modern-frontend` |
| `/courses?page=2&page_size=2` | 200 | `web-security`, `backend-fastapi` |
| `/courses?page=3&page_size=2` | 200 | `databases-postgresql`, `api-design` |
| `/courses?page=4&page_size=2` | 200 | `[]` |
| `/courses?is_elective=false&sort=title&page=2&page_size=2` | 200 | `databases-postgresql`, `web-security` |
| `/courses?q=react` | 200 | `modern-frontend` |
| `/courses?q=API` | 200 | `backend-fastapi`, `api-design` |
| `/courses?q=not-a-course` | 200 | `[]` |
| `/courses?q=API&is_elective=true&page_size=1` | 200 | `api-design` |
| `/courses?sort=banana` | 422 | Ошибка допустимых значений сортировки |
| `/courses?page=0` и `/courses?page=-1` | 422 | Страница должна быть ≥ 1 |
| `/courses?page_size=0` и `/courses?page_size=1000` | 422 | Размер страницы должен быть от 1 до 100 |
| `/courses?page=abc` | 422 | Ожидается целое число |
| `/courses?is_elective=banana` | 422 | Ожидается логическое значение |
| `/courses?page_size=100` | 200 | Все шесть курсов |
| `/docs` и `/redoc` | 200 | Документация доступна и отображается в браузере |
| `/openapi.json` | 200 | Три GET-маршрута, схема `Course`, параметры запросов |

Swagger UI дополнительно проверен в браузере Microsoft Edge: через `Try it out` → `Execute` выполнены запрос списка с `page=2`, `page_size=2` и запрос курса `nope`. Подтверждены ответы 200 и 404, отображение `Request URL` и `Response body`, наличие выпадающих списков `is_elective` и `sort`. ReDoc также отобразил маршруты.

Проверка модели из задания:

```python
from models import Course

Course(id="x", title="t", description="d", credits="five")
# ValidationError: Input should be a valid integer

course = Course(id="x", title="t", description="d", credits="5")
print(course.credits, course.is_elective, course.likes)
# 5 False 0
```

Оба случая проверены. Дополнительно подтверждено: изменение копии списка не изменяет исходный список, запросы с сортировкой не меняют порядок в `COURSES`, `pip check` не обнаружил конфликтов зависимостей.

Как повторить проверку перед защитой:

1. Откройте `/docs` и убедитесь, что видны три GET-маршрута.
2. Разверните `GET /courses`, нажмите `Try it out`, задайте параметры из таблицы и нажмите `Execute`.
3. Сравните `Request URL`, код ответа и ID в `Response body` с таблицей.
4. В `GET /courses/{course_id}` проверьте `web-security` и `nope`.
5. В `Schemas` разверните `Course` и покажите типы и значения по умолчанию.
6. Откройте `/redoc` и `/openapi.json`.
7. Выполните `git log --oneline` и `git status --short`: история содержит больше четырёх осмысленных коммитов, рабочее дерево чистое.
