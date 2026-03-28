import sqlite3
import asyncio
from datetime import datetime, timedelta
import aiosqlite

DB_PATH = "w1npaksham.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                pac_balance INTEGER DEFAULT 5,
                total_games INTEGER DEFAULT 0,
                turnover INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0,
                is_premium INTEGER DEFAULT 0,
                premium_until TIMESTAMP,
                total_donated INTEGER DEFAULT 0,
                last_daily TIMESTAMP,
                last_withdraw TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS mines (
                user_id INTEGER PRIMARY KEY,
                level INTEGER DEFAULT 1,
                last_collect TIMESTAMP,
                accumulated INTEGER DEFAULT 0,
                total_mined INTEGER DEFAULT 0
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS withdraw_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount_pac INTEGER,
                amount_rub INTEGER,
                status TEXT DEFAULT 'pending'
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

async def add_income(source, amount, user_id=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bot_income (source, amount, user_id) VALUES (?, ?, ?)",
            (source, amount, user_id)
        )
        await db.commit()

async def get_top_users(limit=10, by="turnover"):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(f"SELECT user_id, username, {by} FROM users ORDER BY {by} DESC LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()

async def create_deposit_request(user_id, amount, method):
    from config import PAC_PRICE
    amount_pac = amount * (PAC_PRICE // 100)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO deposit_requests (user_id, amount, amount_pac, method) VALUES (?, ?, ?, ?)",
            (user_id, amount, amount_pac, method)
        )
        await db.commit()
        return True, cursor.lastrowid, amount_pac

async def approve_deposit(request_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, amount_pac FROM deposit_requests WHERE id = ? AND status = 'pending'", (request_id,)) as cursor:
            req = await cursor.fetchone()
        if not req:
            return False, "Заявка не найдена"
        user_id, amount_pac = req
        user = await get_user(user_id)
        await update_user(user_id, pac_balance=user["pac_balance"] + amount_pac)
        await db.execute("UPDATE deposit_requests SET status = 'approved' WHERE id = ?", (request_id,))
        await db.commit()
        return True, f"✅ Пополнено {amount_pac} PAC!"

async def create_withdraw_request(user_id, amount_pac):
    from config import MIN_WITHDRAW_PAC, PAC_TO_RUB_RATE
    user = await get_user(user_id)
    if amount_pac < MIN_WITHDRAW_PAC:
        return False, f"❌ Минимум {MIN_WITHDRAW_PAC} PAC"
    if user["pac_balance"] < amount_pac:
        return False, "❌ Недостаточно средств"
    amount_rub = int(amount_pac * PAC_TO_RUB_RATE)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO withdraw_requests (user_id, amount_pac, amount_rub) VALUES (?, ?, ?)",
            (user_id, amount_pac, amount_rub)
        )
        await db.commit()
        await update_user(user_id, pac_balance=user["pac_balance"] - amount_pac)
        return True, f"✅ Заявка #{cursor.lastrowid} создана! Вы получите {amount_rub}₽"