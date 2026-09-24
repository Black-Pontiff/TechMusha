import hashlib, os, uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from ..db import get_db
from ..models import Document, User
from ..schemas import DocumentOut
from ..deps import current_user, require_role
from ..config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED = {"pdf","epub","mobi","docx","pptx","xlsx","txt","md","rtf","html","png","jpg","jpeg","svg","gif","webp","mp4","webm","mp3","m4a","py","js","ts","java","cpp","c","go","rs"}

@router.get("", response_model=list[DocumentOut])
def list_docs(q: str | None = None, category: str | None = None,
              tag: str | None = None, sort: str = "newest",
              limit: int = Query(50, le=100), offset: int = 0,
              db: Session = Depends(get_db)):
    stmt = select(Document).where(Document.visibility == "public", Document.status == "approved")
    if q: stmt = stmt.where(or_(Document.title.ilike(f"%{q}%"), Document.author.ilike(f"%{q}%")))
    if category: stmt = stmt.where(Document.category == category)
    if sort == "popular": stmt = stmt.order_by(Document.downloads.desc())
    else: stmt = stmt.order_by(Document.created_at.desc())
    return db.scalars(stmt.limit(limit).offset(offset)).all()

@router.post("", response_model=DocumentOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    title: str = Form(...),
    author: str = Form(""),
    category: str = Form(""),
    tags: str = Form(""),
    description: str = Form(""),
    language: str = Form("en"),
    visibility: str = Form("private"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Unsupported format: {ext}")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "File too large")
    digest = hashlib.sha256(data).hexdigest()
    existing = db.scalar(select(Document).where(Document.hash == digest,
                                                Document.visibility == visibility))
    if existing:
        return existing
    os.makedirs(settings.storage_path, exist_ok=True)
    stored = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(settings.storage_path, stored)
    with open(path, "wb") as f: f.write(data)
    status = "pending" if visibility == "public" else "approved"
    d = Document(uploader_id=user.id, title=title, author=author or None,
                 format=ext, size=len(data), hash=digest, visibility=visibility,
                 status=status, category=category or None,
                 tags=[t.strip() for t in tags.split(",") if t.strip()] or None,
                 description=description or None, language=language,
                 url=f"/documents/{stored}/raw")
    db.add(d); db.commit(); db.refresh(d)
    return d

@router.get("/{doc_id}/raw")
def raw(doc_id: str, db: Session = Depends(get_db)):
    d = db.get(Document, doc_id)
    if not d: raise HTTPException(404)
    if d.visibility == "public" and d.status != "approved":
        raise HTTPException(403, "Not approved")
    stored = d.url.rsplit("/", 2)[-2]
    path = os.path.join(settings.storage_path, stored)
    if not os.path.exists(path): raise HTTPException(404, "File missing")
    d.downloads += 1; db.commit()
    return FileResponse(path, filename=f"{d.title}.{d.format}")

@router.post("/{doc_id}/report")
def report(doc_id: str, reason: str = Form(""), _: User = Depends(current_user),
           db: Session = Depends(get_db)):
    d = db.get(Document, doc_id)
    if not d: raise HTTPException(404)
    d.status = "pending"
    db.commit()
    return {"ok": True, "reason": reason}