import asyncio, os, asyncpg, json
from dotenv import load_dotenv

load_dotenv("app/.env")
URL = os.getenv("DATABASE_URL")

async def run():
    conn = await asyncpg.connect(URL)
    print("CONNECTED! FETCHING AS RAW TEXT...", flush=True)
    # Fetching by casting to text bypasses asyncpg jsonb C-code parser!
    rows = await conn.fetch("SELECT id, CAST(data AS TEXT) as raw_data FROM strokes")
    print(f"FETCHED {len(rows)} ROWS OF RAW TEXT SUCCESSFULLY!!!", flush=True)
    
    success = 0
    failed = 0
    for r in rows:
        try:
            d = json.loads(r['raw_data'])
            success += 1
        except Exception as e:
            print(f"CRITICAL: ROW {r['id']} FAILED TO PARSE IN PYTHON: {str(e)}", flush=True)
            failed += 1
            
    print(f"PARSING SUMMARY: {success} parsed successfully, {failed} failed.", flush=True)
    await conn.close()

asyncio.run(run())
