from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import asyncio
import random

from config import *
from database import *
from keyboards import *
from games import *
from rpg import *

# ==================== СОСТОЯНИЯ ====================
class AdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()
    waiting_days = State()

class GameStates(StatesGroup):
    waiting_bet = State()

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

# ==================== /start ====================
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    stats = await get_player_stats(user_id)
    
    if user.get("pac_balance", 0) == 100 and stats.get("level", 1) == 1:
        await update_user(user_id, pac_balance=BONUS_PAC, username=message.from_user.username or str(user_id))
        await message.answer(
            f"🎉 **Добро пожаловать в W1NPAKSHAM!**\n\n"
            f"💰 Вы получили {BONUS_PAC} {COIN_NAME} бонуса!\n"
            f"🪙 Стартовый набор: {RPG_COIN_NAME} 0\n"
            f"👤 Ваш ID: {user_id}\n\n"
            f"🎮 Играй в казино или ⚔️ сражайся с боссами!\n"
            f"💡 Кузнец поможет улучшить оружие, а в пещерах добудешь ресурсы!",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update_user(user_id, username=message.from_user.username or str(user_id))
        await message.answer(
            f"🎮 **С возвращением!**\n\n"
            f"👤 ID: {user_id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n\n"
            f"Выбирай режим!",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )

# ==================== ГЛАВНЫЙ ОБРАБОТЧИК ====================
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
            f"🎮 **Главное меню**\n\n"
            f"👤 ID: {user_id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n\n"
            f"Выберите действие:",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    # ==================== ИГРЫ (КАЗИНО) ====================
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
        await callback.message.edit_text(
            f"⚔️ **RPG РАЗДЕЛ** ⚔️\n\n"
            f"📊 Уровень: {stats['level']}\n"
            f"⭐ Опыт: {stats['exp']}/{stats['level']*100}\n"
            f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"🗡️ Оружие: {WEAPONS.get(stats['weapon_id'], WEAPONS[1])['name']} +{stats['weapon_upgrade']}\n"
            f"🛡️ Броня: {ARMORS.get(stats['armor_id'], ARMORS[1])['name']} +{stats['armor_upgrade']}\n"
            f"💀 Побед: {stats['kills']} | Поражений: {stats['deaths']}\n\n"
            f"Выберите действие:",
            reply_markup=get_rpg_keyboard(),
            parse_mode="Markdown"
        )
    
    # БОССЫ
    elif data == "fight_boss":
        await callback.message.edit_text("⚔️ **Выберите босса:**", reply_markup=get_boss_keyboard(), parse_mode="Markdown")
    
    elif data.startswith("boss_"):
        boss_id = int(data.split("_")[1])
        success, result = await fight_boss(user_id, boss_id, callback.message)
        if "Победа" in result or "Поражение" in result:
            await callback.message.edit_text(result[:3000], reply_markup=get_rpg_keyboard(), parse_mode="Markdown")
        else:
            await callback.answer(result[:200], show_alert=True)
    
    # ПЕЩЕРА
    elif data == "cave":
        success, result = await go_to_cave(user_id, callback.message)
        await callback.answer(result[:200], show_alert=True)
        if success:
            stats = await get_player_stats(user_id)
            await callback.message.edit_text(
                f"⚔️ **RPG РАЗДЕЛ** ⚔️\n\n"
                f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n\n"
                f"Выберите действие:",
                reply_markup=get_rpg_keyboard(),
                parse_mode="Markdown"
            )
    
    # КУЗНЕЦ
    elif data == "forge":
        stats = await get_player_stats(user_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗡️ Улучшить оружие", callback_data="upgrade_weapon")],
            [InlineKeyboardButton(text="🛡️ Улучшить броню", callback_data="upgrade_armor")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")]
        ])
        await callback.message.edit_text(
            f"🔨 **Кузнец**\n\n"
            f"🗡️ Оружие: +{stats['weapon_upgrade']} (след. уровень: {100 * (2 ** stats['weapon_upgrade'])} 🪙)\n"
            f"🛡️ Броня: +{stats['armor_upgrade']} (след. уровень: {80 * (2 ** stats['armor_upgrade'])} 🪙)\n\n"
            f"Улучшение увеличивает атаку/защиту!",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    
    elif data == "upgrade_weapon":
        success, result = await upgrade_weapon(user_id)
        await callback.answer(result[:200], show_alert=True)
        if success:
            stats = await get_player_stats(user_id)
            await callback.message.edit_text(
                f"🔨 **Кузнец**\n\n"
                f"🗡️ Оружие: +{stats['weapon_upgrade']}\n"
                f"🛡️ Броня: +{stats['armor_upgrade']}\n\n"
                f"Выберите действие:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗡️ Улучшить оружие", callback_data="upgrade_weapon")],
                    [InlineKeyboardButton(text="🛡️ Улучшить броню", callback_data="upgrade_armor")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")]
                ]),
                parse_mode="Markdown"
            )
    
    elif data == "upgrade_armor":
        success, result = await upgrade_armor(user_id)
        await callback.answer(result[:200], show_alert=True)
        if success:
            stats = await get_player_stats(user_id)
            await callback.message.edit_text(
                f"🔨 **Кузнец**\n\n"
                f"🗡️ Оружие: +{stats['weapon_upgrade']}\n"
                f"🛡️ Броня: +{stats['armor_upgrade']}\n\n"
                f"Выберите действие:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗡️ Улучшить оружие", callback_data="upgrade_weapon")],
                    [InlineKeyboardButton(text="🛡️ Улучшить броню", callback_data="upgrade_armor")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")]
                ]),
                parse_mode="Markdown"
            )
    
    # МАГАЗИН
    elif data == "shop":
        await callback.message.edit_text("🏪 **Магазин**\n\nВыберите категорию:", reply_markup=get_shop_keyboard(), parse_mode="Markdown")
    
    elif data.startswith("buy_weapon_"):
        item_id = int(data.split("_")[2])
        item = WEAPONS[item_id]
        success, result = await buy_item(user_id, "weapon", item_id, item["price"])
        await callback.answer(result, show_alert=True)
    
    elif data.startswith("buy_armor_"):
        item_id = int(data.split("_")[2])
        item = ARMORS[item_id]
        success, result = await buy_item(user_id, "armor", item_id, item["price"])
        await callback.answer(result, show_alert=True)
    
    elif data.startswith("buy_potion_"):
        potion_id = data.split("_")[2]
        item = POTIONS[potion_id]
        success, result = await buy_item(user_id, "potion", potion_id, item["price"])
        await callback.answer(result, show_alert=True)
    
    # ИНВЕНТАРЬ
    elif data == "my_inventory":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT item_type, item_id, quantity FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
                items = await cursor.fetchall()
        
        if not items:
            text = "🎒 **Инвентарь пуст!**\n\nКупите предметы в магазине."
        else:
            text = "🎒 **Ваш инвентарь:**\n\n"
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
                elif item_type == "resource":
                    name = RESOURCES[item_id]["name"]
                    icon = RESOURCES[item_id]["icon"]
                else:
                    continue
                text += f"{icon} {name} x{qty}\n"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗡️ Экипировать оружие", callback_data="equip_weapon")],
            [InlineKeyboardButton(text="🛡️ Экипировать броню", callback_data="equip_armor")],
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
        success, result = await equip_item(user_id, "weapon", wid)
        await callback.answer(result, show_alert=True)
    
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
        success, result = await equip_item(user_id, "armor", aid)
        await callback.answer(result, show_alert=True)
    
    # ХАРАКТЕРИСТИКИ
    elif data == "my_stats_rpg":
        stats = await get_player_stats(user_id)
        user = await get_user(user_id)
        weapon = WEAPONS.get(stats["weapon_id"], WEAPONS[1])
        armor = ARMORS.get(stats["armor_id"], ARMORS[1])
        total_attack = 10 + stats["level"] + weapon["attack"] + (stats["weapon_upgrade"] * 5)
        total_defense = stats["level"] + armor["defense"] + (stats["armor_upgrade"] * 3)
        
        await callback.message.edit_text(
            f"📊 **Ваши характеристики:**\n\n"
            f"⭐ Уровень: {stats['level']}\n"
            f"📈 Опыт: {stats['exp']}/{stats['level']*100}\n"
            f"❤️ HP: {stats['hp']}/{stats['max_hp']}\n"
            f"🗡️ Атака: {total_attack} (база 10 + ур. {stats['level']} + оружие {weapon['attack']} + улучшение {stats['weapon_upgrade']*5})\n"
            f"🛡️ Защита: {total_defense} (ур. {stats['level']} + броня {armor['defense']} + улучшение {stats['armor_upgrade']*3})\n"
            f"💀 Побед над боссами: {stats['kills']}\n"
            f"⚰️ Поражений: {stats['deaths']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n\n"
            f"⚔️ **Снаряжение:**\n"
            f"• Оружие: {weapon['icon']} {weapon['name']} (+{weapon['attack']} атаки) +{stats['weapon_upgrade']}\n"
            f"• Броня: {armor['icon']} {armor['name']} (+{armor['defense']} защиты) +{stats['armor_upgrade']}",
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
        success, result = await use_potion(user_id, potion_id)
        await callback.answer(result, show_alert=True)
    
    # ЛУТБОКСЫ
    elif data == "lottery_box":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Обычный сундук (20 🪙)", callback_data="open_box_common")],
            [InlineKeyboardButton(text="🔵 Редкий сундук (100 🪙)", callback_data="open_box_rare")],
            [InlineKeyboardButton(text="🟣 Эпический сундук (500 🪙)", callback_data="open_box_epic")],
            [InlineKeyboardButton(text="🟠 Легендарный сундук (2000 🪙)", callback_data="open_box_legendary")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")]
        ])
        await callback.message.edit_text("🎁 **Лутбоксы**\n\nВыберите сундук:", reply_markup=kb, parse_mode="Markdown")
    
    elif data.startswith("open_box_"):
        box_type = data.split("_")[2]
        price = LOTTERY_BOXES[box_type]["price"]
        user = await get_user(user_id)
        
        if user["rpg_balance"] < price:
            await callback.answer(f"❌ Недостаточно {RPG_COIN_NAME}! Нужно {price}", show_alert=True)
            return
        
        # Рандомный предмет
        if box_type == "common":
            rarities = ["common", "common", "common", "rare", "rare", "epic"]
        elif box_type == "rare":
            rarities = ["common", "rare", "rare", "rare", "epic", "epic", "legendary"]
        elif box_type == "epic":
            rarities = ["rare", "rare", "epic", "epic", "epic", "legendary", "legendary"]
        else:
            rarities = ["epic", "epic", "legendary", "legendary", "legendary"]
        
        rarity = random.choice(rarities)
        
        if rarity == "common":
            items = [(1, WEAPONS[1]), (2, WEAPONS[2]), (1, ARMORS[1]), (2, ARMORS[2])]
            item_type, item = random.choice(items)
            if item_type == 1 or item_type == 2:
                item_type = "weapon"
            else:
                item_type = "armor"
        elif rarity == "rare":
            items = [(3, WEAPONS[3]), (4, WEAPONS[4]), (3, ARMORS[3])]
            item_type, item = random.choice(items)
            item_type = "weapon" if item_type in [3,4] else "armor"
        elif rarity == "epic":
            items = [(5, WEAPONS[5]), (6, WEAPONS[6]), (4, ARMORS[4])]
            item_type, item = random.choice(items)
            item_type = "weapon" if item_type in [5,6] else "armor"
        else:
            items = [(7, WEAPONS[7]), (5, ARMORS[5])]
            item_type, item = random.choice(items)
            item_type = "weapon" if item_type == 7 else "armor"
        
        await update_user(user_id, rpg_balance=user["rpg_balance"] - price)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, ?, ?, 1) ON CONFLICT DO UPDATE SET quantity = quantity + 1", (user_id, item_type, str(item_type == "weapon" and item or item_type == "armor" and item or "")))
            await db.commit()
        
        await callback.answer(f"🎁 Вы открыли {LOTTERY_BOXES[box_type]['name']} и получили {item['icon']} {item['name']}!", show_alert=True)
    
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
    
    # ПОПОЛНЕНИЕ
    elif data == "deposit":
        await callback.message.edit_text(
            f"💎 **Пополнение {COIN_NAME}**\n\n"
            f"💰 1 {COIN_NAME} = 0.8₽\n"
            f"⚡ Минимальная покупка: 10 {COIN_NAME} (8₽)\n\n"
            f"Способ оплаты: СБП\n"
            f"📱 Номер телефона: `{SBP_PHONE}`\n\n"
            f"После оплаты напишите /confirm_сумма",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # ПРЕМИУМ
    elif data == "premium":
        user = await get_user(user_id)
        if user.get("is_premium"):
            await callback.message.edit_text(
                f"👑 **У вас есть премиум!**\n\nАктивен до: {user['premium_until']}",
                reply_markup=get_back_keyboard(),
                parse_mode="Markdown"
            )
        else:
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
        user = await get_user(user_id)
        if user["pac_balance"] >= PREMIUM_PRICE_PAC:
            await update_user(user_id, 
                pac_balance=user["pac_balance"] - PREMIUM_PRICE_PAC,
                is_premium=1,
                premium_until=(datetime.now() + timedelta(days=30)).isoformat()
            )
            await add_transaction(user_id, "premium", -PREMIUM_PRICE_PAC, "Премиум подписка")
            await callback.answer("✅ Премиум активирован на 30 дней!", show_alert=True)
            await callback.message.edit_text("👑 **Премиум активирован!**", reply_markup=get_main_keyboard(), parse_mode="Markdown")
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
                f"⛏️ **Шахта**\n\n"
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
    
    elif data == "mine_upgrade":
        success, msg = await upgrade_mine(user_id)
        await callback.answer(msg, show_alert=True)
    
    # СТАТИСТИКА
    elif data == "stats":
        user = await get_user(user_id)
        stats = await get_player_stats(user_id)
        await callback.message.edit_text(
            f"📊 **Ваша статистика**\n\n"
            f"👤 ID: {user_id}\n"
            f"💎 {COIN_NAME}: {user['pac_balance']}\n"
            f"🪙 {RPG_COIN_NAME}: {user['rpg_balance']}\n"
            f"🎮 Игр: {user['total_games']}\n"
            f"🔄 Оборот: {user['turnover']} {COIN_NAME}\n"
            f"👥 Рефералов: {user['referrals']}\n"
            f"👑 Премиум: {'✅' if user['is_premium'] else '❌'}\n"
            f"⭐ Уровень: {stats['level']}\n"
            f"💀 Побед: {stats['kills']}\n"
            f"⚰️ Поражений: {stats['deaths']}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
    
    # ТОП-10
    elif data == "top":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id, username, kills FROM player_stats ORDER BY kills DESC LIMIT 10") as cursor:
                top_kills = await cursor.fetchall()
        text = "🏆 **ТОП-10 по убийствам боссов:**\n\n"
        for i, (uid, name, kills) in enumerate(top_kills, 1):
            text += f"{i}. {name or uid} — {kills} убийств\n"
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    # ЕЖЕДНЕВНЫЙ БОНУС
    elif data == "daily":
        success, msg = await claim_daily_bonus(user_id)
        await callback.answer(msg, show_alert=True)
        if success:
            user = await get_user(user_id)
            await callback.message.edit_text(
                f"🎮 **Главное меню**\n\n"
                f"💎 {COIN_NAME}: {user['pac_balance']}",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    
    # РЕФЕРАЛЫ
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
    
    # ВЫВОД
    elif data == "withdraw":
        await callback.answer("⏸️ Вывод временно недоступен.", show_alert=True)
    
    # ПОМОЩЬ
    elif data == "help":
        text = (
            "❓ **Помощь**\n\n"
            "🎮 **Казино:** 15 игр на выбор\n"
            "⚔️ **RPG режим:**\n"
            "• Сражайся с 10 боссами\n"
            "• Добывай ресурсы в пещерах\n"
            "• Улучшай оружие и броню у кузнеца\n"
            "• Покупай предметы в магазине\n"
            "• Открывай лутбоксы\n\n"
            "🔄 100 {RPG_COIN_NAME} = 1 {COIN_NAME}\n"
            "👑 Премиум даёт шахту и бонусы\n\n"
            "📞 По вопросам: @ZOJlOTOY"
        )
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
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
