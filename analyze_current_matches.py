# analyze_current_matches.py
"""
Анализ текущих матчей с учетом забитых голов
Запуск: python analyze_current_matches.py
"""

import requests
import json
from datetime import datetime
from advanced_match_analyzer import AdvancedMatchAnalyzer

def get_current_matches():
    """Получает текущие live-матчи (имитация)"""
    
    # Здесь должен быть реальный API запрос
    # Пока используем тестовые данные
    
    matches = [
        {
            'id': 1,
            'home': 'Arsenal',
            'away': 'Chelsea',
            'minute': 35,
            'score': '0:0',
            'possession': 52,
            'shots': 4,
            'goals': 0
        },
        {
            'id': 2,
            'home': 'Liverpool',
            'away': 'Man City',
            'minute': 68,
            'score': '1:1',
            'possession': 48,
            'shots': 7,
            'goals': 2
        },
        {
            'id': 3,
            'home': 'Barcelona',
            'away': 'Real Madrid',
            'minute': 82,
            'score': '2:0',
            'possession': 58,
            'shots': 11,
            'goals': 2
        }
    ]
    
    return matches

def main():
    print("="*60)
    print("🔍 АНАЛИЗ ТЕКУЩИХ МАТЧЕЙ")
    print("="*60)
    
    analyzer = AdvancedMatchAnalyzer()
    matches = get_current_matches()
    
    for match in matches:
        print(f"\n📋 МАТЧ: {match['home']} vs {match['away']}")
        print(f"   ⏱ {match['minute']}' | Счет: {match['score']}")
        print(f"   🎯 Владение: {match['possession']}% | Удары: {match['shots']}")
        
        # Анализируем матч
        result = analyzer.analyze_live_match(match)
        
        print(f"\n   📊 Вероятность гола в следующем отрезке: {result['probability']*100:.1f}%")
        print(f"   🎯 Уровень уверенности: {result['confidence']}")
        
        # Рекомендация
        if result['probability'] > 0.5:
            print(f"   🔴 РЕКОМЕНДАЦИЯ: СЛЕДИТЬ ЗА МАТЧЕМ!")
        elif result['probability'] > 0.4:
            print(f"   🟠 Рекомендация: обратить внимание")
        else:
            print(f"   🟢 Рекомендация: низкая вероятность")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()