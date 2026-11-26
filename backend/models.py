import os
from datetime import datetime
from sqlalchemy import create_engine, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./fitwell.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    job_title: Mapped[str] = mapped_column(String(120))
    score: Mapped[float] = mapped_column(Float)
    matched: Mapped[list] = mapped_column(JSON)
    missing: Mapped[list] = mapped_column(JSON)
    breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    disclaimer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
