import asyncio
import logging
import random
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = "8593186262:AAGN6sTyBa1RlJ0eVWwNVzgYUb6aVy_H9LA"
ADMIN_ID = 8493522297

# Настройки валют
MSG_REWARD = 0.05
MSG_COOLDOWN = 20

# Курсы валют
PAK_TO_RUB = 4  # 4 PAK = 1 рубль
RUB_TO_STARS = 2  # 2 рубля = 1 звезда

# Ферма
FARM_BASE_RATE = 2
FARM_UPGRADE_COST = 100
FARM_UPGRADE_INCREMENT = 100
FARM_RATE_INCREMENT = 1

# Кланы
CLAN_CREATE_COST = 1000
CLAN_REWARD = 2
CLAN_REWARD_INTERVAL = 3600

# ==================== БАЗА ДАННЫХ ====================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                pak_balance INTEGER DEFAULT 0,
                rub_balance INTEGER DEFAULT 0,
                last_message_time TIMESTAMP,
                last_clan_reward TIMESTAMP,
                last_farm_collect TIMESTAMP,
                farm_level INTEGER DEFAULT 0,
                farm_rate INTEGER DEFAULT 2,
                total_farm_earned INTEGER DEFAULT 0,
                in_clan INTEGER DEFAULT NULL,
                clan_role TEXT DEFAULT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clans (
                clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                owner_id INTEGER,
                created_at TIMESTAMP,
                member_count INTEGER DEFAULT 1
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clan_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_id INTEGER,
                user_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS duels (
                duel_id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER,
                opponent_id INTEGER,
                bet_pak INTEGER,
                bet_rub INTEGER,
                status TEXT,
                winner_id INTEGER DEFAULT NULL,
                created_at TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def register_user(self, user_id, username):
        now = datetime.now()
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (
                user_id, username, last_message_time, 
                last_clan_reward, last_farm_collect, farm_rate
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, now, now, now, 2))
        self.conn.commit()
    
    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def update_balance(self, user_id, pak_change=0, rub_change=0):
        self.cursor.execute('''
            UPDATE users 
            SET pak_balance = pak_balance + ?,
                rub_balance = rub_balance + ?
            WHERE user_id = ?
        ''', (pak_change, rub_change, user_id))
        self.conn.commit()
    
    def can_get_message_reward(self, user_id):
        self.cursor.execute('SELECT last_message_time FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            last_time = datetime.fromisoformat(result[0])
            if datetime.now() - last_time > timedelta(seconds=20):
                return True
        return True
    
    def update_message_time(self, user_id):
        self.cursor.execute('UPDATE users SET last_message_time = ? WHERE user_id = ?', (datetime.now(), user_id))
        self.conn.commit()
    
    # ============ ФЕРМА ============
    def get_farm_info(self, user_id):
        self.cursor.execute('SELECT farm_level, farm_rate, total_farm_earned, last_farm_collect FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def get_farm_available(self, user_id):
        self.cursor.execute('SELECT last_farm_collect, farm_rate FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            last_collect = datetime.fromisoformat(result[0])
            hours_passed = (datetime.now() - last_collect).total_seconds() / 3600
            if hours_passed >= 1:
                return True, int(hours_passed * result[1])
        return False, 0
    
    def collect_farm(self, user_id):
        self.cursor.execute('SELECT farm_rate, total_farm_earned, last_farm_collect FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if result:
            rate = result[0]
            last_collect = datetime.fromisoformat(result[2])
            hours_passed = int((datetime.now() - last_collect).total_seconds() / 3600)
            if hours_passed >= 1:
                earned = hours_passed * rate
                self.cursor.execute('''
                    UPDATE users 
                    SET pak_balance = pak_balance + ?,
                        total_farm_earned = total_farm_earned + ?,
                        last_farm_collect = ?
                    WHERE user_id = ?
                ''', (earned, earned, datetime.now(), user_id))
                self.conn.commit()
                return earned
        return 0
    
    def upgrade_farm(self, user_id):
        self.cursor.execute('SELECT farm_level, farm_rate FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if result:
            level = result[0]
            current_rate = result[1]
            upgrade_cost = 100 + (level * 100)
            self.cursor.execute('SELECT pak_balance FROM users WHERE user_id = ?', (user_id,))
            balance = self.cursor.fetchone()
            if balance and balance[0] >= upgrade_cost:
                new_rate = current_rate + 1
                new_level = level + 1
                self.cursor.execute('''
                    UPDATE users 
                    SET pak_balance = pak_balance - ?,
                        farm_level = ?,
                        farm_rate = ?
                    WHERE user_id = ?
                ''', (upgrade_cost, new_level, new_rate, user_id))
                self.conn.commit()
                return True, upgrade_cost, new_level, new_rate
        return False, 0, 0, 0
    
    def get_farm_leaderboard(self, limit=10):
        self.cursor.execute('SELECT username, farm_level, farm_rate, total_farm_earned FROM users ORDER BY total_farm_earned DESC LIMIT ?', (limit,))
        return self.cursor.fetchall()
    
    # ============ КЛАНЫ ============
    def create_clan(self, name, description, owner_id):
        try:
            self.cursor.execute('''
                INSERT INTO clans (name, description, owner_id, created_at, member_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, owner_id, datetime.now(), 1))
            clan_id = self.cursor.lastrowid
            self.cursor.execute('UPDATE users SET in_clan = ?, clan_role = "owner" WHERE user_id = ?', (clan_id, owner_id))
            self.conn.commit()
            return clan_id
        except sqlite3.IntegrityError:
            return None
    
    def get_all_clans(self):
        self.cursor.execute('''
            SELECT c.clan_id, c.name, c.description, c.member_count,
                   COALESCE(SUM(u.pak_balance + u.rub_balance * 4), 0) as total_wealth
            FROM clans c
            LEFT JOIN users u ON u.in_clan = c.clan_id
            GROUP BY c.clan_id
            ORDER BY total_wealth DESC
        ''')
        return self.cursor.fetchall()
    
    def get_clan_by_id(self, clan_id):
        self.cursor.execute('SELECT * FROM clans WHERE clan_id = ?', (clan_id,))
        return self.cursor.fetchone()
    
    def get_clan_members(self, clan_id):
        self.cursor.execute('SELECT user_id, username, clan_role, pak_balance, rub_balance FROM users WHERE in_clan = ?', (clan_id,))
        return self.cursor.fetchall()
    
    def get_clan_owner(self, clan_id):
        self.cursor.execute('SELECT owner_id FROM clans WHERE clan_id = ?', (clan_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_clan_total_wealth(self, clan_id):
        self.cursor.execute('SELECT COALESCE(SUM(pak_balance + rub_balance * 4), 0) FROM users WHERE in_clan = ?', (clan_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def send_clan_request(self, clan_id, user_id):
        self.cursor.execute('SELECT * FROM clan_requests WHERE clan_id = ? AND user_id = ? AND status = "pending"', (clan_id, user_id))
        if self.cursor.fetchone():
            return False
        self.cursor.execute('INSERT INTO clan_requests (clan_id, user_id, created_at) VALUES (?, ?, ?)', (clan_id, user_id, datetime.now()))
        self.conn.commit()
        return True
    
    def get_clan_requests(self, clan_id):
        self.cursor.execute('''
            SELECT r.request_id, r.user_id, u.username, r.created_at
            FROM clan_requests r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.clan_id = ? AND r.status = "pending"
        ''', (clan_id,))
        return self.cursor.fetchall()
    
    def accept_clan_request(self, request_id, clan_id):
        self.cursor.execute('SELECT user_id FROM clan_requests WHERE request_id = ?', (request_id,))
        result = self.cursor.fetchone()
        if not result:
            return False
        user_id = result[0]
        self.cursor.execute('UPDATE clan_requests SET status = "accepted" WHERE request_id = ?', (request_id,))
        self.cursor.execute('UPDATE users SET in_clan = ?, clan_role = "member" WHERE user_id = ?', (clan_id, user_id))
        self.cursor.execute('UPDATE clans SET member_count = member_count + 1 WHERE clan_id = ?', (clan_id,))
        self.conn.commit()
        return user_id
    
    def reject_clan_request(self, request_id):
        self.cursor.execute('UPDATE clan_requests SET status = "rejected" WHERE request_id = ?', (request_id,))
        self.conn.commit()
    
    def remove_from_clan(self, user_id):
        self.cursor.execute('SELECT in_clan FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            clan_id = result[0]
            self.cursor.execute('UPDATE clans SET member_count = member_count - 1 WHERE clan_id = ?', (clan_id,))
        self.cursor.execute('UPDATE users SET in_clan = NULL, clan_role = NULL WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def kick_from_clan(self, clan_id, user_id):
        self.cursor.execute('UPDATE users SET in_clan = NULL, clan_role = NULL WHERE user_id = ? AND in_clan = ?', (user_id, clan_id))
        self.cursor.execute('UPDATE clans SET member_count = member_count - 1 WHERE clan_id = ?', (clan_id,))
        self.conn.commit()
    
    def get_clan_reward_available(self, user_id):
        self.cursor.execute('SELECT last_clan_reward, in_clan FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if not result or not result[1]:
            return False
        last_reward = datetime.fromisoformat(result[0])
        if datetime.now() - last_reward > timedelta(hours=1):
            return True
        return False
    
    def update_clan_reward_time(self, user_id):
        self.cursor.execute('UPDATE users SET last_clan_reward = ? WHERE user_id = ?', (datetime.now(), user_id))
        self.conn.commit()
    
    def give_clan_reward(self, user_id):
        self.cursor.execute('UPDATE users SET pak_balance = pak_balance + 2 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def get_clan_leaderboard(self, limit=10):
        self.cursor.execute('''
            SELECT c.name, COUNT(u.user_id) as members, 
                   COALESCE(SUM(u.pak_balance), 0) as total_pak,
                   COALESCE(SUM(u.rub_balance), 0) as total_rub,
                   COALESCE(SUM(u.pak_balance + u.rub_balance * 4), 0) as total_wealth
            FROM clans c
            LEFT JOIN users u ON u.in_clan = c.clan_id
            GROUP BY c.clan_id
            ORDER BY total_wealth DESC
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()
    
    # ============ ДУЭЛИ ============
    def create_duel(self, challenger_id, opponent_id, bet_pak, bet_rub):
        self.cursor.execute('''
            INSERT INTO duels (challenger_id, opponent_id, bet_pak, bet_rub, status, created_at)
            VALUES (?, ?, ?, ?, "pending", ?)
        ''', (challenger_id, opponent_id, bet_pak, bet_rub, datetime.now()))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def complete_duel(self, duel_id, winner_id):
        self.cursor.execute('UPDATE duels SET status = "completed", winner_id = ? WHERE duel_id = ?', (winner_id, duel_id))
        self.conn.commit()
    
    def get_user_by_username(self, username):
        self.cursor.execute('SELECT user_id, username FROM users WHERE username = ?', (username,))
        return self.cursor.fetchone()
    
    def get_leaderboard(self, limit=10):
        self.cursor.execute('''
            SELECT username, pak_balance, rub_balance, (pak_balance + rub_balance * 4) as total_wealth
            FROM users 
            ORDER BY total_wealth DESC 
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()

db = Database()

# ==================== ВЕБ-СЕРВЕР ДЛЯ RENDER ====================
async def health_check(request):
    return web.Response(text="Bot is alive!", status=200)

async def handle_web(request):
    return web.Response(text="W1nPAK Bot is running!", status=200)

async def start_web_server():
    port = int(os.environ.get('PORT', 8080))
    app = web.Application()
    app.router.add_get('/', handle_web)
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}")

# ==================== ХРАНИЛИЩЕ ДУЭЛЕЙ ====================
active_duels = {}

# ==================== ИГРЫ КАЗИНО ====================
class CasinoGames:
    @staticmethod
    async def roll_dice(update, context, bet_pak, bet_rub):
        player_roll = random.randint(1, 6)
        computer_roll = random.randint(1, 6)
        
        if player_roll > computer_roll:
            win_multiplier = random.uniform(1.1, 1.5)
            win_pak = int(bet_pak * win_multiplier)
            win_rub = int(bet_rub * win_multiplier)
            result_text = f"""🎲 ИГРА В КОСТИ!

Ваш бросок: {player_roll}
Бросок казино: {computer_roll}

🎉 ВЫ ВЫИГРАЛИ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ
⭐ Множитель: x{win_multiplier:.1f}"""
            return True, win_pak, win_rub, result_text
        elif player_roll == computer_roll:
            result_text = f"""🎲 ИГРА В КОСТИ!

Ваш бросок: {player_roll}
Бросок казино: {computer_roll}

🤝 НИЧЬЯ!
💰 Возврат ставки: {bet_pak} PAK и {bet_rub} РУБ"""
            return None, bet_pak, bet_rub, result_text
        else:
            loss_multiplier = random.uniform(1.2, 1.8)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            result_text = f"""🎲 ИГРА В КОСТИ!

Ваш бросок: {player_roll}
Бросок казино: {computer_roll}

💔 ВЫ ПРОИГРАЛИ!
💸 Потеряно: -{loss_pak} PAK и -{loss_rub} РУБ"""
            return False, loss_pak, loss_rub, result_text
    
    @staticmethod
    async def blackjack(update, context, bet_pak, bet_rub):
        def get_card():
            return random.randint(1, 11)
        
        player_cards = [get_card(), get_card()]
        dealer_cards = [get_card()]
        player_score = sum(player_cards)
        
        if random.random() < 0.35:
            win_multiplier = random.uniform(1.1, 1.4)
            win_pak = int(bet_pak * win_multiplier)
            win_rub = int(bet_rub * win_multiplier)
            result_text = f"""🃏 БЛЭКДЖЕК!

Ваши карты: {player_cards[0]} + {player_cards[1]} = {player_score}

🎉 ВЫ ВЫИГРАЛИ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ"""
            return True, win_pak, win_rub, result_text
        elif random.random() < 0.55:
            loss_multiplier = random.uniform(1.3, 2.0)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            result_text = f"""🃏 БЛЭКДЖЕК!

Ваши карты: {player_cards[0]} + {player_cards[1]} = {player_score}

💔 ВЫ ПРОИГРАЛИ!
💸 Потеряно: -{loss_pak} PAK и -{loss_rub} РУБ"""
            return False, loss_pak, loss_rub, result_text
        else:
            result_text = f"""🃏 БЛЭКДЖЕК!

Ваши карты: {player_cards[0]} + {player_cards[1]} = {player_score}

🤝 НИЧЬЯ!
💰 Возврат ставки: {bet_pak} PAK и {bet_rub} РУБ"""
            return None, bet_pak, bet_rub, result_text
    
    @staticmethod
    async def slot_machine(update, context, bet_pak, bet_rub):
        symbols = ['🍒', '🍋', '🍊', '🍉', '⭐', '💎', '7️⃣']
        results = [random.choice(symbols) for _ in range(3)]
        
        if results[0] == results[1] == results[2]:
            if results[0] == '💎':
                multiplier = 5.0
                win_text = "🎉 ДЖЕКПОТ! 🎉"
            elif results[0] == '7️⃣':
                multiplier = 4.0
                win_text = "🔥 СУПЕР ВЫИГРЫШ! 🔥"
            elif results[0] == '⭐':
                multiplier = 3.0
                win_text = "✨ БОЛЬШОЙ ВЫИГРЫШ! ✨"
            else:
                multiplier = 2.0
                win_text = "🎰 ВЫИГРЫШ! 🎰"
            win_pak = int(bet_pak * multiplier)
            win_rub = int(bet_rub * multiplier)
            result_text = f"""🎰 СЛОТ-МАШИНА!

[{results[0]}] [{results[1]}] [{results[2]}]

{win_text}
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ"""
            return True, win_pak, win_rub, result_text
        elif results[0] == results[1] or results[1] == results[2] or results[0] == results[2]:
            multiplier = 1.3
            win_pak = int(bet_pak * multiplier)
            win_rub = int(bet_rub * multiplier)
            result_text = f"""🎰 СЛОТ-МАШИНА!

[{results[0]}] [{results[1]}] [{results[2]}]

🎯 МАЛЕНЬКИЙ ВЫИГРЫШ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ"""
            return True, win_pak, win_rub, result_text
        else:
            loss_multiplier = random.uniform(1.5, 2.5)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            result_text = f"""🎰 СЛОТ-МАШИНА!

[{results[0]}] [{results[1]}] [{results[2]}]

💔 ВЫ ПРОИГРАЛИ!
💸 Потеряно: -{loss_pak} PAK и -{loss_rub} РУБ"""
            return False, loss_pak, loss_rub, result_text
    
    @staticmethod
    async def high_risk(update, context, bet_pak, bet_rub):
        chance = random.random()
        if chance < 0.15:
            multiplier = 5.0
            win_pak = int(bet_pak * multiplier)
            win_rub = int(bet_rub * multiplier)
            result_text = f"""💀 HIGH RISK GAME 💀

🎉 ЧУДО! ВЫ ВЫИГРАЛИ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ"""
            return True, win_pak, win_rub, result_text
        elif chance < 0.35:
            multiplier = 2.0
            win_pak = int(bet_pak * multiplier)
            win_rub = int(bet_rub * multiplier)
            result_text = f"""💀 HIGH RISK GAME 💀

🎉 ВЫ ВЫИГРАЛИ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ"""
            return True, win_pak, win_rub, result_text
        else:
            loss_multiplier = random.uniform(2.5, 4.0)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            result_text = f"""💀 HIGH RISK GAME 💀

💔 ВЫ ПРОИГРАЛИ!
💸 Потеряно: -{loss_pak} PAK и -{loss_rub} РУБ"""
            return False, loss_pak, loss_rub, result_text

# ==================== КОМАНДЫ БОТА ====================

# СТАРТ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(user.id, user.username or str(user.id))
    text = """🎮 Добро пожаловать в W1nPAK Бот!

💰 Доступные команды:
/balance - Баланс
/farm - Ферма
/casino - Казино
/duel - Дуэль
/clan - Кланы
/buy - Купить PAK за звезды
/withdraw - Вывод средств
/leaderboard - Топ игроков
/clan_leaderboard - Топ кланов

💡 Подсказка: Установи @W1npakshambot в описании профиля и получай 5 PAK за каждое сообщение!"""
    await update.message.reply_text(text)

# БАЛАНС
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if user_data:
        rub_from_pak = user_data[2] / 4
        total_rub_value = user_data[3] + rub_from_pak
        stars_value = total_rub_value / 2
        text = f"""💰 ТВОЙ БАЛАНС:

💎 PAK: {user_data[2]}
💵 РУБ: {user_data[3]}

📊 ЭКВИВАЛЕНТ:
💵 В рублях: {total_rub_value:.1f} ₽
⭐ В звездах: {stars_value:.1f} ⭐

🌾 ФЕРМА:
📈 Уровень: {user_data[6]}
⚡ Добыча/час: {user_data[7]} PAK
🏆 Всего добыто: {user_data[8]} PAK

👥 КЛАН: {'✅ В клане' if user_data[9] else '❌ Не в клане'}

📈 КУРСЫ:
4 PAK = 1 ₽
2 ₽ = 1 ⭐"""
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("❌ Ошибка! Напиши /start")

# ФЕРМА
async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌾 Собрать урожай", callback_data="farm_collect")],
        [InlineKeyboardButton("📈 Улучшить ферму", callback_data="farm_upgrade")],
        [InlineKeyboardButton("📊 Статистика фермы", callback_data="farm_stats")],
        [InlineKeyboardButton("🏆 Топ фермеров", callback_data="farm_leaderboard")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌾 УПРАВЛЕНИЕ ФЕРМОЙ 🌾", reply_markup=reply_markup)

async def farm_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    available, amount = db.get_farm_available(user_id)
    if available:
        earned = db.collect_farm(user_id)
        user_data = db.get_user(user_id)
        await update.callback_query.edit_message_text(
            f"🌾 ВЫ СОБРАЛИ УРОЖАЙ!\n\n"
            f"💰 Получено: +{earned} PAK\n"
            f"💎 Текущий баланс: {user_data[2]} PAK\n"
            f"⚡ Добыча/час: {user_data[7]} PAK"
        )
    else:
        user_data = db.get_user(user_id)
        last_collect = datetime.fromisoformat(user_data[10])
        hours_left = 1 - (datetime.now() - last_collect).total_seconds() / 3600
        minutes_left = int(hours_left * 60)
        await update.callback_query.edit_message_text(
            f"⏳ Урожай еще не готов!\n\n"
            f"Следующий сбор через: {minutes_left} минут\n"
            f"Текущая добыча: {user_data[7]} PAK/час"
        )

async def farm_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    success, cost, new_level, new_rate = db.upgrade_farm(user_id)
    if success:
        user_data = db.get_user(user_id)
        await update.callback_query.edit_message_text(
            f"📈 ФЕРМА УЛУЧШЕНА!\n\n"
            f"💰 Потрачено: {cost} PAK\n"
            f"📊 Новый уровень: {new_level}\n"
            f"⚡ Новая добыча: {new_rate} PAK/час\n"
            f"💎 Остаток PAK: {user_data[2]}"
        )
    else:
        user_data = db.get_user(user_id)
        next_cost = 100 + (user_data[6] * 100)
        await update.callback_query.edit_message_text(
            f"❌ НЕДОСТАТОЧНО PAK!\n\n"
            f"💰 Нужно: {next_cost} PAK\n"
            f"💎 У вас: {user_data[2]} PAK\n"
            f"⚡ Текущая добыча: {user_data[7]} PAK/час"
        )

async def farm_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    next_cost = 100 + (user_data[6] * 100)
    text = f"""🌾 СТАТИСТИКА ФЕРМЫ:

📊 Уровень: {user_data[6]}
⚡ Добыча/час: {user_data[7]} PAK
🏆 Всего добыто: {user_data[8]} PAK

💰 Следующее улучшение:
Стоимость: {next_cost} PAK
Добыча станет: {user_data[7] + 1} PAK/час

💡 Совет: Чем выше уровень, тем быстрее окупаются улучшения!"""
    await update.callback_query.edit_message_text(text)

async def farm_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_farmers = db.get_farm_leaderboard(10)
    if not top_farmers:
        await update.callback_query.edit_message_text("🏆 Пока нет фермеров!")
        return
    text = "🌾 ТОП ФЕРМЕРОВ 🌾\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, farmer in enumerate(top_farmers):
        text += f"{medals[i]} {farmer[0]}: 📊{farmer[1]} ур. | ⚡{farmer[2]} PAK/ч | 🏆{farmer[3]} PAK\n"
    await update.callback_query.edit_message_text(text)

# КАЗИНО
async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 Кости", callback_data="game_dice")],
        [InlineKeyboardButton("🃏 Блэкджек", callback_data="game_blackjack")],
        [InlineKeyboardButton("🎰 Слоты", callback_data="game_slots")],
        [InlineKeyboardButton("💀 High Risk", callback_data="game_highrisk")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎮 ВЫБЕРИ ИГРУ 🎮", reply_markup=reply_markup)
    context.user_data['waiting_for_bet'] = True

async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_bet'):
        return
    user_id = update.effective_user.id
    text = update.message.text.split()
    if len(text) != 2:
        await update.message.reply_text("❌ Введите: PAK РУБ\nПример: 100 50")
        return
    try:
        bet_pak = int(text[0])
        bet_rub = int(text[1])
    except:
        await update.message.reply_text("❌ Ставки должны быть числами!")
        return
    user_data = db.get_user(user_id)
    if user_data[2] < bet_pak or user_data[3] < bet_rub:
        await update.message.reply_text("❌ Недостаточно средств!")
        context.user_data['waiting_for_bet'] = False
        return
    game = context.user_data.get('selected_game', 'dice')
    if game == 'dice':
        win, change_pak, change_rub, result_text = await CasinoGames.roll_dice(update, context, bet_pak, bet_rub)
    elif game == 'blackjack':
        win, change_pak, change_rub, result_text = await CasinoGames.blackjack(update, context, bet_pak, bet_rub)
    elif game == 'slots':
        win, change_pak, change_rub, result_text = await CasinoGames.slot_machine(update, context, bet_pak, bet_rub)
    elif game == 'highrisk':
        win, change_pak, change_rub, result_text = await CasinoGames.high_risk(update, context, bet_pak, bet_rub)
    else:
        await update.message.reply_text("❌ Игра не найдена!")
        context.user_data['waiting_for_bet'] = False
        return
    if win is True:
        db.update_balance(user_id, change_pak, change_rub)
    elif win is False:
        db.update_balance(user_id, -change_pak, -change_rub)
    await update.message.reply_text(result_text)
    new_balance = db.get_user(user_id)
    await update.message.reply_text(f"💰 Новый баланс: {new_balance[2]} PAK, {new_balance[3]} РУБ")
    context.user_data['waiting_for_bet'] = False

# ДУЭЛИ
async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚔️ ИСПОЛЬЗОВАНИЕ ДУЭЛИ:\n\n/duel @username [PAK] [РУБ]\n\nПример: /duel @ivan 100 50")
        return
    opponent_username = args[0].replace('@', '')
    try:
        bet_pak = int(args[1])
        bet_rub = int(args[2])
    except:
        await update.message.reply_text("❌ Ставки должны быть числами!")
        return
    challenger_data = db.get_user(user_id)
    if challenger_data[2] < bet_pak or challenger_data[3] < bet_rub:
        await update.message.reply_text("❌ Недостаточно средств!")
        return
    opponent = db.get_user_by_username(opponent_username)
    if not opponent:
        await update.message.reply_text(f"❌ Пользователь @{opponent_username} не найден!")
        return
    opponent_id = opponent[0]
    if opponent_id == user_id:
        await update.message.reply_text("❌ Нельзя вызвать себя!")
        return
    duel_id = db.create_duel(user_id, opponent_id, bet_pak, bet_rub)
    active_duels[opponent_id] = {'duel_id': duel_id, 'challenger_id': user_id, 'bet_pak': bet_pak, 'bet_rub': bet_rub}
    await update.message.reply_text(f"⚔️ Вы вызвали @{opponent_username} на дуэль!\n💰 Ставка: {bet_pak} PAK, {bet_rub} РУБ")
    try:
        await context.bot.send_message(chat_id=opponent_id, text=f"⚔️ Вас вызвали на дуэль!\n\n👤 Противник: @{update.effective_user.username or 'Игрок'}\n💰 Ставка: {bet_pak} PAK, {bet_rub} РУБ\n\n✅ /duel_accept - принять дуэль\n❌ /duel_cancel - отклонить")
    except:
        pass

async def duel_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_duels:
        await update.message.reply_text("❌ У вас нет активных приглашений на дуэль!")
        return
    duel_info = active_duels[user_id]
    challenger_id = duel_info['challenger_id']
    bet_pak = duel_info['bet_pak']
    bet_rub = duel_info['bet_rub']
    duel_id = duel_info['duel_id']
    acceptor_data = db.get_user(user_id)
    if acceptor_data[2] < bet_pak or acceptor_data[3] < bet_rub:
        await update.message.reply_text("❌ Недостаточно средств для дуэли!")
        del active_duels[user_id]
        return
    db.update_balance(challenger_id, -bet_pak, -bet_rub)
    db.update_balance(user_id, -bet_pak, -bet_rub)
    challenger_roll = random.randint(1, 6)
    acceptor_roll = random.randint(1, 6)
    if challenger_roll > acceptor_roll:
        winner_id = challenger_id
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        result_text = f"🎲 {challenger_roll} vs {acceptor_roll}\n🏆 ПОБЕДИЛ ВЫЗЫВАЮЩИЙ!"
    elif acceptor_roll > challenger_roll:
        winner_id = user_id
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        result_text = f"🎲 {challenger_roll} vs {acceptor_roll}\n🏆 ПОБЕДИЛ ПРИНЯВШИЙ!"
    else:
        db.update_balance(challenger_id, bet_pak, bet_rub)
        db.update_balance(user_id, bet_pak, bet_rub)
        result_text = f"🎲 {challenger_roll} vs {acceptor_roll}\n🤝 НИЧЬЯ! Ставки возвращены."
        db.complete_duel(duel_id, None)
        del active_duels[user_id]
        await update.message.reply_text(result_text)
        try:
            await context.bot.send_message(chat_id=challenger_id, text=result_text)
        except:
            pass
        return
    await update.message.reply_text(f"⚔️ РЕЗУЛЬТАТ ДУЭЛИ!\n\n{result_text}\n\n💰 Выигрыш: {bet_pak} PAK и {bet_rub} РУБ")
    try:
        await context.bot.send_message(chat_id=challenger_id, text=f"⚔️ РЕЗУЛЬТАТ ДУЭЛИ!\n\n{result_text}\n\n💰 {'Вы выиграли' if winner_id == challenger_id else 'Вы проиграли'} {bet_pak} PAK и {bet_rub} РУБ")
    except:
        pass
    db.complete_duel(duel_id, winner_id)
    del active_duels[user_id]

async def duel_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cancelled = False
    for opponent_id, duel_info in list(active_duels.items()):
        if duel_info['challenger_id'] == user_id:
            await update.message.reply_text("❌ Вы отменили дуэль")
            try:
                await context.bot.send_message(chat_id=opponent_id, text="❌ Противник отменил дуэль")
            except:
                pass
            del active_duels[opponent_id]
            cancelled = True
            break
    if not cancelled:
        await update.message.reply_text("❌ У вас нет активных дуэлей!")

# КЛАНЫ
async def clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    keyboard = [
        [InlineKeyboardButton("📋 Список кланов", callback_data="clan_list")],
        [InlineKeyboardButton("➕ Создать клан", callback_data="clan_create")],
        [InlineKeyboardButton("👥 Мой клан", callback_data="clan_my")],
        [InlineKeyboardButton("💰 Получить награду клана (2 PAK/час)", callback_data="clan_reward")],
    ]
    if user_data and user_data[9]:
        keyboard.append([InlineKeyboardButton("🚪 Покинуть клан", callback_data="clan_leave")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👥 УПРАВЛЕНИЕ КЛАНАМИ 👥\n\nНаграда: 2 PAK каждый час!", reply_markup=reply_markup)

async def clan_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_clans = db.get_clan_leaderboard(10)
    if not top_clans:
        await update.message.reply_text("🏰 Пока нет кланов!")
        return
    text = "🏆 ТОП КЛАНОВ ПО БОГАТСТВУ 🏆\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, clan in enumerate(top_clans):
        name, members, total_pak, total_rub, total_wealth = clan
        text += f"{medals[i]} {name}\n   👥 {members} участников\n   💎 {total_pak} PAK | 💵 {total_rub} РУБ\n   💰 Общая ценность: {total_wealth:.0f} PAK\n   ➖➖➖➖➖➖➖\n"
    await update.message.reply_text(text)

# ПОКУПКА И ВЫВОД
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ 2 рубля → 1 звезда", callback_data="buy_rub_for_stars")],
        [InlineKeyboardButton("💎 Купить PAK за звезды", callback_data="buy_pak_menu")],
        [InlineKeyboardButton("💵 Купить РУБ за звезды", callback_data="buy_rub_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⭐ ПОКУПКА ЗА ЗВЕЗДЫ ⭐\n\nКурс: 2 ₽ = 1 ⭐\n4 PAK = 1 ₽\n\nВыбери действие:", reply_markup=reply_markup)

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💸 ВЫВОД СРЕДСТВ 💸\n\n⚙️ Функция вывода средств находится в разработке!\n\nСкоро вы сможете выводить средства!\nСледите за обновлениями! 🔜")

# ТОП ИГРОКОВ
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = db.get_leaderboard(10)
    if not top_users:
        await update.message.reply_text("🏆 Пока нет игроков!")
        return
    text = "🏆 ТОП ИГРОКОВ ПО БОГАТСТВУ 🏆\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, user in enumerate(top_users):
        username, pak, rub, wealth = user
        text += f"{medals[i]} {username}: 💎{pak} PAK | 💵{rub} РУБ | 💰{wealth:.0f} PAK\n"
    await update.message.reply_text(text)

# GIVE (АДМИН)
async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Недостаточно прав!")
        return
    if len(context.args) == 0:
        db.update_balance(user_id, 10000, 1000)
        await update.message.reply_text("✅ Выдано себе: 10000 PAK и 1000 РУБ")
        return
    if len(context.args) < 3:
        await update.message.reply_text("❌ Использование: /give @username PAK РУБ")
        return
    username = context.args[0].replace('@', '')
    try:
        pak = int(context.args[1])
        rub = int(context.args[2])
    except:
        await update.message.reply_text("❌ Суммы должны быть числами!")
        return
    await update.message.reply_text(f"✅ Выдано {pak} PAK и {rub} РУБ пользователю @{username}")

# ОБРАБОТЧИК СООБЩЕНИЙ
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('creating_clan') == 'waiting_name':
        await clan_create_name(update, context)
        return
    elif context.user_data.get('creating_clan') == 'waiting_description':
        await clan_create_description(update, context)
        return
    if context.user_data.get('waiting_for_bet'):
        await handle_bet(update, context)
        return
    if update.message.text and update.message.text.startswith('/'):
        return
    user_id = update.effective_user.id
    user = update.effective_user
    db.register_user(user_id, user.username or str(user_id))
    if db.can_get_message_reward(user_id):
        if user.bio and "W1npakshambot" in user.bio:
            db.update_balance(user_id, MSG_REWARD, 0)
            db.update_message_time(user_id)
            await update.message.reply_text(f"💎 +{MSG_REWARD} PAK за сообщение!")

# ОБРАБОТЧИК CALLBACK
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "farm_collect":
        await farm_collect(update, context)
    elif data == "farm_upgrade":
        await farm_upgrade(update, context)
    elif data == "farm_stats":
        await farm_stats(update, context)
    elif data == "farm_leaderboard":
        await farm_leaderboard(update, context)
    elif data == "clan_list":
        await clan_list(update, context)
    elif data == "clan_create":
        await clan_create_start(update, context)
    elif data == "clan_my":
        await clan_my(update, context)
    elif data == "clan_leave":
        await clan_leave(update, context)
    elif data == "clan_reward":
        await clan_reward(update, context)
    elif data == "clan_back":
        await clan(update, context)
    elif data.startswith("clan_join_"):
        clan_id = int(data.replace("clan_join_", ""))
        await clan_join(update, context, clan_id)
    elif data.startswith("clan_requests_"):
        clan_id = int(data.replace("clan_requests_", ""))
        await clan_requests(update, context, clan_id)
    elif data.startswith("clan_accept_"):
        parts = data.split("_")
        request_id = int(parts[2])
        clan_id = int(parts[3])
        await clan_accept(update, context, request_id, clan_id)
    elif data.startswith("clan_reject_"):
        request_id = int(data.replace("clan_reject_", ""))
        await clan_reject(update, context, request_id)
    elif data.startswith("clan_kick_"):
        clan_id = int(data.replace("clan_kick_", ""))
        await clan_kick(update, context, clan_id)
    elif data.startswith("clan_kick_user_"):
        parts = data.split("_")
        clan_id = int(parts[3])
        user_id = int(parts[4])
        await clan_kick_user(update, context, clan_id, user_id)
    elif data.startswith("game_"):
        game = data.replace("game_", "")
        context.user_data['selected_game'] = game
        await query.edit_message_text(f"🎮 Выбрана игра: {game}\n\n💰 Введите ставку в формате: PAK РУБ\n\nПример: 100 50")
        context.user_data['waiting_for_bet'] = True

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ КЛАНОВ ====================
async def clan_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if user_data[9]:
        await update.callback_query.edit_message_text("❌ Вы уже состоите в клане!")
        return
    if user_data[2] < CLAN_CREATE_COST:
        await update.callback_query.edit_message_text(f"❌ Недостаточно PAK! Нужно {CLAN_CREATE_COST} PAK")
        return
    await update.callback_query.edit_message_text("🏰 Введите название клана:")
    context.user_data['creating_clan'] = 'waiting_name'

async def clan_create_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('creating_clan') == 'waiting_name':
        return
    name = update.message.text.strip()
    if len(name) < 3 or len(name) > 20:
        await update.message.reply_text("❌ Название должно быть от 3 до 20 символов!")
        return
    context.user_data['clan_name'] = name
    context.user_data['creating_clan'] = 'waiting_description'
    await update.message.reply_text("📝 Введите описание клана:")

async def clan_create_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('creating_clan') == 'waiting_description':
        return
    user_id = update.effective_user.id
    name = context.user_data['clan_name']
    description = update.message.text.strip()
    if len(description) > 200:
        await update.message.reply_text("❌ Описание слишком длинное (макс 200 символов)!")
        return
    db.update_balance(user_id, -CLAN_CREATE_COST, 0)
    clan_id = db.create_clan(name, description, user_id)
    if clan_id:
        await update.message.reply_text(f"✅ Клан '{name}' успешно создан!\n\n📝 Описание: {description}\n💰 Снято: {CLAN_CREATE_COST} PAK")
    else:
        db.update_balance(user_id, CLAN_CREATE_COST, 0)
        await update.message.reply_text("❌ Клан с таким названием уже существует!")
    context.user_data.pop('creating_clan', None)
    context.user_data.pop('clan_name', None)

async def clan_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clans = db.get_all_clans()
    if not clans:
        await update.callback_query.edit_message_text("❌ Нет созданных кланов!")
        return
    text = "🏰 ТОП КЛАНОВ ПО БОГАТСТВУ 🏰\n\n"
    keyboard = []
    for clan in clans:
        clan_id, name, description, members, wealth = clan
        text += f"🏰 {name}\n📝 {description[:50]}...\n👥 Участников: {members}\n💰 Богатство: {wealth:.0f} PAK\n➖➖➖➖➖➖➖\n"
        keyboard.append([InlineKeyboardButton(f"📩 Вступить в {name}", callback_data=f"clan_join_{clan_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def clan_join(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if user_data[9]:
        await update.callback_query.edit_message_text("❌ Вы уже состоите в клане!")
        return
    db.send_clan_request(clan_id, user_id)
    clan = db.get_clan_by_id(clan_id)
    owner_id = db.get_clan_owner(clan_id)
    await update.callback_query.edit_message_text(f"✅ Заявка на вступление в клан '{clan[1]}' отправлена!\nОжидайте подтверждения от лидера клана.")
    try:
        keyboard = [[InlineKeyboardButton("📋 Посмотреть заявки", callback_data=f"clan_requests_{clan_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=owner_id, text=f"👥 Новая заявка в клан '{clan[1]}' от @{update.effective_user.username or 'игрока'}!", reply_markup=reply_markup)
    except:
        pass

async def clan_my(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if not user_data[9]:
        await update.callback_query.edit_message_text("❌ Вы не состоите в клане!")
        return
    clan = db.get_clan_by_id(user_data[9])
    members = db.get_clan_members(user_data[9])
    total_wealth = db.get_clan_total_wealth(user_data[9])
    text = f"🏰 {clan[1]}\n📝 {clan[2]}\n👑 Лидер: @{db.get_user(clan[3])[1] if db.get_user(clan[3]) else 'Неизвестно'}\n👥 Участников: {len(members)}\n💰 Богатство клана: {total_wealth:.0f} PAK\n📅 Создан: {clan[4][:10]}\n\n👥 УЧАСТНИКИ:\n"
    for member in members:
        role_icon = "👑" if member[2] == "owner" else "👤"
        text += f"{role_icon} @{member[1]} | 💎{member[3]} PAK | 💵{member[4]} РУБ\n"
    keyboard = []
    if user_data[10] == 'owner':
        keyboard.append([InlineKeyboardButton("📋 Заявки", callback_data=f"clan_requests_{clan[0]}")])
        keyboard.append([InlineKeyboardButton("👋 Выгнать участника", callback_data=f"clan_kick_{clan[0]}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def clan_requests(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int):
    requests = db.get_clan_requests(clan_id)
    if not requests:
        await update.callback_query.edit_message_text("❌ Нет активных заявок!")
        return
    text = "📋 ЗАЯВКИ НА ВСТУПЛЕНИЕ 📋\n\n"
    keyboard = []
    for req in requests:
        req_id, user_id, username, created_at = req
        text += f"👤 @{username}\n📅 {created_at[:10]}\n\n"
        keyboard.append([InlineKeyboardButton(f"✅ Принять @{username}", callback_data=f"clan_accept_{req_id}_{clan_id}"), InlineKeyboardButton(f"❌ Отклонить", callback_data=f"clan_reject_{req_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_my")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def clan_accept(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int, clan_id: int):
    user_id = db.accept_clan_request(request_id, clan_id)
    if user_id:
        await update.callback_query.edit_message_text("✅ Заявка принята!")
        try:
            await context.bot.send_message(chat_id=user_id, text="🎉 Поздравляем! Вы приняты в клан!\n💰 Каждый час вы получаете 2 PAK!")
        except:
            pass
    else:
        await update.callback_query.edit_message_text("❌ Ошибка при принятии заявки!")

async def clan_reject(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    db.reject_clan_request(request_id)
    await update.callback_query.edit_message_text("✅ Заявка отклонена!")

async def clan_kick(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int):
    members = db.get_clan_members(clan_id)
    keyboard = []
    for member in members:
        if member[2] != 'owner':
            keyboard.append([InlineKeyboardButton(f"👋 Выгнать @{member[1]}", callback_data=f"clan_kick_user_{clan_id}_{member[0]}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_my")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Выберите участника для исключения:", reply_markup=reply_markup)

async def clan_kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int, user_id: int):
    db.kick_from_clan(clan_id, user_id)
    await update.callback_query.edit_message_text("✅ Участник исключен из клана!")

async def clan_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.remove_from_clan(user_id)
    await update.callback_query.edit_message_text("✅ Вы покинули клан!")

async def clan_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.get_clan_reward_available(user_id):
        await update.callback_query.edit_message_text("❌ Награду можно получать раз в час!")
        return
    db.give_clan_reward(user_id)
    db.update_clan_reward_time(user_id)
    user_data = db.get_user(user_id)
    await update.callback_query.edit_message_text(f"💰 Вы получили 2 PAK за участие в клане!\n💎 Новый баланс: {user_data[2]} PAK")

# ==================== ФОНОВАЯ ЗАДАЧА ====================
async def keep_alive():
    while True:
        await asyncio.sleep(600)
        now = datetime.now()
        print(f"🤖 Бот активен - {now.strftime('%H:%M:%S')}")

# ==================== ЗАПУСК ====================
async def main():
    print("🚀 Запуск бота W1nPAK...")
    await start_web_server()
    asyncio.create_task(keep_alive())
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("farm", farm))
    application.add_handler(CommandHandler("casino", casino))
    application.add_handler(CommandHandler("duel", duel))
    application.add_handler(CommandHandler("duel_accept", duel_accept))
    application.add_handler(CommandHandler("duel_cancel", duel_cancel))
    application.add_handler(CommandHandler("clan", clan))
    application.add_handler(CommandHandler("clan_leaderboard", clan_leaderboard))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("withdraw", withdraw))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("give", give))
    application.add_handler(CommandHandler("help", start))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ Бот успешно запущен и готов к работе!")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("🤖 Бот начал polling...")
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
            
