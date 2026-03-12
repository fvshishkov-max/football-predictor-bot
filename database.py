# database.py
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    """Работа с базой данных SQLite"""
    
    def __init__(self, db_path: str = 'football.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализация таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица оповещений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    text TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def add_alert(self, match_id: int, alert_type: str, text: str):
        """Добавляет оповещение"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (match_id, timestamp, type, text)
                VALUES (?, ?, ?, ?)
            ''', (
                match_id,
                datetime.now().isoformat(),
                alert_type,
                text
            ))
            conn.commit()
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Получает последние оповещения"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM alerts 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append({
                    'id': row[0],
                    'match_id': row[1],
                    'timestamp': row[2],
                    'type': row[3],
                    'text': row[4]
                })
            return alerts