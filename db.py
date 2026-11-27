from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, MetaData, String, Table, Text, create_engine, text
from sqlalchemy.engine import URL
import config


def make_engine():
    if config.DATABASE_URL:
        return create_engine(config.DATABASE_URL)
    url = URL.create("mysql+pymysql", config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_PORT)
    with create_engine(url).begin() as c:
        c.execute(text(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` CHARACTER SET utf8mb4"))
    return create_engine(url.set(database=config.DB_NAME), pool_pre_ping=True)


engine = make_engine()
meta = MetaData()
users = Table(
    "users", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("role", String(10), nullable=False),               # admin / employee
    Column("login_id", String(120), unique=True, nullable=False),  # Admin ID or employee email
    Column("name", String(100), nullable=False),
    Column("email", String(120), nullable=False),
    Column("department", String(40)),
    Column("password_hash", String(255), nullable=False),
    Column("created_at", DateTime, nullable=False),
)
tickets = Table(
    "tickets", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ticket_id", String(20), unique=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("title", String(150), nullable=False),
    Column("description", Text, nullable=False),
    Column("category", String(60)), Column("sub_category", String(60)),
    Column("severity", String(10)), Column("confidence", Float),
    Column("ai_status", String(15)),                           # Classified / Needs review
    Column("priority", String(20)), Column("sla_hours", Integer),
    Column("status", String(10), nullable=False),              # Open / Closed
    Column("created_at", DateTime, nullable=False),
    Column("due_at", DateTime), Column("closed_at", DateTime),
)
meta.create_all(engine)
