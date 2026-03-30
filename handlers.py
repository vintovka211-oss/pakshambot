from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import asyncio
import random
import aiosqlite

from config import *
from database import *
from keyboards import *
from games import *
from rpg import *
from clans import *

# ==================== СОСТОЯНИЯ ====================
class AdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()
    waiting_days = State()

class GameStates(StatesGroup):
    waiting_bet = State()

class ClanStates(StatesGroup):
    waiting_name = State()

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

async def admin_give_rpg(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("👤 Введите ID пользователя:")
    await state.set_state(AdminStates.waiting_user_id)
    await state.update_data(action="give_rpg")

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
    elif action == "give_rpg":
        await message.answer(f"🪙 Введите количество RPG для {user_id}:")
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
    
    if action == "give_pac":
        user = await get_user(target_user)
        await update_user(target_user, pac_balance=user["pac_balance"] + amount)
        await add_transaction(target_user, "admin_gift", amount, f"Админ выдал {amount} PAC")
        await message.answer(f"✅ Выдано {amount} PAC пользователю {target_user}")
    elif action == "give_rpg":
        user = await get_user(target_user)
        await update_user(target_user, rpg_balance=user["rpg_balance"] + amount)
        await add_transaction(target_user, "admin_gift", amount, f"Админ выдал {amount} RPG")
        await message.answer(f"✅ Выдано {amount} RPG пользователю {target_user}")
    elif action == "give_bonus":
        user = await get_user(target_user)
        await update_user(target_user, pac_balance=user["pac_balance"] + amount)
        await add_transaction(target_user, "admin_gift", amount, f"Админ выдал {amount} PAC")
        await message.answer(f"✅ Выдано {amount} PAC пользователю {target_user}")
    
    await state.clear()
    
    try:
        from bot import bot
        await bot.send_message(target_user, f"🎁 Администратор выдал вам награду!")
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

# ==================== КЛАНЫ ====================
async def clan_name_handler(message: types.Message, state: FSMContext):
    clan_name = message.text.strip()
    if len(clan_name) > 20:
        await message.answer("❌ Название клана не должно превышать 20 символов!")
        return
    
    success, msg = await create_clan(message.from_user.id, clan_name)
    await message.answer(msg)
    await state.clear()
    
    if success:
        user = await get_user(message.from_user.id)
        stats = await get_player_stats(message.from_user.id)
        await message.answer(
            f"🎮 **Главное меню**\n\n"
            f"👤 ID: {message.from_user.id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"❤️ HP: {stats['hp']}/{stats['max_hp']}",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )

# ==================== /start ====================
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    stats = await get_player_stats(user_id)
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("clan_"):
        clan_id = int(args[1].split("_")[1])
        success, msg = await join_clan(user_id, clan_id)
        await message.answer(msg)
    
    if user.get("pac_balance", 0) == 100 and stats.get("level", 1) == 1:
        await update_user(user_id, pac_balance=BONUS_PAC, username=message.from_user.username or str(user_id))
        await message.answer(
            f"🎉 **Добро пожаловать в W1NPAKSHAM!** 🎉\n\n"
            f"💰 Вы получили {BONUS_PAC} {COIN_NAME} бонуса!\n"
            f"🪙 Стартовый набор: {RPG_COIN_NAME} 0\n"
            f"👤 Ваш ID: {user_id}\n"
            f"⚔️ Уровень: {stats['level']}\n\n"
            f"🎮 Играй в казино или ⚔️ сражайся с боссами!\n"
            f"💡 Кузнец поможет улучшить оружие, а в пещерах добудешь ресурсы!\n\n"
            f"🔥 **Активные ивенты:**\n"
            f"• {EVENTS['double_rpg']['name']} - до конца дня!",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update_user(user_id, username=message.from_user.username or str(user_id))
        await message.answer(
            f"🎮 **С возвращением!** 🎮\n\n"
            f"👤 ID: {user_id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n"
            f"⚔️ Уровень: {stats['level']}\n"
            f"⭐ Опыт: {stats['exp']}/{stats['level']*100}\n\n"
            f"Выбирай режим!",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )

# ==================== ПРИВЕТСТВИЕ В ЧАТЕ ====================
async def welcome_new_member(message: types.Message):
    for member in message.new_chat_members:
        if member.id == (await message.bot.me()).id:
            await message.answer(
                f"🎉 **Привет! Я W1NPAKSHAM Bot!** 🎉\n\n"
                f"💰 **Мои возможности:**\n"
                f"• 🎮 15 азартных игр\n"
                f"• ⚔️ 30 боссов с уникальными наградами\n"
                f"• ⛏️ Шахта для пассивного дохода\n"
                f"• 🧪 Зелья, артефакты, улучшения\n"
                f"• 🏰 Кланы и клановые боссы\n"
                f"• 💰 Вывод средств на карту\n\n"
                f"📱 **Играй прямо сейчас:** @W1NPakshamNewBot\n"
                f"📞 По вопросам: @ZOJlOTOY",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                f"🎉 **Добро пожаловать, {member.first_name}!** 🎉\n\n"
                f"🔥 Здесь ты найдёшь:\n"
                f"• 🎮 Азартные игры с выводом средств\n"
                f"• ⚔️ 30 боссов с крутыми наградами\n"
                f"• ⛏️ Шахту для пассивного дохода\n"
                f"• 🧪 Зелья, артефакты, прокачку\n"
                f"• 🏰 Кланы и клановые боссы\n\n"
                f"💎 **Начать игру:** @W1NPakshamNewBot\n"
                f"💰 **Бонус 100 PAC за регистрацию!**\n\n"
                f"👋 Приятной игры!",
                parse_mode="Markdown"
            )

# ==================== ОСНОВНОЙ ОБРАБОТЧИК ====================
async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = callback.data
    
    # АДМИН
    if data == "admin_panel" and await is_admin(user_id):
        await admin_panel(callback.message)
        await callback.answer()
        return
    elif data in ["admin_give_pac", "admin_give_rpg", "admin_give_premium", "admin_give_bonus"] and await is_admin(user_id):
        if data == "admin_give_pac":
            await admin_give_pac(callback, state)
        elif data == "admin_give_rpg":
            await admin_give_rpg(callback, state)
        elif data == "admin_give_premium":
            await admin_give_premium(callback, state)
        else:
            await admin_give_bonus(callback, state)
        await callback.answer()
        return
    
    # ГЛАВНОЕ МЕНЮ
    if data == "main_menu":
        user = await get_user(user_id)
        stats = await get_player_stats(user_id)
        await callback.message.edit_text(
            f"🎮 **Главное меню** 🎮\n\n"
            f"👤 ID: {user_id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n"
            f"⚔️ Уровень: {stats['level']}\n\n"
            f"🔥 **Активный ивент:** {EVENTS['double_rpg']['name']}\n\n"
            f"Выберите действие:",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    # ПОПОЛНЕНИЕ
    elif data == "deposit":
        await callback.message.edit_text(
            f"💎 **Пополнение {COIN_NAME}** 💎\n\n"
            f"💰 1 {COIN_NAME} = 0.8₽\n"
            f"⚡ Минимальная покупка: 10 {COIN_NAME} (8₽)\n\n"
            f"💳 **Оплата через СБП**\n"
            f"📱 Номер телефона: `{SBP_PHONE}`\n\n"
            f"После оплаты напишите /confirm_сумма",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # ВЫВОД
    elif data == "withdraw":
        await callback.answer("⏸️ Вывод временно недоступен.", show_alert=True)
    
    # ПРЕМИУМ
    elif data == "premium":
        user = await get_user(user_id)
        if user.get("is_premium"):
            await callback.message.edit_text(
                f"👑 **У вас есть премиум!** 👑\n\nАктивен до: {user['premium_until']}",
                reply_markup=get_back_keyboard(),
                parse_mode="Markdown"
            )
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"💎 Купить за {PREMIUM_PRICE_PAC} PAC", callback_data="buy_premium")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
            ])
            await callback.message.edit_text(
                f"👑 **Премиум подписка** 👑\n\n"
                f"💰 Стоимость: {PREMIUM_PRICE_PAC} {COIN_NAME}\n\n"
                f"✨ **Преимущества:**\n"
                f"• ⛏️ Шахта (до 250 PAC/день)\n"
                f"• +15 PAC/день бонус\n"
                f"• Скидка 20% в магазине\n\n"
                f"Купить подписку?",
                reply_markup=kb,
                parse_mode="Markdown"
            )
    
    elif data == "buy_premium":
        user = await get_user(user_id)
        if user["pac_balance"] >= PREMIUM_PRICE_PAC:
            await update_user(user_id, 
                pac_balance=user["pac_balance"] - PREMIUM_PRICE_PAC,
                is_premium=1,
                premium_until=(datetime.now() + timedelta(days=30)).isoformat()
            )
            await add_transaction(user_id, "premium", -PREMIUM_PRICE_PAC, "Премиум подписка")
            await callback.answer("✅ Премиум активирован на 30 дней!", show_alert=True)
            user = await get_user(user_id)
            stats = await get_player_stats(user_id)
            await callback.message.edit_text(
                f"🎮 **Главное меню** 🎮\n\n"
                f"👤 ID: {user_id}\n"
                f"💎 {COIN_NAME}: {user['pac_balance']}\n"
                f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
                f"❤️ HP: {stats['hp']}/{stats['max_hp']}",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await callback.answer(f"❌ Недостаточно {COIN_NAME}!", show_alert=True)
    
    # ШАХТА
    elif data == "mine":
        info = await get_mine_info(user_id)
        if "error" in info:
            await callback.message.edit_text(info["error"], reply_markup=get_back_keyboard(), parse_mode="Markdown")
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⛏️ Собрать", callback_data="mine_collect")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
            ])
            if not info["max_level"]:
                kb.inline_keyboard.insert(0, [InlineKeyboardButton(text=f"⬆️ Улучшить ({info['upgrade_cost']} PAC)", callback_data="mine_upgrade")])
            await callback.message.edit_text(
                f"⛏️ **Шахта** ⛏️\n\n"
                f"📊 Уровень: {info['level']}/7\n"
                f"⚡ Добыча: {info['daily_output']} PAC/день\n"
                f"📦 Накоплено: {info['accumulated']} PAC\n\n"
                f"💡 Шахта копит PAC до 3 дней!",
                reply_markup=kb,
                parse_mode="Markdown"
            )
    
    elif data == "mine_collect":
        success, msg = await collect_mine(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            info = await get_mine_info(user_id)
            await callback.message.edit_text(
                f"⛏️ **Шахта** ⛏️\n\n"
                f"📊 Уровень: {info['level']}/7\n"
                f"⚡ Добыча: {info['daily_output']} PAC/день\n"
                f"📦 Накоплено: {info['accumulated']} PAC",
                reply_markup=get_back_keyboard(),
                parse_mode="Markdown"
            )
    
    elif data == "mine_upgrade":
        success, msg = await upgrade_mine(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            info = await get_mine_info(user_id)
            await callback.message.edit_text(
                f"⛏️ **Шахта** ⛏️\n\n"
                f"📊 Уровень: {info['level']}/7\n"
                f"⚡ Добыча: {info['daily_output']} PAC/день\n"
                f"📦 Накоплено: {info['accumulated']} PAC",
                reply_markup=get_back_keyboard(),
                parse_mode="Markdown"
            )
    
    # ЕЖЕДНЕВНЫЙ БОНУС
    elif data == "daily":
        success, msg = await claim_daily_bonus(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            user = await get_user(user_id)
            stats = await get_player_stats(user_id)
            await callback.message.edit_text(
                f"🎮 **Главное меню** 🎮\n\n"
                f"👤 ID: {user_id}\n"
                f"💎 {COIN_NAME}: {user['pac_balance']}\n"
                f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
                f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n"
                f"⚔️ Уровень: {stats['level']}",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    
    # РЕФЕРАЛЫ
    elif data == "referral":
        user = await get_user(user_id)
        ref_link = f"https://t.me/W1NPakshamNewBot?start={user_id}"
        await callback.message.edit_text(
            f"👥 **Реферальная система** 👥\n\n"
            f"💰 За друга: +5 {COIN_NAME}\n"
            f"👥 Ваших рефералов: {user['referrals']}\n"
            f"🔗 Ссылка:\n`{ref_link}`",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # ПОМОЩЬ
    elif data == "help":
        text = (
            "❓ **Помощь** ❓\n\n"
            "🎮 **Казино:** 15 игр на выбор\n"
            "⚔️ **RPG режим:**\n"
            "• Сражайся с 30 боссами\n"
            "• Добывай ресурсы в 7 пещерах (от 5 до 120 минут)\n"
            "• Улучшай оружие и броню у кузнеца\n"
            "• Покупай предметы в магазине\n"
            "• Собирай артефакты и ресурсы\n\n"
            "🏰 **Кланы:**\n"
            "• Создай клан за 1000 RPG\n"
            "• Сражайся с клановыми боссами\n"
            "• Получай бонусы за уровень клана\n\n"
            "🔄 100 {RPG_COIN_NAME} = 1 {COIN_NAME}\n"
            "👑 Премиум даёт шахту и бонусы\n\n"
            "🔥 **Ежедневные ивенты:**\n"
            "• Пн: Двойные RPG монеты\n"
            "• Вт: Двойной опыт\n"
            "• Ср: Половина стоимости HP\n"
            "• Чт: Скидка 30% в магазине\n"
            "• Пт: Легендарные боссы чаще\n"
            "• Сб: Все бонусы сразу\n"
            "• Вс: Удвоенная удача\n\n"
            "📞 По вопросам: @ZOJlOTOY"
        )
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # ТОП-10
    elif data == "top":
        top_players = await get_top_players()
        text = "🏆 **ТОП-10 по убийствам боссов:** 🏆\n\n"
        for i, (uid, name, kills) in enumerate(top_players, 1):
            username = name or str(uid)
            text += f"{i}. {username} — {kills} убийств\n"
        if not top_players:
            text += "Пока нет убийств боссов!"
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # СТАТИСТИКА
    elif data == "stats":
        user = await get_user(user_id)
        stats = await get_player_stats(user_id)
        weapon = WEAPONS.get(stats["weapon_id"], WEAPONS[1])
        armor = ARMORS.get(stats["armor_id"], ARMORS[1])
        await callback.message.edit_text(
            f"📊 **Ваша статистика** 📊\n\n"
            f"👤 ID: {user_id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"🎮 Игр: {user['total_games']}\n"
            f"🔄 Оборот: {user['turnover']} {COIN_NAME}\n"
            f"👥 Рефералов: {user['referrals']}\n"
            f"👑 Премиум: {'✅' if user['is_premium'] else '❌'}\n"
            f"⭐ Уровень: {stats['level']}\n"
            f"📈 Опыт: {stats['exp']}/{stats['level']*100}\n"
            f"💀 Побед: {stats['kills']}\n"
            f"⚰️ Поражений: {stats['deaths']}\n"
            f"🗡️ Оружие: {weapon['icon']} {weapon['name']} +{stats['weapon_upgrade']}\n"
            f"🛡️ Броня: {armor['icon']} {armor['name']} +{stats['armor_upgrade']}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # ==================== ИГРЫ ====================
    elif data == "games":
        await callback.message.edit_text("🎮 **Выберите игру:**", reply_markup=get_games_keyboard(), parse_mode="Markdown")
    
    # СЛОТЫ
    elif data == "game_slots":
        await callback.message.edit_text("🎰 **Слоты**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("slots"), parse_mode="Markdown")
    elif data.startswith("slots_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_slots(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # КУБИК
    elif data == "game_dice":
        await callback.message.edit_text("🎲 **Кубик**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("dice"), parse_mode="Markdown")
    elif data.startswith("dice_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"🎲 **Кубик**\n\nСтавка: {bet} {COIN_NAME}\n\nУгадайте число:", reply_markup=get_dice_choice_keyboard(bet), parse_mode="Markdown")
    elif data.startswith("dice_choice_"):
        parts = data.split("_")
        choice = int(parts[2])
        bet = int(parts[3])
        win, result = await play_dice(user_id, bet, choice, callback.message)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # РУЛЕТКА
    elif data == "game_roulette":
        await callback.message.edit_text("🎡 **Рулетка**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("roulette"), parse_mode="Markdown")
    elif data.startswith("roulette_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"🎡 **Рулетка**\n\nСтавка: {bet} {COIN_NAME}\n\nВыберите цвет:", reply_markup=get_roulette_choice_keyboard(bet), parse_mode="Markdown")
    elif data.startswith("roulette_choice_"):
        parts = data.split("_")
        color = parts[2]
        bet = int(parts[3])
        win, result = await play_roulette(user_id, bet, color, callback.message)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # ОРЁЛ/РЕШКА
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
    
    # МИНЫ
    elif data == "game_mines":
        await callback.message.edit_text("💣 **Мины**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("mines"), parse_mode="Markdown")
    elif data.startswith("mines_bet_"):
        bet = int(data.split("_")[2])
        await callback.message.edit_text(f"💣 **Мины**\n\nСтавка: {bet} {COIN_NAME}\n\nВыберите ячейку (1-9):", reply_markup=get_mines_choice_keyboard(bet), parse_mode="Markdown")
    elif data.startswith("mines_choice_"):
        parts = data.split("_")
        cell = int(parts[2]) - 1
        bet = int(parts[3])
        win, result = await play_mines(user_id, bet, cell, callback.message)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # КОЛЕСО
    elif data == "game_wheel":
        await callback.message.edit_text("🎡 **Колесо Фортуны**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("wheel"), parse_mode="Markdown")
    elif data.startswith("wheel_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_wheel(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # БЛЭКДЖЕК
    elif data == "game_blackjack":
        await callback.message.edit_text("🃏 **Блэкджек**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("blackjack"), parse_mode="Markdown")
    elif data.startswith("blackjack_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_blackjack(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # ПАЛКИ
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
    
    # БОЛЬШЕ-МЕНЬШЕ
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
    
    # КЕНО
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
    
    # БАККАРА
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
    
    # ПОКЕР
    elif data == "game_poker":
        await callback.message.edit_text("🃏 **Покер**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("poker"), parse_mode="Markdown")
    elif data.startswith("poker_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_poker(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # КРЭПС
    elif data == "game_craps":
        await callback.message.edit_text("🎲 **Крэпс**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("craps"), parse_mode="Markdown")
    elif data.startswith("craps_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_craps(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # ВИДЕО-ПОКЕР
    elif data == "game_video_poker":
        await callback.message.edit_text("🎰 **Видео-покер**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("video_poker"), parse_mode="Markdown")
    elif data.startswith("video_poker_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_video_poker(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # ЛАККИ 7
    elif data == "game_lucky7":
        await callback.message.edit_text("7️⃣ **Лакки 7**\n\nВыберите ставку:", reply_markup=get_bet_keyboard("lucky7"), parse_mode="Markdown")
    elif data.startswith("lucky7_bet_"):
        bet = int(data.split("_")[2])
        win, result = await play_lucky7(user_id, bet)
        user = await get_user(user_id)
        await callback.message.edit_text(f"{result}\n\n💎 Баланс: {user['pac_balance']} {COIN_NAME}", reply_markup=get_games_keyboard(), parse_mode="Markdown")
        if win > 0:
            await show_animation(callback.message, win)
    
    # ==================== RPG РАЗДЕЛ ====================
    elif data == "rpg_menu":
        user = await get_user(user_id)
        stats = await get_player_stats(user_id)
        tool = await get_tool(user_id)
        await callback.message.edit_text(
            f"⚔️ **RPG РАЗДЕЛ** ⚔️\n\n"
            f"📊 Уровень: {stats['level']}\n"
            f"⭐ Опыт: {stats['exp']}/{stats['level']*100}\n"
            f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"🗡️ Оружие: {WEAPONS.get(stats['weapon_id'], WEAPONS[1])['name']} +{stats['weapon_upgrade']}\n"
            f"🛡️ Броня: {ARMORS.get(stats['armor_id'], ARMORS[1])['name']} +{stats['armor_upgrade']}\n"
            f"🔧 Инструмент: {tool['name']}\n"
            f"💀 Побед: {stats['kills']} | Поражений: {stats['deaths']}\n\n"
            f"🔥 **Доступно боссов:** {len([b for b in BOSSES.values() if b['min_level'] <= stats['level']])}/{len(BOSSES)}\n\n"
            f"Выберите действие:",
            reply_markup=get_rpg_keyboard(),
            parse_mode="Markdown"
        )
    
    # УЛУЧШЕНИЕ ИНСТРУМЕНТА
    elif data == "upgrade_tool":
        await upgrade_tool(user_id, callback.message)
    
    # ПРОДАЖА РУДЫ
    elif data == "sell_ores":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT item_id, quantity FROM inventory WHERE user_id = ? AND item_type = 'ore' AND quantity > 0", (user_id,)) as cursor:
                ores = await cursor.fetchall()
        
        if not ores:
            await callback.answer("❌ У вас нет руды для продажи!", show_alert=True)
            return
        
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        for ore_id, qty in ores:
            ore = ORES[ore_id]
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"{ore['icon']} {ore['name']} x{qty} - {ore['value'] * qty} 🪙", callback_data=f"sell_ore_{ore_id}_{qty}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")])
        await callback.message.edit_text("💰 **Продажа руды**\n\nВыберите ресурс для продажи:", reply_markup=kb, parse_mode="Markdown")
    
    elif data.startswith("sell_ore_"):
        parts = data.split("_")
        ore_id = parts[2]
        quantity = int(parts[3])
        await sell_ore(user_id, ore_id, quantity, callback.message)
    
        # БОССЫ
    elif data == "fight_boss":
        await callback.message.edit_text("⚔️ **Выберите босса:**", reply_markup=get_boss_keyboard(), parse_mode="Markdown")
    
    elif data.startswith("boss_"):
        boss_id = int(data.split("_")[1])
        await fight_boss_start(user_id, boss_id, callback.message)
    
    elif data == "fight_attack":
        await fight_attack(user_id, callback, callback.message)
    
    elif data == "fight_heal":
        await fight_heal(user_id, callback, callback.message)
    
    # ПЕЩЕРА
    elif data == "cave_menu":
        await callback.message.edit_text("⛏️ **Выберите пещеру:**", reply_markup=get_cave_keyboard(), parse_mode="Markdown")
    
    elif data.startswith("cave_") and not data.startswith("cave_time_"):
        cave_level = int(data.split("_")[1])
        cave = CAVES[cave_level]
        await callback.message.edit_text(
            f"⛏️ **{cave['name']}** ⛏️\n\n"
            f"💰 Добыча: {cave['min_resources']}-{cave['max_resources']} ресурсов\n"
            f"🔧 Требуется инструмент: {TOOLS[cave['required_tool']]['name']}\n"
            f"🎁 Ресурсы: {', '.join([t for t in cave['tiers']])}\n\n"
            f"Выберите время добычи:",
            reply_markup=get_cave_duration_keyboard(cave_level),
            parse_mode="Markdown"
        )
    
    elif data.startswith("cave_time_"):
        parts = data.split("_")
        cave_level = int(parts[2])
        duration = int(parts[3])
        await go_to_cave(user_id, cave_level, duration, callback.message)
    
    # КУЗНЕЦ
    elif data == "forge":
        stats = await get_player_stats(user_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗡️ Улучшить оружие", callback_data="upgrade_weapon")],
            [InlineKeyboardButton(text="🛡️ Улучшить броню", callback_data="upgrade_armor")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")]
        ])
        await callback.message.edit_text(
            f"🔨 **Кузнец** 🔨\n\n"
            f"🗡️ Оружие: +{stats['weapon_upgrade']} (след. уровень: {100 * (2 ** stats['weapon_upgrade'])} 🪙)\n"
            f"🛡️ Броня: +{stats['armor_upgrade']} (след. уровень: {80 * (2 ** stats['armor_upgrade'])} 🪙)\n\n"
            f"Улучшение увеличивает атаку/защиту!",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    
    elif data == "upgrade_weapon":
        await upgrade_weapon(user_id, callback.message)
    
    elif data == "upgrade_armor":
        await upgrade_armor(user_id, callback.message)
    
    # МАГАЗИН
    elif data == "shop":
        await callback.message.edit_text("🏪 **Магазин** 🏪\n\nВыберите категорию:", reply_markup=get_shop_keyboard(), parse_mode="Markdown")
    
    elif data.startswith("buy_weapon_"):
        item_id = int(data.split("_")[2])
        item = WEAPONS[item_id]
        await buy_item(user_id, "weapon", item_id, item["price"], callback.message)
    
    elif data.startswith("buy_armor_"):
        item_id = int(data.split("_")[2])
        item = ARMORS[item_id]
        await buy_item(user_id, "armor", item_id, item["price"], callback.message)
    
    elif data.startswith("buy_potion_"):
        potion_id = data.split("_")[2]
        item = POTIONS[potion_id]
        await buy_item(user_id, "potion", potion_id, item["price"], callback.message)
    
    # ИНВЕНТАРЬ
    elif data == "my_inventory":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT item_type, item_id, quantity FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
                items = await cursor.fetchall()
        
        if not items:
            text = "🎒 **Инвентарь пуст!**\n\nКупите предметы в магазине."
        else:
            text = "🎒 **Ваш инвентарь:** 🎒\n\n"
            for item_type, item_id, qty in items:
                if item_type == "weapon":
                    name = WEAPONS[int(item_id)]["name"]
                    icon = WEAPONS[int(item_id)]["icon"]
                elif item_type == "armor":
                    name = ARMORS[int(item_id)]["name"]
                    icon = ARMORS[int(item_id)]["icon"]
                elif item_type == "potion":
                    name = POTIONS[item_id]["name"]
                    icon = POTIONS[item_id]["icon"]
                elif item_type == "ore":
                    name = ORES[item_id]["name"]
                    icon = ORES[item_id]["icon"]
                elif item_type == "artifact":
                    name = ARTIFACTS[int(item_id)]["name"]
                    icon = ARTIFACTS[int(item_id)]["icon"]
                else:
                    continue
                text += f"{icon} {name} x{qty}\n"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗡️ Экипировать оружие", callback_data="equip_weapon")],
            [InlineKeyboardButton(text="🛡️ Экипировать броню", callback_data="equip_armor")],
            [InlineKeyboardButton(text="✨ Экипировать артефакт", callback_data="equip_artifact")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")]
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    
    elif data == "equip_weapon":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT item_id FROM inventory WHERE user_id = ? AND item_type = 'weapon'", (user_id,)) as cursor:
                weapons = await cursor.fetchall()
        
        if not weapons:
            await callback.answer("❌ У вас нет оружия!", show_alert=True)
            return
        
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        for w in weapons:
            wid = int(w[0])
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"{WEAPONS[wid]['icon']} {WEAPONS[wid]['name']}", callback_data=f"equip_weapon_{wid}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="my_inventory")])
        await callback.message.edit_text("🗡️ **Выберите оружие для экипировки:**", reply_markup=kb, parse_mode="Markdown")
    
    elif data.startswith("equip_weapon_"):
        wid = int(data.split("_")[2])
        await equip_item(user_id, "weapon", wid, callback.message)
    
    elif data == "equip_armor":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT item_id FROM inventory WHERE user_id = ? AND item_type = 'armor'", (user_id,)) as cursor:
                armors = await cursor.fetchall()
        
        if not armors:
            await callback.answer("❌ У вас нет брони!", show_alert=True)
            return
        
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        for a in armors:
            aid = int(a[0])
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"{ARMORS[aid]['icon']} {ARMORS[aid]['name']}", callback_data=f"equip_armor_{aid}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="my_inventory")])
        await callback.message.edit_text("🛡️ **Выберите броню для экипировки:**", reply_markup=kb, parse_mode="Markdown")
    
    elif data.startswith("equip_armor_"):
        aid = int(data.split("_")[2])
        await equip_item(user_id, "armor", aid, callback.message)
    
    elif data == "equip_artifact":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT item_id FROM inventory WHERE user_id = ? AND item_type = 'artifact'", (user_id,)) as cursor:
                artifacts = await cursor.fetchall()
        
        if not artifacts:
            await callback.answer("❌ У вас нет артефактов!", show_alert=True)
            return
        
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        for a in artifacts:
            aid = int(a[0])
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"{ARTIFACTS[aid]['icon']} {ARTIFACTS[aid]['name']}", callback_data=f"equip_artifact_{aid}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="my_inventory")])
        await callback.message.edit_text("✨ **Выберите артефакт для экипировки:**", reply_markup=kb, parse_mode="Markdown")
    
    elif data.startswith("equip_artifact_"):
        aid = int(data.split("_")[2])
        await equip_item(user_id, "artifact", aid, callback.message)
    
    # ХАРАКТЕРИСТИКИ
    elif data == "my_stats_rpg":
        stats = await get_player_stats(user_id)
        user = await get_user(user_id)
        weapon = WEAPONS.get(stats["weapon_id"], WEAPONS[1])
        armor = ARMORS.get(stats["armor_id"], ARMORS[1])
        tool = await get_tool(user_id)
        total_attack = 10 + stats["level"] + weapon["attack"] + (stats["weapon_upgrade"] * 5)
        total_defense = stats["level"] + armor["defense"] + (stats["armor_upgrade"] * 3)
        
        await callback.message.edit_text(
            f"📊 **Ваши характеристики:** 📊\n\n"
            f"⭐ Уровень: {stats['level']}\n"
            f"📈 Опыт: {stats['exp']}/{stats['level']*100}\n"
            f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n"
            f"🗡️ Атака: {total_attack}\n"
            f"🛡️ Защита: {total_defense}\n"
            f"💀 Побед: {stats['kills']}\n"
            f"⚰️ Поражений: {stats['deaths']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n\n"
            f"⚔️ **Снаряжение:**\n"
            f"• Оружие: {weapon['icon']} {weapon['name']} +{stats['weapon_upgrade']}\n"
            f"• Броня: {armor['icon']} {armor['name']} +{stats['armor_upgrade']}\n"
            f"🔧 Инструмент: {tool['name']}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # ЗЕЛЬЯ
    elif data == "use_potion":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT item_id, quantity FROM inventory WHERE user_id = ? AND item_type = 'potion' AND quantity > 0", (user_id,)) as cursor:
                potions = await cursor.fetchall()
        
        if not potions:
            await callback.answer("❌ У вас нет зелий! Купите в магазине.", show_alert=True)
            return
        
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        for p in potions:
            pid = p[0]
            qty = p[1]
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"{POTIONS[pid]['icon']} {POTIONS[pid]['name']} x{qty}", callback_data=f"use_potion_{pid}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")])
        await callback.message.edit_text("🧪 **Выберите зелье:**", reply_markup=kb, parse_mode="Markdown")
    
    elif data.startswith("use_potion_"):
        potion_id = data.split("_")[2]
        await use_potion(user_id, potion_id, callback.message)
    
    # ОБМЕН ВАЛЮТЫ
    elif data == "exchange_rpg":
        user = await get_user(user_id)
        if user["rpg_balance"] < RPG_TO_PAC_RATE:
            await callback.answer(f"❌ Нужно {RPG_TO_PAC_RATE} {RPG_COIN_NAME} для обмена!", show_alert=True)
            return
        
        pac_amount = user["rpg_balance"] // RPG_TO_PAC_RATE
        new_rpg = user["rpg_balance"] % RPG_TO_PAC_RATE
        new_pac = user["pac_balance"] + pac_amount
        
        await update_user(user_id, rpg_balance=new_rpg, pac_balance=new_pac)
        await add_transaction(user_id, "exchange", pac_amount, f"Обмен {pac_amount} RPG → {pac_amount} PAC")
        
        await callback.answer(f"🔄 Обмен завершён! {pac_amount} {RPG_COIN_NAME} → {pac_amount} {COIN_NAME}", show_alert=True)
        user = await get_user(user_id)
        stats = await get_player_stats(user_id)
        await callback.message.edit_text(
            f"⚔️ **RPG РАЗДЕЛ** ⚔️\n\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n\n"
            f"Выберите действие:",
            reply_markup=get_rpg_keyboard(),
            parse_mode="Markdown"
        )
    
    # ==================== КЛАНЫ ====================
    elif data == "clan_menu":
        clan = await get_user_clan(user_id)
        if clan:
            text = await get_clan_info(clan["id"])
            await callback.message.edit_text(text, reply_markup=get_clan_keyboard(), parse_mode="Markdown")
        else:
            await callback.message.edit_text("🏰 **Кланы**\n\nВы не состоите в клане!\n\nСоздайте свой клан или вступите в существующий.", 
                                            reply_markup=get_no_clan_keyboard(), parse_mode="Markdown")
    
    elif data == "clan_create":
        await callback.message.answer("🏷️ Введите название клана (до 20 символов):")
        await state.set_state(ClanStates.waiting_name)
    
    elif data == "clan_info":
        clan = await get_user_clan(user_id)
        if clan:
            text = await get_clan_info(clan["id"])
            await callback.message.edit_text(text, reply_markup=get_clan_keyboard(), parse_mode="Markdown")
    
    elif data == "clan_members":
        clan = await get_user_clan(user_id)
        if clan:
            members = eval(clan["members"])
            text = "👥 **Участники клана:**\n\n"
            for i, member in enumerate(members, 1):
                user = await get_user(member)
                stats = await get_player_stats(member)
                role = "👑 Лидер" if member == clan["leader_id"] else "⚔️ Воин"
                text += f"{i}. {user['username'] or member} - {role} (Ур.{stats['level']})\n"
            await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data == "clan_boss":
        clan = await get_user_clan(user_id)
        if clan:
            success, msg = await start_clan_boss(clan["id"])
            await callback.answer(msg, show_alert=True)
            if success:
                await callback.message.edit_text(msg, reply_markup=get_clan_keyboard(), parse_mode="Markdown")
    
    elif data == "clan_upgrade":
        clan = await get_user_clan(user_id)
        if clan and clan["leader_id"] == user_id:
            next_level = CLAN_LEVELS.get(clan["level"] + 1)
            if next_level and clan["exp"] >= next_level["exp_needed"]:
                success, msg = await update_clan_exp(clan["id"], clan["exp"])
                await callback.answer(msg, show_alert=True)
            else:
                await callback.answer(f"❌ Нужно {next_level['exp_needed']} опыта!", show_alert=True)
        else:
            await callback.answer("❌ Только лидер может улучшить клан!", show_alert=True)
    
    elif data == "clan_leave":
        success, msg = await leave_clan(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            await callback.message.edit_text("🏰 **Кланы**\n\nВы покинули клан.", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    elif data == "clan_disband":
        success, msg = await disband_clan(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            await callback.message.edit_text("🏰 **Кланы**\n\nКлан распущен.", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    elif data == "clan_search":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT id, name, level FROM clans ORDER BY level DESC LIMIT 20") as cursor:
                clans = await cursor.fetchall()
        
        text = "🔍 **Поиск кланов:**\n\n"
        for cid, name, level in clans:
            level_data = CLAN_LEVELS.get(level, CLAN_LEVELS[1])
            text += f"{level_data['icon']} {name} (Ур.{level})\n"
            text += f"   [Вступить](https://t.me/W1NPakshamNewBot?start=clan_{cid})\n\n"
        
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data.startswith("clan_") and data != "clan_menu" and data != "clan_info" and data != "clan_members" and data != "clan_boss" and data != "clan_upgrade" and data != "clan_leave" and data != "clan_disband" and data != "clan_search":
        clan_id = int(data.split("_")[1])
        success, msg = await join_clan(user_id, clan_id)
        await callback.answer(msg, show_alert=True)
        if success:
            await callback.message.edit_text("🏰 **Кланы**\n\nВы вступили в клан!", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    await callback.answer()

# ==================== ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ====================
async def confirm_deposit(message: types.Message):
    try:
        amount = int(message.text.split("_")[1])
        user = await get_user(message.from_user.id)
        await update_user(message.from_user.id, pac_balance=user["pac_balance"] + amount)
        await add_transaction(message.from_user.id, "deposit", amount, f"Пополнение на {amount}₽")
        await message.answer(f"✅ Пополнение подтверждено! Начислено {amount} {COIN_NAME}!")
    except:
        await message.answer("❌ Используйте: /confirm_сумма")
