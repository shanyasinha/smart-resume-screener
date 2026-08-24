import datetime
import enum
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base


class CandidateStatus(str, enum.Enum):
    new = "new"
    shortlisted = "shortlisted"
    rejected = "rejected"


class Job(Base):
    """A single job opening: a title + job description recruiters screen resumes against."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    must_have_skills = Column(JSON, default=list)  # extracted once at job-creation time
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    """One parsed + scored resume, tied to a job."""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    filename = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)

    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)

    skills = Column(JSON, default=list)
    experience_years = Column(Float, nullable=True)
    education = Column(JSON, default=list)

    match_score = Column(Float, nullable=False, default=0.0)       # 0-100 blended score
    llm_score = Column(Float, nullable=True)                       # 0-100 raw LLM score
    keyword_score = Column(Float, nullable=True)                   # 0-100 rules-based score
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    justification = Column(Text, nullable=True)                    # LLM's plain-English reasoning

    status = Column(Enum(CandidateStatus), default=CandidateStatus.new)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    job = relationship("Job", back_populates="candidates")
