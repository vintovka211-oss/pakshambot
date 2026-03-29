import random
from config import BOSSES, WEAPONS, ARMORS, POTIONS, ARTIFACTS, RESOURCES, TOOLS, RPG_COIN_NAME, COIN_NAME
from database import get_user, update_user, add_transaction, get_player_stats, update_player_stats

async def fight_boss(user_id, boss_id, message):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    boss = BOSSES.get(boss_id)
    
    if not boss:
        return False, "❌ Босс не найден!"
    
    if stats["hp"] <= 0:
        return False, "❌ У вас недостаточно здоровья! Восстановитесь в магазине."
    
    weapon = WEAPONS.get(stats["weapon_id"], WEAPONS[1])
    armor = ARMORS.get(stats["armor_id"], ARMORS[1])
    
    player_attack = 10 + stats["level"] + weapon["attack"] + (stats["weapon_upgrade"] * 5)
    boss_attack = boss["attack"]
    
    player_hp = stats["hp"]
    boss_hp = boss["hp"]
    
    # Анимация боя
    fight_msg = await message.answer(f"⚔️ **Бой с {boss['name']}** ⚔️\n\n❤️ Ваше HP: {player_hp}\n💀 HP босса: {boss_hp}")
    
    while player_hp > 0 and boss_hp > 0:
        boss_hp -= player_attack
        if boss_hp <= 0:
            break
        player_hp -= boss_attack
        await fight_msg.edit_text(f"⚔️ **Бой с {boss['name']}** ⚔️\n\n❤️ Ваше HP: {player_hp}\n💀 HP босса: {max(0, boss_hp)}")
        await asyncio.sleep(0.5)
    
    if player_hp <= 0:
        await update_player_stats(user_id, hp=player_hp, deaths=stats["deaths"] + 1)
        return False, f"💀 **Поражение!**\n\n{boss['icon']} {boss['name']} победил вас!\n💔 У вас осталось {player_hp} HP"
    
    # Награда
    rpg_reward = boss["rpg_reward"]
    exp_gain = boss["exp"]
    
    # Шанс на артефакт
    artifact_reward = ""
    if random.randint(1, 100) <= boss["artifact_chance"]:
        artifact_id = boss["artifact_id"]
        artifact = ARTIFACTS[artifact_id]
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO artifacts (user_id, artifact_id) VALUES (?, ?)", (user_id, artifact_id))
            await db.commit()
        artifact_reward = f"\n🎁 Артефакт: {artifact['icon']} {artifact['name']}!"
    
    # Ресурсы
    resources_gained = {k: random.randint(1, 3) for k in RESOURCES.keys()}
    resource_text = "\n📦 Ресурсы: " + ", ".join([f"{RESOURCES[k]['icon']} {v}" for k, v in resources_gained.items()])
    
    new_rpg = user["rpg_balance"] + rpg_reward
    new_exp = stats["exp"] + exp_gain
    new_level = stats["level"]
    
    if new_exp >= new_level * 100:
        new_level += 1
        new_exp -= (new_level - 1) * 100
        await update_player_stats(user_id, hp=stats["max_hp"] + 10, max_hp=stats["max_hp"] + 10)
    
    await update_player_stats(user_id, exp=new_exp, level=new_level, hp=player_hp, kills=stats["kills"] + 1)
    await update_user(user_id, rpg_balance=new_rpg)
    await add_transaction(user_id, "boss_fight", rpg_reward, f"Победа над {boss['name']}")
    
    # Добавляем ресурсы в инвентарь
    async with aiosqlite.connect(DB_PATH) as db:
        for res, qty in resources_gained.items():
            await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, 'resource', ?, ?) ON CONFLICT DO UPDATE SET quantity = quantity + ?", (user_id, res, qty, qty))
        await db.commit()
    
    return True, f"🎉 **Победа!**\n\n{boss['icon']} {boss['name']} повержен!\n🪙 Награда: +{rpg_reward} {RPG_COIN_NAME}\n⭐ Опыт: +{exp_gain}\n📈 Уровень: {new_level}{artifact_reward}{resource_text}"

async def go_to_cave(user_id, message):
    stats = await get_player_stats(user_id)
    if stats["hp"] <= 0:
        return False, "❌ У вас недостаточно здоровья! Восстановитесь."
    
    tool = TOOLS.get(stats["tool_level"], TOOLS[1])
    resources_gained = {}
    
    for res, data in RESOURCES.items():
        qty = random.randint(1, tool["efficiency"])
        resources_gained[res] = qty
    
    hp_cost = 10
    new_hp = stats["hp"] - hp_cost
    
    await update_player_stats(user_id, hp=new_hp)
    
    async with aiosqlite.connect(DB_PATH) as db:
        for res, qty in resources_gained.items():
            await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, 'resource', ?, ?) ON CONFLICT DO UPDATE SET quantity = quantity + ?", (user_id, res, qty, qty))
        await db.commit()
    
    resource_text = "\n".join([f"{RESOURCES[k]['icon']} {v} {RESOURCES[k]['name']}" for k, v in resources_gained.items()])
    
    return True, f"⛏️ **Поход в пещеру**\n\nВы нашли:\n{resource_text}\n\n❤️ Здоровье: {stats['hp']} → {new_hp}/{stats['max_hp']}"

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
    await add_transaction(user_id, "upgrade", -cost, f"Улучшение оружия до +{current_upgrade + 1}")
    
    return True, f"✅ Оружие улучшено до +{current_upgrade + 1}!\n🗡️ Атака увеличена на 5"

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
    await add_transaction(user_id, "upgrade", -cost, f"Улучшение брони до +{current_upgrade + 1}")
    
    return True, f"✅ Броня улучшена до +{current_upgrade + 1}!\n🛡️ Защита увеличена на 3"

async def buy_item(user_id, item_type, item_id, price):
    user = await get_user(user_id)
    if user["rpg_balance"] < price:
        return False, f"❌ Недостаточно {RPG_COIN_NAME}!"
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - price)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, ?, ?, 1) ON CONFLICT DO UPDATE SET quantity = quantity + 1", (user_id, item_type, str(item_id)))
        await db.commit()
    await add_transaction(user_id, "shop", -price, f"Покупка {item_type} {item_id}")
    
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
            await db.execute("INSERT INTO artifacts (user_id, artifact_id) VALUES (?, ?)", (user_id, int(item_id)))
            await db.commit()
        return True, f"✨ Вы экипировали {ARTIFACTS[int(item_id)]['name']}!"
    else:
        return False, "❌ Этот предмет нельзя экипировать!"

async def use_potion(user_id, potion_id):
    stats = await get_player_stats(user_id)
    if stats["hp"] >= stats["max_hp"]:
        return False, "❤️ У вас полное здоровье!"
    
    potion = POTIONS[potion_id]
    
    # Проверяем наличие зелья в инвентаре
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
