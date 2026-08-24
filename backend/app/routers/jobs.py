from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Candidate
from app.schemas import JobCreate, JobOut
from app.parsing import extract_must_have_skills

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobOut, status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    job = Job(
        title=payload.title,
        description=payload.description,
        must_have_skills=extract_must_have_skills(payload.description),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return JobOut(**job.__dict__, candidate_count=0)


@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    rows = (
        db.query(Job, func.count(Candidate.id).label("candidate_count"))
        .outerjoin(Candidate)
        .group_by(Job.id)
        .order_by(Job.created_at.desc())
        .all()
    )
    return [JobOut(**job.__dict__, candidate_count=count) for job, count in rows]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    count = db.query(func.count(Candidate.id)).filter(Candidate.job_id == job_id).scalar()
    return JobOut(**job.__dict__, candidate_count=count)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    db.delete(job)
    db.commit()
