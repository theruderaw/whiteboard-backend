import asyncio, os, asyncpg, json
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT id, data FROM strokes")
    list_count = 0
    dict_count = 0
    flat_count = 0
    nested_count = 0
    
    for row in rows:
        d = json.loads(row['data']) if isinstance(row['data'], str) else row['data']
        pts = d.get('points')
        if not pts: continue
        
        first = pts[0]
        if isinstance(first, (int, float)):
            flat_count += 1
        elif isinstance(first, dict):
            dict_count += 1
        elif isinstance(first, list):
            nested_count += 1
    
    print(f"RESULTS:\nFLAT (Numbers): {flat_count}\nLEGACY (Dicts): {dict_count}\nNESTED (Arrays of Arrays): {nested_count}")
    await conn.close()
asyncio.run(check())
