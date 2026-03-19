# migrate_db.py
import sqlite3
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Обновляет структуру базы данных"""
    db_path = 'data/matches_history.db'
    
    if not os.path.exists(db_path):
        logger.info("База данных не существует, будет создана при первом запуске")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Получаем информацию о текущей структуре
            cursor.execute('PRAGMA table_info(matches_history)')
            columns = [col[1] for col in cursor.fetchall()]
            
            logger.info(f"Текущие колонки: {columns}")
            
            # Добавляем недостающие колонки
            if 'home_xg' not in columns:
                cursor.execute('ALTER TABLE matches_history ADD COLUMN home_xg REAL DEFAULT 0')
                logger.info("✅ Добавлена колонка home_xg")
            
            if 'away_xg' not in columns:
                cursor.execute('ALTER TABLE matches_history ADD COLUMN away_xg REAL DEFAULT 0')
                logger.info("✅ Добавлена колонка away_xg")
            
            if 'league_level' not in columns:
                cursor.execute('ALTER TABLE matches_history ADD COLUMN league_level INTEGER DEFAULT 1')
                logger.info("✅ Добавлена колонка league_level")
            
            conn.commit()
            logger.info("✅ Миграция базы данных завершена")
            
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")

if __name__ == "__main__":
    migrate_database()