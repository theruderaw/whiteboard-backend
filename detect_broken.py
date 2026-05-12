import asyncio, os, asyncpg, json
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT * FROM strokes")
    broken = 0
    for row in rows:
        d = json.loads(row['data']) if isinstance(row['data'], str) else row['data']
        # Test if critical fields exist
        pts = d.get('points')
        lw = d.get('lineWidth')
        c = d.get('color')
        if not pts or not isinstance(pts, list) or len(pts) % 2 != 0:
            print(f"BAD POINTS format on stroke {row['id']}")
            broken += 1
        elif not lw or not c:
            print(f"MISSING LW or C on stroke {row['id']}")
            broken += 1
    print(f"TOTAL BAD STROKES: {broken} out of {len(rows)}")
    await conn.close()
asyncio.run(check())
