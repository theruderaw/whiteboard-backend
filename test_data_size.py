import asyncio, os, asyncpg
from dotenv import load_dotenv

load_dotenv("app/.env")
URL = os.getenv("DATABASE_URL")

async def run():
    conn = await asyncpg.connect(URL)
    print("CONNECTED! MEASURING DATA LENGTHS...", flush=True)
    # Query Postgres character count of the data column directly on server
    rows = await conn.fetch("SELECT id, LENGTH(CAST(data AS TEXT)) as sz FROM strokes ORDER BY sz DESC LIMIT 10")
    print("TOP 10 LARGEST STROKES:", flush=True)
    for r in rows:
        print(f"ID: {r['id']}, Size in Bytes: {r['sz']}", flush=True)
    await conn.close()

asyncio.run(run())
