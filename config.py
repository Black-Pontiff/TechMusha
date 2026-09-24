from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://techmusha:techmusha@db:5432/techmusha"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    refresh_token_days: int = 30
    sandbox_url: str = "http://sandbox:9000"
    sandbox_token: str = "dev-token"
    storage_path: str = "/data/storage"
    max_upload_mb: int = 100
    cors_origins: str = "*"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()