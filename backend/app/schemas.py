import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    title: str
    description: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    must_have_skills: list[str] = []
    created_at: datetime.datetime
    candidate_count: int = 0


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    filename: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: list[str] = []
    experience_years: Optional[float] = None
    education: list[str] = []
    match_score: float
    llm_score: Optional[float] = None
    keyword_score: Optional[float] = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    justification: Optional[str] = None
    status: str
    created_at: datetime.datetime


class CandidateSummary(BaseModel):
    """Lighter payload for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    name: Optional[str] = None
    match_score: float
    status: str


class StatusUpdate(BaseModel):
    status: str
