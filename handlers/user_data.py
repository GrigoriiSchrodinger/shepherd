import sqlite3
from typing import Optional, Dict

class UserDB:
    def __init__(self):
        self.conn = sqlite3.connect('bot.db')
    
    def add_user(self, user_data: Dict):
        query = '''
            INSERT OR REPLACE INTO user 
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (
            user_data['user_id'],
            user_data['rights'],
            user_data['dates'],
            user_data['turnover_days_max'],
            user_data['revenue_min'],
            user_data['category']
        ))
        self.conn.commit()
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'user_id': row[0],
                'rights': row[1],
                'dates': row[2],
                'turnover_days_max': row[3],
                'revenue_min': row[4],
                'category': row[5]
            }
        return None