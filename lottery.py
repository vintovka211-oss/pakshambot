from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, add_transaction, add_income
from config import LOTTERY_TICKET_PRICE, LOTTERY_COMMISSION, COIN_NAME, CURRENCY
import aiosqlite
import random
from datetime import datetime, timedelta

DB_PATH = "w1npaksham.db"

async def get_active_lottery():
    """Получить активную лотерею"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, round_number, prize_pool, total_tickets FROM lotteries WHERE status = 'active' ORDER BY created_at DESC LIMIT 1"
        ) as cursor:
            return await cursor.fetchone()

async def create_lottery_round():
    """Создать новый розыгрыш"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT MAX(round_number) FROM lotteries") as cursor:
            max_round = await cursor.fetchone()
            round_number = (max_round[0] or 0) + 1
        
        draw_at = datetime.now() + timedelta(days=7)
        
        cursor = await db.execute(
            "INSERT INTO lotteries (round_number, prize_pool, total_tickets, draw_at) VALUES (?, ?, ?, ?)",
            (round_number, 0, 0, draw_at)
        )
        await db.commit()
        return cursor.lastrowid

async def buy_lottery_ticket(user_id: int) -> tuple:
    """Купить билет лотереи"""
    user = await get_user(user_id)
    
    if user["balance"] < LOTTERY_TICKET_PRICE:
        return False, f"❌ Недостаточно средств! Нужно: {LOTTERY_TICKET_PRICE}{CURRENCY}"
    
    lottery = await get_active_lottery()
    
    if not lottery:
        lottery_id = await create_lottery_round()
    else:
        lottery_id = lottery[0]
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM lottery_tickets WHERE lottery_id = ?",
            (lottery_id,)
        ) as cursor:
            ticket_count = (await cursor.fetchone())[0]
        
        ticket_number = ticket_count + 1
        
        await db.execute(
            "INSERT INTO lottery_tickets (lottery_id, user_id, ticket_number) VALUES (?, ?, ?)",
            (lottery_id, user_id, ticket_number)
        )
        
        prize_add = int(LOTTERY_TICKET_PRICE * (100 - LOTTERY_COMMISSION) / 100)
        
        await db.execute(
            "UPDATE lotteries SET prize_pool = prize_pool + ?, total_tickets = total_tickets + 1 WHERE id = ?",
            (prize_add, lottery_id)
        )
        
        new_balance = user["balance"] - LOTTERY_TICKET_PRICE
        await db.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (new_balance, user_id)
        )
        
        await db.commit()
        
        await add_transaction(user_id, "lottery_ticket", -LOTTERY_TICKET_PRICE, f"Билет лотереи #{lottery_id}")
        await add_income("lottery", LOTTERY_TICKET_PRICE - prize_add, user_id)
        
        return True, f"✅ Билет #{ticket_number} куплен! Призовой фонд: {prize_add}{CURRENCY}"

async def get_lottery_info() -> tuple:
    """Получить информацию о лотерее"""
    lottery = await get_active_lottery()
    
    if not lottery:
        return "🎫 **Лотерея**\n\nСкоро начнется новый розыгрыш!", None
    
    lottery_id, round_num, prize_pool, total_tickets = lottery
    
    text = (
        f"🎫 **Лотерея #{round_num}**\n\n"
        f"💰 Призовой фонд: {prize_pool}{CURRENCY}\n"
        f"🎟️ Всего билетов: {total_tickets}\n"
        f"💵 Цена билета: {LOTTERY_TICKET_PRICE}{CURRENCY}\n"
        f"📊 Комиссия: {LOTTERY_COMMISSION}%\n\n"
        f"🎲 Чем больше билетов, тем выше шанс выиграть!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎫 Купить билет", callback_data="lottery_buy"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"),
        ]
    ])
    
    return text, keyboard

async def lottery_menu(user_id: int) -> tuple:
    """Меню лотереи"""
    return await get_lottery_info()
