# Smart Resume Screener

Parses resumes, extracts structured candidate data, and uses an LLM to score candidate fit against a job description — with a transparent, explainable justification for every score. Supports both **single-resume** analysis and **bulk (batch)** analysis.

![status](https://img.shields.io/badge/status-working_demo-4FD1C5)
![python](https://img.shields.io/badge/backend-FastAPI-1A222D)
![frontend](https://img.shields.io/badge/frontend-React_%2B_Vite-1A222D)

## What it does

1. A recruiter creates a **job opening** by pasting a job description.
2. They upload one resume (single-CV analysis) or a batch of resumes (bulk analysis) as PDF, DOCX, or TXT.
3. Each resume is parsed into structured fields (name, contact info, skills, education, estimated years of experience) and scored against the JD.
4. Scores, matched/missing skills, and a plain-English justification are shown in a ranked, filterable dashboard.
5. Recruiters can move candidates through a status pipeline (**new → shortlisted / rejected**) and export the shortlist to CSV.

## 🎥 Demo Video

Watch the complete Smart Resume Screener walkthrough:

👉 **[▶️ Watch the Demo Video](https://drive.google.com/file/d/1Q-ZoFXrLEMszKLw3Z3BXLLZzuNDTH7Fg/view?usp=drivesdk)**

The demo showcases the complete workflow:

* Creating a job opening from a job description
* Uploading a single resume
* Bulk resume analysis
* Resume parsing and structured data extraction
* AI-powered candidate scoring
* Matched and missing skill detection
* Explainable score justification
* Candidate ranking and filtering
* Updating candidate status
* Exporting shortlisted candidates to CSV

> **Note:** Make sure the Google Drive video's sharing permission is set to **Anyone with the link → Viewer** so recruiters and interviewers can access it.

## Architecture

```text
┌─────────────────┐        REST/JSON        ┌──────────────────────┐
│   React + Vite  │ <────────────────────> │   FastAPI Backend    │
│   Frontend      │                         │                      │
│                 │                         │  ┌────────────────┐  │
│  • Dashboard    │                         │  │ parsing.py     │  │
│  • Job detail   │                         │  │                │  │
│  • Candidate    │                         │  │ PDF/DOCX/TXT → │  │
│    detail       │                         │  │ structured data │  │
└─────────────────┘                         │  └────────────────┘  │
                                           │                      │
                                           │  ┌────────────────┐  │
                                           │  │ llm_matcher.py │  │
                                           │  │                │  │
                                           │  │ LLM + keyword  │  │
                                           │  │ blended scoring│  │
                                           │  └────────────────┘  │
                                           │           │          │
                                           │           ▼          │
                                           │      SQLite Database │
                                           │      Jobs/Candidates │
                                           └──────────────────────┘
                                                      │
                                                      ▼
                                           Anthropic Claude /
                                           OpenAI API
```

### Backend

The `/backend` directory contains the FastAPI application.

* **FastAPI** — REST API backend
* **SQLAlchemy** — database ORM
* **SQLite** — local database
* **Pydantic** — request/response validation

Important files:

* `app/parsing.py` — extracts text from PDF/DOCX/TXT (`pdfplumber`, `python-docx`) and pulls structured fields such as name, email, phone, skills, education, and estimated experience using regex and a skill-vocabulary match.
* `app/llm_matcher.py` — sends the resume and JD to an LLM, receives a structured score and justification, and blends it with a transparent keyword-overlap score.
* `app/models.py` / `schemas.py` — SQLAlchemy models and Pydantic schemas for `Job` and `Candidate`.
* `app/routers/jobs.py` — job CRUD operations.
* `app/routers/resumes.py` — single and bulk resume analysis.
* `app/routers/candidates.py` — candidate listing, filtering, status updates, and CSV export.

The parsing layer runs **before** the LLM call and acts as both a fallback and a cross-check.

For PDFs with no usable text layer, the system automatically falls back to OCR using **PyMuPDF + Tesseract**.

### Frontend

The `/frontend` directory contains the React + Vite application.

The frontend provides three main screens:

#### Dashboard

* Create a new job opening
* Browse existing job openings

#### Job Detail

* View the job description
* Automatically extract must-have skills
* Drag-and-drop resume upload
* Upload one or multiple resumes
* View ranked candidates
* Filter candidates by minimum score
* Change candidate status

#### Candidate Detail

* View complete match score
* Radial "match dial"
* Matched skills
* Missing skills
* LLM justification
* Parsed education
* Estimated experience
* Candidate status

## Scoring Methodology

Every candidate receives **two independent scores** that are blended into the final `match_score` from **0–100**.

| Signal          | What it measures                                                                                               | Weight |
| --------------- | -------------------------------------------------------------------------------------------------------------- | -----: |
| `keyword_score` | Overlap between skills detected in the JD and skills detected in the resume using a ~90-term skill vocabulary. |    30% |
| `llm_score`     | LLM's semantic judgement of overall candidate fit on a 1–10 scale.                                             |    70% |

The final score combines both signals:

```text
Final Score =
    (Keyword Score × 30%)
    +
    (LLM Score × 70%)
```

The weight is configurable through:

```text
LLM_SCORE_WEIGHT
```

in the `.env` file.

This blended approach provides two advantages:

1. **Transparency** — the keyword component provides a deterministic and explainable signal.
2. **Semantic understanding** — the LLM can recognize skills and experience implied by project descriptions that simple keyword matching may miss.

If the LLM call fails because of a missing API key, rate limit, network error, or another failure, the application **degrades gracefully to keyword-based scoring** rather than failing the entire request.

## LLM Prompts

### System Prompt

```text
You are an expert technical recruiter's assistant. You evaluate how well a
candidate's resume fits a job description. You are rigorous and
evidence-based: every claim you make must be traceable to specific text in
the resume. You never invent experience the resume does not support. You
output ONLY valid JSON, no prose, no markdown fences.
```

### User Prompt

The application compares the candidate's resume with the job description and asks the LLM to rate the overall fit from 1–10.

```text
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

Full implementation:

```text
backend/app/llm_matcher.py
```

## OCR Fallback for Image-Only PDFs

Some PDFs — particularly scanned documents or resumes exported by certain resume-builder websites — contain visually readable text without a usable text layer.

In these cases, normal PDF extraction may return little or no text.

`parsing.py` detects this situation and automatically falls back to OCR:

```text
PDF
 ↓
Normal text extraction
 ↓
Is usable text available?
 ├── Yes → Continue parsing
 │
 └── No
      ↓
Render PDF page as image
      ↓
Tesseract OCR
      ↓
Extract text
      ↓
Continue parsing
```

### Tesseract Installation

Tesseract must be installed as a **system binary**, not just as a Python package.

#### Docker Compose

Tesseract is already included in `backend/Dockerfile`.

No additional setup is required.

#### Windows

Install the UB-Mannheim Tesseract build:

https://github.com/UB-Mannheim/tesseract/wiki

Make sure Tesseract is available on your system `PATH`.

#### macOS

```bash
brew install tesseract
```

#### Linux

```bash
sudo apt install tesseract-ocr
```

If Tesseract is unavailable, the application does not crash. It simply skips the OCR step and reports the file as unreadable.

## Getting Started

### Option A — Docker Compose

Recommended for the easiest setup.

```bash
cp backend/.env.example backend/.env
```

Optionally add an Anthropic or OpenAI API key to:

```text
backend/.env
```

Then run:

```bash
docker compose up --build
```

The application will be available at:

* Frontend: http://localhost:5173
* Backend API documentation: http://localhost:8000/docs

## Option B — Run Locally

### Backend

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

#### Windows

```bash
.venv\Scripts\activate
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```bash
cp .env.example .env
```

Optionally configure an LLM API key.

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

### Frontend

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

## Try It Without an API Key

The application works without an external LLM API.

Set:

```text
LLM_PROVIDER=none
```

or simply leave the API key unconfigured.

In this mode, the system uses the transparent keyword-matching score.

You can create a job, upload the sample resumes, and test the complete workflow without an external API dependency.

## Sample Data

The repository contains sample data under:

```text
backend/sample_data/
```

Included files:

```text
backend/sample_data/job_description.txt
backend/sample_data/candidate_strong_fit.txt
backend/sample_data/candidate_partial_fit.txt
backend/sample_data/candidate_weak_fit.txt
```

The three sample candidates represent:

* **Strong fit**
* **Partial fit**
* **Weak fit**

These files can be used to quickly demonstrate the ranking and scoring functionality.

## Project Workflow

The complete processing pipeline is:

```text
Job Description
       │
       ▼
Extract JD Skills
       │
       ▼
Upload Resume(s)
       │
       ▼
PDF / DOCX / TXT Parsing
       │
       ▼
OCR Fallback if Required
       │
       ▼
Structured Candidate Data
       │
       ├───────────────┐
       ▼               ▼
Keyword Matching    LLM Analysis
       │               │
       └───────┬───────┘
               ▼
        Blended Score
               │
               ▼
     Matched / Missing Skills
               │
               ▼
      Explainable Justification
               │
               ▼
       Candidate Ranking
               │
               ▼
     Shortlist / Reject
               │
               ▼
          CSV Export
```

## Key Features

* 📄 **Multi-format resume parsing** — PDF, DOCX, and TXT
* 🤖 **LLM-powered candidate evaluation**
* 🔍 **Transparent keyword-based scoring**
* 🧠 **Semantic skill matching**
* 📊 **Blended candidate score**
* 🎯 **Matched and missing skill detection**
* 📝 **Explainable recruiter-friendly justification**
* 📦 **Bulk resume analysis**
* 🔎 **Candidate filtering and ranking**
* 🔄 **Candidate status pipeline**
* 📥 **CSV shortlist export**
* 🖼️ **OCR support for image-only PDFs**
* ⚡ **Graceful fallback when LLM APIs are unavailable**
* 💾 **SQLite persistence**
* 🔌 **REST API using FastAPI**

## Known Limitations

### Experience Estimation

The experience-years estimate is heuristic.

The system sums date ranges found in the resume, which can sometimes double-count overlapping periods, particularly when education and employment dates overlap.

The result should therefore be treated as an **estimate**, not a guaranteed accurate value.

### Skill Extraction

The keyword layer currently uses a fixed vocabulary of approximately 90 skills.

Niche or emerging technologies outside the vocabulary may not be detected by the keyword layer.

The LLM layer can still identify some of these skills through semantic analysis.

### Name Extraction

Name extraction is best-effort and is based on heuristics such as the first name-like line in the resume.

Unusually formatted resumes may require manual correction.

### Authentication

The current application does not include an authentication or authorization layer.

It is intended as a **local/demo deployment** and is not production-hardened for multi-tenant usage.

## Tech Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* SQLite
* Pydantic
* pdfplumber
* python-docx
* PyMuPDF
* Tesseract OCR
* Anthropic SDK
* OpenAI SDK

### Frontend

* React
* Vite
* Tailwind CSS
* React Router

## Future Improvements

Potential improvements for a production-ready version include:

* Authentication and role-based access control
* PostgreSQL instead of SQLite
* Background job processing for large resume batches
* Better resume section classification
* Larger and configurable skill taxonomy
* Advanced experience calculation
* Duplicate resume detection
* Recruiter notes and candidate comments
* Job-specific scoring weights
* Candidate comparison view
* Analytics dashboard
* Cloud deployment
* Audit logs for candidate decisions
* Improved OCR and document parsing
* Automated interview recommendations

## Project Structure

```text
smart-resume-screener/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── jobs.py
│   │   │   ├── resumes.py
│   │   │   └── candidates.py
│   │   │
│   │   ├── parsing.py
│   │   ├── llm_matcher.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── main.py
│   │
│   ├── sample_data/
│   │   ├── job_description.txt
│   │   ├── candidate_strong_fit.txt
│   │   ├── candidate_partial_fit.txt
│   │   └── candidate_weak_fit.txt
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.*
│
├── docker-compose.yml
└── README.md
```

## License

This project is intended as a demonstration of an AI-assisted resume screening and candidate matching system.
