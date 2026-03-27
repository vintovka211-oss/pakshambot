from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, add_transaction, add_income
from config import TOURNAMENT_ENTRY_FEE, TOURNAMENT_COMMISSION, CURRENCY
import aiosqlite
from datetime import datetime

DB_PATH = "w1npaksham.db"

async def get_active_tournaments():
    """Получить активные турниры"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM tournaments WHERE status = 'waiting' ORDER BY created_at DESC"
        ) as cursor:
            return await cursor.fetchall()

async def create_tournament(name: str, entry_fee: int, max_players: int) -> int:
    """Создать турнир"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tournaments (name, entry_fee, prize_pool, max_players) VALUES (?, ?, ?, ?)",
            (name, entry_fee, 0, max_players)
        )
        await db.commit()
        return cursor.lastrowid

async def join_tournament(user_id: int, tournament_id: int) -> tuple:
    """Записаться на турнир"""
    user = await get_user(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM tournaments WHERE id = ? AND status = 'waiting'",
            (tournament_id,)
        ) as cursor:
            tournament = await cursor.fetchone()
        
        if not tournament:
            return False, "❌ Турнир не найден или уже начался"
        
        tour_id, name, entry_fee, prize_pool, max_players, current_players, status, start_time, end_time, created_at = tournament
        
        async with db.execute(
            "SELECT * FROM tournament_participants WHERE tournament_id = ? AND user_id = ?",
            (tournament_id, user_id)
        ) as cursor:
            if await cursor.fetchone():
                return False, "❌ Вы уже участвуете в этом турнире"
        
        if user["balance"] < entry_fee:
            return False, f"❌ Недостаточно средств! Нужно: {entry_fee}{CURRENCY}"
        
        await db.execute(
            "INSERT INTO tournament_participants (tournament_id, user_id) VALUES (?, ?)",
            (tournament_id, user_id)
        )
        
        prize_add = int(entry_fee * (100 - TOURNAMENT_COMMISSION) / 100)
        new_prize_pool = prize_pool + prize_add
        new_players = current_players + 1
        
        await db.execute(
            "UPDATE tournaments SET prize_pool = ?, current_players = ? WHERE id = ?",
            (new_prize_pool, new_players, tournament_id)
        )
        
        new_balance = user["balance"] - entry_fee
        await db.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (new_balance, user_id)
        )
        
        await db.commit()
        
        await add_transaction(user_id, "tournament_fee", -entry_fee, f"Участие в турнире {name}")
        await add_income("tournament", entry_fee - prize_add, user_id)
        
        return True, f"✅ Вы записаны на турнир {name}!"

async def tournaments_menu(user_id: int) -> tuple:
    """Меню турниров"""
    tournaments = await get_active_tournaments()
    
    if not tournaments:
        text = "🏆 **Турниры**\n\nАктивных турниров нет. Скоро появятся новые!"
        return text, None
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for tour in tournaments:
        tour_id, name, entry_fee, prize_pool, max_players, current_players, status, start_time, end_time, created_at = tour
        
        button_text = f"🏆 {name} | {current_players}/{max_players} | {prize_pool}{CURRENCY}"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"tournament_join_{tour_id}")
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    ])
    
    text = (
        f"🏆 **Активные турниры**\n\n"
        f"💵 Входной взнос: {TOURNAMENT_ENTRY_FEE}{CURRENCY}\n"
        f"📊 Комиссия: {TOURNAMENT_COMMISSION}%\n\n"
        f"Выберите турнир:"
    )
    
    return text, keyboard
