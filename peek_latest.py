import asyncio
import os
import asyncpg
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT data FROM strokes ORDER BY created_at DESC LIMIT 1")
        d = json.loads(row['data'])
        # Print first 10 points only
        print(f"POINTS SAMPLE: {d.get('points', [])[:10]}")
        print(f"LINEWIDTH: {d.get('lineWidth')}")
    finally:
        await conn.close()

asyncio.run(check())
