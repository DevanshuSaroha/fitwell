import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
from fastapi.testclient import TestClient
from main import app
import ml

client = TestClient(app)
RESUME = "Python developer with FastAPI, SQL and Docker experience. Built machine learning models with scikit-learn."
JOB = "We need an engineer skilled in Python, FastAPI, SQL, Docker, Kubernetes and AWS to build APIs."


def auth():
    r = client.post("/api/auth/register", json={"email": "a@b.com", "password": "secret1"})
    if r.status_code == 409:
        r = client.post("/api/auth/login", json={"email": "a@b.com", "password": "secret1"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_skill_matching():
    r = ml.analyze(RESUME, JOB)
    assert "python" in r["matched"] and "kubernetes" in r["missing"]
    assert 0 <= r["score"] <= 100


def test_auth_rules():
    auth()
    assert client.post("/api/auth/register", json={"email": "a@b.com", "password": "secret1"}).status_code == 409
    assert client.post("/api/auth/login", json={"email": "a@b.com", "password": "wrong-pass"}).status_code == 401
    assert client.post("/api/auth/register", json={"email": "bad", "password": "secret1"}).status_code == 422
    assert client.get("/api/analyses").status_code == 401


def test_analysis_flow():
    h = auth()
    r = client.post("/api/analyses", headers=h, json={"job_title": "Backend Engineer", "job_description": JOB, "resume": RESUME})
    assert r.status_code == 201 and r.json()["score"] > 30
    assert len(client.get("/api/analyses", headers=h).json()) == 1
    assert client.get("/api/stats", headers=h).json()["total"] == 1
    assert client.delete(f"/api/analyses/{r.json()['id']}", headers=h).status_code == 204
    assert client.get("/api/stats", headers=h).json()["total"] == 0
