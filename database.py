import aiosqlite
import json
from datetime import datetime, timedelta

DB_PATH = "w1npaksham.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                pac_balance INTEGER DEFAULT 100,
                rpg_balance INTEGER DEFAULT 0,
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
                clan_id INTEGER DEFAULT 0
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                user_id INTEGER PRIMARY KEY,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                hp INTEGER DEFAULT 100,
                max_hp INTEGER DEFAULT 100,
                weapon_id INTEGER DEFAULT 1,
                weapon_upgrade INTEGER DEFAULT 0,
                armor_id INTEGER DEFAULT 1,
                armor_upgrade INTEGER DEFAULT 0,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                tool_level INTEGER DEFAULT 1,
                achievements TEXT DEFAULT '{}'
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_type TEXT,
                item_id TEXT,
                quantity INTEGER DEFAULT 1,
                durability INTEGER DEFAULT 100
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS artifacts (
                user_id INTEGER,
                artifact_id INTEGER,
                PRIMARY KEY (user_id, artifact_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                leader_id INTEGER,
                members TEXT DEFAULT '[]',
                balance INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS pvp_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id INTEGER,
                to_id INTEGER,
                bet INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS marketplace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                item_type TEXT,
                item_id TEXT,
                quantity INTEGER,
                price INTEGER,
                status TEXT DEFAULT 'active'
            )
        ''')
        await db.commit()
        print("✅ База данных инициализирована")

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

async def get_player_stats(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM player_stats WHERE user_id = ?", (user_id,)) as cursor:
            stats = await cursor.fetchone()
            if not stats:
                await db.execute("INSERT INTO player_stats (user_id) VALUES (?)", (user_id,))
                await db.commit()
                async with db.execute("SELECT * FROM player_stats WHERE user_id = ?", (user_id,)) as cursor2:
                    stats = await cursor2.fetchone()
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, stats))

async def update_player_stats(user_id, **kwargs):
    async with aiosqlite.connect(DB_PATH) as db:
        for key, value in kwargs.items():
            await db.execute(f"UPDATE player_stats SET {key} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()
