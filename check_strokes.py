import sys
print("PYTHON HAS BOOTED AND IS ALIVE!!!", flush=True)

import asyncio
import os
import asyncpg
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

async def check():
    print(f"Attempting connection to {DATABASE_URL[:20]}...", flush=True)
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("CONNECTION SUCCESS!", flush=True)
        rows = await conn.fetch("SELECT data FROM strokes")
        print(f"Fetched {len(rows)} rows.", flush=True)
        flat = 0
        legacy = 0
        other = 0
        for row in rows:
            d = row['data']
            if isinstance(d, str): d = json.loads(d)
            pts = d.get('points')
            if not pts: continue
            if len(pts) > 0:
                first = pts[0]
                if isinstance(first, (int, float)): flat += 1
                elif isinstance(first, dict): legacy += 1
                else: other += 1
        print(f"SUMMARY: Flat={flat}, Legacy={legacy}, Other={other}", flush=True)
        await conn.close()
    except Exception as e:
        print(f"ERROR OCCURRED: {str(e)}", flush=True)

print("Triggering asyncio.run...", flush=True)
asyncio.run(check())
print("Finished execution of asyncio.run", flush=True)
