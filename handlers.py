from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from config import *
from database import *
from keyboards import *
from games import *

# ==================== СОСТОЯНИЯ ====================
class GameStates(StatesGroup):
    waiting_bet = State()

class DonateStates(StatesGroup):
    waiting_amount = State()
    waiting_method = State()

class WithdrawStates(StatesGroup):
    waiting_amount = State()

# ==================== /start ====================
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    await update_user(user_id, username=message.from_user.username or str(user_id))
    
    await message.answer(
        f"🎮 **Добро пожаловать!**\n\n"
        f"👤 ID: {user_id}\n"
        f"💰 Баланс: {user['balance']}{CURRENCY}\n"
        f"💎 {COIN_NAME}: {user['pac_balance']}\n\n"
        f"Используйте кнопки ниже!",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# ==================== ОБРАБОТЧИК КНОПОК ====================
async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = callback.data
    
    # ГЛАВНОЕ МЕНЮ
    if data == "main_menu":
        user = await get_user(user_id)
        await callback.message.edit_text(
            f"👤 ID: {user_id}\n💰 Баланс: {user['balance']}{CURRENCY}\n💎 {COIN_NAME}: {user['pac_balance']}",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    # ИГРЫ
    elif data == "games":
        await callback.message.edit_text("🎮 Выберите игру:", reply_markup=get_games_keyboard())
    
    elif data == "game_slots":
        await callback.message.answer("🎰 Введите сумму ставки:")
        await state.update_data(game="slots")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "game_dice":
        await callback.message.answer("🎲 Введите сумму ставки и число (1-6), например: 100 5")
        await state.update_data(game="dice")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "game_roulette":
        await callback.message.answer("🎡 Введите сумму и цвет (🔴/⚫/🟢), например: 100 🔴")
        await state.update_data(game="roulette")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "game_blackjack":
        await callback.message.answer("🃏 Введите сумму ставки:")
        await state.update_data(game="blackjack")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "game_mines":
        await callback.message.answer("💣 Введите сумму ставки:")
        await state.update_data(game="mines")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "game_wheel":
        await callback.message.answer("🎡 Введите сумму ставки:")
        await state.update_data(game="wheel")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "game_coin":
        await callback.message.answer("🪙 Введите сумму и выбор (орел/решка), например: 100 орел")
        await state.update_data(game="coin")
        await state.set_state(GameStates.waiting_bet)
    
    # ПОПОЛНЕНИЕ
    elif data == "deposit":
        await callback.message.edit_text(
            f"💎 Введите сумму в {CURRENCY}:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(DonateStates.waiting_amount)
    
    # ВЫВОД
    elif data == "withdraw":
        user = await get_user(user_id)
        await callback.message.edit_text(
            f"💸 Баланс: {user['pac_balance']} {COIN_NAME}\nМин. вывод: {MIN_WITHDRAW_PAC} {COIN_NAME}\n\nВведите сумму:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(WithdrawStates.waiting_amount)
    
    # ПРЕМИУМ
    elif data == "premium":
        user = await get_user(user_id)
        if user.get("is_premium"):
            await callback.message.edit_text(
                f"👑 У вас есть премиум до {user['premium_until']}",
                reply_markup=get_back_keyboard()
            )
        else:
            await callback.message.edit_text(
                f"👑 **Премиум подписка**\n\n"
                f"💰 {PREMIUM_PRICE_RUB}{CURRENCY} / {PREMIUM_PRICE_PAC} {COIN_NAME}\n\n"
                f"✨ **Преимущества:**\n"
                f"• ⛏️ Шахта (100 PAC/мес)\n"
                f"• +7 PAC/день\n"
                f"• +5% кэшбэк\n\n"
                f"Купить за {COIN_NAME}? Напишите /premium",
                reply_markup=get_back_keyboard(),
                parse_mode="Markdown"
            )
    
    # ШАХТА
    elif data == "mine":
        user = await get_user(user_id)
        if not user.get("is_premium"):
            await callback.message.edit_text(
                "❌ Шахта доступна только премиум-пользователям!",
                reply_markup=get_back_keyboard()
            )
        else:
            await callback.message.edit_text(
                f"⛏️ **Шахта**\n\n"
                f"Уровень: 1\n"
                f"Добыча: 3.33 PAC/день\n"
                f"Накоплено: 0 PAC\n\n"
                f"Улучшение стоит 500 PAC",
                reply_markup=get_back_keyboard(),
                parse_mode="Markdown"
            )
    
    # СТАТИСТИКА
    elif data == "stats":
        user = await get_user(user_id)
        await callback.message.edit_text(
            f"📊 **Ваша статистика**\n\n"
            f"👤 ID: {user_id}\n"
            f"💰 Баланс: {user['balance']}{CURRENCY}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🎮 Игр сыграно: {user['total_games']}\n"
            f"🔄 Оборот: {user['turnover']}{CURRENCY}\n"
            f"👥 Рефералов: {user['referrals']}\n"
            f"👑 Премиум: {'✅' if user['is_premium'] else '❌'}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # ТОП-10
    elif data == "top":
        top_users = await get_top_users(10, "turnover")
        text = "🏆 **ТОП-10 по обороту:**\n\n"
        for i, (uid, username, turnover) in enumerate(top_users, 1):
            name = username or str(uid)
            text += f"{i}. {name} — {turnover}{CURRENCY}\n"
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # ПОМОЩЬ
    elif data == "help":
        text = (
            "❓ **Помощь**\n\n"
            "🎮 **Игры:** Слоты, Кубик, Рулетка, Блэкджек, Мины, Колесо Фортуны, Орёл/Решка\n"
            "💰 **Пополнение:** кнопка Пополнить\n"
            "💸 **Вывод:** раз в неделю, комиссия 68%\n"
            "👑 **Премиум:** шахта + бонусы\n"
            "⛏️ **Шахта:** пассивный доход\n\n"
            "По вопросам: @support"
        )
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # ЕЖЕДНЕВНЫЙ БОНУС
    elif data == "daily":
        success, msg = await claim_daily_bonus(user_id)
        await callback.answer(msg, show_alert=True)
    
    # РЕФЕРАЛЫ
    elif data == "referral":
        user = await get_user(user_id)
        ref_link = f"https://t.me/W1NPakshamNewBot?start={user_id}"
        await callback.message.edit_text(
            f"👥 **Реферальная система**\n\n"
            f"💰 За друга: +5 {COIN_NAME}\n"
            f"👥 Ваших рефералов: {user['referrals']}\n"
            f"🔗 Ссылка:\n`{ref_link}`",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    await callback.answer()

# ==================== ОБРАБОТКА СТАВОК ====================
async def handle_bet(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split()
        bet = int(parts[0])
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    game = data.get("game")
    user_id = message.from_user.id
    
    if game == "slots":
        win, result = await play_slots(user_id, bet)
        await message.answer(result)
    
    elif game == "dice":
        choice = int(parts[1]) if len(parts) > 1 else None
        win, result = await play_dice(user_id, bet, choice)
        await message.answer(result)
    
    elif game == "roulette":
        color = parts[1] if len(parts) > 1 else "🔴"
        win, result = await play_roulette(user_id, bet, color)
        await message.answer(result)
    
    elif game == "blackjack":
        win, result = await play_blackjack(user_id, bet)
        await message.answer(result)
    
    elif game == "mines":
        win, result = await play_mines(user_id, bet)
        await message.answer(result)
    
    elif game == "wheel":
        win, result = await play_wheel(user_id, bet)
        await message.answer(result)
    
    elif game == "coin":
        choice = parts[1] if len(parts) > 1 else "орел"
        win, result = await play_coin(user_id, bet, choice)
        await message.answer(result)
    
    await state.clear()

# ==================== ДОНАТ ====================
async def handle_donate_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    if amount < 100 or amount > 50000:
        await message.answer(f"❌ Сумма от 100 до 50000 {CURRENCY}!")
        return
    
    await state.update_data(amount=amount)
    await message.answer("Выберите способ оплаты:", reply_markup=get_payment_keyboard())
    await state.set_state(DonateStates.waiting_method)

async def handle_donate_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[2]
    data = await state.get_data()
    amount = data.get("amount")
    
    success, req_id, pac = await create_deposit_request(callback.from_user.id, amount, method)
    if not success:
        await callback.answer("Ошибка!")
        return
    
    wallet = YOUR_WALLETS.get(method, "Уточните")
    await callback.message.edit_text(
        f"💎 **Заявка #{req_id}**\n\n"
        f"💰 {amount}{CURRENCY} → {pac} {COIN_NAME}\n"
        f"💳 {PAYMENT_METHODS[method]}\n\n"
        f"💳 **Реквизиты:**\n`{wallet}`\n\n"
        f"После оплаты отправьте /confirm_{req_id}",
        parse_mode="Markdown"
    )
    await state.clear()

async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    success, result = await create_withdraw_request(message.from_user.id, amount)
    await message.answer(result)
    await state.clear()

async def confirm_deposit(message: types.Message):
    try:
        req_id = int(message.text.split("_")[1])
    except:
        await message.answer("❌ Используйте: /confirm_123")
        return
    
    success, result = await approve_deposit(req_id)
    await message.answer(result)
