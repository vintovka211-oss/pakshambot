#!/usr/bin/env python3
"""
W1NPAKSHAM BOT - Простой и надежный скрипт для Render
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ==================== ИМПОРТ ВАШИХ МОДУЛЕЙ ====================
from config import BOT_TOKEN, ADMIN_IDS, COIN_NAME, CURRENCY
from database import get_user, update_user, init_db
from keyboards import get_main_keyboard
from handlers import start_command

# ==================== НАСТРОЙКИ ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8080))
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ==================== ПРОСТОЙ KEEP-ALIVE ====================
async def keep_alive():
    """Простой пинг чтобы сервер не засыпал"""
    while True:
        await asyncio.sleep(300)  # каждые 5 минут
        try:
            me = await bot.get_me()
            logger.info(f"Бот {me.username} жив, время: {datetime.now()}")
        except Exception as e:
            logger.error(f"Keep-alive ошибка: {e}")

# ==================== ПРОСТОЙ HEALTH CHECK ====================
async def health_check(request):
    """Проверка что бот работает"""
    return web.Response(text="OK")

# ==================== ПРОСТОЙ БЭКАП ====================
async def simple_backup():
    """Простое копирование БД раз в час"""
    import shutil
    while True:
        await asyncio.sleep(3600)  # каждый час
        try:
            if os.path.exists("w1npaksham.db"):
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d')}.db"
                shutil.copy("w1npaksham.db", backup_name)
                logger.info(f"Бэкап создан: {backup_name}")
        except Exception as e:
            logger.error(f"Бэкап ошибка: {e}")

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================
async def main():
    """Запуск бота"""
    print("🚀 Бот запускается...")
    
    # Инициализация БД
    await init_db()
    print("✅ База данных готова")
    
    # Запускаем фоновые задачи
    asyncio.create_task(keep_alive())
    asyncio.create_task(simple_backup())
    
    # Запускаем веб-сервер для Render
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Веб-сервер на порту {PORT}")
    
    # Запускаем бота
    print("🎮 Бот готов!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
