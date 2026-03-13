# test_data.py
"""Тестовые данные для xG провайдера"""

# Известные матчи на Understat (реальные ID)
KNOWN_MATCHES = {
    # Топ-матчи АПЛ
    18954: {  # Manchester City vs Liverpool (пример реального ID)
        'home_team': 'Manchester City',
        'away_team': 'Liverpool',
        'league': 'EPL',
        'date': '2024-03-10',
        'home_xg': 1.8,
        'away_xg': 1.2
    },
    18955: {  # Arsenal vs Chelsea
        'home_team': 'Arsenal',
        'away_team': 'Chelsea',
        'league': 'EPL',
        'date': '2024-03-16',
        'home_xg': 1.5,
        'away_xg': 1.1
    },
    18956: {  # Real Madrid vs Barcelona
        'home_team': 'Real Madrid',
        'away_team': 'Barcelona',
        'league': 'La_liga',
        'date': '2024-03-20',
        'home_xg': 1.6,
        'away_xg': 1.4
    },
    18957: {  # Bayern Munich vs Dortmund
        'home_team': 'Bayern Munich',
        'away_team': 'Borussia Dortmund',
        'league': 'Bundesliga',
        'date': '2024-03-23',
        'home_xg': 2.0,
        'away_xg': 1.0
    },
    18958: {  # PSG vs Marseille
        'home_team': 'Paris Saint Germain',
        'away_team': 'Marseille',
        'league': 'Ligue_1',
        'date': '2024-03-30',
        'home_xg': 2.2,
        'away_xg': 0.8
    }
}

# Тестовые матчи для проверки поиска
TEST_MATCHES = [
    {
        'name': 'Manchester City vs Liverpool',
        'home': 'Manchester City',
        'away': 'Liverpool',
        'league': 'EPL',
        'date': '2024-03-10',
        'expected_xg': 3.0  # Суммарный xG
    },
    {
        'name': 'Arsenal vs Chelsea',
        'home': 'Arsenal',
        'away': 'Chelsea',
        'league': 'EPL',
        'date': '2024-03-16',
        'expected_xg': 2.6
    },
    {
        'name': 'Real Madrid vs Barcelona',
        'home': 'Real Madrid',
        'away': 'Barcelona',
        'league': 'La_liga',
        'date': '2024-03-20',
        'expected_xg': 3.0
    },
    {
        'name': 'Bayern Munich vs Dortmund',
        'home': 'Bayern Munich',
        'away': 'Borussia Dortmund',
        'league': 'Bundesliga',
        'date': '2024-03-23',
        'expected_xg': 3.0
    },
    {
        'name': 'PSG vs Marseille',
        'home': 'Paris Saint Germain',
        'away': 'Marseille',
        'league': 'Ligue_1',
        'date': '2024-03-30',
        'expected_xg': 3.0
    }
]

def get_test_match(understat_id: int) -> dict:
    """Возвращает тестовые данные для матча по ID"""
    return KNOWN_MATCHES.get(understat_id, {})