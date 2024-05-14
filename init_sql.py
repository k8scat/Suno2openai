import asyncio
import aiomysql
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'https://studio-api.suno.ai')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', '')
DB_PORT = os.getenv('DB_PORT', 3306)

async def create_database_and_table():
    # Connect to the MySQL Server
    conn = await aiomysql.connect(host=DB_HOST, port=int(DB_PORT),
                                  user=DB_USER, password=DB_PASSWORD)
    cursor = await conn.cursor()

    # Create a new database 'SunoAPI' (if it doesn't exist)
    # await cursor.execute("CREATE DATABASE IF NOT EXISTS WSunoAPI")

    # Select the newly created database
    await cursor.execute(f"USE {DB_USER}")

    # Create a new table 'cookies' (if it doesn't exist)
    await cursor.execute("""
        CREATE TABLE IF NOT EXISTS cookies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cookie TEXT NOT NULL,
            count INT NOT NULL,
            working BOOLEAN NOT NULL
            )
    """)

    await cursor.close()
    conn.close()


async def main():
    if DB_HOST == '' or DB_PASSWORD == '' or DB_USER == '':
        raise ValueError("BASE_URL is not set")
    else:
        await create_database_and_table()
        # Here, you can continue with other database operations such as insert, update, etc.


# if __name__ == "__main__":
#     asyncio.run(main())
