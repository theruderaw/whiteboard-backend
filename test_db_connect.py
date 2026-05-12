print("BOOTING ASYNC TEST...", flush=True)
import asyncio, os, asyncpg
from dotenv import load_dotenv

load_dotenv("app/.env")
URL = os.getenv("DATABASE_URL")

async def go():
    print(f"READY TO CONNECT TO: {URL[:15]}...", flush=True)
    try:
        # Set connection timeout to 5 seconds max so it doesn't hang forever!
        conn = await asyncio.wait_for(asyncpg.connect(URL), timeout=5.0)
        print("CONNECTION ACTUALLY SUCCEEDED!!!!!!!!!", flush=True)
        await conn.close()
    except asyncio.TimeoutError:
        print("CONNECTION TIMED OUT!!!", flush=True)
    except Exception as e:
        print(f"CRASHED WITH ERROR: {type(e).__name__}: {str(e)}", flush=True)

print("INVOKING ASYNCIO.RUN NOW!", flush=True)
asyncio.run(go())
print("ASYNCIO.RUN COMPLETED EXECUTION!", flush=True)
