import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, complete_mine_upgrades, process_withdraw_requests
from handlers import (
    start_command, handle_callback, handle_bet, handle_donate_amount,
    handle_donate_method, handle_withdraw_amount, confirm_deposit,
    GameStates, DonateStates, WithdrawStates
)
from admin import handle_admin_callback

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрация обработчиков
dp.message.register(start_command, Command("start"))
dp.message.register(confirm_deposit, lambda msg: msg.text and msg.text.startswith("/confirm_"))
dp.callback_query.register(handle_callback)
dp.callback_query.register(handle_donate_method, DonateStates.waiting_method)
dp.message.register(handle_bet, GameStates.waiting_bet)
dp.message.register(handle_donate_amount, DonateStates.waiting_amount)
dp.message.register(handle_withdraw_amount, WithdrawStates.waiting_amount)

async def scheduler():
    """Фоновая задача"""
    while True:
        await asyncio.sleep(3600)  # Каждый час
        
        # Завершаем улучшения шахт
        completed = await complete_mine_upgrades()
        if completed:
            print(f"✅ Завершено улучшений шахт: {completed}")
        
        # Обрабатываем выводы
        withdraw_count = await process_withdraw_requests()
        if withdraw_count:
            print(f"✅ Обработано заявок на вывод: {withdraw_count}")

async def main():
    """Главная функция"""
    print("🚀 Бот W1NPAKSHAM запускается...")
    print("=" * 40)
    
    await init_db()
    print("✅ База данных подключена")
    
    asyncio.create_task(scheduler())
    print("✅ Планировщик задач запущен")
    
    print("=" * 40)
    print("🎮 Бот готов к работе!")
    print(f"👑 Админ ID: {ADMIN_IDS[0]}")
    print("=" * 40)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
