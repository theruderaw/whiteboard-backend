import asyncio
import os
import json
import asyncpg
from dotenv import load_dotenv

# Ensure the relative dotenv can be found, depending on execution spot.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "app", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

async def migrate():
    if not DATABASE_URL:
        print("DATABASE_URL not found in app/.env!")
        return

    print(f"Connecting to DB to migrate strokes...")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("SELECT id, data FROM strokes")
        print(f"Found {len(rows)} strokes. Processing...")
        
        migrated_count = 0
        for row in rows:
            data = row["data"]
            # It's probably a dict (from auto-deserialization by asyncpg) or a JSON string.
            if isinstance(data, str):
                data = json.loads(data)
            
            if not data or "points" not in data:
                continue
            
            points = data["points"]
            # Check if it's already flattened (a list of numbers)
            if points and isinstance(points[0], (int, float)):
                continue # Already flat
            
            # Flatten [{x:val, y:val}, ...] -> [val, val, ...]
            new_points = []
            for p in points:
                if isinstance(p, dict):
                    new_points.append(p.get("x", 0))
                    new_points.append(p.get("y", 0))
                elif isinstance(p, list) and len(p) == 2:
                    new_points.extend(p)
            
            # Overwrite points list
            data["points"] = new_points
            
            # Update back
            await conn.execute(
                "UPDATE strokes SET data = $1 WHERE id = $2",
                json.dumps(data), row["id"]
            )
            migrated_count += 1
        
        print(f"Successfully migrated {migrated_count} strokes to the new flat array format.")
    
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
