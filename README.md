# Fitwell: resume-to-job match analyzer

Paste a resume and a job description; Fitwell scores the match, lists the skills you have and the ones you're missing, and keeps a history in your account.

## Tech
- **Frontend:** React, TypeScript, React Router, Vite
- **Backend:** Python, FastAPI, SQLAlchemy, SQLite, JWT authentication
- **ML:** scikit-learn TF-IDF cosine similarity combined with skill-overlap scoring
- **Quality:** pytest API tests, Docker Compose

## How the score works
`score = 60% skill coverage (job skills found in the resume) + 40% TF-IDF text similarity`

## Run locally
    # backend
    cd backend && python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt && uvicorn main:app --reload
    # frontend (new terminal)
    cd frontend && npm install && npm run dev
Open http://localhost:5173. API docs: http://localhost:8000/docs

## Run with Docker
    docker compose up --build

## Tests
    cd backend && pytest

## API
| Method | Path | Purpose |
|---|---|---|
| POST | /api/auth/register, /api/auth/login | Create account / get token |
| POST | /api/analyses | Run and save a match analysis |
| GET | /api/analyses | List my analyses |
| DELETE | /api/analyses/{id} | Delete one |
| GET | /api/stats | Totals, average and best score |

## Ideas to extend
PDF resume upload, a trained model on real job postings, per-skill learning links, deployment (Render + Vercel).
