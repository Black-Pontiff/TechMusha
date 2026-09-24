from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, or_, func
from ..db import get_db
from ..models import Course, Module, Lesson, User, Review
from ..schemas import CourseOut, CourseDetailOut, CourseCreateIn, ReviewOut
from ..deps import current_user, require_role
import re

router = APIRouter(prefix="/courses", tags=["courses"])

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

@router.get("", response_model=list[CourseOut])
def list_courses(
    q: str | None = None,
    category: str | None = None,
    level: str | None = None,
    free: bool | None = None,
    language: str | None = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = select(Course).where(Course.published == True)
    if q: stmt = stmt.where(or_(Course.title.ilike(f"%{q}%"), Course.description.ilike(f"%{q}%")))
    if category: stmt = stmt.where(Course.category == category)
    if level: stmt = stmt.where(Course.level == level)
    if free is not None: stmt = stmt.where(Course.price == 0) if free else stmt.where(Course.price > 0)
    if language: stmt = stmt.where(Course.language == language)
    stmt = stmt.order_by(Course.created_at.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()

@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    rows = db.execute(select(Course.category, func.count()).where(Course.published == True)
                      .group_by(Course.category)).all()
    return [{"category": c, "count": n} for c, n in rows]

@router.get("/{slug}", response_model=CourseDetailOut)
def get_course(slug: str, db: Session = Depends(get_db)):
    course = db.scalar(
        select(Course).options(selectinload(Course.modules).selectinload(Module.lessons))
        .where(Course.slug == slug)
    )
    if not course: raise HTTPException(404, "Course not found")
    return course

@router.get("/{slug}/reviews", response_model=list[ReviewOut])
def course_reviews(slug: str, db: Session = Depends(get_db)):
    course = db.scalar(select(Course).where(Course.slug == slug))
    if not course: raise HTTPException(404, "Course not found")
    return db.scalars(select(Review).where(Review.course_id == course.id)
                      .order_by(Review.created_at.desc())).all()

@router.post("", response_model=CourseDetailOut, status_code=201)
def create_course(body: CourseCreateIn,
                  user: User = Depends(require_role("instructor", "admin")),
                  db: Session = Depends(get_db)):
    slug = slugify(body.title)
    if db.scalar(select(Course).where(Course.slug == slug)):
        slug = f"{slug}-{int(__import__('time').time())}"
    c = Course(**body.model_dump(), slug=slug, instructor_id=user.id)
    db.add(c); db.commit(); db.refresh(c)
    return c