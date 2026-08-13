import os
from dotenv import load_dotenv

load_dotenv()

# Path configurations
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
DATA_DIR = os.getenv("DATA_DIR", "./resources/data")
DB_PATH = os.getenv("DB_PATH", "users.db")

# Model configurations
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "openai/gpt-oss-120b"