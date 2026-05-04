import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL       = os.getenv("DATABASE_URL")
JWT_SECRET         = os.getenv("JWT_SECRET")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET")
JWT_RESET_SECRET   = os.getenv("JWT_RESET_SECRET")
ENV                = os.getenv("ENV", "development")