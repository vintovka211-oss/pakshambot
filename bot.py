import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db
from handlers import *

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.message.register(start_command, Command("start"))
dp.message.register(confirm_deposit, lambda m: m.text and m.text.startswith("/confirm_"))
dp.message.register(admin_process_user_id, AdminStates.waiting_user_id)
dp.message.register(admin_process_amount, AdminStates.waiting_amount)
dp.message.register(admin_process_premium, AdminStates.waiting_days)
dp.callback_query.register(handle_callback)

async def main():
    print("🚀 Бот запускается с 15 играми!")
    await init_db()
    print("✅ База данных готова")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
