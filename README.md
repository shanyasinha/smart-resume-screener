# Smart Resume Screener

Parses resumes, extracts structured candidate data, and uses an LLM to score
candidate fit against a job description — with a transparent, explainable
justification for every score. Supports both **single-resume** analysis and
**bulk** (batch) analysis.

![status](https://img.shields.io/badge/status-working_demo-4FD1C5)
![python](https://img.shields.io/badge/backend-FastAPI-1A222D)
![frontend](https://img.shields.io/badge/frontend-React_%2B_Vite-1A222D)

## What it does

1. A recruiter creates a **job opening** by pasting a job description.
2. They upload one resume (single-CV analysis) or a batch of resumes
   (bulk analysis) as PDF, DOCX, or TXT.
3. Each resume is parsed into structured fields (name, contact info, skills,
   education, estimated years of experience) and scored against the JD.
4. Scores, matched/missing skills, and a plain-English justification are
   shown in a ranked, filterable dashboard. Recruiters can move candidates
   through a status pipeline (new → shortlisted / rejected) and export the
   shortlist to CSV.

## Architecture

```
┌─────────────────┐        REST/JSON        ┌──────────────────────┐
│   React + Vite   │ <──────────────────────> │   FastAPI backend     │
│   frontend        │                          │                        │
│                    │                          │  ┌──────────────────┐  │
│  Dashboard         │                          │  │ parsing.py        │  │
│  Job detail        │                          │  │ (PDF/DOCX/TXT →   │  │
│  Candidate detail   │                         │  │  structured data) │  │
└─────────────────┘                            │  └──────────────────┘  │
                                                 │  ┌──────────────────┐  │
                                                 │  │ llm_matcher.py    │  │
                                                 │  │ (LLM + keyword    │  │
                                                 │  │  blended scoring) │  │
                                                 │  └──────────────────┘  │
                                                 │           │            │
                                                 │           ▼            │
                                                 │      SQLite (Jobs,     │
                                                 │      Candidates)       │
                                                 └──────────────────────┘
                                                            │
                                                            ▼
                                              Anthropic Claude / OpenAI API
```

**Backend** (`/backend`) — FastAPI + SQLAlchemy + SQLite.
- `app/parsing.py` — extracts text from PDF/DOCX/TXT (`pdfplumber`,
  `python-docx`) and pulls structured fields (name, email, phone, skills,
  education, estimated experience) using regex + a skill-vocabulary match.
  This runs **before** the LLM call and acts as both a fallback and a
  cross-check. Falls back to OCR (via PyMuPDF + Tesseract) for PDFs with no
  extractable text layer — see [OCR fallback](#ocr-fallback-for-image-only-pdfs)
  below.
- `app/llm_matcher.py` — sends the resume + JD to an LLM, gets back a
  structured score/justification, and **blends** it with a transparent
  keyword-overlap score (see [Scoring methodology](#scoring-methodology)
  below). If no LLM API key is configured, the app still works end-to-end
  using the keyword score alone.
- `app/models.py` / `schemas.py` — SQLAlchemy models + Pydantic schemas for
  `Job` and `Candidate`.
- `app/routers/` — `jobs.py` (CRUD), `resumes.py` (single + bulk analyze),
  `candidates.py` (list/filter/status update/CSV export).

**Frontend** (`/frontend`) — React + Vite + Tailwind, three screens:
- **Dashboard** — create a job, browse existing job openings.
- **Job detail** — JD panel with auto-extracted must-have skills, a
  drag-and-drop upload zone (single or multi-file), a ranked candidate
  table with a live minimum-score filter and inline status changes.
- **Candidate detail** — full score breakdown (radial "match dial"),
  matched vs. missing skills, the LLM's justification, and parsed
  education/experience.

## Scoring methodology

Every candidate gets **two independent scores** that are blended into the
final `match_score` (0–100):

| Signal | What it measures | Weight |
|---|---|---|
| `keyword_score` | Overlap between skills detected in the JD and skills detected in the resume, against a ~90-term skill vocabulary. Deterministic and fully transparent. | 30% |
| `llm_score` | The LLM's semantic judgement of overall fit (1–10), which also produces the plain-English justification and can catch skills implied by project descriptions that keyword matching misses. | 70% |

The weight is configurable via `LLM_SCORE_WEIGHT` in `.env`. Blending both
means the score is never a pure LLM black box, and never purely
keyword-matching that misses paraphrased skills. If the LLM call fails for
any reason (no API key, rate limit, network error), the app **degrades
gracefully** to the keyword score rather than failing the request.

### LLM prompts

**System prompt:**
```
You are an expert technical recruiter's assistant. You evaluate how well a
candidate's resume fits a job description. You are rigorous and
evidence-based: every claim you make must be traceable to specific text in
the resume. You never invent experience the resume does not support. You
output ONLY valid JSON, no prose, no markdown fences.
```

**User prompt** (per the assignment's suggested framing — "Compare the
following resume with this job description and rate fit on 1–10 with
justification"):
```
Compare the following resume with this job description and rate the
fit on a 1-10 scale, with justification.

JOB DESCRIPTION:
"""
{job_description}
"""

RESUME:
"""
{resume_text}
"""

Return ONLY a JSON object with exactly this shape:
{
  "score": <integer 1-10, overall fit>,
  "matched_skills": [<skills/requirements from the JD the resume clearly demonstrates>],
  "missing_skills": [<skills/requirements from the JD the resume does not show>],
  "experience_assessment": "<one sentence on whether experience level fits>",
  "justification": "<2-3 sentences a recruiter could read directly, citing specific resume evidence>"
}
```

Full source: [`backend/app/llm_matcher.py`](backend/app/llm_matcher.py).

## OCR fallback for image-only PDFs

Some PDFs — scanned documents, or ones exported by certain resume-builder
sites — have subsetted fonts with no Unicode character map. The text is
visually present and even selectable in a PDF viewer, but no library can
recover the actual characters from it (this trips up real-world ATS tools
too, not just this project). `parsing.py` detects when normal extraction
returns near-empty text and automatically falls back to rendering the page
as an image and running Tesseract OCR on it.

This requires the **Tesseract OCR** program installed as a system binary
(not just a Python package):
- **Docker Compose users**: already included in `backend/Dockerfile` — no
  action needed.
- **Windows (running locally)**: install from the
  [UB-Mannheim Tesseract build](https://github.com/UB-Mannheim/tesseract/wiki),
  then make sure it's on your PATH (the installer offers to do this).
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt install tesseract-ocr`

If Tesseract isn't installed, the app doesn't crash — it just skips the OCR
step and reports the file as unreadable, same as before this feature
existed.

## Getting started

### Option A — Docker Compose (recommended, one command)

```bash
cp backend/.env.example backend/.env
# optionally add an ANTHROPIC_API_KEY or OPENAI_API_KEY to backend/.env
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

### Option B — run locally

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # optionally add an API key
uvicorn app.main:app --reload
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

### Try it without any API key

The app works out of the box with `LLM_PROVIDER=none` (or simply no key set)
— it falls back to the transparent keyword-matching score, so you can
create a job, upload the sample resumes in `backend/sample_data/`, and see
the full flow without any external dependency.

## Sample data

`backend/sample_data/` contains a sample job description and three resumes
(strong / partial / weak fit) for a quick demo:
```
backend/sample_data/job_description.txt
backend/sample_data/candidate_strong_fit.txt
backend/sample_data/candidate_partial_fit.txt
backend/sample_data/candidate_weak_fit.txt
```

## Known limitations

- **Experience-years estimate** is a heuristic (sums date ranges found in
  the text) and can double-count if a resume lists both an education date
  range and overlapping work date ranges — shown as an estimate, not a
  guaranteed-accurate figure.
- **Skill extraction** uses a fixed ~90-term vocabulary rather than a full
  taxonomy; niche or emerging skills outside that list won't be tagged by
  the keyword layer (though the LLM layer can still catch them).
- **Name extraction** is a best-effort heuristic (first name-like line);
  unusually formatted resumes may need manual correction.
- No authentication layer — this is a local/demo deployment, not
  production-hardened for multi-tenant use.

## Tech stack

Backend: FastAPI, SQLAlchemy, SQLite, pdfplumber, python-docx, Anthropic/OpenAI SDKs
Frontend: React, Vite, Tailwind CSS, React Router
