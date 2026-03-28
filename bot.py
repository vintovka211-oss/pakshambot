import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
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
dp.callback_query.register(handle_callback)
dp.message.register(handle_bet, GameStates.waiting_bet)
dp.message.register(handle_donate_amount, DonateStates.waiting_amount)
dp.message.register(handle_withdraw_amount, WithdrawStates.waiting_amount)

async def main():
    print("🚀 Бот запускается...")
    await init_db()
    print("✅ База данных готова")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())