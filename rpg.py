import random
import aiosqlite
from datetime import datetime
from config import CLAN_CREATE_PRICE, CLAN_MAX_MEMBERS, CLAN_LEVELS, CLAN_BOSSES, RPG_COIN_NAME, WEAPONS
from database import get_user, update_user, add_transaction, get_player_stats, DB_PATH

async def get_clan(clan_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM clans WHERE id = ?", (clan_id,)) as cursor:
            clan = await cursor.fetchone()
            if not clan:
                return None
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, clan))

async def get_user_clan(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT clan_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if not result or not result[0]:
                return None
            return await get_clan(result[0])

async def create_clan(user_id, clan_name):
    user = await get_user(user_id)
    
    if user["rpg_balance"] < CLAN_CREATE_PRICE:
        return False, f"❌ Недостаточно {RPG_COIN_NAME}! Нужно {CLAN_CREATE_PRICE}"
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT clan_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if await cursor.fetchone():
                return False, "❌ Вы уже состоите в клане!"
        
        try:
            cursor = await db.execute("INSERT INTO clans (name, leader_id, members) VALUES (?, ?, ?)", (clan_name, user_id, f'[{user_id}]'))
            await db.commit()
            clan_id = cursor.lastrowid
            
            await db.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan_id, user_id))
            await db.commit()
            
            await update_user(user_id, rpg_balance=user["rpg_balance"] - CLAN_CREATE_PRICE)
            await add_transaction(user_id, "clan_create", -CLAN_CREATE_PRICE, f"Создание клана {clan_name}")
            
            return True, f"✅ Клан **{clan_name}** успешно создан!"
        except:
            return False, "❌ Клан с таким названием уже существует!"

async def join_clan(user_id, clan_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT clan_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if await cursor.fetchone():
                return False, "❌ Вы уже состоите в клане!"
        
        clan = await get_clan(clan_id)
        if not clan:
            return False, "❌ Клан не найден!"
        
        members = eval(clan["members"])
        if len(members) >= CLAN_MAX_MEMBERS:
            return False, "❌ Клан переполнен!"
        
        members.append(user_id)
        await db.execute("UPDATE clans SET members = ? WHERE id = ?", (str(members), clan_id))
        await db.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan_id, user_id))
        await db.commit()
        
        return True, f"✅ Вы вступили в клан **{clan['name']}**!"

async def leave_clan(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        clan = await get_user_clan(user_id)
        if not clan:
            return False, "❌ Вы не состоите в клане!"
        
        members = eval(clan["members"])
        if clan["leader_id"] == user_id:
            return False, "❌ Лидер не может покинуть клан! Передайте лидерство или распустите клан."
        
        members.remove(user_id)
        await db.execute("UPDATE clans SET members = ? WHERE id = ?", (str(members), clan["id"]))
        await db.execute("UPDATE users SET clan_id = NULL WHERE user_id = ?", (user_id,))
        await db.commit()
        
        return True, f"✅ Вы покинули клан **{clan['name']}**!"

async def disband_clan(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        clan = await get_user_clan(user_id)
        if not clan:
            return False, "❌ Вы не состоите в клане!"
        
        if clan["leader_id"] != user_id:
            return False, "❌ Только лидер может распустить клан!"
        
        members = eval(clan["members"])
        for member in members:
            await db.execute("UPDATE users SET clan_id = NULL WHERE user_id = ?", (member,))
        
        await db.execute("DELETE FROM clans WHERE id = ?", (clan["id"],))
        await db.commit()
        
        return True, f"✅ Клан **{clan['name']}** распущен!"

async def start_clan_boss(clan_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM clan_boss_fights WHERE clan_id = ?", (clan_id,)) as cursor:
            if await cursor.fetchone():
                return False, "❌ Клановый босс уже активен!"
        
        clan = await get_clan(clan_id)
        if not clan:
            return False, "❌ Клан не найден!"
        
        level = clan["level"]
        boss = CLAN_BOSSES.get(level, CLAN_BOSSES[1])
        
        await db.execute("INSERT INTO clan_boss_fights (clan_id, boss_id, current_hp, started_at) VALUES (?, ?, ?, ?)", 
                         (clan_id, level, boss["hp"], datetime.now().isoformat()))
        await db.commit()
        
        return True, f"⚔️ **Клановый босс {boss['icon']} {boss['name']} появился!**\n\nHP: {boss['hp']}\nНаграда: {boss['reward']} {RPG_COIN_NAME}"

async def attack_clan_boss(user_id, clan_id):
    user = await get_user(user_id)
    stats = await get_player_stats(user_id)
    clan = await get_clan(clan_id)
    
    if not clan:
        return False, "❌ Клан не найден!"
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM clan_boss_fights WHERE clan_id = ?", (clan_id,)) as cursor:
            fight = await cursor.fetchone()
            if not fight:
                return False, "❌ Нет активного кланового босса!"
        
        fight_id, cid, boss_id, current_hp, started_at, last_hit = fight
        boss = CLAN_BOSSES.get(boss_id, CLAN_BOSSES[1])
        
        weapon = WEAPONS.get(stats["weapon_id"], WEAPONS[1])
        damage = 10 + stats["level"] + weapon["attack"] + random.randint(1, 20)
        
        new_hp = current_hp - damage
        
        await db.execute("UPDATE clan_boss_fights SET current_hp = ?, last_hit = ? WHERE id = ?", (new_hp, datetime.now().isoformat(), fight_id))
        
        if new_hp <= 0:
            await db.execute("DELETE FROM clan_boss_fights WHERE id = ?", (fight_id,))
            
            members = eval(clan["members"])
            reward_per_member = boss["reward"] // len(members)
            
            for member in members:
                member_user = await get_user(member)
                await update_user(member, rpg_balance=member_user["rpg_balance"] + reward_per_member)
                await add_transaction(member, "clan_boss_reward", reward_per_member, f"Награда за победу над клановым боссом")
            
            new_exp = clan["exp"] + boss["reward"] * 10
            await update_clan_exp(clan_id, new_exp)
            
            return True, f"🎉 **Клановый босс побеждён!** 🎉\n\nКаждый участник получил +{reward_per_member} {RPG_COIN_NAME}!"
        
        return True, f"⚔️ **Бой с {boss['name']}** ⚔️\n\n💥 Вы нанесли {damage} урона!\n💀 HP босса: {new_hp}/{boss['hp']}"

async def update_clan_exp(clan_id, new_exp):
    async with aiosqlite.connect(DB_PATH) as db:
        clan = await get_clan(clan_id)
        current_level = clan["level"]
        next_level_data = CLAN_LEVELS.get(current_level + 1)
        
        if next_level_data and new_exp >= next_level_data["exp_needed"]:
            await db.execute("UPDATE clans SET level = ?, exp = ? WHERE id = ?", (current_level + 1, new_exp, clan_id))
            return True, f"🎉 **Клан повысил уровень!** 🎉\n\nТеперь {next_level_data['name']}!"
        else:
            await db.execute("UPDATE clans SET exp = ? WHERE id = ?", (new_exp, clan_id))
            return False, ""

async def get_clan_info(clan_id):
    clan = await get_clan(clan_id)
    if not clan:
        return None
    
    members = eval(clan["members"])
    level_data = CLAN_LEVELS.get(clan["level"], CLAN_LEVELS[1])
    next_level = CLAN_LEVELS.get(clan["level"] + 1)
    
    text = (
        f"🏰 **{clan['name']}** {level_data['icon']}\n\n"
        f"📊 Уровень: {clan['level']}\n"
        f"⭐ Опыт: {clan['exp']}/{next_level['exp_needed'] if next_level else 'MAX'}\n"
        f"👥 Участников: {len(members)}/{CLAN_MAX_MEMBERS}\n"
        f"👑 Лидер: {clan['leader_id']}\n"
        f"💰 Казна: {clan['balance']} {RPG_COIN_NAME}\n"
        f"✨ Бонус: +{level_data['bonus']}% к опыту\n"
    )
    
    return text
