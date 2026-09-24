from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..db import get_db
from ..models import Review, Course, Enrollment, User
from ..schemas import ReviewIn, ReviewOut
from ..deps import current_user

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/course/{course_id}", response_model=ReviewOut, status_code=201)
def create(course_id: str, body: ReviewIn, user: User = Depends(current_user),
           db: Session = Depends(get_db)):
    if not db.get(Course, course_id): raise HTTPException(404)
    if not db.scalar(select(Enrollment).where(Enrollment.user_id == user.id,
                                              Enrollment.course_id == course_id)):
        raise HTTPException(403, "Enroll first")
    existing = db.scalar(select(Review).where(Review.user_id == user.id,
                                              Review.course_id == course_id))
    if existing:
        existing.rating = body.rating; existing.comment = body.comment
        db.commit(); db.refresh(existing); return existing
    r = Review(user_id=user.id, course_id=course_id, **body.model_dump())
    db.add(r); db.commit(); db.refresh(r)
    return r

@router.get("/course/{course_id}/stats")
def stats(course_id: str, db: Session = Depends(get_db)):
    row = db.execute(select(func.avg(Review.rating), func.count())
                     .where(Review.course_id == course_id)).one()
    return {"avg": float(row[0] or 0), "count": row[1]}