import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
ENV_FILE = BACKEND_DIR / ".env"

print("ENV FILE:")
print(ENV_FILE)

print("\n.env EXISTS:")
print(ENV_FILE.exists())

load_dotenv(
    dotenv_path=ENV_FILE,
    override=True,
)

print("\nDATABASE_URL loaded:")
print(bool(os.getenv("DATABASE_URL")))

print("GEMINI_API_KEY loaded:")
print(bool(os.getenv("GEMINI_API_KEY")))