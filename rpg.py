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

async def upgrade_tool(user_id):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    
    current_level = stats.get("tool_level", 1)
    if current_level >= len(TOOLS):
        return False, "🏆 У вас уже максимальный инструмент!"
    
    next_tool = TOOLS[current_level + 1]
    cost = next_tool["price"]
    
    if user["rpg_balance"] < cost:
        return False, f"❌ Недостаточно {RPG_COIN_NAME}! Нужно {cost}"
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - cost)
    await update_player_stats(user_id, tool_level=current_level + 1)
    await add_transaction(user_id, "tool_upgrade", -cost, f"Улучшение инструмента до {next_tool['name']}")
    return True, f"✅ Инструмент улучшен до {next_tool['name']}!"

# ==================== ДОБЫЧА В ПЕЩЕРЕ ====================
async def go_to_cave(user_id, cave_level, duration_minutes):
    stats = await get_player_stats(user_id)
    cave = CAVES.get(cave_level, CAVES[1])
    tool = await get_tool(user_id)
    
    if tool["level"] < cave["required_tool"]:
        required_tool = TOOLS[cave["required_tool"]]["name"]
        return False, f"❌ Для этой пещеры нужен {required_tool}! Ваш инструмент: {tool['name']}"
    
    if user_id in active_mining:
        return False, "⏳ Вы уже добываете ресурсы! Подождите окончания."
    
    task = asyncio.create_task(mine_in_background(user_id, cave_level, duration_minutes, tool["level"]))
    active_mining[user_id] = task
    
    return True, f"⛏️ **{cave['name']}**\n\nВы отправились добывать ресурсы!\n🔧 Инструмент: {tool['name']}\n⏱️ Время: {duration_minutes} минут\n\n💰 Ресурсы появятся в инвентаре через {duration_minutes} минут!"

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
            ore_data = ORES[ore]
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
async def sell_ore(user_id, ore_id, quantity):
    user = await get_user(user_id)
    ore = ORES.get(ore_id)
    
    if not ore:
        return False, "❌ Такой руды не существует!"
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_type = 'ore' AND item_id = ?", (user_id, ore_id)) as cursor:
            result = await cursor.fetchone()
            if not result or result[0] < quantity:
                return False, f"❌ У вас нет {quantity} {ore['name']}!"
            await db.execute("UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_type = 'ore' AND item_id = ?", (quantity, user_id, ore_id))
            await db.commit()
    
    total_value = ore["value"] * quantity
    await update_user(user_id, rpg_balance=user["rpg_balance"] + total_value)
    await add_transaction(user_id, "sell_ore", total_value, f"Продажа {quantity} {ore['name']}")
    
    return True, f"💰 Вы продали {quantity} {ore['icon']} {ore['name']} за {total_value} {RPG_COIN_NAME}!"

# ==================== БОЙ С БОССОМ ====================
async def fight_boss_start(user_id, boss_id, message):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    boss = BOSSES.get(boss_id)
    
    if not boss:
        return False, "❌ Босс не найден!"
    
    if stats["level"] < boss["min_level"]:
        return False, f"❌ Ваш уровень {stats['level']} слишком низкий! Нужно {boss['min_level']} уровень."
    
    if stats["hp"] <= 0:
        await message.answer("❌ У вас недостаточно здоровья! Восстановитесь в магазине.", show_alert=True)
        return False, "dead"
    
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
        "message_id": message.message_id
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
        reply_markup=get_fight_keyboard(fight_data),
        parse_mode="Markdown"
    )
    
    return True, fight_data

async def fight_attack(user_id, callback, fight_data):
    if user_id not in active_fights:
        await callback.answer("❌ Бой не найден! Начните новый бой.", show_alert=True)
        return "error"
    
    current_fight = active_fights[user_id]
    
    boss_id = current_fight["boss_id"]
    player_hp = current_fight["player_hp"]
    boss_hp = current_fight["boss_hp"]
    player_attack = current_fight["player_attack"]
    boss_attack = current_fight["boss_attack"]
    
    boss = BOSSES.get(boss_id)
    
    damage = player_attack + random.randint(-5, 5)
    boss_hp -= damage
    damage_text = f"🗡️ Вы нанесли {damage} урона!"
    
    if boss_hp <= 0:
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
        
        if user_id in active_fights:
            del active_fights[user_id]
        
        await callback.message.edit_text(
            f"🎉 **ПОБЕДА!** 🎉\n\n"
            f"Вы победили {boss['icon']} {boss['name']}!\n"
            f"🪙 Награда: +{rpg_reward} {RPG_COIN_NAME}\n"
            f"⭐ Опыт: +{exp_gain}\n"
            f"📈 Уровень: {new_level}{reward_text}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return "win"
    
    boss_damage = boss_attack + random.randint(-3, 3)
    player_hp -= boss_damage
    damage_text += f"\n⚔️ Босс нанёс {boss_damage} урона!"
    
    if player_hp <= 0:
        stats = await get_player_stats(user_id)
        await update_player_stats(user_id, hp=player_hp, deaths=stats["deaths"] + 1)
        
        if user_id in active_fights:
            del active_fights[user_id]
        
        await callback.message.edit_text(
            f"💀 **ПОРАЖЕНИЕ!** 💀\n\n"
            f"{boss['icon']} {boss['name']} победил вас!\n"
            f"💔 У вас осталось {player_hp} HP",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return "lose"
    
    current_fight["player_hp"] = player_hp
    current_fight["boss_hp"] = boss_hp
    
    from keyboards import get_fight_keyboard
    await callback.message.edit_text(
        f"⚔️ **Бой с {boss['name']}** ⚔️\n\n"
        f"❤️ Ваше HP: {player_hp}\n"
        f"💀 HP босса: {boss_hp}\n"
        f"🗡️ Ваша атака: {player_attack}\n"
        f"⚔️ Атака босса: {boss_attack}\n\n"
        f"{damage_text}\n\n"
        f"Выберите действие:",
        reply_markup=get_fight_keyboard(current_fight),
        parse_mode="Markdown"
    )
    return "continue"

async def fight_heal(user_id, callback, fight_data):
    if user_id not in active_fights:
        await callback.answer("❌ Бой не найден! Начните новый бой.", show_alert=True)
        return "error"
    
    current_fight = active_fights[user_id]
    
    boss_id = current_fight["boss_id"]
    player_hp = current_fight["player_hp"]
    boss_hp = current_fight["boss_hp"]
    player_attack = current_fight["player_attack"]
    boss_attack = current_fight["boss_attack"]
    
    boss = BOSSES.get(boss_id)
    stats = await get_player_stats(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_type = 'potion' AND item_id = 'small'", (user_id,)) as cursor:
            result = await cursor.fetchone()
    
    if not result or result[0] <= 0:
        await callback.answer("❌ У вас нет зелий! Купите в магазине.", show_alert=True)
        return "no_potion"
    
    heal_amount = 20 + random.randint(-5, 10)
    new_hp = min(player_hp + heal_amount, stats["max_hp"])
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = 'potion' AND item_id = 'small'", (user_id,))
        await db.commit()
    
    current_fight["player_hp"] = new_hp
    
    from keyboards import get_fight_keyboard
    await callback.message.edit_text(
        f"⚔️ **Бой с {boss['name']}** ⚔️\n\n"
        f"❤️ Ваше HP: {new_hp}\n"
        f"💀 HP босса: {boss_hp}\n"
        f"🗡️ Ваша атака: {player_attack}\n"
        f"⚔️ Атака босса: {boss_attack}\n\n"
        f"🧪 Вы использовали зелье! +{heal_amount} HP\n\n"
        f"Выберите действие:",
        reply_markup=get_fight_keyboard(current_fight),
        parse_mode="Markdown"
    )
    return "healed"

# ==================== МАГАЗИН, ИНВЕНТАРЬ, УЛУЧШЕНИЯ ====================
async def buy_item(user_id, item_type, item_id, price):
    user = await get_user(user_id)
    if user["rpg_balance"] < price:
        return False, f"❌ Недостаточно {RPG_COIN_NAME}!"
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - price)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, ?, ?, 1) ON CONFLICT DO UPDATE SET quantity = quantity + 1", (user_id, item_type, str(item_id)))
        await db.commit()
    await add_transaction(user_id, "shop", -price, f"Покупка")
    return True, f"✅ Предмет куплен!"

async def equip_item(user_id, item_type, item_id):
    if item_type == "weapon":
        await update_player_stats(user_id, weapon_id=int(item_id))
        return True, f"🗡️ Вы экипировали {WEAPONS[int(item_id)]['name']}!"
    elif item_type == "armor":
        await update_player_stats(user_id, armor_id=int(item_id))
        return True, f"🛡️ Вы экипировали {ARMORS[int(item_id)]['name']}!"
    elif item_type == "artifact":
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, 'artifact', ?, 1) ON CONFLICT DO UPDATE SET quantity = quantity + 1", (user_id, str(item_id)))
            await db.commit()
        return True, f"✨ Вы экипировали {ARTIFACTS[int(item_id)]['name']}!"
    else:
        return False, "❌ Этот предмет нельзя экипировать!"

async def use_potion(user_id, potion_id):
    stats = await get_player_stats(user_id)
    if stats["hp"] >= stats["max_hp"]:
        return False, "❤️ У вас полное здоровье!"
    
    potion = POTIONS[potion_id]
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_type = 'potion' AND item_id = ?", (user_id, potion_id)) as cursor:
            result = await cursor.fetchone()
            if not result or result[0] <= 0:
                return False, f"❌ У вас нет {potion['name']}!"
            await db.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = 'potion' AND item_id = ?", (user_id, potion_id))
            await db.commit()
    
    if potion["heal"] == "full":
        new_hp = stats["max_hp"]
    else:
        new_hp = min(stats["hp"] + potion["heal"], stats["max_hp"])
    
    await update_player_stats(user_id, hp=new_hp)
    await add_transaction(user_id, "potion", 0, f"Использовано {potion['name']}")
    
    return True, f"🍃 Вы использовали {potion['name']}!\n❤️ Здоровье: {stats['hp']} → {new_hp}/{stats['max_hp']}"

async def upgrade_weapon(user_id):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    
    current_upgrade = stats["weapon_upgrade"]
    if current_upgrade >= 10:
        return False, "❌ Оружие уже максимально улучшено (+10)!"
    
    cost = 100 * (2 ** current_upgrade)
    if user["rpg_balance"] < cost:
        return False, f"❌ Недостаточно {RPG_COIN_NAME}! Нужно {cost}"
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - cost)
    await update_player_stats(user_id, weapon_upgrade=current_upgrade + 1)
    await add_transaction(user_id, "upgrade", -cost, f"Улучшение оружия")
    return True, f"✅ Оружие улучшено до +{current_upgrade + 1}!"

async def upgrade_armor(user_id):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    
    current_upgrade = stats["armor_upgrade"]
    if current_upgrade >= 10:
        return False, "❌ Броня уже максимально улучшена (+10)!"
    
    cost = 80 * (2 ** current_upgrade)
    if user["rpg_balance"] < cost:
        return False, f"❌ Недостаточно {RPG_COIN_NAME}! Нужно {cost}"
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - cost)
    await update_player_stats(user_id, armor_upgrade=current_upgrade + 1)
    await add_transaction(user_id, "upgrade", -cost, f"Улучшение брони")
    return True, f"✅ Броня улучшена до +{current_upgrade + 1}!"
