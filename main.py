from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data import find_course, get_all_courses
from models import Course

app = FastAPI(title="Course Catalog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Course Catalog API is running"}


def pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, int]:
    return {"offset": (page - 1) * page_size, "limit": page_size}


@app.get("/courses", response_model=list[Course])
def list_courses(
    is_elective: bool | None = None,
    sort: Literal["popular", "title"] = "popular",
    q: str | None = None,
    p: dict[str, int] = Depends(pagination),
):
    courses = get_all_courses()
    if is_elective is not None:
        courses = [course for course in courses if course.is_elective == is_elective]
    if q is not None:
        courses = [course for course in courses if q.lower() in course.title.lower()]
    if sort == "title":
        courses = sorted(courses, key=lambda course: course.title)
    else:
        courses = sorted(courses, key=lambda course: course.likes, reverse=True)
    offset = p["offset"]
    return courses[offset : offset + p["limit"]]


@app.get("/courses/{course_id}", response_model=Course)
def get_course(course_id: str):
    course = find_course(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
