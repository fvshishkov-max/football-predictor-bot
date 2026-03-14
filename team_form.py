import sqlite3
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import os

logger = logging.getLogger(__name__)

class TeamFormAnalyzer:
    """
    Класс для анализа формы футбольных команд на основе истории матчей.
    Использует SQLite для хранения данных о завершенных матчах.
    """
    
    def __init__(self, db_path: str = 'data/matches_history.db'):
        """
        Инициализация анализатора формы
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self._init_db()
        logger.info(f"TeamFormAnalyzer инициализирован, БД: {db_path}")
    
    def _init_db(self):
        """Создает таблицу для хранения истории матчей, если её нет"""
        try:
            # Создаем директорию data, если её нет
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS matches_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_id INTEGER UNIQUE,
                        home_team_id INTEGER,
                        away_team_id INTEGER,
                        home_score INTEGER,
                        away_score INTEGER,
                        match_date TEXT,
                        league_id INTEGER,
                        processed INTEGER DEFAULT 0
                    )
                ''')
                conn.commit()
                logger.info(f"✅ Таблица matches_history инициализирована в {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def save_match(self, match_id: int, home_id: int, away_id: int, 
                   home_score: int, away_score: int, match_date: datetime, 
                   league_id: Optional[int] = None):
        """
        Сохраняет информацию о завершенном матче в базу данных
        
        Args:
            match_id: ID матча
            home_id: ID домашней команды
            away_id: ID гостевой команды
            home_score: Голы хозяев
            away_score: Голы гостей
            match_date: Дата матча
            league_id: ID лиги (опционально)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO matches_history 
                    (match_id, home_team_id, away_team_id, home_score, away_score, match_date, league_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match_id, home_id, away_id, home_score, away_score, 
                    match_date.isoformat(), league_id
                ))
                conn.commit()
                logger.debug(f"Матч {match_id} сохранен в историю")
        except Exception as e:
            logger.error(f"Ошибка сохранения матча {match_id}: {e}")
    
    def get_team_form(self, team_id: int, days: int = 30, limit: int = 10) -> Dict:
        """
        Анализирует форму команды за последние N дней
        
        Args:
            team_id: ID команды
            days: Количество дней для анализа
            limit: Максимальное количество матчей для анализа
            
        Returns:
            Dict с информацией о форме команды:
            - form: числовая оценка формы (0-1)
            - avg_scored: среднее количество забитых голов
            - avg_conceded: среднее количество пропущенных голов
            - trend: тренд формы (-1 падение, 0 стабильно, 1 рост)
            - matches_analyzed: количество проанализированных матчей
            - form_string: строковое представление формы (WDLWW)
            - points_per_game: среднее количество очков за матч
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT home_score, away_score, home_team_id, away_team_id, match_date
                    FROM matches_history 
                    WHERE (home_team_id = ? OR away_team_id = ?) 
                        AND match_date > ?
                    ORDER BY match_date DESC
                    LIMIT ?
                ''', (team_id, team_id, cutoff_date.isoformat(), limit))
                
                matches = cursor.fetchall()
                
                if not matches:
                    logger.debug(f"Нет данных о форме для команды {team_id}, используем значения по умолчанию")
                    return self._get_default_form()
                
                total_scored = 0
                total_conceded = 0
                total_points = 0
                form_chars = []
                
                # Анализируем каждый матч в обратном хронологическом порядке (от новых к старым)
                for home_score, away_score, home_id, away_id, match_date in matches:
                    if home_id == team_id:
                        # Команда играла дома
                        scored = home_score
                        conceded = away_score
                        
                        if home_score > away_score:
                            points = 3
                            form_chars.append('W')
                        elif home_score == away_score:
                            points = 1
                            form_chars.append('D')
                        else:
                            points = 0
                            form_chars.append('L')
                    else:
                        # Команда играла в гостях
                        scored = away_score
                        conceded = home_score
                        
                        if away_score > home_score:
                            points = 3
                            form_chars.append('W')
                        elif away_score == home_score:
                            points = 1
                            form_chars.append('D')
                        else:
                            points = 0
                            form_chars.append('L')
                    
                    total_scored += scored
                    total_conceded += conceded
                    total_points += points
                
                # Рассчитываем средние показатели
                matches_count = len(matches)
                avg_scored = total_scored / matches_count
                avg_conceded = total_conceded / matches_count
                points_per_game = total_points / matches_count
                
                # Нормализуем форму от 0 до 1
                # Используем points_per_game (максимум 3 очка за матч)
                form = points_per_game / 3.0
                
                # Определяем тренд (сравниваем первые 3 матча с последними 3)
                trend = 0
                if matches_count >= 6:
                    first_half = form_chars[:3]
                    second_half = form_chars[-3:]
                    
                    # Считаем очки в первой и второй половине
                    points_first = sum(3 if c == 'W' else 1 if c == 'D' else 0 for c in first_half)
                    points_second = sum(3 if c == 'W' else 1 if c == 'D' else 0 for c in second_half)
                    
                    if points_second > points_first + 2:
                        trend = 1  # Рост формы
                    elif points_second < points_first - 2:
                        trend = -1  # Падение формы
                
                form_string = ''.join(form_chars)
                
                logger.debug(f"Команда {team_id}: форма {form:.2f}, матчей {matches_count}, строка {form_string}")
                
                return {
                    'form': round(form, 3),
                    'avg_scored': round(avg_scored, 2),
                    'avg_conceded': round(avg_conceded, 2),
                    'trend': trend,
                    'matches_analyzed': matches_count,
                    'form_string': form_string,
                    'points_per_game': round(points_per_game, 2)
                }
                
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка SQLite при получении формы команды {team_id}: {e}")
            return self._get_default_form()
        except Exception as e:
            logger.error(f"❌ Ошибка получения формы команды {team_id}: {e}")
            return self._get_default_form()
    
    def _get_default_form(self) -> Dict:
        """Возвращает значения формы по умолчанию"""
        return {
            'form': 0.5,
            'avg_scored': 1.0,
            'avg_conceded': 1.0,
            'trend': 0,
            'matches_analyzed': 0,
            'form_string': '',
            'points_per_game': 1.0
        }
    
    def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 10) -> Dict:
        """
        Анализирует историю встреч между двумя командами
        
        Args:
            team1_id: ID первой команды
            team2_id: ID второй команды
            limit: Максимальное количество матчей для анализа
            
        Returns:
            Dict с информацией об истории встреч
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT home_score, away_score, home_team_id, away_team_id, match_date
                    FROM matches_history 
                    WHERE (home_team_id = ? AND away_team_id = ?) 
                       OR (home_team_id = ? AND away_team_id = ?)
                    ORDER BY match_date DESC
                    LIMIT ?
                ''', (team1_id, team2_id, team2_id, team1_id, limit))
                
                matches = cursor.fetchall()
                
                if not matches:
                    return {
                        'matches_played': 0,
                        'team1_wins': 0,
                        'team2_wins': 0,
                        'draws': 0,
                        'team1_goals': 0,
                        'team2_goals': 0,
                        'last_result': None
                    }
                
                team1_wins = 0
                team2_wins = 0
                draws = 0
                team1_goals = 0
                team2_goals = 0
                
                for home_score, away_score, home_id, away_id, match_date in matches:
                    if home_id == team1_id:
                        # team1 дома, team2 в гостях
                        team1_goals += home_score
                        team2_goals += away_score
                        
                        if home_score > away_score:
                            team1_wins += 1
                        elif home_score < away_score:
                            team2_wins += 1
                        else:
                            draws += 1
                    else:
                        # team2 дома, team1 в гостях
                        team1_goals += away_score
                        team2_goals += home_score
                        
                        if away_score > home_score:
                            team1_wins += 1
                        elif away_score < home_score:
                            team2_wins += 1
                        else:
                            draws += 1
                
                # Определяем последний результат
                last_match = matches[0]
                last_result = None
                
                if last_match[2] == team1_id:  # team1 дома
                    if last_match[0] > last_match[1]:
                        last_result = 'team1_win'
                    elif last_match[0] < last_match[1]:
                        last_result = 'team2_win'
                    else:
                        last_result = 'draw'
                else:  # team2 дома
                    if last_match[1] > last_match[0]:
                        last_result = 'team1_win'
                    elif last_match[1] < last_match[0]:
                        last_result = 'team2_win'
                    else:
                        last_result = 'draw'
                
                return {
                    'matches_played': len(matches),
                    'team1_wins': team1_wins,
                    'team2_wins': team2_wins,
                    'draws': draws,
                    'team1_goals': team1_goals,
                    'team2_goals': team2_goals,
                    'team1_avg_goals': round(team1_goals / len(matches), 2),
                    'team2_avg_goals': round(team2_goals / len(matches), 2),
                    'last_result': last_result
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения истории встреч {team1_id} vs {team2_id}: {e}")
            return {
                'matches_played': 0,
                'team1_wins': 0,
                'team2_wins': 0,
                'draws': 0,
                'team1_goals': 0,
                'team2_goals': 0,
                'error': str(e)
            }
    
    def get_league_statistics(self, league_id: int, days: int = 90) -> Dict:
        """
        Получает статистику по лиге
        
        Args:
            league_id: ID лиги
            days: Количество дней для анализа
            
        Returns:
            Dict со статистикой лиги
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT home_score, away_score
                    FROM matches_history 
                    WHERE league_id = ? AND match_date > ?
                ''', (league_id, cutoff_date.isoformat()))
                
                matches = cursor.fetchall()
                
                if not matches:
                    return {
                        'matches_analyzed': 0,
                        'avg_goals_per_match': 2.5,
                        'avg_home_goals': 1.4,
                        'avg_away_goals': 1.1,
                        'home_win_rate': 0.45,
                        'draw_rate': 0.25,
                        'away_win_rate': 0.30
                    }
                
                total_goals = 0
                home_goals = 0
                away_goals = 0
                home_wins = 0
                away_wins = 0
                draws = 0
                
                for home_score, away_score in matches:
                    total_goals += home_score + away_score
                    home_goals += home_score
                    away_goals += away_score
                    
                    if home_score > away_score:
                        home_wins += 1
                    elif home_score < away_score:
                        away_wins += 1
                    else:
                        draws += 1
                
                matches_count = len(matches)
                
                return {
                    'matches_analyzed': matches_count,
                    'avg_goals_per_match': round(total_goals / matches_count, 2),
                    'avg_home_goals': round(home_goals / matches_count, 2),
                    'avg_away_goals': round(away_goals / matches_count, 2),
                    'home_win_rate': round(home_wins / matches_count, 3),
                    'draw_rate': round(draws / matches_count, 3),
                    'away_win_rate': round(away_wins / matches_count, 3)
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики лиги {league_id}: {e}")
            return {
                'matches_analyzed': 0,
                'avg_goals_per_match': 2.5,
                'avg_home_goals': 1.4,
                'avg_away_goals': 1.1,
                'home_win_rate': 0.45,
                'draw_rate': 0.25,
                'away_win_rate': 0.30,
                'error': str(e)
            }
    
    def cleanup_old_matches(self, days: int = 365):
        """
        Удаляет старые матчи из базы данных
        
        Args:
            days: Максимальный возраст матчей в днях
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM matches_history 
                    WHERE match_date < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted = cursor.rowcount
                conn.commit()
                
                logger.info(f"Удалено {deleted} старых матчей (старше {days} дней)")
                
        except Exception as e:
            logger.error(f"Ошибка при очистке старых матчей: {e}")
    
    def get_teams_with_most_matches(self, limit: int = 20) -> List[Tuple[int, int]]:
        """
        Возвращает список команд с наибольшим количеством матчей в базе
        
        Args:
            limit: Максимальное количество команд
            
        Returns:
            List[Tuple[int, int]]: Список пар (team_id, matches_count)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT team_id, COUNT(*) as matches_count
                    FROM (
                        SELECT home_team_id as team_id FROM matches_history
                        UNION ALL
                        SELECT away_team_id as team_id FROM matches_history
                    )
                    GROUP BY team_id
                    ORDER BY matches_count DESC
                    LIMIT ?
                ''', (limit,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Ошибка получения списка команд: {e}")
            return []
    
    def export_form_stats(self, filename: str = 'data/form_stats.csv'):
        """Экспортирует статистику формы всех команд в CSV"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT home_team_id FROM matches_history
                    UNION
                    SELECT DISTINCT away_team_id FROM matches_history
                ''')
                teams = cursor.fetchall()
                
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['team_id', 'form', 'avg_scored', 'avg_conceded', 
                                    'matches', 'form_string', 'points_per_game'])
                    
                    for (team_id,) in teams:
                        form_data = self.get_team_form(team_id)
                        writer.writerow([
                            team_id,
                            form_data['form'],
                            form_data['avg_scored'],
                            form_data['avg_conceded'],
                            form_data['matches_analyzed'],
                            form_data['form_string'],
                            form_data['points_per_game']
                        ])
                
                logger.info(f"📊 Статистика формы экспортирована в {filename}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта статистики: {e}")