from aiogram import types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from config import (
    COIN_NAME, CURRENCY, RANKS, PAC_PRICE, MIN_DONATION, MAX_DONATION,
    PAYMENT_METHODS, YOUR_WALLETS, PREMIUM_BENEFITS, MONTHLY_FREE_LIMITS
)
from database import (
    get_user, update_user, add_transaction, add_income, get_top_users,
    create_deposit_request, claim_daily_bonus, create_withdraw_request,
    get_monthly_free_stats, get_mine_info, upgrade_mine, collect_mine,
    init_mine, approve_deposit
)
from keyboards import (
    get_main_keyboard, get_games_keyboard, get_back_keyboard,
    get_premium_keyboard, get_mine_keyboard
)
from games import play_slots, play_dice, play_roulette
from admin import is_admin, admin_panel, handle_admin_callback
from premium_services import (
    buy_premium_with_pac, get_premium_stats, get_mine_text
)
from lottery import lottery_menu, buy_lottery_ticket
from tournaments import tournaments_menu, join_tournament
import aiosqlite

class GameStates(StatesGroup):
    waiting_bet = State()

class DonateStates(StatesGroup):
    waiting_amount = State()
    waiting_method = State()

class WithdrawStates(StatesGroup):
    waiting_amount = State()

def get_user_rank(turnover: int, total_donated: int = 0) -> dict:
    """Получить ранг"""
    rank_level = 0
    for level in sorted(RANKS.keys(), reverse=True):
        if turnover >= level and total_donated >= RANKS[level]["min_donate"]:
            rank_level = level
            break
    return RANKS[rank_level]

async def start_command(message: types.Message):
    """Обработчик /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    user = await get_user(user_id)
    await update_user(user_id, username=username)
    
    # Реферальная система
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != user_id and user["ref_by"] is None:
            await update_user(user_id, ref_by=ref_id)
            referrer = await get_user(ref_id)
            await update_user(ref_id, referrals=referrer["referrals"] + 1)
            await update_user(ref_id, pac_balance=referrer["pac_balance"] + 5)
    
    rank = get_user_rank(user["turnover"], user["total_donated"])
    stats = await get_monthly_free_stats(user_id)
    
    text = (
        f"🎮 **Добро пожаловать в W1NPAKSHAM!**\n\n"
        f"👤 ID: {user_id}\n"
        f"💰 Баланс: {user['balance']}{CURRENCY}\n"
        f"💎 {COIN_NAME}: {user['pac_balance']}\n"
        f"⭐ Ранг: {rank['icon']} {rank['name']}\n"
        f"💸 Кэшбек: +{rank['cashback']}%\n\n"
        f"📊 Лимит халявы: {stats['total_used']}/{stats['total_limit']} {COIN_NAME}/месяц\n\n"
        f"💡 Премиум даёт +100 PAC/месяц с шахты и +200 PAC бонусами!\n"
        f"Играй и зарабатывай! 🚀"
    )
    
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик callback-запросов"""
    user_id = callback.from_user.id
    data = callback.data
    
    # Админ-панель
    if data.startswith("admin_") or data == "admin_panel":
        if await is_admin(user_id):
            await handle_admin_callback(callback)
        else:
            await callback.answer("❌ Нет доступа!")
        return
    
    # Главное меню
    if data == "main_menu":
        user = await get_user(user_id)
        rank = get_user_rank(user["turnover"], user["total_donated"])
        stats = await get_monthly_free_stats(user_id)
        text = (
            f"👤 ID: {user_id}\n"
            f"💰 Баланс: {user['balance']}{CURRENCY}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"⭐ Ранг: {rank['icon']} {rank['name']}\n"
            f"📊 Халява: {stats['total_used']}/{stats['total_limit']} {COIN_NAME}/мес"
        )
        await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    # Игры
    elif data == "games_menu":
        await callback.message.edit_text("🎮 Выберите игру:", reply_markup=get_games_keyboard(), parse_mode="Markdown")
    
    elif data == "game_slots":
        await callback.message.answer("🎰 Введите сумму ставки:")
        await state.update_data(game="slots")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "game_dice":
        await callback.message.answer("🎲 Введите сумму ставки (угадайте число 1-6):")
        await state.update_data(game="dice")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "game_roulette":
        await callback.message.answer("🎡 Введите сумму ставки и цвет (🔴/⚫/🟢) через пробел:")
        await state.update_data(game="roulette")
        await state.set_state(GameStates.waiting_bet)
    
    # Донат
    elif data == "deposit":
        await callback.message.edit_text(
            f"💎 **Пополнение**\n\n"
            f"Курс: 100 {COIN_NAME} = {PAC_PRICE}{CURRENCY}\n"
            f"🎁 Бонус за первый донат: +20%\n"
            f"🎁 Бонус за крупный донат: до +30%\n"
            f"👑 VIP статус при донате от 2000₽\n\n"
            f"Введите сумму в {CURRENCY}:",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(DonateStates.waiting_amount)
    
    # Вывод
    elif data == "withdraw":
        user = await get_user(user_id)
        await callback.message.edit_text(
            f"💸 **Вывод средств**\n\n"
            f"💰 Баланс: {user['pac_balance']} {COIN_NAME}\n"
            f"💱 Курс: 1 {COIN_NAME} = 0.32{CURRENCY}\n"
            f"📊 Комиссия: 68%\n"
            f"⚠️ Минимум: 250 {COIN_NAME}\n"
            f"📅 Вывод раз в неделю\n\n"
            f"Введите сумму в {COIN_NAME}:",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(WithdrawStates.waiting_amount)
    
    # Премиум
    elif data == "premium_buy":
        user = await get_user(user_id)
        
        if user["is_premium"]:
            text = await get_premium_stats(user_id)
            await callback.message.edit_text(text, reply_markup=get_premium_keyboard(), parse_mode="Markdown")
        else:
            text = (
                f"👑 **Премиум подписка**\n\n"
                f"💰 Стоимость: {PREMIUM_PRICE_RUB}{CURRENCY} / {PREMIUM_PRICE_PAC} {COIN_NAME}\n\n"
                f"✨ **Что дает премиум:**\n"
                f"• ⛏️ Шахта (100 PAC/месяц)\n"
                f"• +{PREMIUM_BENEFITS['daily_bonus']} PAC/день (200 PAC/мес)\n"
                f"• Итого: 300 PAC/месяц бесплатно!\n"
                f"• +{PREMIUM_BENEFITS['cashback_bonus']}% кэшбэк\n"
                f"• {PREMIUM_BENEFITS['lottery_tickets']} билета в лотерею\n\n"
                f"💡 **Окупаемость:** 300 PAC ≈ 300₽, подписка 350₽ — окупается за месяц!\n\n"
                f"Купить за {COIN_NAME}?"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="💎 Купить за PAC", callback_data="premium_buy_pac"),
                    InlineKeyboardButton(text="💰 Купить за рубли", callback_data="premium_buy_rub"),
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
            ])
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif data == "premium_buy_pac":
        success, message = await buy_premium_with_pac(user_id)
        await callback.answer(message, show_alert=True)
        if success:
            await callback.message.edit_text(
                "✅ Премиум активирован!\n⛏️ Вам открыта шахта!",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    
    elif data == "premium_menu":
        text = await get_premium_stats(user_id)
        await callback.message.edit_text(text, reply_markup=get_premium_keyboard(), parse_mode="Markdown")
    
    elif data == "premium_stats":
        text = await get_premium_stats(user_id)
        await callback.message.edit_text(text, reply_markup=get_premium_keyboard(), parse_mode="Markdown")
    
    # Шахта
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
        success, message = await collect_mine(user_id)
        await callback.answer(message, show_alert=True)
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
        success, message = await upgrade_mine(user_id)
        await callback.answer(message, show_alert=True)
        if success:
            text = await get_mine_text(user_id)
            mine_info = await get_mine_info(user_id)
            keyboard = get_mine_keyboard(
                mine_info.get("is_upgrading", False),
                mine_info.get("max_level", False),
                mine_info.get("next_level_cost")
            )
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Ежедневный бонус
    elif data == "daily_bonus":
        success, message = await claim_daily_bonus(user_id)
        await callback.answer(message, show_alert=True)
        if success:
            user = await get_user(user_id)
            stats = await get_monthly_free_stats(user_id)
            rank = get_user_rank(user["turnover"], user["total_donated"])
            text = (
                f"👤 ID: {user_id}\n"
                f"💰 Баланс: {user['balance']}{CURRENCY}\n"
                f"💎 {COIN_NAME}: {user['pac_balance']}\n"
                f"⭐ Ранг: {rank['icon']} {rank['name']}\n\n"
                f"📊 Лимит халявы: {stats['total_used']}/{stats['total_limit']} {COIN_NAME}/мес"
            )
            await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    # Рефералы
    elif data == "referral":
        user = await get_user(user_id)
        ref_link = f"https://t.me/W1NPAKSHAM_BOT?start={user_id}"
        
        text = (
            f"👥 **Реферальная система**\n\n"
            f"💰 За каждого друга: +5 {COIN_NAME}\n"
            f"👥 Ваших рефералов: {user['referrals']}\n"
            f"🔗 Ваша ссылка:\n`{ref_link}`\n\n"
            f"Поделитесь ссылкой с друзьями!"
        )
        
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # Лотерея
    elif data == "lottery_menu":
        text, keyboard = await lottery_menu(user_id)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif data == "lottery_buy":
        success, message = await buy_lottery_ticket(user_id)
        await callback.answer(message, show_alert=True)
        if success:
            text, keyboard = await lottery_menu(user_id)
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Турниры
    elif data == "tournaments_menu":
        text, keyboard = await tournaments_menu(user_id)
        if keyboard:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data.startswith("tournament_join_"):
        tournament_id = int(data.split("_")[2])
        success, message = await join_tournament(user_id, tournament_id)
        await callback.answer(message, show_alert=True)
        if success:
            text, keyboard = await tournaments_menu(user_id)
            if keyboard:
                await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Статистика
    elif data == "my_stats":
        user = await get_user(user_id)
        stats = await get_monthly_free_stats(user_id)
        rank = get_user_rank(user["turnover"], user["total_donated"])
        mine_info = await get_mine_info(user_id)
        
        text = (
            f"📊 **Ваша статистика**\n\n"
            f"👤 ID: {user_id}\n"
            f"⭐ Ранг: {rank['icon']} {rank['name']}\n"
            f"💰 Баланс: {user['balance']}{CURRENCY}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🎮 Игр сыграно: {user['total_games']}\n"
            f"🔄 Оборот: {user['turnover']}{CURRENCY}\n"
            f"👥 Рефералов: {user['referrals']}\n"
            f"💸 Всего донатов: {user['total_donated']}{CURRENCY}\n\n"
            f"📅 **Лимит халявы:** {stats['total_used']}/{stats['total_limit']} {COIN_NAME}/мес\n"
        )
        
        if user["is_premium"] and "error" not in mine_info:
            text += f"⛏️ **Шахта:** {mine_info['level']}/7 ур. | {mine_info['monthly_output']} PAC/мес\n"
        
        if not user["is_premium"]:
            text += f"\n💡 **Купи премиум за {PREMIUM_PRICE_PAC} {COIN_NAME} и получай 300 PAC/мес бесплатно!**"
        
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # Топ
    elif data == "top":
        top_users = await get_top_users(10, "turnover")
        text = "🏆 **ТОП-10 по обороту:**\n\n"
        for i, (uid, username, turnover) in enumerate(top_users, 1):
            rank = get_user_rank(turnover)
            name = username or str(uid)
            text += f"{i}. {rank['icon']} {name} — {turnover}{CURRENCY}\n"
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # Помощь
    elif data == "help":
        text = (
            "❓ **Помощь**\n\n"
            "🎮 **Игры:** Слоты, Кубик, Рулетка\n"
            "💰 **Пополнение:** /deposit\n"
            "💸 **Вывод:** раз в неделю, комиссия 68%\n"
            "👑 **Премиум:** шахта (100 PAC/мес) + бонусы (200 PAC/мес)\n"
            "⛏️ **Шахта:** пассивный доход, можно улучшать до 5000 PAC/мес\n"
            "🎫 **Лотерея:** билет 50₽, джекпот накапливается\n"
            "🏆 **Турниры:** соревнуйся и выигрывай\n\n"
            "📞 По вопросам: @support"
        )
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data == "add_to_chat":
        text = (
            "➕ **Добавить бота в чат**\n\n"
            "1. Добавьте @W1NPAKSHAM_BOT в ваш чат\n"
            "2. Сделайте бота администратором\n"
            "3. Используйте /start для активации\n\n"
            "После добавления будут доступны РvР дуэли и командные турниры!"
        )
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    await callback.answer()

# ==================== ОБРАБОТЧИКИ ВВОДА ====================
async def handle_bet(message: types.Message, state: FSMContext):
    """Обработка ставки"""
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
        if len(parts) > 1:
            try:
                choice = int(parts[1])
                if 1 <= choice <= 6:
                    win, result = await play_dice(user_id, bet, choice)
                else:
                    await message.answer("❌ Выберите число от 1 до 6!")
                    await state.clear()
                    return
            except:
                await message.answer("❌ Введите число от 1 до 6!")
                await state.clear()
                return
        else:
            win, result = await play_dice(user_id, bet)
        await message.answer(result)
    
    elif game == "roulette":
        if len(parts) > 1:
            color = parts[1]
            if color in ["🔴", "⚫", "🟢"]:
                win, result = await play_roulette(user_id, bet, color)
            else:
                await message.answer("❌ Выберите цвет: 🔴, ⚫, 🟢")
                await state.clear()
                return
        else:
            await message.answer("❌ Укажите цвет! Пример: 100 🔴")
            await state.clear()
            return
        await message.answer(result)
    
    await state.clear()

async def handle_donate_amount(message: types.Message, state: FSMContext):
    """Обработка суммы доната"""
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    if amount < MIN_DONATION or amount > MAX_DONATION:
        await message.answer(f"❌ Сумма от {MIN_DONATION} до {MAX_DONATION} {CURRENCY}!")
        return
    
    await state.update_data(amount=amount)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for method, name in PAYMENT_METHODS.items():
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"💳 {name}", callback_data=f"donate_method_{method}")
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    ])
    
    await message.answer(
        f"💎 Сумма: {amount}{CURRENCY}\n\nВыберите способ оплаты:",
        reply_markup=keyboard
    )
    await state.set_state(DonateStates.waiting_method)

async def handle_donate_method(callback: types.CallbackQuery, state: FSMContext):
    """Обработка способа оплаты"""
    method = callback.data.split("_")[2]
    data = await state.get_data()
    amount = data.get("amount")
    
    success, request_id, amount_pac = await create_deposit_request(callback.from_user.id, amount, method)
    
    if not success:
        await callback.answer("❌ Ошибка!", show_alert=True)
        return
    
    wallet = YOUR_WALLETS.get(method, "Уточните у администратора")
    
    text = (
        f"💎 **Заявка #{request_id}**\n\n"
        f"💰 Сумма: {amount}{CURRENCY}\n"
        f"🎁 Получите: {amount_pac} {COIN_NAME}\n"
        f"💳 Способ: {PAYMENT_METHODS[method]}\n\n"
        f"💳 **Реквизиты:**\n`{wallet}`\n\n"
        f"📝 После оплаты отправьте /confirm_{request_id}\n"
        f"⚠️ В комментарии укажите ID заявки"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.clear()

async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    """Обработка суммы вывода"""
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    success, result = await create_withdraw_request(message.from_user.id, amount)
    await message.answer(result)
    await state.clear()

async def confirm_deposit(message: types.Message):
    """Подтверждение оплаты"""
    try:
        request_id = int(message.text.split("_")[1])
    except:
        await message.answer("❌ Используйте: /confirm_123")
        return
    
    success, result = await approve_deposit(request_id)
    await message.answer(result)
    
    if success:
        from bot import bot
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, f"💎 Заявка #{request_id} подтверждена!")
            except:
                pass
```

---
