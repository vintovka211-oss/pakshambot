import aiosqlite
from datetime import datetime, timedelta

DB_PATH = "w1npaksham.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                pac_balance INTEGER DEFAULT 100,
                total_games INTEGER DEFAULT 0,
                turnover INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0,
                is_premium INTEGER DEFAULT 0,
                premium_until TIMESTAMP,
                last_daily TIMESTAMP,
                last_withdraw TIMESTAMP,
                consecutive_wins INTEGER DEFAULT 0,
                mine_level INTEGER DEFAULT 1,
                mine_last_collect TIMESTAMP,
                mine_accumulated INTEGER DEFAULT 0,
                active_items TEXT DEFAULT '{}'
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS deposit_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                amount_pac INTEGER,
                method TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user:
                await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
                await db.commit()
                async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor2:
                    user = await cursor2.fetchone()
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, user))

async def update_user(user_id, **kwargs):
    async with aiosqlite.connect(DB_PATH) as db:
        for key, value in kwargs.items():
            await db.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()

async def add_transaction(user_id, type, amount, description=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
            (user_id, type, amount, description)
        )
        await db.commit()

async def get_top_users(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, username, turnover FROM users ORDER BY turnover DESC LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()

# ==================== ШАХТА ====================
async def get_mine_info(user_id):
    user = await get_user(user_id)
    if not user.get("is_premium"):
        return {"error": "❌ Шахта доступна только премиум-пользователям!"}
    
    level = user.get("mine_level", 1)
    last_collect = user.get("mine_last_collect")
    accumulated = user.get("mine_accumulated", 0)
    
    from config import MINE_LEVELS
    level_data = MINE_LEVELS.get(level, MINE_LEVELS[1])
    
    if last_collect:
        last = datetime.fromisoformat(last_collect) if isinstance(last_collect, str) else last_collect
        hours = (datetime.now() - last).total_seconds() / 3600
        accumulated += level_data["daily_output"] / 24 * hours
        accumulated = min(accumulated, level_data["daily_output"] * 3)
    
    return {
        "level": level,
        "name": level_data["name"],
        "icon": level_data["icon"],
        "daily_output": level_data["daily_output"],
        "accumulated": int(accumulated),
        "upgrade_cost": level_data.get("upgrade_cost"),
        "max_level": level == len(MINE_LEVELS)
    }

async def collect_mine(user_id):
    info = await get_mine_info(user_id)
    if "error" in info:
        return False, info["error"]
    if info["accumulated"] <= 0:
        return False, "⛏️ В шахте пока ничего не накопилось!"
    
    user = await get_user(user_id)
    await update_user(user_id, 
        pac_balance=user["pac_balance"] + info["accumulated"],
        mine_accumulated=0,
        mine_last_collect=datetime.now().isoformat()
    )
    await add_transaction(user_id, "mine", info["accumulated"], "Сбор шахты")
    return True, f"⛏️ Вы собрали {info['accumulated']} PAC из {info['name']}!"

async def upgrade_mine(user_id):
    user = await get_user(user_id)
    if not user.get("is_premium"):
        return False, "❌ Шахта доступна только премиум-пользователям!"
    
    current_level = user.get("mine_level", 1)
    from config import MINE_LEVELS
    if current_level >= len(MINE_LEVELS):
        return False, "🏆 Максимальный уровень!"
    
    next_level_data = MINE_LEVELS[current_level + 1]
    cost = next_level_data["upgrade_cost"]
    
    if user["pac_balance"] < cost:
        return False, f"❌ Нужно {cost} PAC!"
    
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - cost,
        mine_level=current_level + 1
    )
    await add_transaction(user_id, "mine_upgrade", -cost, f"Улучшение шахты до {current_level + 1} уровня")
    return True, f"✅ Шахта улучшена до {next_level_data['name']}!"

# ==================== ЕЖЕДНЕВНЫЙ БОНУС ====================
async def claim_daily_bonus(user_id):
    user = await get_user(user_id)
    if user.get("last_daily"):
        last = datetime.fromisoformat(user["last_daily"]) if isinstance(user["last_daily"], str) else user["last_daily"]
        if (datetime.now() - last).days < 1:
            return False, "❌ Бонус уже получен сегодня!"
    
    bonus = 15 if user.get("is_premium") else 5
    await update_user(user_id, pac_balance=user["pac_balance"] + bonus, last_daily=datetime.now().isoformat())
    await add_transaction(user_id, "daily_bonus", bonus, "Ежедневный бонус")
    return True, f"✅ Вы получили {bonus} PAC!"

# ==================== ПРЕМИУМ ====================
async def buy_premium(user_id):
    from config import PREMIUM_PRICE_PAC
    user = await get_user(user_id)
    if user.get("is_premium"):
        return False, "❌ У вас уже есть премиум!"
    
    if user["pac_balance"] < PREMIUM_PRICE_PAC:
        return False, f"❌ Нужно {PREMIUM_PRICE_PAC} PAC!"
    
    premium_until = (datetime.now() + timedelta(days=30)).isoformat()
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - PREMIUM_PRICE_PAC,
        is_premium=1,
        premium_until=premium_until
    )
    await add_transaction(user_id, "premium", -PREMIUM_PRICE_PAC, "Премиум подписка")
    return True, f"✅ Премиум активирован на 30 дней!"
