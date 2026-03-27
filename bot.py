#!/usr/bin/env python3
"""
W1NPAKSHAM BOT - Полноценный бот со всеми функциями
Оптимизирован для Render с Python 3.11
"""

import asyncio
import logging
import os
import sys
import shutil
from datetime import datetime
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ==================== ИМПОРТ МОДУЛЕЙ ====================
from config import BOT_TOKEN, ADMIN_IDS, COIN_NAME, CURRENCY
from database import init_db, get_user, update_user, get_top_users
from keyboards import get_main_keyboard, get_back_keyboard
from games import play_slots, play_dice, play_roulette
from admin import is_admin, admin_panel
from premium_services import buy_premium_with_pac, get_premium_stats, get_mine_text, get_mine_keyboard
from lottery import lottery_menu, buy_lottery_ticket
from tournaments import tournaments_menu, join_tournament
from handlers import (
    start_command, handle_callback, handle_bet, handle_donate_amount,
    handle_donate_method, handle_withdraw_amount, confirm_deposit,
    GameStates, DonateStates, WithdrawStates
)

# ==================== НАСТРОЙКИ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8080))
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ==================== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ====================
dp.message.register(start_command, Command("start"))
dp.message.register(confirm_deposit, lambda msg: msg.text and msg.text.startswith("/confirm_"))
dp.callback_query.register(handle_callback)
dp.callback_query.register(handle_donate_method, DonateStates.waiting_method)
dp.message.register(handle_bet, GameStates.waiting_bet)
dp.message.register(handle_donate_amount, DonateStates.waiting_amount)
dp.message.register(handle_withdraw_amount, WithdrawStates.waiting_amount)

# ==================== KEEP-ALIVE ====================
async def keep_alive():
    """Пинг чтобы сервер не засыпал"""
    while True:
        await asyncio.sleep(300)  # каждые 5 минут
        try:
            me = await bot.get_me()
            logger.info(f"✅ Бот {me.username} жив, время: {datetime.now()}")
        except Exception as e:
            logger.error(f"❌ Keep-alive ошибка: {e}")

# ==================== БЭКАП БАЗЫ ДАННЫХ ====================
async def backup_database():
    """Автоматическое резервное копирование БД"""
    while True:
        await asyncio.sleep(3600)  # каждый час
        try:
            if os.path.exists("w1npaksham.db"):
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H')}.db"
                shutil.copy("w1npaksham.db", backup_name)
                logger.info(f"💾 Бэкап создан: {backup_name}")
                
                # Удаляем старые бэкапы (оставляем последние 24)
                backups = sorted([f for f in os.listdir() if f.startswith("backup_")])
                for old in backups[:-24]:
                    os.remove(old)
        except Exception as e:
            logger.error(f"❌ Бэкап ошибка: {e}")

# ==================== HEALTH CHECK ====================
async def health_check(request):
    """Проверка работоспособности"""
    try:
        # Проверяем БД
        from database import get_user
        await get_user(1)
        return web.json_response({
            "status": "ok",
            "time": datetime.now().isoformat(),
            "bot": "W1NPAKSHAM"
        })
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)

# ==================== СТАТИСТИКА ДЛЯ МОНИТОРИНГА ====================
async def stats_check(request):
    """Статистика для мониторинга"""
    try:
        from database import get_user
        import aiosqlite
        
        async with aiosqlite.connect("w1npaksham.db") as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                users = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1") as cursor:
                premium = (await cursor.fetchone())[0]
        
        return web.json_response({
            "status": "ok",
            "users": users,
            "premium": premium,
            "time": datetime.now().isoformat()
        })
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)

# ==================== ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОШИБОК ====================
@dp.errors()
async def global_error_handler(update: types.Update, exception: Exception):
    """Обработка ошибок"""
    error_text = f"Ошибка: {type(exception).__name__}: {exception}"
    logger.error(error_text)
    
    # Отправляем админу
    try:
        for admin_id in ADMIN_IDS:
            await bot.send_message(admin_id, f"⚠️ {error_text[:500]}")
    except:
        pass
    
    return True

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================
async def main():
    """Запуск бота"""
    print("=" * 50)
    print("🚀 W1NPAKSHAM BOT ЗАПУСКАЕТСЯ")
    print("=" * 50)
    
    # Инициализация базы данных
    try:
        await init_db()
        print("✅ База данных готова")
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return
    
    # Запускаем фоновые задачи
    asyncio.create_task(keep_alive())
    asyncio.create_task(backup_database())
    print("✅ Фоновые задачи запущены")
    
    # Запускаем веб-сервер для Render
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    app.router.add_get("/stats", stats_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Веб-сервер на порту {PORT}")
    
    print("=" * 50)
    print(f"🎮 БОТ ГОТОВ К РАБОТЕ!")
    print(f"👑 Админ ID: {ADMIN_IDS[0]}")
    print(f"💎 Валюта: {COIN_NAME}")
    print("=" * 50)
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
