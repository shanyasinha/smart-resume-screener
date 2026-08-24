"""
Computes the match between one resume and one job description.

Two independent scores are blended:
  1. keyword_score  - transparent overlap between JD skills and resume skills
  2. llm_score      - semantic judgement from the LLM, which also produces
                       the plain-English justification recruiters read

Blending both (see LLM_SCORE_WEIGHT in config.py) means the final score is
never purely an LLM black box, and never purely keyword-matching that misses
paraphrased or implied skills.
"""
import json
import re

from app.config import (
    LLM_PROVIDER, ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL, LLM_SCORE_WEIGHT, KEYWORD_SCORE_WEIGHT,
)

SYSTEM_PROMPT = """You are an expert technical recruiter's assistant. You evaluate how well a \
candidate's resume fits a job description. You are rigorous and evidence-based: every \
claim you make must be traceable to specific text in the resume. You never invent \
experience the resume does not support. You output ONLY valid JSON, no prose, no markdown \
fences."""

USER_PROMPT_TEMPLATE = """Compare the following resume with this job description and rate the \
fit on a 1-10 scale, with justification.

JOB DESCRIPTION:
\"\"\"
{job_description}
\"\"\"

RESUME:
\"\"\"
{resume_text}
\"\"\"

Return ONLY a JSON object with exactly this shape:
{{
  "score": <integer 1-10, overall fit>,
  "matched_skills": [<skills/requirements from the JD the resume clearly demonstrates>],
  "missing_skills": [<skills/requirements from the JD the resume does not show>],
  "experience_assessment": "<one sentence on whether experience level fits>",
  "justification": "<2-3 sentences a recruiter could read directly, citing specific resume evidence>"
}}"""


def _extract_json(raw: str) -> dict:
    """LLMs occasionally wrap JSON in prose or fences despite instructions;
    pull out the first {...} block defensively."""
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError(f"No JSON object found in LLM response: {raw[:200]}")
    return json.loads(match.group(0))


def _call_anthropic(job_description: str, resume_text: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                job_description=job_description, resume_text=resume_text[:12000]
            ),
        }],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _extract_json(text)


def _call_openai(job_description: str, resume_text: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                job_description=job_description, resume_text=resume_text[:12000]
            )},
        ],
        temperature=0.2,
    )
    return _extract_json(response.choices[0].message.content)


def _keyword_fallback(jd_skills: list[str], resume_skills: list[str]) -> dict:
    """Used when no LLM key is configured, and as the keyword_score even when
    the LLM is available — see module docstring."""
    matched = sorted(set(jd_skills) & set(resume_skills))
    missing = sorted(set(jd_skills) - set(resume_skills))
    score_10 = round((len(matched) / len(jd_skills)) * 10, 1) if jd_skills else 5.0
    return {
        "score": score_10,
        "matched_skills": matched,
        "missing_skills": missing,
        "experience_assessment": "Not assessed (no LLM configured).",
        "justification": (
            f"Keyword-only match: {len(matched)}/{len(jd_skills)} required skills found "
            f"in the resume ({', '.join(matched) if matched else 'none'})."
        ),
    }


def score_resume(job_description: str, resume_text: str, jd_skills: list[str],
                  resume_skills: list[str]) -> dict:
    """Returns a dict with match_score (0-100), llm_score, keyword_score,
    matched_skills, missing_skills, justification."""
    keyword_result = _keyword_fallback(jd_skills, resume_skills)
    keyword_score_100 = keyword_result["score"] * 10

    llm_result = None
    if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        llm_result = _safe_call(_call_anthropic, job_description, resume_text)
    elif LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        llm_result = _safe_call(_call_openai, job_description, resume_text)

    if llm_result is None:
        # No LLM available/succeeded -> keyword result IS the result.
        return {
            "match_score": round(keyword_score_100, 1),
            "llm_score": None,
            "keyword_score": round(keyword_score_100, 1),
            "matched_skills": keyword_result["matched_skills"],
            "missing_skills": keyword_result["missing_skills"],
            "justification": keyword_result["justification"],
        }

    llm_score_100 = float(llm_result.get("score", 5)) * 10
    blended = LLM_SCORE_WEIGHT * llm_score_100 + KEYWORD_SCORE_WEIGHT * keyword_score_100

    # Union skills from both signals so a skill the LLM caught (e.g. implied
    # by a project description) but the keyword pass missed still surfaces.
    matched = sorted(set(llm_result.get("matched_skills", [])) | set(keyword_result["matched_skills"]))
    missing = sorted(set(llm_result.get("missing_skills", [])) & set(keyword_result["missing_skills"]))

    justification = llm_result.get("justification", "").strip()
    experience_note = llm_result.get("experience_assessment", "").strip()
    if experience_note:
        justification = f"{justification} {experience_note}".strip()

    return {
        "match_score": round(blended, 1),
        "llm_score": round(llm_score_100, 1),
        "keyword_score": round(keyword_score_100, 1),
        "matched_skills": matched,
        "missing_skills": missing,
        "justification": justification or keyword_result["justification"],
    }


def _safe_call(fn, job_description: str, resume_text: str) -> dict | None:
    """LLM calls can fail (rate limit, network, malformed JSON). We never let
    that crash the request — we fall back to the keyword score instead, and
    the caller logs nothing sensitive since resume text never leaves this
    process on failure."""
    try:
        return fn(job_description, resume_text)
    except Exception as exc:  # noqa: BLE001 - intentionally broad: any LLM failure should degrade gracefully
        print(f"[llm_matcher] LLM call failed, falling back to keyword score: {exc}")
        return None
