from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Candidate
from app.schemas import CandidateOut
from app.parsing import parse_resume
from app.llm_matcher import score_resume

router = APIRouter(prefix="/api/jobs/{job_id}/resumes", tags=["resumes"])

ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")
MAX_FILE_SIZE = 8 * 1024 * 1024  # 8 MB per resume


def _get_job_or_404(job_id: int, db: Session) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


async def _analyze_one(job: Job, upload: UploadFile, db: Session) -> Candidate | None:
    """Parses + scores a single uploaded file into a stored Candidate row.
    Returns None (and skips, rather than failing the whole batch) for a file
    that's the wrong type or too large — one bad file in a bulk upload
    shouldn't sink the other 49."""
    if not upload.filename.lower().endswith(ALLOWED_EXTENSIONS):
        return None

    file_bytes = await upload.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        return None
    if not file_bytes:
        return None

    parsed = parse_resume(upload.filename, file_bytes)
    if not parsed["raw_text"].strip():
        return None  # unreadable / scanned-image PDF with no extractable text

    match = score_resume(
        job_description=job.description,
        resume_text=parsed["raw_text"],
        jd_skills=job.must_have_skills or [],
        resume_skills=parsed["skills"],
    )

    candidate = Candidate(
        job_id=job.id,
        filename=upload.filename,
        raw_text=parsed["raw_text"],
        name=parsed["name"],
        email=parsed["email"],
        phone=parsed["phone"],
        skills=parsed["skills"],
        education=parsed["education"],
        experience_years=parsed["experience_years"],
        match_score=match["match_score"],
        llm_score=match["llm_score"],
        keyword_score=match["keyword_score"],
        matched_skills=match["matched_skills"],
        missing_skills=match["missing_skills"],
        justification=match["justification"],
    )
    db.add(candidate)
    return candidate


@router.post("/analyze", response_model=CandidateOut)
async def analyze_single_resume(
    job_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Single-CV analysis: upload one resume, get back its full scored profile."""
    job = _get_job_or_404(job_id, db)
    candidate = await _analyze_one(job, file, db)
    if candidate is None:
        raise HTTPException(400, f"Could not read '{file.filename}' — use PDF, DOCX, or TXT under 8MB.")
    db.commit()
    db.refresh(candidate)
    return candidate


@router.post("/analyze-bulk", response_model=list[CandidateOut])
async def analyze_bulk_resumes(
    job_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db)
):
    """Bulk-CV analysis: upload many resumes at once, get back a scored,
    rank-able list. Each file is parsed and scored independently so one
    failure doesn't block the batch."""
    job = _get_job_or_404(job_id, db)
    if len(files) > 100:
        raise HTTPException(400, "Max 100 resumes per batch.")

    results = []
    for upload in files:
        candidate = await _analyze_one(job, upload, db)
        if candidate is not None:
            results.append(candidate)

    db.commit()
    for c in results:
        db.refresh(c)

    if not results:
        raise HTTPException(400, "None of the uploaded files could be read as PDF/DOCX/TXT resumes.")
    return results
