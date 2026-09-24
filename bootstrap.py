"""Called by docker-compose before uvicorn starts."""
from .db import Base, engine, SessionLocal
from .models import User, Course, Module, Lesson
from .security import hash_password
from sqlalchemy import select
import time

def wait_for_db():
    for _ in range(30):
        try:
            with engine.connect(): return
        except Exception:
            time.sleep(1)
    raise RuntimeError("DB unavailable")

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == "admin@techmusha.dev")):
            return
        admin = User(name="Admin", email="admin@techmusha.dev", role="admin",
                     password_hash=hash_password("password123"), verified=True)
        instr = User(name="Tendai Instructor", email="instructor@techmusha.dev",
                     role="instructor", password_hash=hash_password("password123"),
                     verified=True)
        student = User(name="Rudo Student", email="student@techmusha.dev",
                       password_hash=hash_password("password123"), verified=True)
        db.add_all([admin, instr, student]); db.commit()

        samples = [
            ("Intro to Computer Science", "computer-science", "beginner", 0.0,
             "Foundations of computing: hardware, software, algorithms, and how computers think."),
            ("Modern JavaScript from Scratch", "software-development", "beginner", 0.0,
             "Learn JavaScript with hands-on exercises you can run in the in-app sandbox."),
            ("Cybersecurity Essentials", "cybersecurity", "intermediate", 15.0,
             "Threat models, cryptography basics, network defense, and safe coding practices."),
            ("Networking Fundamentals", "networking", "beginner", 0.0,
             "TCP/IP, DNS, routing, and practical troubleshooting for African ISPs."),
            ("Blockchain & Web3 for Africa", "blockchain", "intermediate", 20.0,
             "Build on public chains, understand smart contracts, and explore remittance use cases."),
        ]
        for title, cat, lvl, price, desc in samples:
            c = Course(title=title, slug=title.lower().replace(" ", "-"),
                       description=desc, category=cat, level=lvl, price=price,
                       instructor_id=instr.id)
            db.add(c); db.flush()
            m = Module(course_id=c.id, title="Getting Started", order=0)
            db.add(m); db.flush()
            db.add(Lesson(module_id=m.id, title="Welcome", type="doc", order=0,
                          body="# Welcome\n\nThis course is offline-ready. Download it to learn without internet."))
            db.add(Lesson(module_id=m.id, title="Your first program", type="code", order=1,
                          language="python", starter_code="print('Mhoro, Zimbabwe!')"))
            m2 = Module(course_id=c.id, title="Core Concepts", order=1)
            db.add(m2); db.flush()
            db.add(Lesson(module_id=m2.id, title="Overview", type="doc", order=0,
                          body="Core concepts go here."))
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    wait_for_db(); seed(); print("Bootstrap complete.")