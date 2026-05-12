import asyncio, os, asyncpg
from dotenv import load_dotenv

load_dotenv("app/.env")
URL = os.getenv("DATABASE_URL")

async def get_one_id():
    conn = await asyncpg.connect(URL)
    row = await conn.fetchrow("SELECT whiteboard_id FROM strokes LIMIT 1")
    print(f"{row['whiteboard_id']}", flush=True)
    await conn.close()

asyncio.run(get_one_id())
