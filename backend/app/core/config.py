import os
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()


def _database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bikebid.db")
    password_placeholder = "${AIVEN_PASSWORD}"
    password = os.getenv("AIVEN_PASSWORD")
    if password_placeholder in database_url and password is not None:
        database_url = database_url.replace(
            password_placeholder,
            quote(password, safe=""),
        )
    return database_url


class Settings:
    DATABASE_URL = _database_url()
    AUTO_CREATE_SCHEMA = os.getenv(
        "AUTO_CREATE_SCHEMA",
        DATABASE_URL.startswith("sqlite+aiosqlite:"),
    ).lower() in {"1", "true", "yes"}
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-before-deploy")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    APP_NAME = "BikeBid"

    @property
    def cors_origins(self) -> list[str]:
        return list(
            dict.fromkeys(
                [
                    self.FRONTEND_URL,
                    "https://bikebid.onrender.com",
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:5174",
                    "http://127.0.0.1:5174",
                ]
            )
        )


settings = Settings()
