# team_form.py
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TeamFormAnalyzer:
    """Анализ формы команд на основе последних матчей"""
    
    def __init__(self, db_path: str = 'data/football.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Создает таблицу для хранения истории матчей, если её нет"""
        try:
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
                logger.info("✅ Таблица matches_history инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def save_match(self, match_id: int, home_id: int, away_id: int, 
                   home_score: int, away_score: int, match_date: datetime, 
                   league_id: int = None):
        """Сохраняет результат матча в историю"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO matches_history 
                    (match_id, home_team_id, away_team_id, home_score, away_score, match_date, league_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (match_id, home_id, away_id, home_score, away_score, 
                      match_date.isoformat(), league_id))
                conn.commit()
                logger.debug(f"💾 Матч {match_id} сохранен в историю")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения матча {match_id}: {e}")
    
    def get_team_form(self, team_id: int, days: int = 30, limit: int = 10) -> Dict:
        """
        Анализирует форму команды за последние N дней
        
        Args:
            team_id: ID команды
            days: период анализа в днях
            limit: максимальное количество матчей для анализа
            
        Returns:
            Dict с параметрами формы:
            - form: коэффициент формы (0-1)
            - avg_scored: среднее забитых голов
            - avg_conceded: среднее пропущенных голов
            - trend: тренд формы (1 - улучшение, 0 - стабильно, -1 - ухудшение)
            - matches_analyzed: количество проанализированных матчей
            - form_string: строка формы (WDLWW...)
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
                    logger.debug(f"Нет данных о форме для команды {team_id}")
                    return {
                        'form': 0.5,
                        'avg_scored': 1.0,
                        'avg_conceded': 1.0,
                        'trend': 0,
                        'matches_analyzed': 0,
                        'form_string': '',
                        'points_per_game': 1.0
                    }
                
                total_goals_scored = 0
                total_goals_conceded = 0
                total_points = 0
                form_chars = []
                
                for match in matches:
                    home_score, away_score, home_id, away_id, _ = match
                    is_home = (home_id == team_id)
                    
                    if is_home:
                        scored = home_score
                        conceded = away_score
                    else:
                        scored = away_score
                        conceded = home_score
                    
                    total_goals_scored += scored
                    total_goals_conceded += conceded
                    
                    if scored > conceded:
                        total_points += 3
                        form_chars.append('W')
                    elif scored == conceded:
                        total_points += 1
                        form_chars.append('D')
                    else:
                        form_chars.append('L')
                
                # Коэффициент формы (0-1)
                form = total_points / (len(matches) * 3)
                
                # Анализ тренда (последние 3 матча против предыдущих 3)
                trend = 0
                if len(matches) >= 6:
                    recent_points = 0
                    for i in range(3):
                        match = matches[i]
                        home_score, away_score, home_id, away_id, _ = match
                        is_home = (home_id == team_id)
                        if is_home:
                            scored, conceded = home_score, away_score
                        else:
                            scored, conceded = away_score, home_score
                        
                        if scored > conceded:
                            recent_points += 3
                        elif scored == conceded:
                            recent_points += 1
                    
                    older_points = 0
                    for i in range(3, 6):
                        match = matches[i]
                        home_score, away_score, home_id, away_id, _ = match
                        is_home = (home_id == team_id)
                        if is_home:
                            scored, conceded = home_score, away_score
                        else:
                            scored, conceded = away_score, home_score
                        
                        if scored > conceded:
                            older_points += 3
                        elif scored == conceded:
                            older_points += 1
                    
                    if recent_points > older_points:
                        trend = 1  # Улучшение
                    elif recent_points < older_points:
                        trend = -1  # Ухудшение
                
                return {
                    'form': round(form, 2),
                    'avg_scored': round(total_goals_scored / len(matches), 2),
                    'avg_conceded': round(total_goals_conceded / len(matches), 2),
                    'trend': trend,
                    'matches_analyzed': len(matches),
                    'form_string': ''.join(form_chars),
                    'points_per_game': round(total_points / len(matches), 2)
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения формы команды {team_id}: {e}")
            return {
                'form': 0.5,
                'avg_scored': 1.0,
                'avg_conceded': 1.0,
                'trend': 0,
                'matches_analyzed': 0,
                'form_string': '',
                'points_per_game': 1.0
            }
    
    def get_h2h_stats(self, team1_id: int, team2_id: int, limit: int = 10) -> Dict:
        """
        Анализирует историю личных встреч команд
        
        Returns:
            Dict с параметрами:
            - advantage: преимущество команды 1 (-1 до 1)
            - avg_goals: среднее голов в матче
            - team1_wins: количество побед команды 1
            - team2_wins: количество побед команды 2
            - draws: количество ничьих
            - last_result: результат последнего матча
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
                        'advantage': 0,
                        'avg_goals': 2.5,
                        'team1_wins': 0,
                        'team2_wins': 0,
                        'draws': 0,
                        'matches': 0,
                        'last_result': 'unknown'
                    }
                
                team1_wins = 0
                team2_wins = 0
                draws = 0
                total_goals = 0
                last_result = ''
                
                for match in matches:
                    home_score, away_score, home_id, away_id, _ = match
                    
                    if home_id == team1_id:
                        team1_score, team2_score = home_score, away_score
                    else:
                        team1_score, team2_score = away_score, home_score
                    
                    total_goals += team1_score + team2_score
                    
                    if team1_score > team2_score:
                        team1_wins += 1
                        if len(matches) == 1: last_result = 'W'
                    elif team1_score < team2_score:
                        team2_wins += 1
                        if len(matches) == 1: last_result = 'L'
                    else:
                        draws += 1
                        if len(matches) == 1: last_result = 'D'
                
                # Преимущество от -1 до 1
                advantage = (team1_wins - team2_wins) / len(matches) if matches else 0
                
                return {
                    'advantage': round(advantage, 2),
                    'avg_goals': round(total_goals / len(matches), 2),
                    'team1_wins': team1_wins,
                    'team2_wins': team2_wins,
                    'draws': draws,
                    'matches': len(matches),
                    'last_result': last_result
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения h2h статистики: {e}")
            return {
                'advantage': 0,
                'avg_goals': 2.5,
                'team1_wins': 0,
                'team2_wins': 0,
                'draws': 0,
                'matches': 0,
                'last_result': 'unknown'
            }
    
    def get_team_stats(self, team_id: int, season: str = None) -> Dict:
        """Получает общую статистику команды за сезон"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT 
                        COUNT(*) as total_matches,
                        SUM(CASE 
                            WHEN (home_team_id = ? AND home_score > away_score) OR
                                 (away_team_id = ? AND away_score > home_score) 
                            THEN 1 ELSE 0 END) as wins,
                        SUM(CASE 
                            WHEN (home_team_id = ? AND home_score < away_score) OR
                                 (away_team_id = ? AND away_score < home_score) 
                            THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) as draws,
                        SUM(CASE WHEN home_team_id = ? THEN home_score ELSE away_score END) as goals_scored,
                        SUM(CASE WHEN home_team_id = ? THEN away_score ELSE home_score END) as goals_conceded
                    FROM matches_history
                '''
                
                params = [team_id, team_id, team_id, team_id, team_id, team_id]
                
                if season:
                    start_date = f"{season}-01-01"
                    end_date = f"{int(season)+1}-01-01"
                    query += " WHERE match_date BETWEEN ? AND ?"
                    params.extend([start_date, end_date])
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                if result and result[0] > 0:
                    total, wins, losses, draws, scored, conceded = result
                    return {
                        'matches': total,
                        'wins': wins,
                        'losses': losses,
                        'draws': draws,
                        'win_rate': round(wins / total * 100, 1),
                        'avg_scored': round(scored / total, 2),
                        'avg_conceded': round(conceded / total, 2),
                        'goal_diff': scored - conceded
                    }
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики команды {team_id}: {e}")
        
        return {
            'matches': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'win_rate': 0,
            'avg_scored': 0,
            'avg_conceded': 0,
            'goal_diff': 0
        }