import asyncio, os, asyncpg, json
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")
async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT data FROM strokes ORDER BY created_at DESC LIMIT 10")
    for i, row in enumerate(rows):
        d = json.loads(row['data'])
        print(f"#{i}: color='{d.get('color')}' isEraser={d.get('isEraser')}")
    await conn.close()
asyncio.run(check())
