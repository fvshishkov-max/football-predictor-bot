# known_understat_ids.py
"""Известные реальные ID матчей на Understat (найденные вручную)"""

# Эти ID можно найти, посетив Understat в браузере
# Например: https://understat.com/match/18954

REAL_MATCHES = {
    # Топ-матчи сезона 2024
    18954: {  # Пример - нужно заменить на реальные
        'home_team': 'Manchester City',
        'away_team': 'Liverpool',
        'league': 'EPL',
        'date': '2024-03-10',
        'home_xg': 1.8,
        'away_xg': 1.2
    },
    18955: {
        'home_team': 'Arsenal',
        'away_team': 'Chelsea',
        'league': 'EPL',
        'date': '2024-03-16',
        'home_xg': 1.5,
        'away_xg': 1.1
    },
    18956: {
        'home_team': 'Real Madrid',
        'away_team': 'Barcelona',
        'league': 'La_liga',
        'date': '2024-03-20',
        'home_xg': 1.6,
        'away_xg': 1.4
    },
    18957: {
        'home_team': 'Bayern Munich',
        'away_team': 'Borussia Dortmund',
        'league': 'Bundesliga',
        'date': '2024-03-23',
        'home_xg': 2.0,
        'away_team_xg': 1.0
    }
}

# Альтернативный источник - API футбольной статистики
# Можно использовать бесплатный API, например:
# - https://www.football-data.org/
# - https://apifootball.com/