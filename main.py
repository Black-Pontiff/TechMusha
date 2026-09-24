from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import Base, engine
from .routers import auth, courses, enrollments, documents, sandbox, reviews, certificates, admin

app = FastAPI(title="TechMusha API", version="0.1.0",
              description="Offline-first learning platform for Zimbabwe.")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for r in (auth.router, courses.router, enrollments.router, documents.router,
          sandbox.router, reviews.router, certificates.router, admin.router):
    app.include_router(r)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)