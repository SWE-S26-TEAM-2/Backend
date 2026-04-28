import os
from pathlib import Path

from dotenv import load_dotenv  # type: ignore

# Resolve app/.env relative to this file (app/core/config.py)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
GOOGLE_CLIENT_ID_ANDROID = os.environ.get("GOOGLE_CLIENT_ID_ANDROID", "")
GOOGLE_CLIENT_ID_IOS = os.environ.get("GOOGLE_CLIENT_ID_IOS", "")
GOOGLE_CLIENT_ID_WEB = os.environ.get("GOOGLE_CLIENT_ID_WEB", "")
FACEBOOK_APP_ID = os.environ.get("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET", "")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "")
ADMIN_BOOTSTRAP_SECRET = os.environ.get("ADMIN_BOOTSTRAP_SECRET", "")
AUTO_CREATE_TABLES = os.environ.get("AUTO_CREATE_TABLES", "").lower() == "true"
