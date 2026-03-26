import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Таблица пользователей (расширенная)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                pak_balance REAL DEFAULT 0.0,
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
        
        # Таблица кланов
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
        
        # Таблица заявок в кланы
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clan_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_id INTEGER,
                user_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP
            )
        ''')
        
        # Таблица дуэлей
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
        
        # Таблица покупок за звезды
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS star_purchases (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stars INTEGER,
                pak_gained INTEGER,
                rub_gained INTEGER,
                created_at TIMESTAMP
            )
        ''')
        
        # Таблица заявок на вывод
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawal_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount_rub INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    # ============ ОСНОВНЫЕ МЕТОДЫ ============
    
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
        self.cursor.execute('''
            SELECT last_message_time FROM users WHERE user_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        
        if result and result[0]:
            last_time = datetime.fromisoformat(result[0])
            if datetime.now() - last_time > timedelta(seconds=20):
                return True
        return True
    
    def update_message_time(self, user_id):
        self.cursor.execute('''
            UPDATE users SET last_message_time = ? WHERE user_id = ?
        ''', (datetime.now(), user_id))
        self.conn.commit()
    
    # ============ ФЕРМА ============
    
    def get_farm_info(self, user_id):
        self.cursor.execute('''
            SELECT farm_level, farm_rate, total_farm_earned, last_farm_collect 
            FROM users WHERE user_id = ?
        ''', (user_id,))
        return self.cursor.fetchone()
    
    def get_farm_available(self, user_id):
        self.cursor.execute('''
            SELECT last_farm_collect, farm_rate FROM users WHERE user_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        
        if result and result[0]:
            last_collect = datetime.fromisoformat(result[0])
            hours_passed = (datetime.now() - last_collect).total_seconds() / 3600
            if hours_passed >= 1:
                return True, int(hours_passed * result[1])  # Возвращаем True и количество PAK
        return False, 0
    
    def collect_farm(self, user_id):
        self.cursor.execute('''
            SELECT farm_rate, total_farm_earned, last_farm_collect FROM users WHERE user_id = ?
        ''', (user_id,))
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
        self.cursor.execute('''
            SELECT farm_level, farm_rate FROM users WHERE user_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        
        if result:
            level = result[0]
            current_rate = result[1]
            upgrade_cost = 100 + (level * 100)  # 100, 200, 300, 400...
            
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
        self.cursor.execute('''
            SELECT username, farm_level, farm_rate, total_farm_earned 
            FROM users 
            ORDER BY total_farm_earned DESC 
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()
    
    # ============ КЛАНЫ (ОБНОВЛЕННЫЕ) ============
    
    def create_clan(self, name, description, owner_id):
        try:
            self.cursor.execute('''
                INSERT INTO clans (name, description, owner_id, created_at, member_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, owner_id, datetime.now(), 1))
            clan_id = self.cursor.lastrowid
            
            self.cursor.execute('''
                UPDATE users SET in_clan = ?, clan_role = 'owner'
                WHERE user_id = ?
            ''', (clan_id, owner_id))
            self.conn.commit()
            return clan_id
        except sqlite3.IntegrityError:
            return None
    
    def get_all_clans(self):
        self.cursor.execute('''
            SELECT c.clan_id, c.name, c.description, c.member_count,
                   (SELECT SUM(u.pak_balance + u.rub_balance * 4) FROM users u WHERE u.in_clan = c.clan_id) as total_wealth
            FROM clans c
            ORDER BY total_wealth DESC
        ''')
        return self.cursor.fetchall()
    
    def get_clan_by_id(self, clan_id):
        self.cursor.execute('SELECT * FROM clans WHERE clan_id = ?', (clan_id,))
        return self.cursor.fetchone()
    
    def get_clan_by_name(self, name):
        self.cursor.execute('SELECT * FROM clans WHERE name = ?', (name,))
        return self.cursor.fetchone()
    
    def get_clan_members(self, clan_id):
        self.cursor.execute('''
            SELECT user_id, username, clan_role, pak_balance, rub_balance 
            FROM users 
            WHERE in_clan = ?
        ''', (clan_id,))
        return self.cursor.fetchall()
    
    def get_clan_owner(self, clan_id):
        self.cursor.execute('SELECT owner_id FROM clans WHERE clan_id = ?', (clan_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_clan_total_wealth(self, clan_id):
        self.cursor.execute('''
            SELECT SUM(pak_balance + rub_balance * 4) FROM users WHERE in_clan = ?
        ''', (clan_id,))
        result = self.cursor.fetchone()
        return result[0] if result[0] else 0
    
    def send_clan_request(self, clan_id, user_id):
        self.cursor.execute('''
            SELECT * FROM clan_requests WHERE clan_id = ? AND user_id = ? AND status = 'pending'
        ''', (clan_id, user_id))
        if self.cursor.fetchone():
            return False
        
        self.cursor.execute('''
            INSERT INTO clan_requests (clan_id, user_id, created_at)
            VALUES (?, ?, ?)
        ''', (clan_id, user_id, datetime.now()))
        self.conn.commit()
        return True
    
    def get_clan_requests(self, clan_id):
        self.cursor.execute('''
            SELECT r.request_id, r.user_id, u.username, r.created_at
            FROM clan_requests r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.clan_id = ? AND r.status = 'pending'
        ''', (clan_id,))
        return self.cursor.fetchall()
    
    def accept_clan_request(self, request_id, clan_id):
        self.cursor.execute('SELECT user_id FROM clan_requests WHERE request_id = ?', (request_id,))
        result = self.cursor.fetchone()
        if not result:
            return False
        
        user_id = result[0]
        
        self.cursor.execute('''
            UPDATE clan_requests SET status = 'accepted' WHERE request_id = ?
        ''', (request_id,))
        
        self.cursor.execute('''
            UPDATE users SET in_clan = ?, clan_role = 'member'
            WHERE user_id = ?
        ''', (clan_id, user_id))
        
        self.cursor.execute('''
            UPDATE clans SET member_count = member_count + 1 WHERE clan_id = ?
        ''', (clan_id,))
        
        self.conn.commit()
        return user_id
    
    def reject_clan_request(self, request_id):
        self.cursor.execute('''
            UPDATE clan_requests SET status = 'rejected' WHERE request_id = ?
        ''', (request_id,))
        self.conn.commit()
    
    def remove_from_clan(self, user_id):
        self.cursor.execute('SELECT in_clan FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            clan_id = result[0]
            self.cursor.execute('''
                UPDATE clans SET member_count = member_count - 1 WHERE clan_id = ?
            ''', (clan_id,))
        
        self.cursor.execute('''
            UPDATE users SET in_clan = NULL, clan_role = NULL
            WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()
    
    def kick_from_clan(self, clan_id, user_id):
        self.cursor.execute('''
            UPDATE users SET in_clan = NULL, clan_role = NULL
            WHERE user_id = ? AND in_clan = ?
        ''', (user_id, clan_id))
        
        self.cursor.execute('''
            UPDATE clans SET member_count = member_count - 1 WHERE clan_id = ?
        ''', (clan_id,))
        self.conn.commit()
    
    def get_clan_reward_available(self, user_id):
        self.cursor.execute('''
            SELECT last_clan_reward, in_clan FROM users WHERE user_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        
        if not result or not result[1]:
            return False
        
        last_reward = datetime.fromisoformat(result[0])
        if datetime.now() - last_reward > timedelta(hours=1):
            return True
        return False
    
    def update_clan_reward_time(self, user_id):
        self.cursor.execute('''
            UPDATE users SET last_clan_reward = ? WHERE user_id = ?
        ''', (datetime.now(), user_id))
        self.conn.commit()
    
    def give_clan_reward(self, user_id):
        self.cursor.execute('''
            UPDATE users SET pak_balance = pak_balance + ? WHERE user_id = ?
        ''', (2, user_id))
        self.conn.commit()
    
    def get_clan_leaderboard(self, limit=10):
        self.cursor.execute('''
            SELECT c.name, COUNT(u.user_id) as members, 
                   SUM(u.pak_balance) as total_pak,
                   SUM(u.rub_balance) as total_rub,
                   SUM(u.pak_balance + u.rub_balance * 4) as total_wealth
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
            VALUES (?, ?, ?, ?, 'pending', ?)
        ''', (challenger_id, opponent_id, bet_pak, bet_rub, datetime.now()))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def complete_duel(self, duel_id, winner_id):
        self.cursor.execute('''
            UPDATE duels SET status = 'completed', winner_id = ? WHERE duel_id = ?
        ''', (winner_id, duel_id))
        self.conn.commit()
    
    def get_user_by_username(self, username):
        self.cursor.execute('SELECT user_id, username FROM users WHERE username = ?', (username,))
        return self.cursor.fetchone()
    
    def get_leaderboard(self, limit=10):
        self.cursor.execute('''
            SELECT username, pak_balance, rub_balance, 
                   (pak_balance + rub_balance * 4) as total_wealth
            FROM users 
            ORDER BY total_wealth DESC 
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()
    
    # ============ ПОКУПКИ И ВЫВОД ============
    
    def add_star_purchase(self, user_id, stars, pak_gained, rub_gained):
        self.cursor.execute('''
            INSERT INTO star_purchases (user_id, stars, pak_gained, rub_gained, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, stars, pak_gained, rub_gained, datetime.now()))
        self.conn.commit()
    
    def add_withdrawal_request(self, user_id, amount_rub):
        self.cursor.execute('''
            INSERT INTO withdrawal_requests (user_id, amount_rub, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, amount_rub, datetime.now()))
        self.conn.commit()
        return self.cursor.lastrowid
