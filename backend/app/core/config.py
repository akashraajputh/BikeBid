import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bikebid.db")
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
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:5174",
                    "http://127.0.0.1:5174",
                ]
            )
        )


settings = Settings()
