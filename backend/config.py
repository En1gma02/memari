"""
config.py - Configuration and Environment Setup for Ari Chatbot

Centralizes all configuration, API keys, model IDs, file paths, and thresholds.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==============================================================================
# API KEYS
# ==============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")
if not CEREBRAS_API_KEY:
    raise ValueError("CEREBRAS_API_KEY environment variable not set")

# ==============================================================================
# MODEL IDS
# ==============================================================================

# Groq Models
GROQ_CHAT_MODEL = "openai/gpt-oss-120b"  # Main chat model with reasoning
GROQ_SAFETY_MODEL = "meta-llama/llama-guard-4-12b"  # Safety/moderation

# Cerebras Model
CEREBRAS_MODEL = "llama-3.1-8b"  # For session rewriting and persona updates

# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ==============================================================================
# FILE PATHS
# ==============================================================================

# Base directory (backend folder)
BASE_DIR = Path(__file__).parent

# FAISS and metadata
FAISS_INDEX_PATH = BASE_DIR / "data/faiss_index.bin"
METADATA_PATH = BASE_DIR / "data/metadata.pkl"

# Ari Life index
ARI_FAISS_INDEX_PATH = BASE_DIR / "data/faiss_index_ari.bin"
ARI_METADATA_PATH = BASE_DIR / "data/metadata_ari.pkl"

# Persona and prompts
USER_PERSONA_PATH = BASE_DIR / "data/user-persona.md"
ARI_LIFE_PATH = BASE_DIR / "data/ari-life.md"

# Chat history
CHAT_HISTORY_PATH = BASE_DIR / "data/CHAT.txt"

# ==============================================================================
# THRESHOLDS AND LIMITS
# ==============================================================================

# RAG retrieval
CONFIDENCE_THRESHOLD = 0.7  # Trigger fusion retrieval if top score < 0.7
TOP_K_RESULTS = 5  # Number of results to retrieve
FUSION_QUERY_COUNT = 5  # Number of query variations for fusion retrieval

# Session management
SESSION_TIMEOUT_MINUTES = 30  # Session ends after 30 mins of inactivity

# API rate limiting
CEREBRAS_DELAY_SECONDS = 2  # Delay between Cerebras API calls (30 req/min limit)

# ==============================================================================
# CHAT SETTINGS
# ==============================================================================

MAX_HISTORY_TURNS = 15  # Maximum conversation history to include in context
TEMPERATURE = 0.7  # Model temperature for chat responses
MAX_TOKENS = 512  # Maximum tokens per response
REASONING_EFFORT = "high"