print("BOOTING ENV TEST...", flush=True)
import os
from dotenv import load_dotenv
print("IMPORTS OK. CALLING LOAD_DOTENV...", flush=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, "app", ".env")
print(f"PATH: {env_path}", flush=True)
load_dotenv(env_path)
print("LOAD_DOTENV FINISHED!!!", flush=True)
print(f"URL: {os.getenv('DATABASE_URL')[:10]}...", flush=True)
