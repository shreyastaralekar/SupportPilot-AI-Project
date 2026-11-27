"""Central configuration for SupportPilot Milestone 2 (RAG pipeline)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
KB_PATH = BASE_DIR / "data" / "knowledge_base.json"
EVAL_RESULTS_PATH = BASE_DIR / "data" / "eval_results.json"
FEEDBACK_DB = BASE_DIR / "feedback.db"

TOP_K = 3                      # documents passed to the generator
MIN_RELEVANCE = float(os.environ.get("MIN_RELEVANCE", 0.10))
# Why 0.10 and not 0.30?  TF-IDF cosine scores on a small knowledge base are low in absolute terms
# (a good match is often 0.15-0.45). The threshold was chosen by running evaluate_retrieval.py:
# it must accept real tickets while rejecting off-topic questions. Re-tune it for a bigger KB.
CATEGORY_BOOST = 0.05          # small score bonus if the KB article category matches the ticket category

# Optional LLM generation (default: built-in extractive generator, no API key needed)
USE_LLM = os.environ.get("SUPPORTPILOT_USE_LLM", "0") == "1"
LLM_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.environ.get("SUPPORTPILOT_MODEL", "claude-sonnet-5-5")
LLM_TIMEOUT_SECONDS = 30
