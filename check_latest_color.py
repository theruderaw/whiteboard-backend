import asyncio, os, asyncpg, json
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")
async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT data FROM strokes ORDER BY created_at DESC LIMIT 1")
    d = json.loads(row['data'])
    print(f"COLOR: '{d.get('color')}'")
    await conn.close()
asyncio.run(check())
