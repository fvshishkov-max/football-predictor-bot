# test_analyzer.py
"""
Тестирование улучшенного анализатора матчей
"""

from match_analyzer import MatchAnalyzer, MatchFilter
from models import Match, Team
import logging

logging.basicConfig(level=logging.INFO)

def test_analyzer():
    """Тестирует работу анализатора"""
    
    print("="*50)
    print("🔍 ТЕСТИРОВАНИЕ АНАЛИЗАТОРА")
    print("="*50)
    
    # Создаем тестовый матч
    match = Match(
        id=1,
        home_team=Team(id=1, name="Team A"),
        away_team=Team(id=2, name="Team B"),
        minute=65,
        home_score=1,
        away_score=0
    )
    
    # Тестовые статистики
    home_stats = {
        'xg': 1.2,
        'shots': 8,
        'shots_on_target': 4,
        'corners': 5,
        'dangerous_attacks': 15
    }
    
    away_stats = {
        'xg': 0.8,
        'shots': 5,
        'shots_on_target': 2,
        'corners': 3,
        'dangerous_attacks': 8
    }
    
    # Создаем анализатор
    analyzer = MatchAnalyzer()
    filter = MatchFilter()
    
    # Тест фильтрации
    print("\n1. ТЕСТ ФИЛЬТРАЦИИ:")
    should, reason = filter.should_analyze(match)
    print(f"   Решение: {should}")
    print(f"   Причина: {reason}")
    
    # Тест анализа
    print("\n2. ТЕСТ АНАЛИЗА:")
    result = analyzer.analyze_match_potential(
        match, home_stats, away_stats, None, None, None
    )
    
    print(f"   Общий счет: {result['total_score']:.2f}")
    print(f"   Уровень: {result['match_level']}")
    print(f"   Приоритет: {result['priority']}")
    print(f"   Рекомендация: {result['recommendation']}")
    
    print("\n3. ФАКТОРЫ:")
    for key, value in result['factors'].items():
        print(f"   {key}: {value:.2f}")
    
    print("\n" + "="*50)
    print("✅ ТЕСТ ЗАВЕРШЕН")
    print("="*50)

if __name__ == "__main__":
    test_analyzer()