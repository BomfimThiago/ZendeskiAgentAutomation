from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    SHOW_DOCS_ENVIRONMENT: tuple = ("local", "staging", "development")

    ZENDESKI_URL: str  # This will read from .env
    ZENDESKI_TOKEN: str  # This will read from .env

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_HEADERS: list[str] = ["*"]

    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()