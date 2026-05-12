import asyncio, os, asyncpg, json
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    # Just select any whiteboard ID currently present in strokes table!
    row = await conn.fetchrow("SELECT DISTINCT whiteboard_id FROM strokes LIMIT 1")
    if row:
        wid = row['whiteboard_id']
        print(f"TESTING WHITEBOARD ID: {wid}")
        # Simulate get_strokes
        rows = await conn.fetch("SELECT * FROM strokes WHERE whiteboard_id = $1 ORDER BY created_at DESC LIMIT 1", wid)
        if rows:
            sample = dict(rows[0])
            if isinstance(sample["data"], str):
                sample["data"] = json.loads(sample["data"])
            print("\n--- API PAYLOAD PREVIEW ---")
            print(json.dumps(sample, default=str, indent=2))
    else:
        print("COULD NOT FIND ANY STROKES AT ALL!")
    await conn.close()
asyncio.run(check())
