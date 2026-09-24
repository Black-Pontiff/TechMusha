from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

# ---- Auth ----
class SignupIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    phone: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# ---- User ----
class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: Optional[str]
    role: str
    avatar: Optional[str]
    country: str
    language: str
    skill_level: str
    goals: Optional[str]
    verified: bool
    class Config: from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    language: Optional[str] = None
    skill_level: Optional[str] = None
    goals: Optional[str] = None
    country: Optional[str] = None

# ---- Courses ----
class LessonOut(BaseModel):
    id: str
    title: str
    type: str
    content_url: Optional[str]
    body: Optional[str]
    duration: int
    order: int
    starter_code: Optional[str]
    language: Optional[str]
    class Config: from_attributes = True

class ModuleOut(BaseModel):
    id: str
    title: str
    order: int
    lessons: List[LessonOut] = []
    class Config: from_attributes = True

class CourseOut(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    category: str
    level: str
    price: float
    currency: str
    instructor_id: str
    thumbnail: Optional[str]
    language: str
    class Config: from_attributes = True

class CourseDetailOut(CourseOut):
    modules: List[ModuleOut] = []

class CourseCreateIn(BaseModel):
    title: str
    description: str
    category: str
    level: str = "beginner"
    price: float = 0.0
    language: str = "en"
    thumbnail: Optional[str] = None

# ---- Enrollment / Progress ----
class EnrollmentOut(BaseModel):
    id: str
    course_id: str
    status: str
    progress: float
    enrolled_at: datetime
    completed_at: Optional[datetime]
    class Config: from_attributes = True

class ProgressIn(BaseModel):
    lesson_id: str
    completed: bool = False
    last_position: int = 0

class ProgressOut(BaseModel):
    lesson_id: str
    completed: bool
    last_position: int
    class Config: from_attributes = True

# ---- Documents ----
class DocumentOut(BaseModel):
    id: str
    title: str
    author: Optional[str]
    format: str
    size: int
    hash: str
    visibility: str
    status: str
    category: Optional[str]
    tags: Optional[List[str]]
    description: Optional[str]
    language: str
    url: str
    downloads: int
    created_at: datetime
    class Config: from_attributes = True

# ---- Reviews ----
class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class ReviewOut(BaseModel):
    id: str
    user_id: str
    course_id: str
    rating: int
    comment: Optional[str]
    created_at: datetime
    class Config: from_attributes = True

# ---- Sandbox ----
class RunIn(BaseModel):
    language: str
    code: str
    stdin: Optional[str] = ""

class RunOut(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    timed_out: bool = False

class SnippetIn(BaseModel):
    title: str = "Untitled"
    language: str
    code: str
    stdin: Optional[str] = ""

class SnippetOut(SnippetIn):
    id: str
    stdout: Optional[str]
    created_at: datetime
    class Config: from_attributes = True