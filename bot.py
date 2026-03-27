#!/usr/bin/env python3
"""
W1NPAKSHAM BOT - Полноценный бот для Render
"""

import asyncio
import logging
import os
import sys
import shutil
from datetime import datetime

from config import MIN_DONATION, MAX_DONATION, PAYMENT_METHODS, YOUR_WALLETS
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ==================== ИМПОРТ МОДУЛЕЙ ====================
from config import BOT_TOKEN, ADMIN_IDS, COIN_NAME, CURRENCY, MIN_DONATION, MAX_DONATION, PAYMENT_METHODS, YOUR_WALLETS
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

# ==================== KEEP-ALIVE (без aiohttp) ====================
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
                    try:
                        os.remove(old)
                    except:
                        pass
        except Exception as e:
            logger.error(f"❌ Бэкап ошибка: {e}")

# ==================== ПРОСТОЙ HTTP СЕРВЕР ДЛЯ RENDER ====================
async def run_http_server():
    """Простой HTTP сервер для health check (без aiohttp)"""
    import socket
    
    async def handle_client(reader, writer):
        """Обработка запроса"""
        try:
            await reader.readline()
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 2\r\n"
                "Connection: close\r\n\r\n"
                "OK"
            )
            writer.write(response.encode())
            await writer.drain()
        except Exception as e:
            logger.error(f"HTTP ошибка: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    server = await asyncio.start_server(
        handle_client,
        "0.0.0.0",
        PORT,
        reuse_port=True
    )
    
    logger.info(f"✅ HTTP сервер запущен на порту {PORT}")
    await server.serve_forever()

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
    asyncio.create_task(run_http_server())
    print("✅ Фоновые задачи запущены")
    
    print("=" * 50)
    print(f"🎮 БОТ ГОТОВ К РАБОТЕ!")
    print(f"👑 Админ ID: {ADMIN_IDS[0]}")
    print(f"💎 Валюта: {COIN_NAME}")
    print("=" * 50)
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
