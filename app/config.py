import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

NUMVERIFY_API_KEY = os.getenv("NUMVERIFY_API_KEY", "")
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY", "")
OFDATA_API_KEY = os.getenv("OFDATA_API_KEY", "")
DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE", "RU")
