# First, install: pip install python-dotenv
import os
from dotenv import load_dotenv

# Load .env file at the very beginning
load_dotenv()

# Get keys safely
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")   # Example for search

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing from .env file!")

print("Keys loaded successfully")