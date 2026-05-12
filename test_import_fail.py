print("BOOTING TEST...", flush=True)
try:
    import asyncpg
    print("ASYNCPG IMPORTED SUCCESS!", flush=True)
except Exception as e:
    print(f"ASYNCPG IMPORT FAILED WITH ERROR: {str(e)}", flush=True)
