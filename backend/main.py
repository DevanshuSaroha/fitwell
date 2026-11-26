import re
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from models import Base, engine, get_db, User, Analysis
from auth import hash_password, verify_password, make_token, current_user
import ml

Base.metadata.create_all(engine)
# Additive SQLite migration for databases created by earlier versions.
with engine.begin() as connection:
    columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(analyses)")}
    if "breakdown" not in columns:
        connection.exec_driver_sql("ALTER TABLE analyses ADD COLUMN breakdown JSON")
    if "evidence" not in columns:
        connection.exec_driver_sql("ALTER TABLE analyses ADD COLUMN evidence JSON")
    if "disclaimer" not in columns:
        connection.exec_driver_sql("ALTER TABLE analyses ADD COLUMN disclaimer VARCHAR(500)")

app = FastAPI(title="Fitwell API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


class Credentials(BaseModel):
    email: str
    password: str = Field(min_length=6, max_length=100)

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("Enter a valid email address.")
        return v


class AnalysisIn(BaseModel):
    job_title: str = Field(min_length=2, max_length=120)
    job_description: str = Field(min_length=30, max_length=8000)
    resume: str = Field(min_length=30, max_length=8000)


def out(a: Analysis) -> dict:
    return {"id": a.id, "job_title": a.job_title, "score": a.score,
            "matched": a.matched, "missing": a.missing, "created": a.created.isoformat(),
            "advice": ml.advice(a.score, a.missing),
            "breakdown": a.breakdown,
            "evidence": a.evidence,
            "disclaimer": a.disclaimer or "Indicative screening aid only—not a hiring decision."}


@app.post("/api/auth/register", status_code=201)
def register(c: Credentials, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == c.email)):
        raise HTTPException(409, "That email is already registered.")
    user = User(email=c.email, password_hash=hash_password(c.password))
    db.add(user); db.commit()
    return {"token": make_token(user.id), "email": user.email}


@app.post("/api/auth/login")
def login(c: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == c.email))
    if not user or not verify_password(c.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    return {"token": make_token(user.id), "email": user.email}


@app.post("/api/analyses", status_code=201)
def create(body: AnalysisIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = ml.analyze(body.resume, body.job_description)
    a = Analysis(user_id=user.id, job_title=body.job_title.strip(),
                 score=r["score"], matched=r["matched"], missing=r["missing"],
                 breakdown=r["breakdown"], evidence=r["evidence"], disclaimer=r["disclaimer"])
    db.add(a); db.commit(); db.refresh(a)
    return out(a)


@app.get("/api/analyses")
def list_all(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Analysis).where(Analysis.user_id == user.id)
                      .order_by(Analysis.id.desc())).all()
    return [out(a) for a in rows]


@app.delete("/api/analyses/{aid}", status_code=204)
def delete(aid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    a = db.get(Analysis, aid)
    if not a or a.user_id != user.id:
        raise HTTPException(404, "Analysis not found.")
    db.delete(a); db.commit()


@app.get("/api/stats")
def stats(user: User = Depends(current_user), db: Session = Depends(get_db)):
    total, avg, best = db.execute(select(func.count(Analysis.id), func.avg(Analysis.score),
                                         func.max(Analysis.score)).where(Analysis.user_id == user.id)).one()
    return {"total": total, "average": round(avg or 0, 1), "best": best or 0}
