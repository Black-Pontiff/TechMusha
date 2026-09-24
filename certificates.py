from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from ..db import get_db
from ..models import Certificate, Course, User
from ..deps import current_user

router = APIRouter(prefix="/certificates", tags=["certificates"])

@router.get("/mine")
def mine(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Certificate, Course.title).join(Course, Course.id == Certificate.course_id)
        .where(Certificate.user_id == user.id)
    ).all()
    return [{"id": c.id, "code": c.code, "issued_at": c.issued_at,
             "course_title": title} for c, title in rows]

@router.get("/verify/{code}")
def verify(code: str, db: Session = Depends(get_db)):
    c = db.scalar(select(Certificate).where(Certificate.code == code))
    if not c: raise HTTPException(404, "Not found")
    course = db.get(Course, c.course_id); user = db.get(User, c.user_id)
    return {"valid": True, "code": code, "issued_at": c.issued_at,
            "student": user.name, "course": course.title}

@router.get("/{code}/pdf")
def pdf(code: str, db: Session = Depends(get_db)):
    c = db.scalar(select(Certificate).where(Certificate.code == code))
    if not c: raise HTTPException(404)
    course = db.get(Course, c.course_id); user = db.get(User, c.user_id)
    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=landscape(A4))
    w, h = landscape(A4)
    p.setFont("Helvetica-Bold", 32); p.drawCentredString(w/2, h-100, "TechMusha Certificate")
    p.setFont("Helvetica", 16); p.drawCentredString(w/2, h-160, "of completion")
    p.setFont("Helvetica-Bold", 22); p.drawCentredString(w/2, h-230, user.name)
    p.setFont("Helvetica", 14); p.drawCentredString(w/2, h-270, "has completed")
    p.setFont("Helvetica-Bold", 18); p.drawCentredString(w/2, h-310, course.title)
    p.setFont("Helvetica", 11); p.drawCentredString(w/2, h-360, f"Verification code: {c.code}")
    p.drawCentredString(w/2, h-380, f"Issued: {c.issued_at.date().isoformat()}")
    p.showPage(); p.save()
    return Response(buf.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{code}.pdf"'})