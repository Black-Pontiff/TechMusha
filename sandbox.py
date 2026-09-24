import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import get_db
from ..models import Snippet, User
from ..schemas import RunIn, RunOut, SnippetIn, SnippetOut
from ..deps import current_user
from ..config import settings

router = APIRouter(prefix="/sandbox", tags=["sandbox"])

ALLOWED_LANGS = {"python", "javascript", "java", "cpp"}

@router.post("/run", response_model=RunOut)
def run(body: RunIn, user: User = Depends(current_user)):
    if body.language not in ALLOWED_LANGS:
        raise HTTPException(400, "Unsupported language")
    try:
        r = httpx.post(f"{settings.sandbox_url}/run",
                       json={"language": body.language, "code": body.code,
                             "stdin": body.stdin or ""},
                       headers={"X-Sandbox-Token": settings.sandbox_token},
                       timeout=30.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Sandbox unavailable: {e}")

@router.get("/snippets", response_model=list[SnippetOut])
def list_snippets(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Snippet).where(Snippet.user_id == user.id)
                      .order_by(Snippet.created_at.desc())).all()

@router.post("/snippets", response_model=SnippetOut, status_code=201)
def save_snippet(body: SnippetIn, user: User = Depends(current_user),
                 db: Session = Depends(get_db)):
    s = Snippet(user_id=user.id, **body.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return s