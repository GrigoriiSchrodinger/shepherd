import sqlite3
from contextlib import closing

def init_db():
    with closing(sqlite3.connect('bot.db')) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                user_id TEXT PRIMARY KEY,
                rights TEXT NOT NULL,
                dates INTEGER NOT NULL,
                turnover_days_max INTEGER NOT NULL,
                revenue_min INTEGER NOT NULL,
                category TEXT NOT NULL
            )
        ''')
        conn.commit()