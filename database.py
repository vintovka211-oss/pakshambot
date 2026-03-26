import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                pak_balance INTEGER DEFAULT 0,
                rub_balance INTEGER DEFAULT 0,
                last_message_time TIMESTAMP,
                last_clan_reward TIMESTAMP,
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
        
        self.conn.commit()
    
    def register_user(self, user_id, username):
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, last_message_time, last_clan_reward)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, datetime.now(), datetime.now()))
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
    
    # ============ МЕТОДЫ ДЛЯ КЛАНОВ ============
    
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
        self.cursor.execute('SELECT clan_id, name, description, member_count FROM clans ORDER BY member_count DESC')
        return self.cursor.fetchall()
    
    def get_clan_by_id(self, clan_id):
        self.cursor.execute('SELECT * FROM clans WHERE clan_id = ?', (clan_id,))
        return self.cursor.fetchone()
    
    def get_clan_by_name(self, name):
        self.cursor.execute('SELECT * FROM clans WHERE name = ?', (name,))
        return self.cursor.fetchone()
    
    def get_clan_members(self, clan_id):
        self.cursor.execute('''
            SELECT user_id, username, clan_role FROM users 
            WHERE in_clan = ?
        ''', (clan_id,))
        return self.cursor.fetchall()
    
    def get_clan_owner(self, clan_id):
        self.cursor.execute('SELECT owner_id FROM clans WHERE clan_id = ?', (clan_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def send_clan_request(self, clan_id, user_id):
        # Проверяем, нет ли уже заявки
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
        
        # Обновляем статус заявки
        self.cursor.execute('''
            UPDATE clan_requests SET status = 'accepted' WHERE request_id = ?
        ''', (request_id,))
        
        # Добавляем пользователя в клан
        self.cursor.execute('''
            UPDATE users SET in_clan = ?, clan_role = 'member'
            WHERE user_id = ?
        ''', (clan_id, user_id))
        
        # Увеличиваем счетчик участников
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
        # Получаем текущий клан пользователя
        self.cursor.execute('SELECT in_clan FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            clan_id = result[0]
            # Уменьшаем счетчик участников
            self.cursor.execute('''
                UPDATE clans SET member
