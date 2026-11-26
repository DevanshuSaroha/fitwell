"""Transparent, explainable resume-to-job matching.

Lexical baseline only: it reports explicit keyword matches and makes no claim
about experience, proficiency, or hiring suitability.
"""
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "sql", "html", "css",
    "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi", "spring boot",
    "machine learning", "deep learning", "nlp", "natural language processing", "computer vision",
    "data analysis", "data science", "statistics", "pandas", "numpy", "scikit-learn", "tensorflow",
    "pytorch", "power bi", "tableau", "excel", "mysql", "postgresql", "mongodb", "redis",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux", "ci/cd", "rest api", "graphql",
    "microservices", "agile", "scrum", "testing", "unit testing", "data structures", "algorithms",
    "oop", "object-oriented programming", "communication", "teamwork", "problem solving",
    "project management", "leadership", "salesforce", "sap", "jira", "confluence", "figma",
    "photoshop", "seo", "content strategy", "financial modeling", "accounting", "audit",
]


def find_skills(text: str) -> set[str]:
    t = text.lower()
    return {skill for skill in SKILLS if re.search(
        r"(?<![a-z0-9+#])" + re.escape(skill) + r"(?![a-z0-9+#])", t
    )}


def evidence(text: str, skill: str) -> str:
    match = re.search(re.escape(skill), text, re.I)
    if not match:
        return ""
    start = max(0, match.start() - 90)
    end = min(len(text), match.end() + 110)
    snippet = re.sub(r"\s+", " ", text[start:end]).strip()
    if start:
        snippet = "…" + snippet
    if end < len(text):
        snippet += "…"
    return snippet


def analyze(resume: str, job: str) -> dict:
    resume_skills, job_skills = find_skills(resume), find_skills(job)
    matched = sorted(job_skills & resume_skills)
    missing = sorted(job_skills - resume_skills)

    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform([resume, job])
    text_sim = float(cosine_similarity(vec[0], vec[1])[0][0])

    if job_skills:
        coverage = len(matched) / len(job_skills)
        score = round(100 * (0.65 * coverage + 0.35 * text_sim), 1)
    else:
        coverage = text_sim
        score = round(100 * text_sim, 1)

    confidence = "high" if len(job_skills) >= 8 else "medium" if len(job_skills) >= 4 else "low"
    return {
        "score": min(score, 100.0),
        "matched": matched,
        "missing": missing,
        "breakdown": {
            "skill_coverage": round(coverage * 100, 1),
            "text_similarity": round(text_sim * 100, 1),
            "confidence": confidence,
            "skills_considered": len(job_skills),
        },
        "evidence": {
            "matched": {skill: evidence(resume, skill) for skill in matched},
            "missing": {skill: evidence(job, skill) for skill in missing},
        },
        "disclaimer": "Indicative screening aid only—not a hiring decision. It checks explicit keyword matches and does not verify experience, proficiency, or employment eligibility.",
    }


def advice(score: float, missing: list[str]) -> str:
    if score >= 75:
        return "Strong textual and skill alignment. Review the evidence, tailor your resume honestly, and apply."
    if score >= 45:
        tip = f" Prioritize verifiable experience with {', '.join(missing[:3])}." if missing else ""
        return "Partial alignment, with several gaps worth addressing." + tip
    return "This appears to be a stretch match. Build relevant evidence through projects or training before applying."
