print("BOOTING ALL IMPORTS TEST...", flush=True)
import sys, os, json, asyncio
print("SYSTEM MODULES IMPORTED", flush=True)
import asyncpg
print("ASYNCPG IMPORTED", flush=True)
from dotenv import load_dotenv
print("DOTENV IMPORTED", flush=True)
print("ALL SUCCESSFUL!!!", flush=True)
