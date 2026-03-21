# advanced_match_analyzer.py
"""
Улучшенный анализатор матчей с учетом времени гола
"""

import json
import sqlite3
from datetime import datetime
from collections import defaultdict
import numpy as np

class AdvancedMatchAnalyzer:
    """
    Анализирует матчи с учетом времени гола
    Статистика считается только после забитого мяча
    """
    
    def __init__(self):
        self.goal_data = []  # Данные о голах
        self.match_data = {}  # Данные о матчах
        self.load_historical_data()
    
    def load_historical_data(self):
        """Загружает исторические данные из базы и JSON"""
        
        # Загружаем из predictions.json
        try:
            with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                predictions = data.get('predictions', [])
                
                # Собираем данные о голах
                for pred in predictions:
                    if pred.get('was_correct', False):
                        self.goal_data.append({
                            'minute': pred.get('minute', 0),
                            'confidence': pred.get('confidence_level', 'MEDIUM'),
                            'probability': pred.get('goal_probability', 0),
                            'home_team': pred.get('home_team'),
                            'away_team': pred.get('away_team')
                        })
                print(f"✅ Загружено {len(self.goal_data)} голов из predictions.json")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки: {e}")
        
        # Загружаем из базы данных матчей
        try:
            conn = sqlite3.connect('data/history/matches_history.db')
            cursor = conn.cursor()
            
            # Проверяем наличие таблицы с голами
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                if 'goal' in table_name.lower() or 'event' in table_name.lower():
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()
                    if rows:
                        print(f"✅ Найдена таблица {table_name} с данными о голах")
            
            conn.close()
        except Exception as e:
            print(f"⚠️ База данных не найдена: {e}")
    
    def analyze_match_timeline(self, match_id: int, events: list):
        """
        Анализирует временную линию матча
        events: список событий с минутами и типами
        """
        
        timeline = {
            'total_goals': 0,
            'goals_by_minute': [],
            'pre_goal_stats': [],  # Статистика до первого гола
            'post_goal_stats': [],  # Статистика после голов
            'intervals': []  # Интервалы между голами
        }
        
        goals = [e for e in events if e.get('type') == 'goal']
        goals.sort(key=lambda x: x['minute'])
        
        timeline['total_goals'] = len(goals)
        timeline['goals_by_minute'] = [g['minute'] for g in goals]
        
        # Интервалы между голами
        for i in range(1, len(goals)):
            interval = goals[i]['minute'] - goals[i-1]['minute']
            timeline['intervals'].append(interval)
        
        return timeline
    
    def get_goal_probability_by_context(self, minute: int, score: str, possession: float, shots: int) -> float:
        """
        Рассчитывает вероятность гола на основе контекста
        Учитывает:
        - Текущий счет
        - Владение мячом
        - Количество ударов
        - Время матча
        - Количество уже забитых голов
        """
        
        # Базовые факторы
        time_factor = self._get_time_factor(minute)
        score_factor = self._get_score_factor(score)
        possession_factor = possession / 100
        shots_factor = min(shots / 15, 1.0)
        
        # Комбинированный счет
        probability = (
            time_factor * 0.30 +
            score_factor * 0.25 +
            possession_factor * 0.25 +
            shots_factor * 0.20
        )
        
        return min(0.95, max(0.05, probability))
    
    def _get_time_factor(self, minute: int) -> float:
        """Фактор времени на основе исторических данных"""
        if minute < 15:
            return 0.70
        elif minute < 30:
            return 0.75
        elif minute < 45:
            return 0.80
        elif minute < 60:
            return 0.85
        elif minute < 75:
            return 0.90
        elif minute < 90:
            return 1.00
        else:
            return 1.10
    
    def _get_score_factor(self, score: str) -> float:
        """Фактор счета"""
        try:
            home, away = map(int, score.split(':'))
            diff = abs(home - away)
            
            if diff == 0:
                return 1.20  # Ничья - высокая вероятность
            elif diff == 1:
                return 1.00  # Минимальное преимущество
            elif diff == 2:
                return 0.70  # Среднее преимущество
            else:
                return 0.40  # Большое преимущество
        except:
            return 1.00
    
    def get_statistics_report(self):
        """Возвращает статистический отчет"""
        
        if not self.goal_data:
            return "❌ Нет данных для анализа"
        
        # Статистика по минутам
        minute_distribution = defaultdict(int)
        for goal in self.goal_data:
            minute = goal['minute']
            minute_distribution[minute] += 1
        
        # Периоды
        periods = {
            '0-15': (0, 15), '15-30': (15, 30), '30-45': (30, 45),
            '45-60': (45, 60), '60-75': (60, 75), '75-90': (75, 90),
            '90+': (90, 120)
        }
        
        period_goals = defaultdict(int)
        for minute, count in minute_distribution.items():
            for period, (start, end) in periods.items():
                if start <= minute < end:
                    period_goals[period] += count
                    break
        
        total_goals = len(self.goal_data)
        
        report = []
        report.append("="*60)
        report.append("📊 АНАЛИЗ ВРЕМЕНИ ГОЛОВ (ТОЛЬКО ЗАБИТЫЕ)")
        report.append("="*60)
        report.append(f"\n📈 Всего голов в истории: {total_goals}")
        report.append(f"📊 Среднее количество голов: {total_goals / len(self.goal_data):.2f}" if self.goal_data else "Нет данных")
        
        report.append("\n⏱ РАСПРЕДЕЛЕНИЕ ПО ПЕРИОДАМ:")
        report.append("-"*40)
        
        for period in periods.keys():
            count = period_goals.get(period, 0)
            percent = (count / total_goals * 100) if total_goals > 0 else 0
            bar = '█' * int(percent / 2)
            report.append(f"  {period}: {count:3d} голов ({percent:5.1f}%) {bar}")
        
        # Самые опасные минуты
        report.append("\n🔥 ТОП-10 МИНУТ ПО КОЛИЧЕСТВУ ГОЛОВ:")
        report.append("-"*40)
        
        top_minutes = sorted(minute_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
        for minute, count in top_minutes:
            percent = (count / total_goals * 100) if total_goals > 0 else 0
            report.append(f"  {minute:2d}' - {count} голов ({percent:.1f}%)")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)
    
    def analyze_live_match(self, match_data):
        """
        Анализирует live-матч с учетом текущего состояния
        Возвращает вероятность гола в следующем отрезке
        """
        
        minute = match_data.get('minute', 0)
        score = match_data.get('score', '0:0')
        possession = match_data.get('possession', 50)
        shots = match_data.get('shots', 0)
        goals_so_far = match_data.get('goals', 0)
        
        # Получаем вероятность
        probability = self.get_goal_probability_by_context(minute, score, possession, shots)
        
        # Корректируем на основе уже забитых голов
        if goals_so_far >= 3:
            probability *= 0.7  # Много голов - снижаем вероятность
        
        # Корректируем на основе оставшегося времени
        if minute > 85:
            probability *= 1.2  # Концовка - повышаем вероятность
        
        return {
            'probability': min(0.95, probability),
            'confidence': self._get_confidence_level(probability),
            'factors': {
                'time': self._get_time_factor(minute),
                'score': self._get_score_factor(score),
                'possession': possession / 100,
                'shots': min(shots / 15, 1.0)
            }
        }
    
    def _get_confidence_level(self, probability: float) -> str:
        """Определяет уровень уверенности"""
        if probability >= 0.65:
            return "VERY_HIGH"
        elif probability >= 0.55:
            return "HIGH"
        elif probability >= 0.45:
            return "MEDIUM"
        elif probability >= 0.35:
            return "LOW"
        else:
            return "VERY_LOW"

def analyze_new_matches():
    """Анализирует новые матчи"""
    
    analyzer = AdvancedMatchAnalyzer()
    
    # Показываем отчет по историческим данным
    print(analyzer.get_statistics_report())
    
    # Пример анализа live-матча
    print("\n" + "="*60)
    print("🔴 ПРИМЕР АНАЛИЗА LIVE-МАТЧА")
    print("="*60)
    
    test_match = {
        'minute': 65,
        'score': '1:1',
        'possession': 55,
        'shots': 8,
        'goals': 2
    }
    
    result = analyzer.analyze_live_match(test_match)
    
    print(f"\n📊 Матч: {test_match['minute']}', счет {test_match['score']}")
    print(f"   Владение: {test_match['possession']}%, Удары: {test_match['shots']}")
    print(f"\n🎯 Вероятность гола: {result['probability']*100:.1f}%")
    print(f"🎯 Уверенность: {result['confidence']}")
    print("\n📈 Факторы:")
    for factor, value in result['factors'].items():
        print(f"   {factor}: {value:.2f}")

if __name__ == "__main__":
    analyze_new_matches()