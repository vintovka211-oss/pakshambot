import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = "8590452175:AAGKpZiKBmneyxUX8Ac9U7w9cRjtWQYT8uU"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("✅ БОТ РАБОТАЕТ НА PYTHON 3.14!")

async def main():
    print("🚀 Бот запущен на Python 3.14")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
