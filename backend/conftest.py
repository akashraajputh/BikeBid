import os


database_url = os.getenv("DATABASE_URL")
if not database_url:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./bikebid_test.db"
    os.environ["AUTO_CREATE_SCHEMA"] = "true"
elif database_url.startswith("sqlite+aiosqlite:"):
    os.environ.setdefault("AUTO_CREATE_SCHEMA", "true")
