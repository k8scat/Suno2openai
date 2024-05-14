import asyncio
import os
from sql_uilts import DatabaseManager

BASE_URL = os.getenv('BASE_URL', 'https://studio-api.suno.ai')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', '')
DB_PORT = os.getenv('DB_PORT', 3306)
cookies = ['']

async def insert_cookie(cookie, db_manager):
    try:
        await db_manager.insert_cookie(cookie, 0, False)
    except:
        print(cookie)

async def main():
    if DB_HOST == '' or DB_PASSWORD == '' or DB_USER == '':
        raise ValueError("invalid db config")
    
    else:
        db_manager = DatabaseManager(DB_HOST, int(DB_PORT), DB_USER, DB_PASSWORD, DB_USER)
        await db_manager.create_pool()
        tasks = [insert_cookie(cookie, db_manager) for cookie in cookies if cookie]
        await asyncio.gather(*tasks)