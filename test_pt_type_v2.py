import asyncio, os, asyncpg, json, traceback
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

async def check():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("SELECT id, data FROM strokes")
        print(f"FOUND {len(rows)} TOTAL ROWS")
        
        flat = 0
        dicts = 0
        nested = 0
        other = 0
        
        for row in rows:
            raw_data = row['data']
            # Just print type of raw_data for first iteration to diagnose
            if flat + dicts + nested + other == 0:
                print(f"DATA COLUMN TYPE: {type(raw_data)}")
            
            d = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            
            # In case it is nested string double encoding
            if isinstance(d, str):
                d = json.loads(d)
                
            pts = d.get('points')
            if not pts: 
                other += 1
                continue
            
            first = pts[0]
            if isinstance(first, (int, float)):
                flat += 1
            elif isinstance(first, dict):
                dicts += 1
            elif isinstance(first, list):
                nested += 1
            else:
                other += 1
                
        print(f"FLAT: {flat}")
        print(f"DICTS: {dicts}")
        print(f"NESTED: {nested}")
        print(f"OTHER: {other}")
        await conn.close()
    except Exception:
        traceback.print_exc()

asyncio.run(check())
