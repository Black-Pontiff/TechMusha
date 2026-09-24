from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import get_db
from ..models import Document, User, Course
from ..schemas import DocumentOut
from ..deps import require_role

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/documents/pending", response_model=list[DocumentOut])
def pending(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return db.scalars(select(Document).where(Document.status == "pending")
                      .order_by(Document.created_at.asc())).all()

@router.post("/documents/{doc_id}/approve")
def approve(doc_id: str, _: User = Depends(require_role("admin")),
            db: Session = Depends(get_db)):
    d = db.get(Document, doc_id) or (_ for _ in ()).throw(HTTPException(404))
    d.status = "approved"; db.commit()
    return {"ok": True}

@router.post("/documents/{doc_id}/reject")
def reject(doc_id: str, _: User = Depends(require_role("admin")),
           db: Session = Depends(get_db)):
    d = db.get(Document, doc_id) or (_ for _ in ()).throw(HTTPException(404))
    d.status = "rejected"; db.commit()
    return {"ok": True}

@router.get("/stats")
def stats(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    from sqlalchemy import func
    return {
        "users": db.scalar(select(func.count()).select_from(User)),
        "courses": db.scalar(select(func.count()).select_from(Course)),
        "documents": db.scalar(select(func.count()).select_from(Document)),
        "pending": db.scalar(select(func.count()).select_from(Document)
                             .where(Document.status == "pending")),
    }