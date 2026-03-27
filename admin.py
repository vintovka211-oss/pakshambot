from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (
    get_user, update_user, add_transaction, add_income,
    get_monthly_free_stats, get_mine_info
)
from config import ADMIN_IDS, COIN_NAME, CURRENCY, PAC_PRICE
from keyboards import get_admin_keyboard, get_back_keyboard
import aiosqlite

DB_PATH = "w1npaksham.db"

async def is_admin(user_id: int) -> bool:
    """Проверка на админа"""
    return user_id in ADMIN_IDS

async def admin_panel(message: types.Message):
    """Открыть админ-панель"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return
    
    await message.answer(
        "🛡️ **Админ-панель**\n\nВыберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

async def show_stats(message: types.Message):
    """Показать статистику"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]
        
        async with db.execute("SELECT SUM(total_games) FROM users") as cursor:
            total_games = (await cursor.fetchone())[0] or 0
        
        async with db.execute("SELECT SUM(turnover) FROM users") as cursor:
            total_turnover = (await cursor.fetchone())[0] or 0
        
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1") as cursor:
            premium_users = (await cursor.fetchone())[0] or 0
        
        async with db.execute("SELECT COUNT(*) FROM withdraw_requests WHERE status = 'pending'") as cursor:
            pending_withdraw = (await cursor.fetchone())[0] or 0
        
        async with db.execute("SELECT COUNT(*) FROM deposit_requests WHERE status = 'pending'") as cursor:
            pending_deposit = (await cursor.fetchone())[0] or 0
        
        async with db.execute("SELECT SUM(amount) FROM bot_income") as cursor:
            total_income = (await cursor.fetchone())[0] or 0
    
    text = (
        f"📊 **Статистика бота**\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"👑 Премиум: {premium_users}\n"
        f"🎮 Сыграно игр: {total_games}\n"
        f"💰 Общий оборот: {total_turnover}{CURRENCY}\n"
        f"💵 Доход бота: {total_income}{CURRENCY}\n"
        f"📝 Заявок на вывод: {pending_withdraw}\n"
        f"💎 Заявок на пополнение: {pending_deposit}"
    )
    
    await message.edit_text(text, parse_mode="Markdown", reply_markup=get_back_keyboard())

async def show_profit(message: types.Message):
    """Показать прибыль"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT SUM(amount) FROM bot_income WHERE source = 'game_commission'") as cursor:
            game_income = (await cursor.fetchone())[0] or 0
        
        async with db.execute("SELECT SUM(amount) FROM bot_income WHERE source = 'deposit'") as cursor:
            deposit_income = (await cursor.fetchone())[0] or 0
        
        async with db.execute("SELECT SUM(amount) FROM bot_income WHERE source = 'premium'") as cursor:
            premium_income = (await cursor.fetchone())[0] or 0
        
        async with db.execute("SELECT SUM(amount) FROM bot_income") as cursor:
            total_income = (await cursor.fetchone())[0] or 0
    
    text = (
        f"💰 **Моя прибыль**\n\n"
        f"📊 Общий доход: {total_income}{CURRENCY}\n\n"
        f"🎮 Комиссия с игр: {game_income}{CURRENCY}\n"
        f"💎 Продажа PAC: {deposit_income}{CURRENCY}\n"
        f"👑 Продажа премиума: {premium_income}{CURRENCY}\n\n"
        f"💡 Чем больше игроков, тем выше прибыль!"
    )
    
    await message.edit_text(text, parse_mode="Markdown", reply_markup=get_back_keyboard())

async def show_withdraw_requests(message: types.Message):
    """Показать заявки на вывод"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, user_id, amount_pac, amount_rub FROM withdraw_requests WHERE status = 'pending'"
        ) as cursor:
            requests = await cursor.fetchall()
    
    if not requests:
        await message.edit_text("📝 Нет активных заявок на вывод", reply_markup=get_back_keyboard())
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for req_id, user_id, amount_pac, amount_rub in requests:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"💰 {user_id} - {amount_pac} PAC ({amount_rub}₽)",
                callback_data=f"admin_process_withdraw_{req_id}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    ])
    
    await message.edit_text(
        "📝 **Заявки на вывод**\n\nНажмите на заявку для обработки:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def show_deposit_requests(message: types.Message):
    """Показать заявки на пополнение"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, user_id, amount, amount_pac FROM deposit_requests WHERE status = 'pending'"
        ) as cursor:
            requests = await cursor.fetchall()
    
    if not requests:
        await message.edit_text("📝 Нет активных заявок на пополнение", reply_markup=get_back_keyboard())
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for req_id, user_id, amount, amount_pac in requests:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"💎 {user_id} - {amount}₽ ({amount_pac} PAC)",
                callback_data=f"admin_approve_deposit_{req_id}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    ])
    
    await message.edit_text(
        "💎 **Заявки на пополнение**\n\nНажмите на заявку для подтверждения:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def approve_deposit_handler(callback: types.CallbackQuery, request_id: int):
    """Подтвердить пополнение"""
    from database import approve_deposit
    
    success, message = await approve_deposit(request_id)
    await callback.answer(message, show_alert=True)
    
    if success:
        await show_deposit_requests(callback.message)

async def handle_admin_callback(callback: types.CallbackQuery):
    """Обработка админ-кнопок"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!")
        return
    
    data = callback.data
    
    if data == "admin_stats":
        await show_stats(callback.message)
    elif data == "admin_profit":
        await show_profit(callback.message)
    elif data == "admin_withdraw_requests":
        await show_withdraw_requests(callback.message)
    elif data == "admin_deposit_requests":
        await show_deposit_requests(callback.message)
    elif data.startswith("admin_approve_deposit_"):
        request_id = int(data.split("_")[3])
        await approve_deposit_handler(callback, request_id)
    elif data == "admin_panel":
        await admin_panel(callback.message)
    
    await callback.answer()
