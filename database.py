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


_pending_edits = {}

def set_pending_edit(username: str, param: str, target: str):
    _pending_edits[username] = {"param": param, "target": target}

def get_pending_edit(username: str):
    return _pending_edits.get(username)

def clear_pending_edit(username: str):
    _pending_edits.pop(username, None)