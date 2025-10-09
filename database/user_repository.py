import sqlite3
from typing import Optional, Dict

class UserRepository:
    def __init__(self, db_path: str = 'bot.db'):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    rights TEXT NOT NULL,
                    dates INTEGER NOT NULL,
                    turnover_days_max INTEGER NOT NULL,
                    revenue_min INTEGER NOT NULL,
                    category TEXT NOT NULL
                )
            ''')

    def user_exists(self, username: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT 1 FROM users WHERE username = ?', 
            (username,)
        )
        return cursor.fetchone() is not None

    def add_user(self, user_data: Dict):
        query = '''
            INSERT OR REPLACE INTO users 
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (
            user_data['username'],
            user_data['rights'],
            user_data['dates'],
            user_data['turnover_days_max'],
            user_data['revenue_min'],
            user_data['category']
        ))
        self.conn.commit()

    def get_user(self, username: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE username = ?', 
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'username': row[0],
                'rights': row[1],
                'dates': row[2],
                'turnover_days_max': row[3],
                'revenue_min': row[4],
                'category': row[5]
            }
        return None