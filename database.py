import sqlite3
from datetime import datetime, timedelta
import json

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
                in_clan INTEGER DEFAULT NULL,
                clan_role TEXT DEFAULT NULL,
                FOREIGN KEY (in_clan) REFERENCES clans(clan_id)
            )
        ''')
        
        # Таблица кланов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clans (
                clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                owner_id INTEGER,
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
                created_at TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def register_user(self, user_id, username):
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, last_message_time)
            VALUES (?, ?, ?)
        ''', (user_id, username, datetime.now()))
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
    
    def create_clan(self, name, description, owner_id):
        try:
            self.cursor.execute('''
                INSERT INTO clans (name, description, owner_id, created_at)
                VALUES (?, ?, ?, ?)
            ''', (name, description, owner_id, datetime.now()))
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
        self.cursor.execute('SELECT clan_id, name, description FROM clans')
        return self.cursor.fetchall()
    
    def get_clan_members(self, clan_id):
        self.cursor.execute('''
            SELECT user_id, username, clan_role FROM users 
            WHERE in_clan = ?
        ''', (clan_id,))
        return self.cursor.fetchall()
    
    def add_to_clan(self, user_id, clan_id):
        self.cursor.execute('''
            UPDATE users SET in_clan = ?, clan_role = 'member'
            WHERE user_id = ?
        ''', (clan_id, user_id))
        self.conn.commit()
    
    def remove_from_clan(self, user_id):
        self.cursor.execute('''
            UPDATE users SET in_clan = NULL, clan_role = NULL
            WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()
    
    def get_leaderboard(self, limit=10):
        self.cursor.execute('''
            SELECT username, pak_balance, rub_balance 
            FROM users 
            ORDER BY pak_balance DESC, rub_balance DESC 
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()
    
    def create_duel(self, challenger_id, opponent_id, bet_pak, bet_rub):
        self.cursor.execute('''
            INSERT INTO duels (challenger_id, opponent_id, bet_pak, bet_rub, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
        ''', (challenger_id, opponent_id, bet_pak, bet_rub, datetime.now()))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_pending_duel(self, user_id):
        self.cursor.execute('''
            SELECT * FROM duels 
            WHERE (opponent_id = ? OR challenger_id = ?) AND status = 'pending'
        ''', (user_id, user_id))
        return self.cursor.fetchone()
    
    def accept_duel(self, duel_id):
        self.cursor.execute('''
            UPDATE duels SET status = 'accepted' WHERE duel_id = ?
        ''', (duel_id,))
        self.conn.commit()
    
    def complete_duel(self, duel_id, winner_id):
        self.cursor.execute('''
            UPDATE duels SET status = 'completed' WHERE duel_id = ?
        ''', (duel_id,))
        self.conn.commit()
        
        # Получаем информацию о дуэли
        self.cursor.execute('SELECT * FROM duels WHERE duel_id = ?', (duel_id,))
        duel = self.cursor.fetchone()
        
        if winner_id == duel[1]:  # challenger выиграл
            self.update_balance(winner_id, duel[3], duel[4])
            loser_id = duel[2]
        else:
            self.update_balance(winner_id, duel[3], duel[4])
            loser_id = duel[1]
        
        self.update_balance(loser_id, -duel[3], -duel[4])
        return duel
    
    def get_clan_members_for_reward(self):
        # Получаем участников кланов для начисления награды
        self.cursor.execute('''
            SELECT user_id FROM users WHERE in_clan IS NOT NULL
        ''')
        return self.cursor.fetchall()
