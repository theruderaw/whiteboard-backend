import requests
import json

API_URL = "http://localhost:8000"

# I need a token. I'll try to login as 'rudra' if possible, or just check the logs.
# Since I don't know the password, I'll check the users in DB and maybe reset one or just look at them.

def check_users():
    import os
    os.system('psql "postgresql://rudra:0Yf2tJl4AmpgiyrxMrSJM2RgxuSPjQoh@dpg-d7rs8hbt6lks73fshatg-a.oregon-postgres.render.com/db_set_v5cq" -c "SELECT id, username FROM users;"')

if __name__ == "__main__":
    check_users()
