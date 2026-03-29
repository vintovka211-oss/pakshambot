import random
import asyncio
from config import BOSSES, WEAPONS, ARMORS, POTIONS, RPG_COIN_NAME, RESOURCES
from database import get_user, update_user, add_transaction, get_player_stats, update_player_stats
import aiosqlite

async def fight_boss_start(user_id, boss_id, message):
    stats = await get_player_stats(user_id)
    user = await get_user(user_id)
    boss = BOSSES.get(boss_id)
    
    if not boss:
        return False, "❌ Босс не найден!"
    
    if stats["hp"] <= 0:
        await message.answer("❌ У вас недостаточно здоровья! Восстановитесь в магазине.", show_alert=True)
        return False, "dead"
    
    weapon = WEAPONS.get(stats["weapon_id"], WEAPONS[1])
    armor = ARMORS.get(stats["armor_id"], ARMORS[1])
    
    player_attack = 10 + stats["level"] + weapon["attack"] + (stats["weapon_upgrade"] * 5)
    boss_attack = boss["attack"]
    
    player_hp = stats["hp"]
    boss_hp = boss["hp"]
    
    # Сохраняем данные боя в state (временно)
    fight_data = {
        "boss_id": boss_id,
        "player_hp": player_hp,
        "boss_hp": boss_hp,
        "player_attack": player_attack,
        "boss_attack": boss_attack
    }
    
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
    boss_id = fight_data["boss_id"]
    player_hp = fight_data["player_hp"]
    boss_hp = fight_data["boss_hp"]
    player_attack = fight_data["player_attack"]
    boss_attack = fight_data["boss_attack"]
    
    boss = BOSSES.get(boss_id)
    
    # Игрок атакует
    boss_hp -= player_attack
    
    if boss_hp <= 0:
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
        resources_gained = {k: random.randint(1, 3) for k in RESOURCES.keys()}
        async with aiosqlite.connect("w1npaksham.db") as db:
            for res, qty in resources_gained.items():
                await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, 'resource', ?, ?) ON CONFLICT DO UPDATE SET quantity = quantity + ?", (user_id, res, qty, qty))
            await db.commit()
        
        resource_text = "\n".join([f"{RESOURCES[k]['icon']} {v} {RESOURCES[k]['name']}" for k, v in resources_gained.items()])
        
        await callback.message.edit_text(
            f"🎉 **Победа!**\n\n"
            f"Вы победили {boss['icon']} {boss['name']}!\n"
            f"🪙 Награда: +{rpg_reward} {RPG_COIN_NAME}\n"
            f"⭐ Опыт: +{exp_gain}\n"
            f"📈 Уровень: {new_level}\n"
            f"📦 Ресурсы:\n{resource_text}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return "win"
    
    # Босс атакует в ответ
    player_hp -= boss_attack
    
    if player_hp <= 0:
        # Поражение
        stats = await get_player_stats(user_id)
        await update_player_stats(user_id, hp=player_hp, deaths=stats["deaths"] + 1)
        await callback.message.edit_text(
            f"💀 **Поражение!**\n\n"
            f"{boss['icon']} {boss['name']} победил вас!\n"
            f"💔 У вас осталось {player_hp} HP",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return "lose"
    
    # Продолжаем бой
    fight_data["player_hp"] = player_hp
    fight_data["boss_hp"] = boss_hp
    
    from keyboards import get_fight_keyboard
    await callback.message.edit_text(
        f"⚔️ **Бой с {boss['name']}** ⚔️\n\n"
        f"❤️ Ваше HP: {player_hp}\n"
        f"💀 HP босса: {boss_hp}\n"
        f"🗡️ Ваша атака: {player_attack}\n"
        f"⚔️ Атака босса: {boss_attack}\n\n"
        f"Выберите действие:",
        reply_markup=get_fight_keyboard(fight_data),
        parse_mode="Markdown"
    )
    return "continue"

async def fight_heal(user_id, callback, fight_data):
    boss_id = fight_data["boss_id"]
    player_hp = fight_data["player_hp"]
    boss_hp = fight_data["boss_hp"]
    player_attack = fight_data["player_attack"]
    boss_attack = fight_data["boss_attack"]
    
    boss = BOSSES.get(boss_id)
    stats = await get_player_stats(user_id)
    
    # Проверяем наличие зелья
    async with aiosqlite.connect("w1npaksham.db") as db:
        async with db.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_type = 'potion' AND item_id = 'small'", (user_id,)) as cursor:
            result = await cursor.fetchone()
    
    if not result or result[0] <= 0:
        await callback.answer("❌ У вас нет зелий! Купите в магазине.", show_alert=True)
        return "no_potion"
    
    # Лечимся
    new_hp = min(player_hp + 20, stats["max_hp"])
    
    async with aiosqlite.connect("w1npaksham.db") as db:
        await db.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = 'potion' AND item_id = 'small'", (user_id,))
        await db.commit()
    
    fight_data["player_hp"] = new_hp
    
    from keyboards import get_fight_keyboard
    await callback.message.edit_text(
        f"⚔️ **Бой с {boss['name']}** ⚔️\n\n"
        f"❤️ Ваше HP: {new_hp}\n"
        f"💀 HP босса: {boss_hp}\n"
        f"🗡️ Ваша атака: {player_attack}\n"
        f"⚔️ Атака босса: {boss_attack}\n\n"
        f"Вы использовали зелье! +20 HP\n\n"
        f"Выберите действие:",
        reply_markup=get_fight_keyboard(fight_data),
        parse_mode="Markdown"
    )
    return "healed"

async def go_to_cave(user_id):
    stats = await get_player_stats(user_id)
    if stats["hp"] <= 0:
        return False, "❌ У вас недостаточно здоровья! Восстановитесь."
    
    resources_gained = {}
    for res in RESOURCES.keys():
        qty = random.randint(1, 5)
        resources_gained[res] = qty
    
    hp_cost = 10
    new_hp = stats["hp"] - hp_cost
    
    await update_player_stats(user_id, hp=new_hp)
    
    async with aiosqlite.connect("w1npaksham.db") as db:
        for res, qty in resources_gained.items():
            await db.execute("INSERT INTO inventory (user_id, item_type, item_id, quantity) VALUES (?, 'resource', ?, ?) ON CONFLICT DO UPDATE SET quantity = quantity + ?", (user_id, res, qty, qty))
        await db.commit()
    
    resource_text = "\n".join([f"{RESOURCES[k]['icon']} {v} {RESOURCES[k]['name']}" for k, v in resources_gained.items()])
    
    return True, f"⛏️ **Поход в пещеру**\n\nВы нашли:\n{resource_text}\n\n❤️ Здоровье: {stats['hp']} → {new_hp}/{stats['max_hp']}"

async def buy_item(user_id, item_type, item_id, price):
    user = await get_user(user_id)
    if user["rpg_balance"] < price:
        return False, f"❌ Недостаточно {RPG_COIN_NAME}!"
    
    await update_user(user_id, rpg_balance=user["rpg_balance"] - price)
    async with aiosqlite.connect("w1npaksham.db") as db:
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
    else:
        return False, "❌ Этот предмет нельзя экипировать!"

async def use_potion(user_id, potion_id):
    stats = await get_player_stats(user_id)
    if stats["hp"] >= stats["max_hp"]:
        return False, "❤️ У вас полное здоровье!"
    
    potion = POTIONS[potion_id]
    
    async with aiosqlite.connect("w1npaksham.db") as db:
        async with db.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_type = 'potion' AND item_id = ?", (user_id, potion_id)) as cursor:
            result = await cursor.fetchone()
            if not result or result[0] <= 0:
                return False, f"❌ У вас нет {potion['name']}!"
            await db.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_type = 'potion' AND item_id = ?", (user_id, potion_id))
            await db.commit()
    
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
