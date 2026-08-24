"""
Turns a raw resume file (PDF / DOCX / TXT) into plain text, then pulls out
lightweight structured fields (name, email, phone, skills, education,
years of experience) with regex + keyword heuristics.

This heuristic layer runs BEFORE the LLM call. It's cheap, deterministic,
and gives us a fallback + a cross-check for the LLM's own extraction —
two independent signals are more trustworthy than one for an ATS tool.

Some PDFs (scanned documents, or ones exported by resume-builder tools
that subset fonts without a proper Unicode character map) have no
extractable text layer at all — pdfplumber returns an empty string even
though the text is visually present. We detect that case and fall back
to OCR (render the page to an image, run Tesseract on it) so those
resumes still get parsed instead of silently failing.
"""
import io
import re
from datetime import datetime

import pdfplumber
import docx

try:
    import fitz  # PyMuPDF, used only to rasterize pages for the OCR fallback
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Below this many characters of "real" (non-whitespace) text, we treat the
# normal extraction as having failed and fall back to OCR.
MIN_EXTRACTED_CHARS = 20

# A reasonably broad seed vocabulary of tech/professional skills. In a real
# ATS you'd load this from a maintained skills taxonomy (e.g. ESCO, LinkedIn
# Skills Graph); this keeps the demo self-contained and dependency-free.
SKILL_VOCAB = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "kotlin", "swift", "sql", "r", "scala", "php", "ruby",
    "react", "angular", "vue", "next.js", "node.js", "express", "django",
    "flask", "fastapi", "spring", "spring boot", ".net",
    "html", "css", "tailwind", "bootstrap",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "ci/cd", "jenkins", "github actions", "git",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "data analysis", "data engineering", "etl", "spark", "hadoop", "airflow",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "rest api", "graphql", "microservices", "system design",
    "agile", "scrum", "jira", "figma",
    "android", "jetpack compose", "ios", "flutter", "react native",
    "excel", "power bi", "tableau", "communication", "leadership",
    "project management", "problem solving", "team management",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{0,4}")
YEAR_RANGE_RE = re.compile(r"(19|20)\d{2}\s*[-–—to]{1,4}\s*((19|20)\d{2}|present|current)", re.I)
DEGREE_KEYWORDS = [
    "b.tech", "btech", "bachelor", "b.sc", "bsc", "b.e", "be ", "m.tech",
    "mtech", "master", "m.sc", "msc", "mba", "phd", "ph.d", "associate degree",
    "diploma",
]


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Dispatch on file extension and return plain text."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        text = _extract_pdf(file_bytes)
        if len(text.strip()) < MIN_EXTRACTED_CHARS and OCR_AVAILABLE:
            ocr_text = _extract_pdf_via_ocr(file_bytes)
            if len(ocr_text.strip()) > len(text.strip()):
                return ocr_text
        return text
    if lower.endswith(".docx"):
        return _extract_docx(file_bytes)
    if lower.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: {filename}")


def _extract_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def _extract_pdf_via_ocr(file_bytes: bytes, dpi: int = 200) -> str:
    """Renders each page to an image and runs Tesseract OCR on it. Slower
    than direct text extraction, so this only runs when the normal path
    comes back empty (see MIN_EXTRACTED_CHARS above) — not on every PDF."""
    text_parts = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    zoom = dpi / 72  # PDF points are 72/inch; scale the render matrix to the target DPI
    matrix = fitz.Matrix(zoom, zoom)
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            text_parts.append(pytesseract.image_to_string(image))
    except pytesseract.TesseractNotFoundError:
        # The Python package is installed but the Tesseract binary itself
        # isn't on PATH (common on a fresh Windows/Mac setup that skipped
        # the system-level install). Degrade to "no OCR" rather than
        # crashing the whole upload — the caller just sees the original
        # (empty) extraction and reports it as unreadable, same as before
        # OCR support existed.
        print("[parsing] Tesseract binary not found on PATH — skipping OCR fallback. "
              "See README for install instructions.")
        return ""
    finally:
        doc.close()
    return "\n".join(text_parts)


def _extract_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs)


def guess_name(text: str, filename: str) -> str:
    """Names aren't reliably labelled in resumes, so we take the best guess:
    the first non-empty line that looks like a name (2-4 title-case words,
    no digits/@ symbols), falling back to the filename."""
    for line in text.strip().splitlines()[:8]:
        line = line.strip()
        if not line or len(line) > 60:
            continue
        if "@" in line or any(ch.isdigit() for ch in line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            return line
    return filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()


def extract_contact(text: str) -> tuple[str | None, str | None]:
    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)
    email = email_match.group(0) if email_match else None
    phone = phone_match.group(0).strip() if phone_match else None
    return email, phone


def extract_skills(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for skill in SKILL_VOCAB:
        # word-boundary-ish match so "r" doesn't match inside "director"
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, lower):
            found.append(skill)
    return sorted(set(found))


def extract_education(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for line in text.splitlines():
        line_lower = line.lower()
        if any(kw in line_lower for kw in DEGREE_KEYWORDS):
            cleaned = line.strip()
            if cleaned and cleaned not in found:
                found.append(cleaned)
    return found[:5]


def estimate_experience_years(text: str) -> float | None:
    """Sums up distinct year-ranges found in the resume (e.g. 2019-2022) as a
    rough proxy for total experience. Not exact, but transparent and
    reproducible — a reasonable heuristic to show alongside the LLM's own
    estimate, rather than trusting either blindly."""
    current_year = datetime.now().year
    spans = []
    for match in YEAR_RANGE_RE.finditer(text):
        chunk = match.group(0)
        all_years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", chunk)]
        if not all_years:
            continue
        start = all_years[0]
        is_ongoing = bool(re.search(r"present|current", chunk, re.I))
        end = current_year if is_ongoing else (all_years[-1] if len(all_years) > 1 else start)
        if end >= start:
            spans.append((start, end))
    if not spans:
        return None
    total_years = sum(end - start for start, end in spans)
    return round(min(total_years, 40), 1)  # cap at 40 to guard against bad parses


def parse_resume(filename: str, file_bytes: bytes) -> dict:
    text = extract_text(filename, file_bytes)
    email, phone = extract_contact(text)
    return {
        "raw_text": text,
        "name": guess_name(text, filename),
        "email": email,
        "phone": phone,
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience_years": estimate_experience_years(text),
    }


def extract_must_have_skills(job_description: str) -> list[str]:
    """Same vocabulary match, run against the JD, to power the keyword score
    and the 'must-have skills' chips shown on the job page."""
    return extract_skills(job_description)
