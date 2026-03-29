import aiosqlite
from datetime import datetime, timedelta

DB_PATH = "w1npaksham.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Пользователи
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
        
        # RPG статистика
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
        
        # Инвентарь
        await db.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_type TEXT,
                item_id INTEGER,
                quantity INTEGER DEFAULT 1,
                durability INTEGER DEFAULT 100,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Артефакты (экипированные)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS artifacts (
                user_id INTEGER,
                artifact_id INTEGER,
                PRIMARY KEY (user_id, artifact_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        await db.commit()
        print("✅ База данных инициализирована")

# Остальные функции database.py (get_user, update_user, add_transaction, get_top_users)
# будут добавлены в следующем сообщении из-за ограничения длины
