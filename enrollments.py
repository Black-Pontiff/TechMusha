from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..db import get_db
from ..models import Enrollment, Course, Lesson, Module, Progress, Certificate, User
from ..schemas import EnrollmentOut, ProgressIn, ProgressOut
from ..deps import current_user
import secrets

router = APIRouter(prefix="/enrollments", tags=["enrollments"])

@router.post("/{course_id}", response_model=EnrollmentOut, status_code=201)
def enroll(course_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course: raise HTTPException(404, "Course not found")
    if course.price > 0:
        raise HTTPException(402, "Paid course — complete payment first")
    existing = db.scalar(select(Enrollment).where(Enrollment.user_id == user.id,
                                                 Enrollment.course_id == course_id))
    if existing: return existing
    e = Enrollment(user_id=user.id, course_id=course_id)
    db.add(e); db.commit(); db.refresh(e)
    return e

@router.get("", response_model=list[EnrollmentOut])
def my_enrollments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Enrollment).where(Enrollment.user_id == user.id)
                      .order_by(Enrollment.enrolled_at.desc())).all()

@router.post("/progress", response_model=ProgressOut)
def update_progress(body: ProgressIn, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    lesson = db.get(Lesson, body.lesson_id)
    if not lesson: raise HTTPException(404, "Lesson not found")
    p = db.scalar(select(Progress).where(Progress.user_id == user.id,
                                         Progress.lesson_id == body.lesson_id))
    if not p:
        p = Progress(user_id=user.id, lesson_id=body.lesson_id,
                     completed=body.completed, last_position=body.last_position)
        db.add(p)
    else:
        p.completed = body.completed or p.completed
        p.last_position = body.last_position
        p.updated_at = datetime.utcnow()
    db.flush()
    _recompute(user.id, lesson.module.course_id, db)
    db.commit(); db.refresh(p)
    return p

def _recompute(user_id: str, course_id: str, db: Session):
    total = db.scalar(select(func.count()).select_from(Lesson)
                      .join(Module).where(Module.course_id == course_id)) or 0
    if total == 0: return
    done = db.scalar(select(func.count()).select_from(Progress)
                     .join(Lesson, Lesson.id == Progress.lesson_id)
                     .join(Module, Module.id == Lesson.module_id)
                     .where(Module.course_id == course_id,
                            Progress.user_id == user_id,
                            Progress.completed == True)) or 0
    pct = round(done * 100.0 / total, 2)
    e = db.scalar(select(Enrollment).where(Enrollment.user_id == user_id,
                                           Enrollment.course_id == course_id))
    if not e: return
    e.progress = pct
    if pct >= 100:
        e.status = "completed"
        e.completed_at = e.completed_at or datetime.utcnow()
        if not db.scalar(select(Certificate).where(Certificate.user_id == user_id,
                                                   Certificate.course_id == course_id)):
            db.add(Certificate(user_id=user_id, course_id=course_id,
                               code=secrets.token_urlsafe(12)))
    elif pct > 0:
        e.status = "in_progress"

@router.get("/course/{course_id}/progress", response_model=list[ProgressOut])
def course_progress(course_id: str, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    stmt = (select(Progress)
            .join(Lesson, Lesson.id == Progress.lesson_id)
            .join(Module, Module.id == Lesson.module_id)
            .where(Module.course_id == course_id, Progress.user_id == user.id))
    return db.scalars(stmt).all()