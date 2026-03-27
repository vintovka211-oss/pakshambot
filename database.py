import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import aiosqlite
import random

DB_PATH = "w1npaksham.db"

async def init_db():
    """Создание всех таблиц"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Пользователи
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                pac_balance INTEGER DEFAULT 5,
                total_games INTEGER DEFAULT 0,
                turnover INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0,
                ref_by INTEGER,
                is_premium INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                premium_until TIMESTAMP,
                vip_until TIMESTAMP,
                total_donated INTEGER DEFAULT 0,
                first_donation INTEGER DEFAULT 0,
                lottery_tickets INTEGER DEFAULT 0,
                tournament_points INTEGER DEFAULT 0,
                total_cashback INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_daily TIMESTAMP,
                last_withdraw TIMESTAMP
            )
        ''')
        
        # Шахта
        await db.execute('''
            CREATE TABLE IF NOT EXISTS mines (
                user_id INTEGER PRIMARY KEY,
                level INTEGER DEFAULT 1,
                last_collect TIMESTAMP,
                upgrade_start TIMESTAMP,
                upgrade_end TIMESTAMP,
                accumulated INTEGER DEFAULT 0,
                total_mined INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Месячные лимиты
        await db.execute('''
            CREATE TABLE IF NOT EXISTS monthly_free_limits (
                user_id INTEGER,
                month TEXT,
                source TEXT,
                amount INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, month, source)
            )
        ''')
        
        # Заявки на вывод
        await db.execute('''
            CREATE TABLE IF NOT EXISTS withdraw_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount_pac INTEGER,
                amount_rub INTEGER,
                status TEXT DEFAULT 'pending',
                withdraw_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Заявки на пополнение
        await db.execute('''
            CREATE TABLE IF NOT EXISTS deposit_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                amount_pac INTEGER,
                method TEXT,
                is_first INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Маркетплейс
        await db.execute('''
            CREATE TABLE IF NOT EXISTS marketplace_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                item_name TEXT,
                item_type TEXT,
                price INTEGER,
                quantity INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Инвентарь
        await db.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_name TEXT,
                item_type TEXT,
                quantity INTEGER DEFAULT 1,
                acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Кэшбэк
        await db.execute('''
            CREATE TABLE IF NOT EXISTS cashback_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Лотереи
        await db.execute('''
            CREATE TABLE IF NOT EXISTS lotteries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_number INTEGER,
                prize_pool INTEGER,
                total_tickets INTEGER,
                winner_id INTEGER,
                status TEXT DEFAULT 'active',
                draw_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Билеты лотереи
        await db.execute('''
            CREATE TABLE IF NOT EXISTS lottery_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lottery_id INTEGER,
                user_id INTEGER,
                ticket_number INTEGER,
                is_free INTEGER DEFAULT 0,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lottery_id) REFERENCES lotteries(id)
            )
        ''')
        
        # Турниры
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                entry_fee INTEGER,
                prize_pool INTEGER,
                max_players INTEGER,
                current_players INTEGER DEFAULT 0,
                status TEXT DEFAULT 'waiting',
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Участники турниров
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tournament_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER,
                user_id INTEGER,
                score INTEGER DEFAULT 0,
                place INTEGER,
                prize INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
            )
        ''')
        
        # Кланы
        await db.execute('''
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                owner_id INTEGER,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Участники кланов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS clan_members (
                user_id INTEGER PRIMARY KEY,
                clan_id INTEGER,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clan_id) REFERENCES clans(id)
            )
        ''')
        
        # Транзакции
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
        
        # Доходы бота
        await db.execute('''
            CREATE TABLE IF NOT EXISTS bot_income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                amount INTEGER,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()
        print("✅ База данных инициализирована")

# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================
async def get_user(user_id: int) -> Dict[str, Any]:
    """Получить данные пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            user = await cursor.fetchone()
            
            if not user:
                await db.execute(
                    "INSERT INTO users (user_id) VALUES (?)",
                    (user_id,)
                )
                await db.commit()
                
                async with db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ) as cursor2:
                    user = await cursor2.fetchone()
            
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, user))

async def update_user(user_id: int, **kwargs):
    """Обновить данные пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        for key, value in kwargs.items():
            await db.execute(
                f"UPDATE users SET {key} = ? WHERE user_id = ?",
                (value, user_id)
            )
        await db.commit()

async def add_transaction(user_id: int, type: str, amount: int, description: str = ""):
    """Добавить транзакцию"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)",
            (user_id, type, amount, description)
        )
        await db.commit()

async def add_income(source: str, amount: int, user_id: int = 0):
    """Записать доход бота"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bot_income (source, amount, user_id) VALUES (?, ?, ?)",
            (source, amount, user_id)
        )
        await db.commit()

async def get_top_users(limit: int = 10, by: str = "turnover"):
    """Получить топ пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT user_id, username, {by} FROM users ORDER BY {by} DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()

# ==================== МЕСЯЧНЫЕ ЛИМИТЫ ====================
async def check_monthly_free_limit(user_id: int, source: str, amount: int) -> tuple:
    """Проверить месячный лимит халявы"""
    from config import MONTHLY_FREE_LIMITS, FREE_SOURCES
    
    user = await get_user(user_id)
    current_month = datetime.now().strftime("%Y-%m")
    
    if user["is_premium"]:
        monthly_limit = MONTHLY_FREE_LIMITS["premium"]
        source_limit = FREE_SOURCES.get(source, {}).get("premium", 0)
    else:
        monthly_limit = MONTHLY_FREE_LIMITS["regular"]
        source_limit = FREE_SOURCES.get(source, {}).get("regular", 0)
    
    if source == "mine" and user["is_premium"]:
        source_limit = 999999
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT SUM(amount) FROM monthly_free_limits WHERE user_id = ? AND month = ? AND source = ?",
            (user_id, current_month, source)
        ) as cursor:
            result = await cursor.fetchone()
            current_source = result[0] if result[0] else 0
        
        async with db.execute(
            "SELECT SUM(amount) FROM monthly_free_limits WHERE user_id = ? AND month = ?",
            (user_id, current_month)
        ) as cursor:
            total_result = await cursor.fetchone()
            total_month = total_result[0] if total_result[0] else 0
        
        if current_source + amount > source_limit:
            remaining = source_limit - current_source
            return False, remaining, current_source
        
        if total_month + amount > monthly_limit:
            remaining = monthly_limit - total_month
            return False, remaining, total_month
        
        if current_source == 0:
            await db.execute(
                "INSERT INTO monthly_free_limits (user_id, month, source, amount) VALUES (?, ?, ?, ?)",
                (user_id, current_month, source, amount)
            )
        else:
            await db.execute(
                "UPDATE monthly_free_limits SET amount = amount + ? WHERE user_id = ? AND month = ? AND source = ?",
                (amount, user_id, current_month, source)
            )
        
        await db.commit()
        
        return True, amount, total_month + amount

async def get_monthly_free_stats(user_id: int) -> dict:
    """Получить статистику халявы за месяц"""
    from config import MONTHLY_FREE_LIMITS
    
    user = await get_user(user_id)
    current_month = datetime.now().strftime("%Y-%m")
    
    if user["is_premium"]:
        monthly_limit = MONTHLY_FREE_LIMITS["premium"]
    else:
        monthly_limit = MONTHLY_FREE_LIMITS["regular"]
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT SUM(amount) FROM monthly_free_limits WHERE user_id = ? AND month = ?",
            (user_id, current_month)
        ) as cursor:
            total_result = await cursor.fetchone()
            total_used = total_result[0] if total_result[0] else 0
    
    return {
        "total_used": total_used,
        "total_limit": monthly_limit,
        "remaining": monthly_limit - total_used,
        "percentage": (total_used / monthly_limit * 100) if monthly_limit > 0 else 0
    }

# ==================== ШАХТА ====================
async def init_mine(user_id: int):
    """Инициализировать шахту"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM mines WHERE user_id = ?", (user_id,)
        ) as cursor:
            if not await cursor.fetchone():
                await db.execute(
                    "INSERT INTO mines (user_id, level, last_collect) VALUES (?, ?, ?)",
                    (user_id, 1, datetime.now())
                )
                await db.commit()

async def get_mine_info(user_id: int) -> dict:
    """Получить информацию о шахте"""
    from config import MINE_LEVELS
    
    user = await get_user(user_id)
    
    if not user["is_premium"]:
        return {"error": "❌ Шахта доступна только премиум-пользователям!"}
    
    await init_mine(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT level, last_collect, upgrade_start, upgrade_end, accumulated, total_mined FROM mines WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            mine = await cursor.fetchone()
    
    if not mine:
        return {"error": "Ошибка загрузки шахты"}
    
    level, last_collect, upgrade_start, upgrade_end, accumulated, total_mined = mine
    level_data = MINE_LEVELS.get(level, MINE_LEVELS[1])
    now = datetime.now()
    
    is_upgrading = False
    upgrade_end_time = None
    if upgrade_end:
        upgrade_end_time = datetime.fromisoformat(upgrade_end) if isinstance(upgrade_end, str) else upgrade_end
        if upgrade_end_time > now:
            is_upgrading = True
    
    if last_collect and not is_upgrading:
        last_time = datetime.fromisoformat(last_collect) if isinstance(last_collect, str) else last_collect
        hours_passed = (now - last_time).total_seconds() / 3600
        hourly_rate = level_data["daily_output"] / 24
        if user["is_vip"]:
            hourly_rate *= 1.2
        accumulated += hourly_rate * hours_passed
        max_accumulation = level_data["daily_output"] * 7
        accumulated = min(accumulated, max_accumulation)
    
    total_cost = sum(MINE_LEVELS[i]["cost"] for i in range(1, level + 1)) if level > 1 else 0
    monthly_income = level_data["monthly_output"]
    payback_months = total_cost / monthly_income if monthly_income > 0 else 0
    
    return {
        "level": level,
        "level_name": level_data["name"],
        "level_icon": level_data["icon"],
        "daily_output": level_data["daily_output"],
        "monthly_output": level_data["monthly_output"],
        "hourly_rate": level_data["daily_output"] / 24,
        "accumulated": int(accumulated),
        "total_mined": total_mined,
        "is_upgrading": is_upgrading,
        "upgrade_end": upgrade_end_time,
        "next_level_cost": level_data.get("upgrade_cost"),
        "next_level_name": MINE_LEVELS.get(level + 1, {}).get("name", "Максимум") if level < 7 else None,
        "max_level": level == 7,
        "total_cost": total_cost,
        "payback_months": round(payback_months, 1)
    }

async def upgrade_mine(user_id: int) -> tuple:
    """Улучшить шахту"""
    from config import MINE_LEVELS
    
    user = await get_user(user_id)
    
    if not user["is_premium"]:
        return False, "❌ Шахта доступна только премиум-пользователям!"
    
    mine_info = await get_mine_info(user_id)
    
    if mine_info.get("error"):
        return False, mine_info["error"]
    
    if mine_info["is_upgrading"]:
        return False, "❌ Шахта уже улучшается! Дождитесь завершения."
    
    if mine_info["max_level"]:
        return False, "🏆 Шахта достигла максимального уровня!"
    
    current_level = mine_info["level"]
    next_level = current_level + 1
    next_level_data = MINE_LEVELS[next_level]
    upgrade_cost = next_level_data["upgrade_cost"]
    
    if user["pac_balance"] < upgrade_cost:
        return False, f"❌ Недостаточно PAC! Нужно: {upgrade_cost} PAC\n\n💡 Это {upgrade_cost // 100}₽ при покупке"
    
    new_balance = user["pac_balance"] - upgrade_cost
    await update_user(user_id, pac_balance=new_balance)
    
    upgrade_time = next_level_data["upgrade_time"]
    now = datetime.now()
    upgrade_end = now + timedelta(seconds=upgrade_time)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE mines SET upgrade_start = ?, upgrade_end = ?, accumulated = 0 WHERE user_id = ?",
            (now, upgrade_end, user_id)
        )
        await db.commit()
    
    await add_transaction(user_id, "mine_upgrade", -upgrade_cost, f"Улучшение шахты до {next_level} уровня")
    
    days = upgrade_time // 86400
    hours = (upgrade_time % 86400) // 3600
    
    return True, (
        f"✅ Начато улучшение шахты до {next_level_data['name']}!\n\n"
        f"📊 **Новый уровень:**\n"
        f"• Доход: {next_level_data['monthly_output']} PAC/месяц\n"
        f"• Стоимость: {upgrade_cost} PAC\n\n"
        f"⏱️ Время: {days}д {hours}ч"
    )

async def collect_mine(user_id: int) -> tuple:
    """Собрать ресурсы с шахты"""
    user = await get_user(user_id)
    
    if not user["is_premium"]:
        return False, "❌ Шахта доступна только премиум-пользователям!"
    
    mine_info = await get_mine_info(user_id)
    
    if mine_info.get("error"):
        return False, mine_info["error"]
    
    if mine_info["is_upgrading"]:
        return False, "❌ Шахта улучшается! Подождите завершения."
    
    if mine_info["accumulated"] <= 0:
        return False, "⛏️ В шахте пока ничего не накопилось."
    
    can_get, actual_reward, _ = await check_monthly_free_limit(user_id, "mine", mine_info["accumulated"])
    
    if not can_get:
        return False, f"❌ Достигнут месячный лимит халявы! Осталось: {actual_reward} PAC"
    
    new_balance = user["pac_balance"] + actual_reward
    await update_user(user_id, pac_balance=new_balance)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE mines SET last_collect = ?, accumulated = 0, total_mined = total_mined + ? WHERE user_id = ?",
            (datetime.now(), actual_reward, user_id)
        )
        await db.commit()
    
    await add_transaction(user_id, "mine", actual_reward, "Сбор ресурсов из шахты")
    
    return True, f"⛏️ Вы собрали {actual_reward} PAC из {mine_info['level_name']}!"

async def complete_mine_upgrades():
       """Завершить улучшения шахт"""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now()
        
        async with db.execute(
            "SELECT user_id, level, upgrade_end FROM mines WHERE upgrade_end IS NOT NULL AND upgrade_end <= ?",
            (now,)
        ) as cursor:
            upgrading_mines = await cursor.fetchall()
        
        for user_id, current_level, _ in upgrading_mines:
            new_level = current_level + 1
            await db.execute(
                "UPDATE mines SET level = ?, upgrade_start = NULL, upgrade_end = NULL WHERE user_id = ?",
                (new_level, user_id)
            )
        
        await db.commit()
        return len(upgrading_mines)

# ==================== БОНУСЫ ====================
async def claim_daily_bonus(user_id: int) -> tuple:
    """Получить ежедневный бонус"""
    user = await get_user(user_id)
    
    if user["last_daily"]:
        last_time = datetime.fromisoformat(user["last_daily"]) if isinstance(user["last_daily"], str) else user["last_daily"]
        if (datetime.now() - last_time).days < 1:
            return False, "❌ Бонус уже получен сегодня!"
    
    if user["is_vip"]:
        bonus = 10
    elif user["is_premium"]:
        bonus = 7
    else:
        bonus = 3
    
    can_get, actual_bonus, _ = await check_monthly_free_limit(user_id, "daily_bonus", bonus)
    
    if not can_get:
        stats = await get_monthly_free_stats(user_id)
        return False, f"❌ Достигнут месячный лимит! Использовано: {stats['total_used']}/{stats['total_limit']} PAC"
    
    new_balance = user["pac_balance"] + actual_bonus
    await update_user(user_id, pac_balance=new_balance, last_daily=datetime.now())
    await add_transaction(user_id, "daily_bonus", actual_bonus, "Ежедневный бонус")
    
    stats = await get_monthly_free_stats(user_id)
    
    return True, f"✅ Вы получили {actual_bonus} PAC!\n📊 В этом месяце: {stats['total_used']}/{stats['total_limit']} PAC"

# ==================== ДОНАТЫ ====================
async def create_deposit_request(user_id: int, amount: int, method: str) -> tuple:
    """Создать заявку на пополнение"""
    from config import PAC_PRICE, FIRST_DONATION_BONUS, LARGE_DONATION_BONUSES, VIP_DONATION_THRESHOLD
    
    user = await get_user(user_id)
    amount_pac = amount * (PAC_PRICE // 100)
    
    is_first = 0
    if user["total_donated"] == 0:
        is_first = 1
        amount_pac = int(amount_pac * (100 + FIRST_DONATION_BONUS) / 100)
    
    for threshold, bonus_percent in sorted(LARGE_DONATION_BONUSES.items(), reverse=True):
        if amount >= threshold:
            amount_pac = int(amount_pac * (100 + bonus_percent) / 100)
            break
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO deposit_requests (user_id, amount, amount_pac, method, is_first) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, amount_pac, method, is_first)
        )
        await db.commit()
        request_id = cursor.lastrowid
    
    if amount >= VIP_DONATION_THRESHOLD:
        vip_until = (datetime.now() + timedelta(days=30)).isoformat()
        await update_user(user_id, is_vip=1, vip_until=vip_until)
    
    return True, request_id, amount_pac

async def approve_deposit(request_id: int) -> tuple:
    """Подтвердить пополнение"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, amount_pac FROM deposit_requests WHERE id = ? AND status = 'pending'",
            (request_id,)
        ) as cursor:
            req = await cursor.fetchone()
        
        if not req:
            return False, "Заявка не найдена"
        
        user_id, amount_pac = req
        
        user = await get_user(user_id)
        new_balance = user["pac_balance"] + amount_pac
        new_donated = user["total_donated"] + (amount_pac // 10)
        
        await db.execute(
            "UPDATE users SET pac_balance = ?, total_donated = ? WHERE user_id = ?",
            (new_balance, new_donated, user_id)
        )
        
        await db.execute(
            "UPDATE deposit_requests SET status = 'approved' WHERE id = ?",
            (request_id,)
        )
        
        await db.commit()
        
        await add_transaction(user_id, "deposit", amount_pac, "Пополнение")
        await add_income("deposit", amount_pac // 10, user_id)
        
        return True, f"✅ Пополнено {amount_pac} PAC!"

# ==================== ВЫВОД ====================
async def create_withdraw_request(user_id: int, amount_pac: int) -> tuple:
    """Создать заявку на вывод"""
    from config import MIN_WITHDRAW_PAC, PAC_TO_RUB_RATE
    
    user = await get_user(user_id)
    
    if amount_pac < MIN_WITHDRAW_PAC:
        return False, f"❌ Минимальная сумма: {MIN_WITHDRAW_PAC} PAC"
    
    if user["pac_balance"] < amount_pac:
        return False, "❌ Недостаточно средств!"
    
    if user["last_withdraw"]:
        last_withdraw = datetime.fromisoformat(user["last_withdraw"]) if isinstance(user["last_withdraw"], str) else user["last_withdraw"]
        if (datetime.now() - last_withdraw).days < 7:
            next_withdraw = last_withdraw + timedelta(days=7)
            return False, f"❌ Вывод раз в неделю! Следующий: {next_withdraw.strftime('%d.%m.%Y')}"
    
    amount_rub = int(amount_pac * PAC_TO_RUB_RATE)
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO withdraw_requests (user_id, amount_pac, amount_rub, withdraw_date) VALUES (?, ?, ?, ?)",
            (user_id, amount_pac, amount_rub, datetime.now().date().isoformat())
        )
        await db.commit()
        request_id = cursor.lastrowid
        
        new_balance = user["pac_balance"] - amount_pac
        await db.execute(
            "UPDATE users SET pac_balance = ? WHERE user_id = ?",
            (new_balance, user_id)
        )
        
        await add_transaction(user_id, "withdraw_request", -amount_pac, f"Заявка #{request_id}")
        
        return True, f"✅ Заявка #{request_id} создана! Вы получите {amount_rub}₽"

async def process_withdraw_requests():
    """Обработать заявки на вывод"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, user_id FROM withdraw_requests WHERE status = 'pending'"
        ) as cursor:
            requests = await cursor.fetchall()
        
        for req_id, user_id in requests:
            await db.execute(
                "UPDATE withdraw_requests SET status = 'processed' WHERE id = ?",
                (req_id,)
            )
            await db.execute(
                "UPDATE users SET last_withdraw = ? WHERE user_id = ?",
                (datetime.now(), user_id)
            )
        
        await db.commit()
        return len(requests)
```

---
