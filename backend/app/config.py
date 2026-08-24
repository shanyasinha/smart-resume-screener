"""
Central configuration, loaded from environment variables (.env).
Keeping this in one place means every module reads settings the same way,
and swapping the LLM provider or DB later only touches this file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- LLM provider -----------------------------------------------------
# Supports Anthropic (default) or OpenAI, chosen via LLM_PROVIDER.
# Falls back to a deterministic heuristic scorer if no key is set, so the
# app still runs end-to-end for a demo/reviewer without API keys.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # "anthropic" | "openai" | "none"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --- Storage ------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'resume_screener.db'}")
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# --- Matching weights -----------------------------------------------------
# Final score blends LLM semantic judgement with a transparent rules-based
# keyword overlap score, so results stay explainable even when the LLM
# reasoning is terse.
LLM_SCORE_WEIGHT = float(os.getenv("LLM_SCORE_WEIGHT", "0.7"))
KEYWORD_SCORE_WEIGHT = 1 - LLM_SCORE_WEIGHT

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
