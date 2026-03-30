import random
import asyncio
import aiosqlite
from config import BOSSES, WEAPONS, ARMORS, POTIONS, ARTIFACTS, ORES, CAVES, TOOLS, EVENTS, RPG_COIN_NAME
from database import get_user, update_user, add_transaction, get_player_stats, update_player_stats, DB_PATH

active_fights = {}
active_mining = {}

# ==================== ИНСТРУМЕНТЫ ====================
async def get_tool(user_id):
    stats = await get_player_stats(user_id)
    tool_level = stats.get("tool_level", 1)
    return TOOLS.get(tool_level, TOOLS[1])

async def upgrade_tool(user_id, message):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    
    current_level = stats.get("tool_level", 1)
    if current_level >= len(TOOLS):
        await message.edit_text("🏆 У вас уже максимальный инструмент!", reply_markup=get_back_keyboard())
        return False
    
    next_tool = TOOLS[current_level + 1]
    cost = next_tool["price"]
    
    if user["rpg_balance"] < cost:
        await message.edit_text(f"❌ Недостаточно {RPG_COIN_NAME}! Нужно {cost}", reply_markup=get_back_keyboard())
        return False
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - cost)
    await update_player_stats(user_id, tool_level=current_level + 1)
    await add_transaction(user_id, "tool_upgrade", -cost, f"Улучшение инструмента до {next_tool['name']}")
    await message.edit_text(f"✅ Инструмент улучшен до {next_tool['name']}!", reply_markup=get_back_keyboard())
    return True

# ==================== ДОБЫЧА В ПЕЩЕРЕ ====================
async def go_to_cave(user_id, cave_level, duration_minutes, message):
    stats = await get_player_stats(user_id)
    cave = CAVES.get(cave_level, CAVES[1])
    tool = await get_tool(user_id)
    
    if tool["level"] < cave["required_tool"]:
        required_tool = TOOLS[cave["required_tool"]]["name"]
        await message.edit_text(f"❌ Для этой пещеры нужен {required_tool}! Ваш инструмент: {tool['name']}", reply_markup=get_back_keyboard())
        return False
    
    if user_id in active_mining:
        await message.edit_text("⏳ Вы уже добываете ресурсы! Подождите окончания.", reply_markup=get_back_keyboard())
        return False
    
    task = asyncio.create_task(mine_in_background(user_id, cave_level, duration_minutes, tool["level"]))
    active_mining[user_id] = task
    
    await message.edit_text(
        f"⛏️ **{cave['name']}**\n\nВы отправились добывать ресурсы!\n🔧 Инструмент: {tool['name']}\n⏱️ Время: {duration_minutes} минут\n\n💰 Ресурсы появятся в инвентаре через {duration_minutes} минут!",
        reply_markup=get_back_keyboard()
    )
    return True

async def mine_in_background(user_id, cave_level, duration_minutes, tool_level):
    await asyncio.sleep(duration_minutes * 60)
    
    cave = CAVES.get(cave_level, CAVES[1])
    resource_tiers = cave["tiers"]
    tool = TOOLS.get(tool_level, TOOLS[1])
    resources_gained = {}
    
    available_ores = [ore for ore_id, ore in ORES.items() if ore["tier"] in tool["can_mine"] and ore["tier"] in resource_tiers]
    
    for _ in range(random.randint(cave["min_resources"], cave["max_resources"])):
        if available_ores:
            ore = random.choice(available_ores)
            qty = random.randint(1, 3)
            resources_gained[ore] = resources_gained.get(ore, 0) + qty
    
    async with aiosqlite.connect(DB_PATH) as db:
        for res, qty in resources_gained.items():
            await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, 'ore', ?, ?) ON CONFLICT DO UPDATE SET quantity = quantity + ?", (user_id, res, qty, qty))
        await db.commit()
    
    resource_text = "\n".join([f"{ORES[r]['icon']} {q} {ORES[r]['name']}" for r, q in resources_gained.items()]) if resources_gained else "Ничего не найдено..."
    
    from bot import bot
    await bot.send_message(user_id, f"⛏️ **Добыча ресурсов завершена!**\n\nВы нашли:\n{resource_text}", parse_mode="Markdown")
    
    if user_id in active_mining:
        del active_mining[user_id]

# ==================== ПРОДАЖА РУДЫ ====================
async def sell_ore(user_id, ore_id, quantity, message):
    user = await get_user(user_id)
    ore = ORES.get(ore_id)
    
    if not ore:
        await message.edit_text("❌ Такой руды не существует!", reply_markup=get_back_keyboard())
        return False
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_type = 'ore' AND item_id = ?", (user_id, ore_id)) as cursor:
            result = await cursor.fetchone()
            if not result or result[0] < quantity:
                await message.edit_text(f"❌ У вас нет {quantity} {ore['name']}!", reply_markup=get_back_keyboard())
                return False
            await db.execute("UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_type = 'ore' AND item_id = ?", (quantity, user_id, ore_id))
            await db.commit()
    
    total_value = ore["value"] * quantity
    await update_user(user_id, rpg_balance=user["rpg_balance"] + total_value)
    await add_transaction(user_id, "sell_ore", total_value, f"Продажа {quantity} {ore['name']}")
    
    await message.edit_text(f"💰 Вы продали {quantity} {ore['icon']} {ore['name']} за {total_value} {RPG_COIN_NAME}!", reply_markup=get_back_keyboard())
    return True

# ==================== БОЙ С БОССОМ (ИСПРАВЛЕННАЯ ВЕРСИЯ) ====================
async def fight_boss_start(user_id, boss_id, message):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    boss = BOSSES.get(boss_id)
    
    if not boss:
        await message.edit_text("❌ Босс не найден!", reply_markup=get_back_keyboard())
        return False
    
    if stats["level"] < boss["min_level"]:
        await message.edit_text(f"❌ Ваш уровень {stats['level']} слишком низкий! Нужно {boss['min_level']} уровень.", reply_markup=get_back_keyboard())
        return False
    
    if stats["hp"] <= 0:
        await message.edit_text("❌ У вас недостаточно здоровья! Восстановитесь в магазине.", reply_markup=get_back_keyboard())
        return False
    
    weapon = WEAPONS.get(stats["weapon_id"], WEAPONS[1])
    armor = ARMORS.get(stats["armor_id"], ARMORS[1])
    
    player_attack = 10 + stats["level"] + weapon["attack"] + (stats["weapon_upgrade"] * 5)
    boss_attack = boss["attack"]
    
    player_hp = stats["hp"]
    boss_hp = boss["hp"]
    
    fight_data = {
        "boss_id": boss_id,
        "player_hp": player_hp,
        "boss_hp": boss_hp,
        "player_attack": player_attack,
        "boss_attack": boss_attack,
        "message_id": message.message_id,
        "last_update": datetime.now().isoformat()
    }
    
    active_fights[user_id] = fight_data
    
    from keyboards import get_fight_keyboard
    await message.edit_text(
        f"⚔️ **Бой с {boss['name']}** ⚔️\n\n"
        f"❤️ Ваше HP: {player_hp}\n"
        f"💀 HP босса: {boss_hp}\n"
        f"🗡️ Ваша атака: {player_attack}\n"
        f"⚔️ Атака босса: {boss_attack}\n\n"
        f"Выберите действие:",
        reply_markup=get_fight_keyboard(user_id),
        parse_mode="Markdown"
    )
    return True

async def fight_attack(user_id, callback, message):
    # Проверяем, есть ли активный бой
    if user_id not in active_fights:
        await message.edit_text("❌ Бой не найден! Начните новый бой.", reply_markup=get_back_keyboard())
        return "error"
    
    # Получаем текущие данные боя
    current_fight = active_fights[user_id]
    boss_id = current_fight["boss_id"]
    player_hp = current_fight["player_hp"]
    boss_hp = current_fight["boss_hp"]
    player_attack = current_fight["player_attack"]
    boss_attack = current_fight["boss_attack"]
    
    boss = BOSSES.get(boss_id)
    
    # Игрок атакует
    damage = player_attack + random.randint(-5, 5)
    new_boss_hp = boss_hp - damage
    damage_text = f"🗡️ Вы нанесли {damage} урона!"
    
    # Обновляем данные боя
    current_fight["boss_hp"] = new_boss_hp
    current_fight["last_update"] = datetime.now().isoformat()
    active_fights[user_id] = current_fight
    
    # Проверяем, победили ли босса
    if new_boss_hp <= 0:
        # Победа!
        rpg_reward = boss["rpg_reward"]
        exp_gain = boss["exp"]
        
        stats = await get_player_stats(user_id)
        user = await get_user(user_id)
        
        new_rpg = user["rpg_balance"] + rpg_reward
        new_exp = stats["exp"] + exp_gain
        new_level = stats["level"]
        
        if new_exp >= new_level * 100:
            new_level += 1
            new_exp -= (new_level - 1) * 100
            await update_player_stats(user_id, hp=stats["max_hp"] + 10, max_hp=stats["max_hp"] + 10)
        
        await update_player_stats(user_id, exp=new_exp, level=new_level, kills=stats["kills"] + 1)
        await update_user(user_id, rpg_balance=new_rpg)
        await add_transaction(user_id, "boss_fight", rpg_reward, f"Победа над {boss['name']}")
        
        # Ресурсы
        reward_text = ""
        resource_rewards = []
        for res_name, res_data in ORES.items():
            if random.random() < 0.7:
                qty = random.randint(1, 3)
                resource_rewards.append((res_name, qty))
        
        async with aiosqlite.connect(DB_PATH) as db:
            for res_name, qty in resource_rewards:
                await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, 'ore', ?, ?) ON CONFLICT DO UPDATE SET quantity = quantity + ?", (user_id, res_name, qty, qty))
            await db.commit()
        
        if resource_rewards:
            reward_text += "\n📦 **Ресурсы:**\n" + "\n".join([f"{ORES[r]['icon']} {q} {ORES[r]['name']}" for r, q in resource_rewards])
        
        # Артефакт
        artifact_chance = {"common": 10, "rare": 20, "epic": 30, "legendary": 40, "mythic": 50, "legend": 60, "god": 70}
        chance = artifact_chance.get(boss["tier"], 10)
        
        if random.randint(1, 100) <= chance:
            available_artifacts = [a for a in ARTIFACTS.values() if a["tier"] == boss["tier"] or 
                                   (boss["tier"] in ["god", "legend"] and a["tier"] in ["legend", "god"])]
            if available_artifacts:
                artifact = random.choice(available_artifacts)
                artifact_id = [aid for aid, a in ARTIFACTS.items() if a["name"] == artifact["name"]][0]
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, 'artifact', ?, 1) ON CONFLICT DO UPDATE SET quantity = quantity + 1", (user_id, str(artifact_id)))
                    await db.commit()
                reward_text += f"\n🎁 **Артефакт:** {artifact['icon']} {artifact['name']}!"
        
        # Удаляем бой из активных
        if user_id in active_fights:
            del active_fights[user_id]
        
        await message.edit_text(
            f"🎉 **ПОБЕДА!** 🎉\n\n"
            f"Вы победили {boss['icon']} {boss['name']}!\n"
            f"🪙 Награда: +{rpg_reward} {RPG_COIN_NAME}\n"
            f"⭐ Опыт: +{exp_gain}\n"
            f"📈 Уровень: {new_level}{reward_text}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return "win"
    
    # Босс атакует в ответ
    boss_damage = boss_attack + random.randint(-3, 3)
    new_player_hp = player_hp - boss_damage
    damage_text += f"\n⚔️ Босс нанёс {boss_damage} урона!"
    
    # Обновляем HP игрока
    current_fight["player_hp"] = new_player_hp
    active_fights[user_id] = current_fight
    
    # Проверяем, не умер ли игрок
    if new_player_hp <= 0:
        stats = await get_player_stats(user_id)
        await update_player_stats(user_id, hp=new_player_hp, deaths=stats["deaths"] + 1)
        
        if user_id in active_fights:
            del active_fights[user_id]
        
        await message.edit_text(
            f"💀 **ПОРАЖЕНИЕ!** 💀\n\n"
            f"{boss['icon']} {boss['name']} победил вас!\n"
            f"💔 У вас осталось {new_player_hp} HP",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return "lose"
    
    # Продолжаем бой
    from keyboards import get_fight_keyboard
    await message.edit_text(
        f"⚔️ **Бой с {boss['name']}** ⚔️\n\n"
        f"❤️ Ваше HP: {new_player_hp}\n"
        f"💀 HP босса: {new_boss_hp}\n"
        f"🗡️ Ваша атака: {player_attack}\n"
        f"⚔️ Атака босса: {boss_attack}\n\n"
        f"{damage_text}\n\n"
        f"Выберите действие:",
        reply_markup=get_fight_keyboard(user_id),
        parse_mode="Markdown"
    )
    return "continue"

async def fight_heal(user_id, callback, message):
    # Проверяем, есть ли активный бой
    if user_id not in active_fights:
        await message.edit_text("❌ Бой не найден! Начните новый бой.", reply_markup=get_back_keyboard())
        return "error"
    
    current_fight = active_fights[user_id]
    boss_id = current_fight["boss_id"]
    player_hp = current_fight["player_hp"]
    boss_hp = current_fight["boss_hp"]
    player_attack = current_fight["player_attack"]
    boss_attack = current_fight["boss_attack"]
    
    boss = BOSSES.get(boss_id)
    stats = await get_player_stats(user_id)
    
    # Проверяем наличие зелья
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_type = 'potion' AND item_id = 'small'", (user_id,)) as cursor:
            result = await cursor.fetchone()
    
    if not result or result[0] <= 0:
        await message.edit_text("❌ У вас нет зелий! Купите в магазине.", reply_markup=get_back_keyboard())
        return "no_potion"
    
    # Лечимся
    heal_amount = 20 + random.randint(-5, 10)
    new_hp = min(player_hp + heal_amount, stats["max_hp"])
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = 'potion' AND item_id = 'small'", (user_id,))
        await db.commit()
    
    # Обновляем данные боя
    current_fight["player_hp"] = new_hp
    active_fights[user_id] = current_fight
    
    from keyboards import get_fight_keyboard
    await message.edit_text(
        f"⚔️ **Бой с {boss['name']}** ⚔️\n\n"
        f"❤️ Ваше HP: {new_hp}\n"
        f"💀 HP босса: {boss_hp}\n"
        f"🗡️ Ваша атака: {player_attack}\n"
        f"⚔️ Атака босса: {boss_attack}\n\n"
        f"🧪 Вы использовали зелье! +{heal_amount} HP\n\n"
        f"Выберите действие:",
        reply_markup=get_fight_keyboard(user_id),
        parse_mode="Markdown"
    )
    return "healed"

# ==================== МАГАЗИН, ИНВЕНТАРЬ, УЛУЧШЕНИЯ ====================
async def buy_item(user_id, item_type, item_id, price, message):
    user = await get_user(user_id)
    if user["rpg_balance"] < price:
        await message.edit_text(f"❌ Недостаточно {RPG_COIN_NAME}!", reply_markup=get_back_keyboard())
        return False
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - price)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, ?, ?, 1) ON CONFLICT DO UPDATE SET quantity = quantity + 1", (user_id, item_type, str(item_id)))
        await db.commit()
    await add_transaction(user_id, "shop", -price, f"Покупка")
    await message.edit_text(f"✅ Предмет куплен!", reply_markup=get_back_keyboard())
    return True

async def equip_item(user_id, item_type, item_id, message):
    if item_type == "weapon":
        await update_player_stats(user_id, weapon_id=int(item_id))
        await message.edit_text(f"🗡️ Вы экипировали {WEAPONS[int(item_id)]['name']}!", reply_markup=get_back_keyboard())
        return True
    elif item_type == "armor":
        await update_player_stats(user_id, armor_id=int(item_id))
        await message.edit_text(f"🛡️ Вы экипировали {ARMORS[int(item_id)]['name']}!", reply_markup=get_back_keyboard())
        return True
    elif item_type == "artifact":
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, 'artifact', ?, 1) ON CONFLICT DO UPDATE SET quantity = quantity + 1", (user_id, str(item_id)))
            await db.commit()
        await message.edit_text(f"✨ Вы экипировали {ARTIFACTS[int(item_id)]['name']}!", reply_markup=get_back_keyboard())
        return True
    else:
        await message.edit_text("❌ Этот предмет нельзя экипировать!", reply_markup=get_back_keyboard())
        return False

async def use_potion(user_id, potion_id, message):
    stats = await get_player_stats(user_id)
    if stats["hp"] >= stats["max_hp"]:
        await message.edit_text("❤️ У вас полное здоровье!", reply_markup=get_back_keyboard())
        return False
    
    potion = POTIONS[potion_id]
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_type = 'potion' AND item_id = ?", (user_id, potion_id)) as cursor:
            result = await cursor.fetchone()
            if not result or result[0] <= 0:
                await message.edit_text(f"❌ У вас нет {potion['name']}!", reply_markup=get_back_keyboard())
                return False
            await db.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = 'potion' AND item_id = ?", (user_id, potion_id))
            await db.commit()
    
    if potion["heal"] == "full":
        new_hp = stats["max_hp"]
    else:
        new_hp = min(stats["hp"] + potion["heal"], stats["max_hp"])
    
    await update_player_stats(user_id, hp=new_hp)
    await add_transaction(user_id, "potion", 0, f"Использовано {potion['name']}")
    
    await message.edit_text(f"🍃 Вы использовали {potion['name']}!\n❤️ Здоровье: {stats['hp']} → {new_hp}/{stats['max_hp']}", reply_markup=get_back_keyboard())
    return True

async def upgrade_weapon(user_id, message):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    
    current_upgrade = stats["weapon_upgrade"]
    if current_upgrade >= 10:
        await message.edit_text("❌ Оружие уже максимально улучшено (+10)!", reply_markup=get_back_keyboard())
        return False
    
    cost = 100 * (2 ** current_upgrade)
    if user["rpg_balance"] < cost:
        await message.edit_text(f"❌ Недостаточно {RPG_COIN_NAME}! Нужно {cost}", reply_markup=get_back_keyboard())
        return False
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - cost)
    await update_player_stats(user_id, weapon_upgrade=current_upgrade + 1)
    await add_transaction(user_id, "upgrade", -cost, f"Улучшение оружия")
    await message.edit_text(f"✅ Оружие улучшено до +{current_upgrade + 1}!", reply_markup=get_back_keyboard())
    return True

async def upgrade_armor(user_id, message):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    
    current_upgrade = stats["armor_upgrade"]
    if current_upgrade >= 10:
        await message.edit_text("❌ Броня уже максимально улучшена (+10)!", reply_markup=get_back_keyboard())
        return False
    
    cost = 80 * (2 ** current_upgrade)
    if user["rpg_balance"] < cost:
        await message.edit_text(f"❌ Недостаточно {RPG_COIN_NAME}! Нужно {cost}", reply_markup=get_back_keyboard())
        return False
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - cost)
    await update_player_stats(user_id, armor_upgrade=current_upgrade + 1)
    await add_transaction(user_id, "upgrade", -cost, f"Улучшение брони")
    await message.edit_text(f"✅ Броня улучшена до +{current_upgrade + 1}!", reply_markup=get_back_keyboard())
    return True
