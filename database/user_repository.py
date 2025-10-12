import sqlite3
from typing import Optional, Dict


class UserRepository:
    def __init__(self, db_path: str = 'bot.db'):
        self.conn = sqlite3.connect(db_path)
        self._create_table()
        self._pending_edits = {}

    def _create_table(self):
        """Создаём таблицу с новыми полями percent и access_until"""
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    rights TEXT NOT NULL,
                    dates INTEGER NOT NULL,
                    turnover_days_max INTEGER NOT NULL,
                    revenue_min INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    percent REAL DEFAULT 0,
                    access_until TEXT DEFAULT NULL
                )
            ''')

        # ✅ Добавляем дефолтного пользователя, если его нет
        if not self.user_exists("ScrodingerGrigorii"):
            default_user = {
                "username": "ScrodingerGrigorii",
                "rights": "root",
                "dates": 30,
                "turnover_days_max": 30,
                "revenue_min": 300000,
                "category": "Женщинам",
                "percent": 20.0,
                "access_until": "31.12.2099"
            }
            self.add_user(default_user)

    def user_exists(self, username: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
        return cursor.fetchone() is not None

    def add_user(self, user_data: Dict):
        query = '''
            INSERT OR REPLACE INTO users 
            (username, rights, dates, turnover_days_max, revenue_min, category, percent, access_until)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (
            user_data['username'],
            user_data['rights'],
            user_data['dates'],
            user_data['turnover_days_max'],
            user_data['revenue_min'],
            user_data['category'],
            user_data.get('percent', 0),
            user_data.get('access_until', None)
        ))
        self.conn.commit()

    def get_user(self, username: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        if row:
            return {
                'username': row[0],
                'rights': row[1],
                'dates': row[2],
                'turnover_days_max': row[3],
                'revenue_min': row[4],
                'category': row[5],
                'percent': row[6],
                'access_until': row[7]
            }
        return None

    # ✅ Методы для работы с редактированием
    def set_pending_edit(self, username: str, param: str, target: str):
        self._pending_edits[username] = {"param": param, "target": target}

    def get_pending_edit(self, username: str):
        return self._pending_edits.get(username)

    def clear_pending_edit(self, username: str):
        self._pending_edits.pop(username, None)

    def update_user_param(self, username: str, param: str, value):
        """Обновление конкретного параметра пользователя в БД"""
        if not self.user_exists(username):
            raise ValueError("Пользователь не найден")
        self._update_field(username, param, value)

    def _update_field(self, username: str, field: str, value):
        with self.conn:
            self.conn.execute(
                f'UPDATE users SET {field} = ? WHERE username = ?',
                (value, username)
            )
