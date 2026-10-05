import os

from dotenv import load_dotenv

load_dotenv()   # root ki .env file se values padhta hai

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")