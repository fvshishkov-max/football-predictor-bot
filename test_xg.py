# test_xg.py
import asyncio
import logging
from datetime import datetime, timedelta
from xg_provider import XGManager
from understat_search import UnderstatSearch
from models import Team, Match

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_xg_search():
    """Тестирует поиск матчей и получение xG"""
    
    print("🔍 Тестирование xG интеграции...")
    print("-" * 50)
    
    # Создаем менеджер
    xg_manager = XGManager()
    
    # Тестовые матчи (известные матчи на Understat)
    test_matches = [
        {
            'name': 'Manchester City vs Liverpool',
            'home': 'Manchester City',
            'away': 'Liverpool',
            'league': 'EPL',
            'date': datetime.now() - timedelta(days=7),  # Неделю назад
            'understat_id': 12345  # Пример ID
        },
        {
            'name': 'Real Madrid vs Barcelona',
            'home': 'Real Madrid',
            'away': 'Barcelona',
            'league': 'La_liga',
            'date': datetime.now() - timedelta(days=14),
            'understat_id': None  # Без ID - проверим поиск
        }
    ]
    
    for i, test in enumerate(test_matches, 1):
        print(f"\n📊 Тест {i}: {test['name']}")
        print(f"   Команды: {test['home']} vs {test['away']}")
        print(f"   Лига: {test['league']}")
        
        # Пробуем получить xG
        xg_data = await xg_manager.get_xg(
            match_id=i,
            understat_id=test['understat_id'],
            home_team=test['home'],
            away_team=test['away'],
            league=test['league'],
            match_date=test['date']
        )
        
        if xg_data:
            print(f"   ✅ xG получен!")
            print(f"   • xG дома: {xg_data.home_xg:.2f}")
            print(f"   • xG в гостях: {xg_data.away_xg:.2f}")
            print(f"   • Всего xG: {xg_data.total_xg:.2f}")
            print(f"   • Ударов: {xg_data.shots or 'N/A'}")
            print(f"   • Источник: {xg_data.source}")
            print(f"   • Understat ID: {xg_data.understat_id}")
        else:
            print(f"   ❌ xG не найден")
    
    # Статистика
    stats = xg_manager.get_stats()
    print("\n📈 Статистика xG менеджера:")
    print(f"   • Всего запросов: {stats['total_requests']}")
    print(f"   • Успешно: {stats['successful']}")
    print(f"   • Из кэша: {stats['cached']}")
    print(f"   • Поисков: {stats.get('search_requests', 0)}")
    print(f"   • Успешный поиск: {stats.get('successful_searches', 0)}")
    print(f"   • Успешность: {stats.get('success_rate', 0)}%")
    
    # Закрываем соединения
    await xg_manager.close()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")

async def test_live_match_simulation():
    """Симулирует live матч с xG"""
    
    print("\n📡 Симуляция live матча с xG...")
    print("-" * 50)
    
    from models import LiveStats
    from predictor import Predictor
    
    # Создаем тестовый матч
    match = Match(
        id=99999,
        home_team=Team(id=1, name="Arsenal", country_code="eng"),
        away_team=Team(id=2, name="Chelsea", country_code="eng"),
        league_id=2,
        league_name="Premier League",
        start_time=datetime.now(),
        understat_id=12346  # Пример ID
    )
    
    # Создаем статистику
    stats = LiveStats(
        minute=35,
        shots_home=8,
        shots_away=5,
        shots_ontarget_home=4,
        shots_ontarget_away=2,
        possession_home=55,
        possession_away=45,
        corners_home=3,
        corners_away=2,
        dangerous_attacks_home=12,
        dangerous_attacks_away=8
    )
    
    # Создаем предиктор
    predictor = Predictor()
    
    print(f"⚽ Матч: {match.home_team.name} vs {match.away_team.name}")
    print(f"⏱️ Минута: {stats.minute}'")
    print(f"📊 Статистика: {stats.total_shots} ударов, {stats.total_shots_ontarget} в створ")
    
    # Получаем анализ
    analysis = await predictor.analyze_live_match(match, stats)
    
    print(f"\n📊 Результат анализа:")
    print(f"   • Активность: {analysis.activity_level}")
    print(f"   • Потенциал: {analysis.attack_potential}")
    
    if analysis.xg_data:
        print(f"   • xG: {analysis.xg_data.home_xg:.2f}-{analysis.xg_data.away_xg:.2f}")
    
    if analysis.has_signal:
        signal = analysis.next_signal
        print(f"\n⚽ СИГНАЛ НА ГОЛ!")
        print(f"   • Время: ~{signal.predicted_minute}'")
        print(f"   • Вероятность: {signal.probability:.1f}%")
        print(f"   • {signal.description}")
    else:
        print(f"\n⏳ Нет сигналов")
    
    # Форматированное сообщение
    print("\n📱 Telegram сообщение:")
    print(analysis.format_telegram_message(match))
    
    await predictor.close()

async def main():
    """Главная функция тестирования"""
    
    print("🚀 Запуск тестирования xG интеграции")
    print("=" * 60)
    
    # Тест 1: Поиск и получение xG
    await test_xg_search()
    
    # Тест 2: Симуляция live матча
    await test_live_match_simulation()
    
    print("\n" + "=" * 60)
    print("✅ Все тесты завершены!")

if __name__ == "__main__":
    asyncio.run(main())