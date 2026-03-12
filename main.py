import time
import json
import numpy as np
from datetime import datetime
from football_analyzer import LiveFootballAnalyzer
from telegram_bot import FootballTelegramBot
import threading

# Конфигурация
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"  # Замените на ваш токен
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"  # Замените на ваш Chat ID

def simulate_match_with_learning():
    """Симуляция матча с самообучением"""
    
    # Инициализируем анализатор
    analyzer = LiveFootballAnalyzer()
    
    # Инициализируем Telegram бот
    bot = FootballTelegramBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=bot.run)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Данные матча LAFC vs Alajuelense
    match_data = {
        'match_id': 'LAFC_ALA_001',
        'home_team': 'Los Angeles FC',
        'away_team': 'LD Alajuelense',
        'current_minute': 1,
        'home_score': 0,
        'away_score': 0,
        'shots': '0-0',
        'shots_on_target': '0-0',
        'possession': '50%-50%',
        'corners': '0-0',
        'fouls': '0-0',
        'dangerous_attacks': '0-0'
    }
    
    # Реальные голы для проверки точности (для симуляции)
    actual_goals = []  # Здесь будут реальные минуты голов
    actual_goal_minutes = []
    
    print("\n🔴 НАЧАЛО АНАЛИЗА МАТЧА")
    print("="*70)
    print(f"🏆 {match_data['home_team']} vs {match_data['away_team']}")
    print("="*70)
    
    # Симулируем развитие матча
    for minute in [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]:
        
        # Обновляем статистику на основе реального сценария
        if minute == 10:
            match_data['shots'] = '2-1'
            match_data['dangerous_attacks'] = '3-1'
        elif minute == 15:
            match_data['shots_on_target'] = '1-0'
            match_data['possession'] = '55%-45%'
        elif minute == 20:
            match_data['shots'] = '4-2'
            match_data['corners'] = '2-1'
        elif minute == 26:  # ГОЛ!
            match_data['home_score'] = 1
            actual_goal_minutes.append(26)
            match_data['shots_on_target'] = '3-1'
            print(f"\n⚽️⚽️⚽️ ГОЛ! {match_data['home_team']} забивает на 26' минуте!")
        elif minute == 30:
            match_data['shots'] = '6-3'
            match_data['shots_on_target'] = '3-2'
            match_data['dangerous_attacks'] = '7-3'
        elif minute == 35:
            match_data['corners'] = '4-2'
        elif minute == 42:
            match_data['shots'] = '8-4'
            match_data['shots_on_target'] = '4-2'
        elif minute == 58:  # ВТОРОЙ ГОЛ
            match_data['away_score'] = 1
            actual_goal_minutes.append(58)
            print(f"\n⚽️⚽️⚽️ ГОЛ! {match_data['away_team']} забивает на 58' минуте!")
        elif minute == 65:
            match_data['shots'] = '10-6'
            match_data['shots_on_target'] = '5-3'
        elif minute == 78:
            match_data['corners'] = '6-4'
        elif minute == 84:  # ТРЕТИЙ ГОЛ
            match_data['home_score'] = 2
            actual_goal_minutes.append(84)
            print(f"\n⚽️⚽️⚽️ ГОЛ! {match_data['home_team']} забивает на 84' минуте!")
        
        match_data['current_minute'] = minute
        
        # Делаем анализ
        prediction = analyzer.analyze_live_match(match_data)
        analyzer.print_live_analysis(prediction)
        
        # Отправляем сигнал в Telegram если есть
        if prediction['goal_alert']:
            # Асинхронно отправляем сообщение
            asyncio_coroutine = bot.send_goal_alert(match_data, prediction)
            # В реальном проекте нужно правильно обработать асинхронность
        
        # Добавляем пример для обучения (в реальности нужно брать реальные данные)
        features = analyzer.extract_features(match_data)
        goal_happened = minute in actual_goal_minutes
        analyzer.add_training_example(features, minute if goal_happened else None, goal_happened)
        
        time.sleep(1)  # Пауза для наглядности
    
    # Финальный счет
    match_data['final_score'] = f"{match_data['home_score']}:{match_data['away_score']}"
    print(f"\n🏁 ФИНАЛЬНЫЙ СЧЕТ: {match_data['final_score']}")
    print(f"⚽️ Голы на минутах: {actual_goal_minutes}")
    
    # Обучаем модель на собранных данных
    print("\n🤖 ОБУЧЕНИЕ МОДЕЛИ...")
    analyzer.train_models()
    
    # Оцениваем точность прогнозов
    evaluation = analyzer.evaluate_prediction(
        match_data['match_id'],
        match_data['home_score'] + match_data['away_score'],
        actual_goal_minutes
    )
    
    # Отправляем финальный отчет в Telegram
    # asyncio_coroutine = bot.send_match_report(match_data, analyzer.match_history, evaluation)
    
    # Сохраняем результаты
    analyzer.save_goal_alerts('lafc_alajuelense_alerts.json')
    analyzer.save_match_history('lafc_alajuelense_analysis.json')
    analyzer.save_prediction_results('lafc_alajuelense_results.json')
    
    # Выводим статистику точности
    if evaluation['accuracy']:
        print(f"\n📊 ТОЧНОСТЬ ПРОГНОЗОВ:")
        print(f"  • Всего сигналов: {evaluation['accuracy'].get('total_alerts', 0)}")
        print(f"  • Точных сигналов: {evaluation['accuracy'].get('correct_alerts', 0)}")
        print(f"  • Точность: {evaluation['accuracy'].get('alerts_accuracy', 0)*100:.1f}%")
    
    return analyzer

def analyze_real_match():
    """Функция для анализа реального матча с API"""
    
    analyzer = LiveFootballAnalyzer()
    
    print("\n🔴 АНАЛИЗ РЕАЛЬНОГО МАТЧА")
    print("="*70)
    print("Для получения данных с API нужно настроить подключение")
    print("к источнику данных (например, API-football)")
    
    # Здесь будет код для получения данных с API
    # и их анализа в реальном времени
    
    return analyzer

if __name__ == "__main__":
    # Выбираем режим
    print("Выберите режим:")
    print("1. Симуляция матча с самообучением")
    print("2. Анализ реального матча (требуется API)")
    
    choice = input("Ваш выбор (1/2): ")
    
    if choice == "1":
        analyzer = simulate_match_with_learning()
    else:
        analyzer = analyze_real_match()