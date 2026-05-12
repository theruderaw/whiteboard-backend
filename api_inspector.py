import asyncio, os, asyncpg, json
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    # Get the last modified whiteboard
    wb = await conn.fetchrow("SELECT id FROM whiteboards ORDER BY created_at DESC LIMIT 1")
    if wb:
        print(f"WHITEBOARD ID: {wb['id']}")
        # Now, manually reproduce what backend/app/whiteboard/router.py:48 get_strokes does!
        rows = await conn.fetch("SELECT * FROM strokes WHERE whiteboard_id = $1 ORDER BY created_at ASC", wb['id'])
        print(f"FETCHED {len(rows)} STROKES")
        if rows:
            import json
            sample = dict(rows[-1]) # Last one
            if isinstance(sample["data"], str):
                sample["data"] = json.loads(sample["data"])
            # This is EXACTLY what gets JSON serialised to frontend!
            print("\n--- FRONTEND JSON REPRESENTATION ---")
            print(json.dumps(sample, default=str, indent=2))
    await conn.close()
asyncio.run(check())
