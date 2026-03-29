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
from pvp import *
from clans import *

# ==================== СОСТОЯНИЯ ====================
class AdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()
    waiting_days = State()

class GameStates(StatesGroup):
    waiting_bet = State()

class PvPStates(StatesGroup):
    waiting_opponent = State()
    waiting_bet = State()

class ClanStates(StatesGroup):
    waiting_name = State()
    waiting_invite = State()

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
    
    # RPG МЕНЮ
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
            [InlineKeyboardButton(text="🔧 Починить предметы", callback_data="repair_items")],
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
    
    elif data == "equip_artifact":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT artifact_id FROM artifacts WHERE user_id = ?", (user_id,)) as cursor:
                artifacts = await cursor.fetchall()
        
        if not artifacts:
            await callback.answer("❌ У вас нет артефактов!", show_alert=True)
            return
        
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        for a in artifacts:
            aid = a[0]
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"{ARTIFACTS[aid]['icon']} {ARTIFACTS[aid]['name']}", callback_data=f"equip_artifact_{aid}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="my_inventory")])
        await callback.message.edit_text("✨ **Выберите артефакт для экипировки:**", reply_markup=kb, parse_mode="Markdown")
    
    elif data.startswith("equip_artifact_"):
        aid = int(data.split("_")[2])
        success, result = await equip_item(user_id, "artifact", aid)
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
    
    # ИГРЫ (КАЗИНО) - обрабатываются отдельно
    elif data == "games":
        await callback.message.edit_text("🎮 **Выберите игру (15 игр):**", reply_markup=get_games_keyboard(), parse_mode="Markdown")
    
    # Обработчики игр (слоты, кубик, рулетка и т.д.) добавляются по аналогии с предыдущими версиями
    
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
            "• Открывай лутбоксы\n"
            "• Создавай клан и сражайся в PvP\n\n"
            "🔄 100 {RPG_COIN_NAME} = 1 {COIN_NAME}\n"
            "👑 Премиум даёт шахту и бонусы\n\n"
            "📞 По вопросам: @ZOJlOTOY"
        )
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data == "top":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id, username, kills FROM player_stats ORDER BY kills DESC LIMIT 10") as cursor:
                top_kills = await cursor.fetchall()
        text = "🏆 **ТОП-10 по убийствам боссов:**\n\n"
        for i, (uid, name, kills) in enumerate(top_kills, 1):
            text += f"{i}. {name or uid} — {kills} убийств\n"
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    await callback.answer()
