import asyncio
from database import init_db

async def main():
    print("Создание базы данных...")
    await init_db()
    print("✅ База данных создана!")

if __name__ == "__main__":
    asyncio.run(main())
