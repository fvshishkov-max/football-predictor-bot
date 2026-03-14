import sqlite3
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import os
import numpy as np

logger = logging.getLogger(__name__)

class TeamFormAnalyzer:
    """
    Класс для анализа формы футбольных команд на основе истории матчей.
    Использует SQLite для хранения данных о завершенных матчах.
    """
    
    def __init__(self, db_path: str = 'data/matches_history.db'):
        self.db_path = db_path
        self._init_db()
        logger.info(f"TeamFormAnalyzer инициализирован, БД: {db_path}")
    
    def _init_db(self):
        """Создает таблицу для хранения истории матчей с поддержкой xG"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем существование таблицы
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='matches_history'
                ''')
                
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    # Проверяем наличие колонки home_xg
                    cursor.execute('PRAGMA table_info(matches_history)')
                    columns = [col[1] for col in cursor.fetchall()]
                    
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
                else:
                    # Создаем таблицу с новыми колонками
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS matches_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            match_id INTEGER UNIQUE,
                            home_team_id INTEGER,
                            away_team_id INTEGER,
                            home_score INTEGER,
                            away_score INTEGER,
                            home_xg REAL DEFAULT 0,
                            away_xg REAL DEFAULT 0,
                            match_date TEXT,
                            league_id INTEGER,
                            league_level INTEGER DEFAULT 1,
                            processed INTEGER DEFAULT 0
                        )
                    ''')
                    logger.info("✅ Создана новая таблица matches_history")
                
                # Создаем таблицу для рейтингов команд
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS team_ratings (
                        team_id INTEGER PRIMARY KEY,
                        rating REAL DEFAULT 1500,
                        matches_played INTEGER DEFAULT 0,
                        last_updated TEXT
                    )
                ''')
                
                conn.commit()
                logger.info(f"✅ Таблицы инициализированы в {self.db_path}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def save_match(self, match_id: int, home_id: int, away_id: int, 
                   home_score: int, away_score: int, match_date: datetime, 
                   league_id: Optional[int] = None, home_xg: float = 0, 
                   away_xg: float = 0, league_level: int = 1):
        """
        Сохраняет информацию о завершенном матче в базу данных
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO matches_history 
                    (match_id, home_team_id, away_team_id, home_score, away_score, 
                     home_xg, away_xg, match_date, league_id, league_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match_id, home_id, away_id, home_score, away_score, 
                    home_xg, away_xg, match_date.isoformat(), league_id, league_level
                ))
                conn.commit()
                
                # Обновляем рейтинги команд после матча
                self._update_team_ratings(home_id, away_id, home_score, away_score, league_level)
                
                logger.debug(f"Матч {match_id} сохранен в историю")
        except Exception as e:
            logger.error(f"Ошибка сохранения матча {match_id}: {e}")
    
    def _update_team_ratings(self, home_id: int, away_id: int, 
                             home_score: int, away_score: int, league_level: int):
        """Обновляет рейтинги команд на основе результатов матча"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем текущие рейтинги
                cursor.execute('SELECT rating FROM team_ratings WHERE team_id = ?', (home_id,))
                home_rating_row = cursor.fetchone()
                home_rating = home_rating_row[0] if home_rating_row else 1500
                
                cursor.execute('SELECT rating FROM team_ratings WHERE team_id = ?', (away_id,))
                away_rating_row = cursor.fetchone()
                away_rating = away_rating_row[0] if away_rating_row else 1500
                
                # Рассчитываем ожидаемый результат
                expected_home = 1 / (1 + 10 ** ((away_rating - home_rating) / 400))
                expected_away = 1 - expected_home
                
                # Фактический результат
                if home_score > away_score:
                    actual_home = 1.0
                    actual_away = 0.0
                elif home_score < away_score:
                    actual_home = 0.0
                    actual_away = 1.0
                else:
                    actual_home = 0.5
                    actual_away = 0.5
                
                # Коэффициент K
                k_factor = 40 if league_level == 1 else 32
                
                # Обновляем рейтинги
                new_home_rating = home_rating + k_factor * (actual_home - expected_home)
                new_away_rating = away_rating + k_factor * (actual_away - expected_away)
                
                # Сохраняем новые рейтинги
                cursor.execute('''
                    INSERT OR REPLACE INTO team_ratings (team_id, rating, matches_played, last_updated)
                    VALUES (?, ?, COALESCE((SELECT matches_played FROM team_ratings WHERE team_id = ?), 0) + 1, ?)
                ''', (home_id, new_home_rating, home_id, datetime.now().isoformat()))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO team_ratings (team_id, rating, matches_played, last_updated)
                    VALUES (?, ?, COALESCE((SELECT matches_played FROM team_ratings WHERE team_id = ?), 0) + 1, ?)
                ''', (away_id, new_away_rating, away_id, datetime.now().isoformat()))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Ошибка обновления рейтингов: {e}")
    
    def get_team_rating(self, team_id: int) -> float:
        """
        Возвращает текущий рейтинг команды
        
        Args:
            team_id: ID команды
            
        Returns:
            float: Рейтинг команды (по умолчанию 1500)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT rating FROM team_ratings WHERE team_id = ?', (team_id,))
                row = cursor.fetchone()
                return row[0] if row else 1500
        except Exception as e:
            logger.error(f"Ошибка получения рейтинга команды {team_id}: {e}")
            return 1500
    
    def get_team_form(self, team_id: int, days: int = 60, limit: int = 10) -> Dict:
        """
        Анализирует форму команды за последние N дней с учетом весов и силы соперника
        
        Args:
            team_id: ID команды
            days: Количество дней для анализа
            limit: Максимальное количество матчей для анализа
            
        Returns:
            Dict с информацией о форме команды:
            - form: числовая оценка формы (0-1) с учетом весов
            - weighted_form: форма с учетом силы соперника
            - avg_scored: среднее количество забитых голов
            - avg_conceded: среднее количество пропущенных голов
            - avg_xg_for: средний xG за игру
            - avg_xg_against: средний xG против
            - trend: тренд формы (-1 падение, 0 стабильно, 1 рост)
            - matches_analyzed: количество проанализированных матчей
            - form_string: строковое представление формы (WDLWW)
            - points_per_game: среднее количество очков за матч
            - opponent_strength: средняя сила соперников
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT home_score, away_score, home_team_id, away_team_id, 
                           match_date, home_xg, away_xg, league_level
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
                total_xg_for = 0
                total_xg_against = 0
                total_points = 0
                total_opponent_rating = 0
                weighted_points = 0
                total_weight = 0
                form_chars = []
                
                # Анализируем каждый матч в обратном хронологическом порядке (от новых к старым)
                for i, (home_score, away_score, home_id, away_id, match_date, 
                        home_xg, away_xg, league_level) in enumerate(matches):
                    
                    # Вес матча: чем свежее, тем больше вес
                    days_ago = (datetime.now() - datetime.fromisoformat(match_date)).days
                    recency_weight = np.exp(-days_ago / 30)  # Экспоненциальное затухание
                    
                    # Вес на основе уровня лиги
                    league_weight = 1.5 if league_level == 1 else 1.0
                    
                    # Определяем, как сыграла наша команда
                    if home_id == team_id:
                        # Команда играла дома
                        scored = home_score
                        conceded = away_score
                        xg_for = home_xg or 0
                        xg_against = away_xg or 0
                        opponent_id = away_id
                        
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
                        xg_for = away_xg or 0
                        xg_against = home_xg or 0
                        opponent_id = home_id
                        
                        if away_score > home_score:
                            points = 3
                            form_chars.append('W')
                        elif away_score == home_score:
                            points = 1
                            form_chars.append('D')
                        else:
                            points = 0
                            form_chars.append('L')
                    
                    # Получаем рейтинг соперника
                    opponent_rating = self.get_team_rating(opponent_id)
                    
                    # Вес на основе силы соперника (игра против сильного соперника важнее)
                    strength_weight = opponent_rating / 1500  # Нормализуем относительно базового рейтинга
                    
                    # Общий вес для этого матча
                    match_weight = recency_weight * league_weight * strength_weight
                    
                    total_scored += scored
                    total_conceded += conceded
                    total_xg_for += xg_for
                    total_xg_against += xg_against
                    total_opponent_rating += opponent_rating
                    
                    # Взвешенные очки
                    weighted_points += points * match_weight
                    total_weight += match_weight
                
                # Рассчитываем средние показатели
                matches_count = len(matches)
                avg_scored = total_scored / matches_count
                avg_conceded = total_conceded / matches_count
                avg_xg_for = total_xg_for / matches_count if total_xg_for > 0 else 1.0
                avg_xg_against = total_xg_against / matches_count if total_xg_against > 0 else 1.0
                points_per_game = total_points / matches_count
                avg_opponent_rating = total_opponent_rating / matches_count
                
                # Взвешенная форма (с учетом силы соперника и свежести)
                weighted_form = weighted_points / (total_weight * 3) if total_weight > 0 else points_per_game / 3
                
                # Нормализуем форму от 0 до 1
                form = weighted_form
                
                # Определяем тренд (сравниваем первые 3 матча с последними 3)
                trend = 0
                if matches_count >= 6:
                    first_half = form_chars[:3]
                    second_half = form_chars[-3:]
                    
                    points_first = sum(3 if c == 'W' else 1 if c == 'D' else 0 for c in first_half)
                    points_second = sum(3 if c == 'W' else 1 if c == 'D' else 0 for c in second_half)
                    
                    if points_second > points_first + 2:
                        trend = 1  # Рост формы
                    elif points_second < points_first - 2:
                        trend = -1  # Падение формы
                
                form_string = ''.join(form_chars)
                
                logger.debug(f"Команда {team_id}: форма {form:.2f}, "
                           f"взвешенная {weighted_form:.2f}, матчей {matches_count}")
                
                return {
                    'form': round(form, 3),
                    'weighted_form': round(weighted_form, 3),
                    'avg_scored': round(avg_scored, 2),
                    'avg_conceded': round(avg_conceded, 2),
                    'avg_xg_for': round(avg_xg_for, 2),
                    'avg_xg_against': round(avg_xg_against, 2),
                    'trend': trend,
                    'matches_analyzed': matches_count,
                    'form_string': form_string,
                    'points_per_game': round(points_per_game, 2),
                    'opponent_strength': round(avg_opponent_rating, 0)
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
            'weighted_form': 0.5,
            'avg_scored': 1.0,
            'avg_conceded': 1.0,
            'avg_xg_for': 1.0,
            'avg_xg_against': 1.0,
            'trend': 0,
            'matches_analyzed': 0,
            'form_string': '',
            'points_per_game': 1.0,
            'opponent_strength': 1500
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
                    SELECT home_score, away_score, home_team_id, away_team_id, 
                           match_date, home_xg, away_xg
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
                        'team1_avg_xg': 0,
                        'team2_avg_xg': 0,
                        'last_result': None,
                        'trend': 0
                    }
                
                team1_wins = 0
                team2_wins = 0
                draws = 0
                team1_goals = 0
                team2_goals = 0
                team1_xg = 0
                team2_xg = 0
                
                for home_score, away_score, home_id, away_id, match_date, home_xg, away_xg in matches:
                    if home_id == team1_id:
                        # team1 дома, team2 в гостях
                        team1_goals += home_score
                        team2_goals += away_score
                        team1_xg += home_xg or 0
                        team2_xg += away_xg or 0
                        
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
                        team1_xg += away_xg or 0
                        team2_xg += home_xg or 0
                        
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
                
                # Определяем тренд в личных встречах
                matches_count = len(matches)
                trend = 0
                if matches_count >= 4:
                    last_two = matches[:2]
                    first_two = matches[-2:]
                    
                    last_two_points = 0
                    first_two_points = 0
                    
                    for match in last_two:
                        if (match[2] == team1_id and match[0] > match[1]) or \
                           (match[3] == team1_id and match[1] > match[0]):
                            last_two_points += 3
                        elif (match[2] == team1_id and match[0] == match[1]) or \
                             (match[3] == team1_id and match[1] == match[0]):
                            last_two_points += 1
                    
                    for match in first_two:
                        if (match[2] == team1_id and match[0] > match[1]) or \
                           (match[3] == team1_id and match[1] > match[0]):
                            first_two_points += 3
                        elif (match[2] == team1_id and match[0] == match[1]) or \
                             (match[3] == team1_id and match[1] == match[0]):
                            first_two_points += 1
                    
                    if last_two_points > first_two_points + 2:
                        trend = 1  # team1 улучшает результаты
                    elif last_two_points < first_two_points - 2:
                        trend = -1  # team1 ухудшает результаты
                
                return {
                    'matches_played': matches_count,
                    'team1_wins': team1_wins,
                    'team2_wins': team2_wins,
                    'draws': draws,
                    'team1_goals': team1_goals,
                    'team2_goals': team2_goals,
                    'team1_avg_goals': round(team1_goals / matches_count, 2),
                    'team2_avg_goals': round(team2_goals / matches_count, 2),
                    'team1_avg_xg': round(team1_xg / matches_count, 2),
                    'team2_avg_xg': round(team2_xg / matches_count, 2),
                    'last_result': last_result,
                    'trend': trend
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
                    SELECT home_score, away_score, home_xg, away_xg
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
                        'avg_home_xg': 1.3,
                        'avg_away_xg': 1.0,
                        'home_win_rate': 0.45,
                        'draw_rate': 0.25,
                        'away_win_rate': 0.30
                    }
                
                total_goals = 0
                home_goals = 0
                away_goals = 0
                home_xg_total = 0
                away_xg_total = 0
                home_wins = 0
                away_wins = 0
                draws = 0
                
                for home_score, away_score, home_xg, away_xg in matches:
                    total_goals += home_score + away_score
                    home_goals += home_score
                    away_goals += away_score
                    home_xg_total += home_xg or 0
                    away_xg_total += away_xg or 0
                    
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
                    'avg_home_xg': round(home_xg_total / matches_count, 2),
                    'avg_away_xg': round(away_xg_total / matches_count, 2),
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
                'avg_home_xg': 1.3,
                'avg_away_xg': 1.0,
                'home_win_rate': 0.45,
                'draw_rate': 0.25,
                'away_win_rate': 0.30,
                'error': str(e)
            }
    
    def get_team_performance_vs_top_teams(self, team_id: int, limit: int = 10) -> Dict:
        """
        Анализирует выступления команды против топ-соперников (рейтинг выше 1600)
        
        Args:
            team_id: ID команды
            limit: Максимальное количество матчей
            
        Returns:
            Dict со статистикой против топ-команд
        """
        try:
            # Получаем рейтинг команды
            team_rating = self.get_team_rating(team_id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT home_score, away_score, home_team_id, away_team_id, match_date
                    FROM matches_history 
                    WHERE (home_team_id = ? OR away_team_id = ?)
                    ORDER BY match_date DESC
                    LIMIT ?
                ''', (team_id, team_id, limit * 2))  # Берем больше для фильтрации
                
                matches = cursor.fetchall()
                
                if not matches:
                    return {
                        'matches_analyzed': 0,
                        'points_per_game': 1.0,
                        'avg_scored': 1.0,
                        'avg_conceded': 1.0,
                        'win_rate': 0.33
                    }
                
                vs_top_matches = []
                for match in matches:
                    home_score, away_score, home_id, away_id, match_date = match
                    
                    # Определяем соперника
                    opponent_id = away_id if home_id == team_id else home_id
                    opponent_rating = self.get_team_rating(opponent_id)
                    
                    # Топ-команды имеют рейтинг выше 1600
                    if opponent_rating > 1600:
                        vs_top_matches.append(match)
                        
                        if len(vs_top_matches) >= limit:
                            break
                
                if not vs_top_matches:
                    return {
                        'matches_analyzed': 0,
                        'points_per_game': 1.0,
                        'avg_scored': 1.0,
                        'avg_conceded': 1.0,
                        'win_rate': 0.33
                    }
                
                total_points = 0
                total_scored = 0
                total_conceded = 0
                
                for match in vs_top_matches:
                    home_score, away_score, home_id, away_id, match_date = match
                    
                    if home_id == team_id:
                        scored = home_score
                        conceded = away_score
                        
                        if home_score > away_score:
                            total_points += 3
                        elif home_score == away_score:
                            total_points += 1
                    else:
                        scored = away_score
                        conceded = home_score
                        
                        if away_score > home_score:
                            total_points += 3
                        elif away_score == home_score:
                            total_points += 1
                    
                    total_scored += scored
                    total_conceded += conceded
                
                matches_count = len(vs_top_matches)
                
                return {
                    'matches_analyzed': matches_count,
                    'points_per_game': round(total_points / matches_count, 2),
                    'avg_scored': round(total_scored / matches_count, 2),
                    'avg_conceded': round(total_conceded / matches_count, 2),
                    'win_rate': round(total_points / (matches_count * 3), 3)
                }
                
        except Exception as e:
            logger.error(f"Ошибка анализа выступлений против топ-команд: {e}")
            return {
                'matches_analyzed': 0,
                'points_per_game': 1.0,
                'avg_scored': 1.0,
                'avg_conceded': 1.0,
                'win_rate': 0.33
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
                    writer.writerow(['team_id', 'form', 'weighted_form', 'avg_scored', 
                                    'avg_conceded', 'avg_xg_for', 'avg_xg_against',
                                    'matches', 'form_string', 'points_per_game', 
                                    'opponent_strength'])
                    
                    for (team_id,) in teams:
                        form_data = self.get_team_form(team_id)
                        writer.writerow([
                            team_id,
                            form_data['form'],
                            form_data['weighted_form'],
                            form_data['avg_scored'],
                            form_data['avg_conceded'],
                            form_data['avg_xg_for'],
                            form_data['avg_xg_against'],
                            form_data['matches_analyzed'],
                            form_data['form_string'],
                            form_data['points_per_game'],
                            form_data['opponent_strength']
                        ])
                
                logger.info(f"📊 Статистика формы экспортирована в {filename}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта статистики: {e}")