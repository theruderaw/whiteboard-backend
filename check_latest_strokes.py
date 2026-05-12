import asyncio
import os
import asyncpg
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT created_at, type FROM strokes ORDER BY created_at DESC LIMIT 1")
        if row:
            print(f"LATEST STROKE TIMESTAMP: {row['created_at']} (TYPE: {row['type']})")
        else:
            print("NO STROKES IN DB")
    finally:
        await conn.close()

asyncio.run(check())
