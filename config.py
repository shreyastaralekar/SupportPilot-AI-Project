import os

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "supportpilot")

DATABASE_URL = os.environ.get("DATABASE_URL")

ADMIN_ID = os.environ.get("ADMIN_ID", "ADMIN001")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("Set the ADMIN_PASSWORD environment variable.")

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Set the SECRET_KEY environment variable.")