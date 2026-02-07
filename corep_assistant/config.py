"""Configuration management for COREP Assistant"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# File paths
CORPUS_PATH = PROCESSED_DATA_DIR / "corpus.jsonl"
FAISS_INDEX_PATH = PROCESSED_DATA_DIR / "faiss.index"
BM25_INDEX_PATH = PROCESSED_DATA_DIR / "bm25.pkl"
METADATA_DB_PATH = PROCESSED_DATA_DIR / "meta.sqlite"

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not set. LLM generation will fail.")

# Model Configuration
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-70b-versatile")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Retrieval Configuration
TOP_K_FAISS = int(os.getenv("TOP_K_FAISS", "10"))
TOP_K_BM25 = int(os.getenv("TOP_K_BM25", "10"))
FINAL_TOP_K = int(os.getenv("FINAL_TOP_K", "6"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))

# Feature Toggles
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "false").lower() == "true"
ENABLE_AUDITOR_PASS = os.getenv("ENABLE_AUDITOR_PASS", "true").lower() == "true"
CITATION_STRICT = os.getenv("CITATION_STRICT", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Chunking Configuration
CHUNK_SIZE = 800  # characters
CHUNK_OVERLAP = 150  # characters

def index_exists() -> bool:
    """Check if all required index files exist"""
    return (
        CORPUS_PATH.exists() and
        FAISS_INDEX_PATH.exists() and
        BM25_INDEX_PATH.exists()
    )
