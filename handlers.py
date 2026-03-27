"""
Обработчики команд для бота W1NPAKSHAM
"""

from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from config import (
    COIN_NAME, CURRENCY, RANKS, PAC_PRICE, MIN_DONATION, MAX_DONATION,
    PAYMENT_METHODS, YOUR_WALLETS, PREMIUM_BENEFITS
)
from database import (
    get_user, update_user, add_transaction, get_top_users,
    create_deposit_request, claim_daily_bonus, create_withdraw_request,
    get_monthly_free_stats, get_mine_info, upgrade_mine, collect_mine,
    approve_deposit
)
from keyboards import (
    get_main_keyboard, get_games_keyboard, get_back_keyboard,
    get_premium_keyboard, get_mine_keyboard, get_payment_keyboard
)
from games import play_slots, play_dice, play_roulette
from admin import is_admin, admin_panel
from premium_services import buy_premium_with_pac, get_premium_stats, get_mine_text
from lottery import lottery_menu, buy_lottery_ticket
from tournaments import tournaments_menu, join_tournament


# ==================== СОСТОЯНИЯ ====================
class GameStates(StatesGroup):
    waiting_bet = State()

class DonateStates(StatesGroup):
    waiting_amount = State()
    waiting_method = State()

class WithdrawStates(StatesGroup):
    waiting_amount = State()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_user_rank(turnover: int, total_donated: int = 0) -> dict:
    for level in sorted(RANKS.keys(), reverse=True):
        if turnover >= level and total_donated >= RANKS[level]["min_donate"]:
            return RANKS[level]
    return RANKS[0]


# ==================== /start ====================
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)
    
    user = await get_user(user_id)
    await update_user(user_id, username=username)
    
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != user_id and user.get("ref_by") is None:
            await update_user(user_id, ref_by=ref_id)
            referrer = await get_user(ref_id)
            await update_user(ref_id, referrals=referrer.get("referrals", 0) + 1)
            await update_user(ref_id, pac_balance=referrer.get("pac_balance", 0) + 5)
    
    rank = get_user_rank(user.get("turnover", 0), user.get("total_donated", 0))
    stats = await get_monthly_free_stats(user_id)
    
    text = (
        f"🎮 **Добро пожаловать в W1NPAKSHAM!**\n\n"
        f"👤 ID: {user_id}\n"
        f"💰 Баланс: {user.get('balance', 0)}{CURRENCY}\n"
        f"💎 {COIN_NAME}: {user.get('pac_balance', 0)}\n"
        f"⭐ Ранг: {rank['icon']} {rank['name']}\n"
        f"💸 Кэшбек: +{rank['cashback']}%\n\n"
        f"📊 Лимит халявы: {stats['total_used']}/{stats['total_limit']} {COIN_NAME}/месяц\n\n"
        f"Играй и зарабатывай! 🚀"
    )
    
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")


# ==================== CALLBACK ОБРАБОТЧИК ====================
async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = callback.data
    
    if data == "admin_panel" and await is_admin(user_id):
        await admin_panel(callback.message)
        await callback.answer()
        return
    
    if data == "main_menu":
        user = await get_user(user_id)
        rank = get_user_rank(user.get("turnover", 0), user.get("total_donated", 0))
        stats = await get_monthly_free_stats(user_id)
        text = (
            f"👤 ID: {user_id}\n"
            f"💰 Баланс: {user.get('balance', 0)}{CURRENCY}\n"
            f"💎 {COIN_NAME}: {user.get('pac_balance', 0)}\n"
            f"⭐ Ранг: {rank['icon']} {rank['name']}\n"
            f"📊 Халява: {stats['total_used']}/{stats['total_limit']} {COIN_NAME}/мес"
        )
        await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    elif data == "games_menu":
        await callback.message.edit_text("🎮 Выберите игру:", reply_markup=get_games_keyboard(), parse_mode="Markdown")
    
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
    
    elif data == "deposit":
        await callback.message.edit_text(
            f"💎 **Пополнение**\n\nКурс: 100 {COIN_NAME} = {PAC_PRICE}{CURRENCY}\n"
            f"🎁 Бонус за первый донат: +20%\n\n"
            f"Введите сумму в {CURRENCY}:",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(DonateStates.waiting_amount)
    
    elif data == "withdraw":
        user = await get_user(user_id)
        await callback.message.edit_text(
            f"💸 **Вывод**\n\n💰 Баланс: {user.get('pac_balance', 0)} {COIN_NAME}\n"
            f"💱 1 {COIN_NAME} = 0.32{CURRENCY}, комиссия 68%\n"
            f"⚠️ Мин. 250 {COIN_NAME}, вывод раз в неделю\n\n"
            f"Введите сумму в {COIN_NAME}:",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(WithdrawStates.waiting_amount)
    
    elif data == "premium_buy":
        user = await get_user(user_id)
        if user.get("is_premium"):
            text = await get_premium_stats(user_id)
            await callback.message.edit_text(text, reply_markup=get_premium_keyboard(), parse_mode="Markdown")
        else:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            text = (
                f"👑 **Премиум подписка**\n\n"
                f"💰 {PREMIUM_PRICE_RUB}{CURRENCY} / {PREMIUM_PRICE_PAC} {COIN_NAME}\n\n"
                f"✨ **Преимущества:**\n"
                f"• ⛏️ Шахта (100 PAC/мес)\n"
                f"• +7 PAC/день\n"
                f"• +5% кэшбэк\n"
                f"• 2 билета в лотерею\n\n"
                f"Купить за {COIN_NAME}?"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💎 Купить за PAC", callback_data="premium_buy_pac")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
            ])
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif data == "premium_buy_pac":
        success, msg = await buy_premium_with_pac(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            await callback.message.edit_text("✅ Премиум активирован!", reply_markup=get_main_keyboard())
    
    elif data == "mine_info":
        text = await get_mine_text(user_id)
        mine_info = await get_mine_info(user_id)
        if "error" not in mine_info:
            keyboard = get_mine_keyboard(
                mine_info.get("is_upgrading", False),
                mine_info.get("max_level", False),
                mine_info.get("next_level_cost")
            )
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data == "mine_collect":
        success, msg = await collect_mine(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            text = await get_mine_text(user_id)
            mine_info = await get_mine_info(user_id)
            keyboard = get_mine_keyboard(
                mine_info.get("is_upgrading", False),
                mine_info.get("max_level", False),
                mine_info.get("next_level_cost")
            )
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif data == "mine_upgrade":
        success, msg = await upgrade_mine(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            text = await get_mine_text(user_id)
            mine_info = await get_mine_info(user_id)
            keyboard = get_mine_keyboard(
                mine_info.get("is_upgrading", False),
                mine_info.get("max_level", False),
                mine_info.get("next_level_cost")
            )
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif data == "daily_bonus":
        success, msg = await claim_daily_bonus(user_id)
        await callback.answer(msg, show_alert=True)
    
    elif data == "referral":
        user = await get_user(user_id)
        ref_link = f"https://t.me/W1NPAKSHAM_BOT?start={user_id}"
        text = (
            f"👥 **Реферальная система**\n\n"
            f"💰 За друга: +5 {COIN_NAME}\n"
            f"👥 Ваших рефералов: {user.get('referrals', 0)}\n"
            f"🔗 Ссылка:\n`{ref_link}`"
        )
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data == "lottery_menu":
        text, keyboard = await lottery_menu(user_id)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif data == "lottery_buy":
        success, msg = await buy_lottery_ticket(user_id)
        await callback.answer(msg, show_alert=True)
    
    elif data == "tournaments_menu":
        text, keyboard = await tournaments_menu(user_id)
        if keyboard:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data.startswith("tournament_join_"):
        tour_id = int(data.split("_")[2])
        success, msg = await join_tournament(user_id, tour_id)
        await callback.answer(msg, show_alert=True)
    
    elif data == "top":
        top_users = await get_top_users(10, "turnover")
        text = "🏆 **ТОП-10 по обороту:**\n\n"
        for i, (uid, username, turnover) in enumerate(top_users, 1):
            rank = get_user_rank(turnover)
            name = username or str(uid)
            text += f"{i}. {rank['icon']} {name} — {turnover}{CURRENCY}\n"
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data == "help":
        text = (
            "❓ **Помощь**\n\n"
            "🎮 **Игры:** Слоты, Кубик, Рулетка\n"
            "💰 **Пополнение:** /start → Пополнить\n"
            "💸 **Вывод:** раз в неделю, комиссия 68%\n"
            "👑 **Премиум:** шахта + бонусы (300 PAC/мес)\n"
            "⛏️ **Шахта:** пассивный доход\n"
            "🎫 **Лотерея:** билет 50₽\n"
            "🏆 **Турниры:** соревнуйся и выигрывай\n\n"
            "📞 По вопросам: @support"
        )
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    await callback.answer()


# ==================== СТАВКИ ====================
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
    
    await state.clear()


# ==================== ДОНАТ ====================
async def handle_donate_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    if amount < MIN_DONATION or amount > MAX_DONATION:
        await message.answer(f"❌ Сумма от {MIN_DONATION} до {MAX_DONATION} {CURRENCY}!")
        return
    
    await state.update_data(amount=amount)
    await message.answer("Выберите способ оплаты:", reply_markup=get_payment_keyboard())
    await state.set_state(DonateStates.waiting_method)


async def handle_donate_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[2]
    data = await state.get_data()
    amount = data.get("amount")
    
    success, request_id, amount_pac = await create_deposit_request(callback.from_user.id, amount, method)
    
    if not success:
        await callback.answer("❌ Ошибка!")
        return
    
    wallet = YOUR_WALLETS.get(method, "Уточните у администратора")
    
    text = (
        f"💎 **Заявка #{request_id}**\n\n"
        f"💰 {amount}{CURRENCY} → {amount_pac} {COIN_NAME}\n"
        f"💳 {PAYMENT_METHODS[method]}\n\n"
        f"💳 **Реквизиты:**\n`{wallet}`\n\n"
        f"После оплаты отправьте /confirm_{request_id}"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.clear()


async def confirm_deposit(message: types.Message):
    try:
        request_id = int(message.text.split("_")[1])
    except:
        await message.answer("❌ Используйте: /confirm_123")
        return
    
    success, result = await approve_deposit(request_id)
    await message.answer(result)


# ==================== ВЫВОД ====================
async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    success, result = await create_withdraw_request(message.from_user.id, amount)
    await message.answer(result)
    await state.clear()
