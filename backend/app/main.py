from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import CORS_ORIGINS
from app.routers import jobs, resumes, candidates

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Resume Screener API",
    description=(
        "Parses resumes, extracts structured data, and uses an LLM to score "
        "candidate fit against a job description — with a transparent, "
        "explainable justification for every score."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(candidates.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
