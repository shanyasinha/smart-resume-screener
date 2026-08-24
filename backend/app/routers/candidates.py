import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Candidate, CandidateStatus
from app.schemas import CandidateOut, StatusUpdate

router = APIRouter(tags=["candidates"])


@router.get("/api/jobs/{job_id}/candidates", response_model=list[CandidateOut])
def list_candidates(
    job_id: int,
    db: Session = Depends(get_db),
    min_score: float = Query(0, ge=0, le=100),
    status: str | None = None,
    sort: str = Query("match_score", pattern="^(match_score|experience_years|created_at)$"),
):
    q = db.query(Candidate).filter(Candidate.job_id == job_id, Candidate.match_score >= min_score)
    if status:
        q = q.filter(Candidate.status == status)
    q = q.order_by(getattr(Candidate, sort).desc())
    return q.all()


@router.get("/api/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    return candidate


@router.patch("/api/candidates/{candidate_id}/status", response_model=CandidateOut)
def update_status(candidate_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    if payload.status not in [s.value for s in CandidateStatus]:
        raise HTTPException(400, f"status must be one of {[s.value for s in CandidateStatus]}")
    candidate.status = payload.status
    db.commit()
    db.refresh(candidate)
    return candidate


@router.delete("/api/candidates/{candidate_id}", status_code=204)
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    db.delete(candidate)
    db.commit()


@router.get("/api/jobs/{job_id}/candidates/export.csv")
def export_candidates_csv(job_id: int, db: Session = Depends(get_db)):
    candidates = (
        db.query(Candidate)
        .filter(Candidate.job_id == job_id)
        .order_by(Candidate.match_score.desc())
        .all()
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Name", "Email", "Phone", "Match Score", "Experience (yrs)",
        "Matched Skills", "Missing Skills", "Status", "Justification",
    ])
    for c in candidates:
        writer.writerow([
            c.name, c.email, c.phone, c.match_score, c.experience_years,
            "; ".join(c.matched_skills or []), "; ".join(c.missing_skills or []),
            c.status, c.justification,
        ])
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}_shortlist.csv"},
    )
