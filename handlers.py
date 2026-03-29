from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from config import *
from database import *
from keyboards import *
from games import *

class GameStates(StatesGroup):
    waiting_bet = State()

class WithdrawStates(StatesGroup):
    waiting_amount = State()

class AdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()
    waiting_days = State()

# ==================== АДМИН ====================
async def is_admin(user_id):
    return user_id in ADMIN_IDS

async def admin_panel(message: types.Message):
    await message.answer(
        "🛡️ **Админ панель**\n\nВыберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

async def admin_give_pac(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("👤 Введите ID пользователя:")
    await state.set_state(AdminStates.waiting_user_id)
    await state.update_data(action="give_pac")

async def admin_give_premium(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("👤 Введите ID пользователя:")
    await state.set_state(AdminStates.waiting_user_id)
    await state.update_data(action="give_premium")

async def admin_give_bonus(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("👤 Введите ID пользователя:")
    await state.set_state(AdminStates.waiting_user_id)
    await state.update_data(action="give_bonus")

async def admin_process_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
    except:
        await message.answer("❌ Неверный ID!")
        await state.clear()
        return
    
    data = await state.get_data()
    action = data.get("action")
    
    if action == "give_pac":
        await message.answer(f"💰 Введите количество PAC для {user_id}:")
        await state.update_data(target_user=user_id)
        await state.set_state(AdminStates.waiting_amount)
    elif action == "give_premium":
        await message.answer(f"👑 Введите количество дней для {user_id}:")
        await state.update_data(target_user=user_id)
        await state.set_state(AdminStates.waiting_days)
    elif action == "give_bonus":
        await message.answer(f"🎁 Введите количество PAC для {user_id}:")
        await state.update_data(target_user=user_id)
        await state.set_state(AdminStates.waiting_amount)

async def admin_process_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    target_user = data.get("target_user")
    action = data.get("action")
    
    if action in ["give_pac", "give_bonus"]:
        user = await get_user(target_user)
        await update_user(target_user, pac_balance=user["pac_balance"] + amount)
        await add_transaction(target_user, "admin_gift", amount, f"Админ выдал {amount} PAC")
        await message.answer(f"✅ Выдано {amount} PAC пользователю {target_user}")
    
    await state.clear()
    
    try:
        from bot import bot
        await bot.send_message(target_user, f"🎁 Администратор выдал вам {amount} PAC!")
    except:
        pass

async def admin_process_premium(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
    except:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    target_user = data.get("target_user")
    
    premium_until = (datetime.now() + timedelta(days=days)).isoformat()
    await update_user(target_user, is_premium=1, premium_until=premium_until)
    await add_transaction(target_user, "admin_premium", 0, f"Премиум на {days} дней")
    await message.answer(f"✅ Выдан премиум на {days} дней пользователю {target_user}")
    await state.clear()

# ==================== /start ====================
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if user.get("pac_balance", 0) == 100:
        await update_user(user_id, pac_balance=BONUS_PAC, username=message.from_user.username or str(user_id))
        await message.answer(
            f"🎉 **Добро пожаловать в W1NPAKSHAM!**\n\n"
            f"💰 Вы получили {BONUS_PAC} {COIN_NAME} бонуса!\n"
            f"👤 Ваш ID: {user_id}\n\n"
            f"Попробуй свои силы в 15 играх! 🚀",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update_user(user_id, username=message.from_user.username or str(user_id))
        await message.answer(
            f"🎮 **С возвращением!**\n\n"
            f"👤 ID: {user_id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n\n"
            f"Выбирай игру!",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )

# ==================== ОБРАБОТЧИК КНОПОК ====================
async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = callback.data
    
    # АДМИН
    if data == "admin_panel" and await is_admin(user_id):
        await admin_panel(callback.message)
        await callback.answer()
        return
    elif data in ["admin_give_pac", "admin_give_premium", "admin_give_bonus"] and await is_admin(user_id):
        if data == "admin_give_pac":
            await admin_give_pac(callback, state)
        elif data == "admin_give_premium":
            await admin_give_premium(callback, state)
        else:
            await admin_give_bonus(callback, state)
        await callback.answer()
        return
    
    # ГЛАВНОЕ МЕНЮ
    if data == "main_menu":
        user = await get_user(user_id)
        await callback.message.edit_text(
            f"🎮 **Главное меню**\n\n"
            f"👤 ID: {user_id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n\n"
            f"Выберите действие:",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    # === ВЫБОР ИГРЫ ===
    elif data == "games":
        await callback.message.edit_text("🎮 **Выберите игру (15 игр):**", reply_markup=get_games_keyboard(), parse_mode="Markdown")
    
    # === СЛОТЫ ===
    elif data == "game_slots":
        await callback.message.edit_text("🎰 **Слоты**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("slots"), parse_mode="Markdown")
    
    elif data.startswith("slots_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_slots(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === КУБИК ===
    elif data == "game_dice":
        await callback.message.edit_text("🎲 **Кубик**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("dice"), parse_mode="Markdown")
    
    elif data.startswith("dice_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"🎲 **Кубик**\n\nСтавка: {bet} {COIN_NAME}\n\nУгадайте число:", reply_markup=get_dice_choice_keyboard(bet), parse_mode="Markdown")
    
    elif data.startswith("dice_choice_"):
        parts = data.split("_")
        choice = int(parts[2])
        bet = int(parts[3])
        win, result = await play_dice(user_id, bet, choice)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === РУЛЕТКА ===
    elif data == "game_roulette":
        await callback.message.edit_text("🎡 **Рулетка**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("roulette"), parse_mode="Markdown")
    
    elif data.startswith("roulette_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"🎡 **Рулетка**\n\nСтавка: {bet} {COIN_NAME}\n\nВыберите цвет:", reply_markup=get_roulette_choice_keyboard(bet), parse_mode="Markdown")
    
    elif data.startswith("roulette_choice_"):
        parts = data.split("_")
        color = parts[2]
        bet = int(parts[3])
        win, result = await play_roulette(user_id, bet, color)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === ОРЁЛ/РЕШКА ===
    elif data == "game_coin":
        await callback.message.edit_text("🪙 **Орёл/Решка**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("coin"), parse_mode="Markdown")
    
    elif data.startswith("coin_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"🪙 **Орёл/Решка**\n\nСтавка: {bet} {COIN_NAME}\n\nВыберите сторону:", reply_markup=get_coin_choice_keyboard(bet), parse_mode="Markdown")
    
    elif data.startswith("coin_choice_"):
        parts = data.split("_")
        choice = parts[2]
        bet = int(parts[3])
        win, result = await play_coin(user_id, bet, choice)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === МИНЫ ===
    elif data == "game_mines":
        await callback.message.edit_text("💣 **Мины**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("mines"), parse_mode="Markdown")
    
    elif data.startswith("mines_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"💣 **Мины**\n\nСтавка: {bet} {COIN_NAME}\n\nВыберите ячейку (1-9):", reply_markup=get_mines_choice_keyboard(bet), parse_mode="Markdown")
    
    elif data.startswith("mines_choice_"):
        parts = data.split("_")
        cell = int(parts[2])
        bet = int(parts[3])
        win, result = await play_mines(user_id, bet, cell)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === КОЛЕСО ===
    elif data == "game_wheel":
        await callback.message.edit_text("🎡 **Колесо Фортуны**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("wheel"), parse_mode="Markdown")
    
    elif data.startswith("wheel_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_wheel(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === БЛЭКДЖЕК ===
    elif data == "game_blackjack":
        await callback.message.edit_text("🃏 **Блэкджек**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("blackjack"), parse_mode="Markdown")
    
    elif data.startswith("blackjack_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_blackjack(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === ПАЛКИ ===
    elif data == "game_sticks":
        await callback.message.edit_text("🥢 **Палки**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("sticks"), parse_mode="Markdown")
    
    elif data.startswith("sticks_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"🥢 **Палки**\n\nСтавка: {bet} {COIN_NAME}\n\nУгадайте число (1-10):", reply_markup=get_sticks_choice_keyboard(bet), parse_mode="Markdown")
    
    elif data.startswith("sticks_choice_"):
        parts = data.split("_")
        choice = int(parts[2])
        bet = int(parts[3])
        win, result = await play_sticks(user_id, bet, choice)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === БОЛЬШЕ-МЕНЬШЕ ===
    elif data == "game_highlow":
        await callback.message.edit_text("📈 **Больше-Меньше**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("highlow"), parse_mode="Markdown")
    
    elif data.startswith("highlow_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"📈 **Больше-Меньше**\n\nСтавка: {bet} {COIN_NAME}\n\nВыберите:", reply_markup=get_highlow_choice_keyboard(bet), parse_mode="Markdown")
    
    elif data.startswith("highlow_choice_"):
        parts = data.split("_")
        choice = parts[2]
        bet = int(parts[3])
        win, result = await play_high_low(user_id, bet, choice)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === КЕНО ===
    elif data == "game_keno":
        await callback.message.edit_text("🎲 **Кено**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("keno"), parse_mode="Markdown")
    
    elif data.startswith("keno_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"🎲 **Кено**\n\nСтавка: {bet} {COIN_NAME}\n\nВыберите число (1-20):", reply_markup=get_keno_choice_keyboard(bet), parse_mode="Markdown")
    
    elif data.startswith("keno_choice_"):
        parts = data.split("_")
        choice = int(parts[2])
        bet = int(parts[3])
        win, result = await play_keno(user_id, bet, choice)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === БАККАРА ===
    elif data == "game_baccarat":
        await callback.message.edit_text("🃏 **Баккара**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("baccarat"), parse_mode="Markdown")
    
    elif data.startswith("baccarat_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"🃏 **Баккара**\n\nСтавка: {bet} {COIN_NAME}\n\nВыберите:", reply_markup=get_baccarat_choice_keyboard(bet), parse_mode="Markdown")
    
    elif data.startswith("baccarat_choice_"):
        parts = data.split("_")
        choice = parts[2]
        bet = int(parts[3])
        win, result = await play_baccarat(user_id, bet, choice)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === ПОКЕР ===
    elif data == "game_poker":
        await callback.message.edit_text("🃏 **Покер**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("poker"), parse_mode="Markdown")
    
    elif data.startswith("poker_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_poker(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === КРЭПС ===
    elif data == "game_craps":
        await callback.message.edit_text("🎲 **Крэпс**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("craps"), parse_mode="Markdown")
    
    elif data.startswith("craps_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_craps(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === ВИДЕО-ПОКЕР ===
    elif data == "game_video_poker":
        await callback.message.edit_text("🎰 **Видео-покер**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("video_poker"), parse_mode="Markdown")
    
    elif data.startswith("video_poker_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_video_poker(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === ЛАККИ 7 ===
    elif data == "game_lucky7":
        await callback.message.edit_text("7️⃣ **Лакки 7**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("lucky7"), parse_mode="Markdown")
    
    elif data.startswith("lucky7_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_lucky7(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # === ПОПОЛНЕНИЕ ===
    elif data == "deposit":
        await callback.message.edit_text(
            f"💎 **Пополнение {COIN_NAME}**\n\n"
            f"💰 1 {COIN_NAME} = 0.8₽\n"
            f"⚡ Минимальная покупка: 10 {COIN_NAME} (8₽)\n\n"
            f"Выберите способ оплаты:",
            reply_markup=get_payment_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "pay_sbp":
        await callback.message.edit_text(
            f"💳 **Оплата через СБП**\n\n"
            f"📱 Номер телефона: `{SBP_PHONE}`\n"
            f"💰 Сумма: любая (от 10₽)\n\n"
            f"После оплаты напишите /confirm_сумма",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "pay_crypto":
        await callback.message.edit_text(
            f"🪙 **Оплата через CryptoBot**\n\n"
            f"Скоро будет доступно...",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # === ВЫВОД ===
    elif data == "withdraw":
        await callback.answer("⏸️ Вывод временно недоступен.", show_alert=True)
    
    # === ПРЕМИУМ ===
    elif data == "premium":
        user = await get_user(user_id)
        if user.get("is_premium"):
            await callback.message.edit_text(
                f"👑 **У вас есть премиум!**\n\nАктивен до: {user['premium_until']}",
                reply_markup=get_back_keyboard(),
                parse_mode="Markdown"
            )
        else:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"💎 Купить за {PREMIUM_PRICE_PAC} PAC", callback_data="buy_premium")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
            ])
            await callback.message.edit_text(
                f"👑 **Премиум подписка**\n\n"
                f"💰 Стоимость: {PREMIUM_PRICE_PAC} {COIN_NAME}\n\n"
                f"✨ **Преимущества:**\n"
                f"• ⛏️ Шахта (до 250 PAC/день)\n"
                f"• +15 PAC/день бонус\n\n"
                f"Купить подписку?",
                reply_markup=kb,
                parse_mode="Markdown"
            )
    
    elif data == "buy_premium":
        success, msg = await buy_premium(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            user = await get_user(user_id)
            await callback.message.edit_text(
                f"👑 **Премиум активирован!**\n\n"
                f"💎 Баланс: {user['pac_balance']} {COIN_NAME}",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    
    # === ШАХТА ===
    elif data == "mine":
        info = await get_mine_info(user_id)
        if "error" in info:
            await callback.message.edit_text(info["error"], reply_markup=get_back_keyboard())
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⛏️ Собрать", callback_data="mine_collect")],
            ])
            if not info["max_level"]:
                kb.inline_keyboard.append([InlineKeyboardButton(text=f"⬆️ Улучшить ({info['upgrade_cost']} PAC)", callback_data="mine_upgrade")])
            kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
            await callback.message.edit_text(
                f"⛏️ **{info['name']}** {info['icon']}\n\n"
                f"📊 Уровень: {info['level']}\n"
                f"⚡ Добыча: {info['daily_output']} PAC/день\n"
                f"📦 Накоплено: {info['accumulated']} PAC",
                reply_markup=kb,
                parse_mode="Markdown"
            )
    
    elif data == "mine_collect":
        success, msg = await collect_mine(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            info = await get_mine_info(user_id)
            await callback.message.edit_text(
                f"⛏️ **{info['name']}** {info['icon']}\n\n"
                f"📊 Уровень: {info['level']}\n"
                f"⚡ Добыча: {info['daily_output']} PAC/день\n"
                f"📦 Накоплено: {info['accumulated']} PAC",
                reply_markup=get_back_keyboard(),
                parse_mode="Markdown"
            )
    
    elif data == "mine_upgrade":
        success, msg = await upgrade_mine(user_id)
        await callback.answer(msg, show_alert=True)
    
    # === СТАТИСТИКА ===
    elif data == "stats":
        user = await get_user(user_id)
        await callback.message.edit_text(
            f"📊 **Ваша статистика**\n\n"
            f"👤 ID: {user_id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🎮 Игр: {user['total_games']}\n"
            f"🔄 Оборот: {user['turnover']} {COIN_NAME}\n"
            f"👥 Рефералов: {user['referrals']}\n"
            f"👑 Премиум: {'✅' if user['is_premium'] else '❌'}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # === ТОП-10 ===
    elif data == "top":
        top = await get_top_users(10)
        text = "🏆 **ТОП-10 игроков:**\n\n"
        for i, (uid, name, val) in enumerate(top, 1):
            text += f"{i}. {name or uid} — {val} {COIN_NAME}\n"
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # === ПОМОЩЬ ===
    elif data == "help":
        text = (
            "❓ **Помощь**\n\n"
            "🎮 **15 игр:** Слоты, Кубик, Рулетка, Блэкджек, Мины, Колесо, Орёл/Решка,\n"
            "🥢 Палки, 📈 Больше-Меньше, 🎲 Кено, 🃏 Баккара, 🃏 Покер, 🎲 Крэпс, 🎰 Видео-покер, 7️⃣ Лакки 7\n\n"
            "💰 **Пополнение:** кнопка Пополнить → СБП\n"
            "💸 **Вывод:** временно недоступен\n"
            "👑 **Премиум:** шахта +15 PAC/день\n"
            "⛏️ **Шахта:** пассивный доход\n\n"
            "📞 **По вопросам:** @ZOJlOTOY"
        )
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # === ЕЖЕДНЕВНЫЙ БОНУС ===
    elif data == "daily":
        success, msg = await claim_daily_bonus(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            user = await get_user(user_id)
            await callback.message.edit_text(
                f"🎮 **Главное меню**\n\n"
                f"👤 ID: {user_id}\n"
                f"💎 {COIN_NAME}: {user['pac_balance']}",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    
    # === РЕФЕРАЛЫ ===
    elif data == "referral":
        user = await get_user(user_id)
        ref_link = f"https://t.me/W1NPakshamNewBot?start={user_id}"
        await callback.message.edit_text(
            f"👥 **Реферальная система**\n\n"
            f"💰 За друга: +5 {COIN_NAME}\n"
            f"👥 Ваших: {user['referrals']}\n"
            f"🔗 Ссылка:\n`{ref_link}`",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # === МАРКЕТПЛЕЙС ===
    elif data == "marketplace":
        await callback.message.edit_text(
            "🛒 **Маркетплейс**\n\nВыберите предмет:",
            reply_markup=get_marketplace_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data.startswith("buy_"):
        item_id = data.split("_")[1]
        item = MARKETPLACE_ITEMS.get(item_id)
        if item:
            user = await get_user(user_id)
            if user["pac_balance"] >= item["price"]:
                await update_user(user_id, pac_balance=user["pac_balance"] - item["price"])
                await add_transaction(user_id, "marketplace", -item["price"], f"Покупка {item['name']}")
                await callback.answer(f"✅ Вы купили {item['name']}!", show_alert=True)
                await callback.message.edit_text(
                    f"🎉 **Поздравляем!**\n\nВы купили {item['emoji']} {item['name']}\n\n{item['description']}",
                    reply_markup=get_back_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await callback.answer(f"❌ Недостаточно {COIN_NAME}!", show_alert=True)
    
    await callback.answer()

# ==================== ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ====================
async def confirm_deposit(message: types.Message):
    try:
        amount = int(message.text.split("_")[1])
        user = await get_user(message.from_user.id)
        pac_amount = amount
        await update_user(message.from_user.id, pac_balance=user["pac_balance"] + pac_amount)
        await add_transaction(message.from_user.id, "deposit", pac_amount, f"Пополнение на {amount}₽")
        await message.answer(f"✅ Пополнение подтверждено! Начислено {pac_amount} {COIN_NAME}!")
    except:
        await message.answer("❌ Используйте: /confirm_сумма")
