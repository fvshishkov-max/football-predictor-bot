# run_stats.py
"""
Ручной запуск статистики по всем матчам
Запуск: python run_stats.py
"""

import sys
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from telegram_bot import TelegramBot
    from config import TELEGRAM_TOKEN, CHANNEL_ID
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что вы запускаете скрипт из корневой папки проекта")
    sys.exit(1)

def load_predictions():
    """Загружает историю предсказаний"""
    files_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json',
        'predictions.json'
    ]
    
    for file_path in files_to_try:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ Загружено из {file_path}")
                return data
            except Exception as e:
                print(f"⚠️ Ошибка загрузки {file_path}: {e}")
    
    print("❌ Не найден файл с предсказаниями")
    return None
    
def ensure_was_correct(predictions):
    """Гарантирует наличие поля was_correct"""
    fixed = 0
    for pred in predictions:
        if 'was_correct' not in pred:
            # Если нет данных, считаем что не сбылось
            pred['was_correct'] = False
            fixed += 1
    return fixed

def calculate_stats(predictions_data):
    """Рассчитывает статистику по предсказаниям"""
    
    predictions = predictions_data.get('predictions', [])
    accuracy_stats = predictions_data.get('accuracy_stats', {})
    
    # Добавляем эту строку
    fixed = ensure_was_correct(predictions)
    if fixed > 0:
        print(f"⚠️ Добавлено поле was_correct для {fixed} предсказаний (по умолчанию False)")
    
    if not predictions and not accuracy_stats:
        print("❌ Нет данных для анализа")
        return None
    
    stats = {
        'total': 0,
        'correct': 0,
        'incorrect': 0,
        'accuracy': 0,
        'by_confidence': defaultdict(lambda: {'total': 0, 'correct': 0}),
        'by_minute': defaultdict(lambda: {'total': 0, 'correct': 0}),
        'by_league': defaultdict(lambda: {'total': 0, 'correct': 0}),
        'recent': [],
        'filtered': {
            'sent': 0,
            'filtered': 0,
            'min_prob': 0.46
        }
    }
    
    # Используем accuracy_stats если есть
    if accuracy_stats:
        stats['total'] = accuracy_stats.get('total_predictions', 0)
        stats['correct'] = accuracy_stats.get('correct_predictions', 0)
        stats['incorrect'] = accuracy_stats.get('incorrect_predictions', 0)
        stats['accuracy'] = accuracy_stats.get('accuracy_rate', 0) * 100
        stats['filtered']['sent'] = accuracy_stats.get('signals_sent_46plus', 0)
        stats['filtered']['filtered'] = accuracy_stats.get('signals_filtered_out', 0)
        
        # Статистика по уверенности
        by_confidence = accuracy_stats.get('by_confidence', {})
        for level, data in by_confidence.items():
            stats['by_confidence'][level] = data
    
    # Если есть отдельные предсказания, используем их для детальной статистики
    if predictions:
        for pred in predictions[-100:]:  # Последние 100
            if 'error' in pred and pred['error']:
                continue
            
            was_correct = pred.get('was_correct', False)
            confidence = pred.get('confidence_level', 'MEDIUM')
            minute = pred.get('minute', 0)
            league_id = pred.get('league_id')
            prob = pred.get('goal_probability', 0)
            
            # Добавляем в статистику по уверенности
            stats['by_confidence'][confidence]['total'] += 1
            if was_correct:
                stats['by_confidence'][confidence]['correct'] += 1
            
            # По минутам
            minute_range = (minute // 15) * 15
            minute_key = f"{minute_range}-{minute_range+15}"
            stats['by_minute'][minute_key]['total'] += 1
            if was_correct:
                stats['by_minute'][minute_key]['correct'] += 1
            
            # Для списка последних
            if len(stats['recent']) < 10:
                stats['recent'].append({
                    'home': pred.get('home_team', 'Unknown'),
                    'away': pred.get('away_team', 'Unknown'),
                    'prob': prob * 100,
                    'correct': was_correct,
                    'confidence': confidence
                })
    
    return stats

def format_stats_message(stats):
    """Форматирует статистику для отправки в Telegram"""
    
    if not stats:
        return "❌ Нет данных для статистики"
    
    lines = [
        "📊 **СТАТИСТИКА ПРОГНОЗОВ**",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"📈 **Всего прогнозов:** {stats['total']}",
        f"✅ **Совпало:** {stats['correct']}",
        f"❌ **Не совпало:** {stats['incorrect']}",
        f"🎯 **Общая точность:** {stats['accuracy']:.1f}%",
        "",
        "📊 **ПО УРОВНЯМ УВЕРЕННОСТИ:**"
    ]
    
    # Сортируем уровни уверенности
    confidence_order = ['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']
    confidence_names = {
        'VERY_HIGH': '🔴 ОЧЕНЬ ВЫСОКАЯ',
        'HIGH': '🟠 ВЫСОКАЯ',
        'MEDIUM': '🟡 СРЕДНЯЯ',
        'LOW': '🟢 НИЗКАЯ',
        'VERY_LOW': '⚪ ОЧЕНЬ НИЗКАЯ'
    }
    
    for level in confidence_order:
        if level in stats['by_confidence']:
            data = stats['by_confidence'][level]
            if data['total'] > 0:
                acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
                lines.append(f"  {confidence_names[level]}: {data['total']} шт, точность {acc:.1f}%")
    
    # Статистика по минутам
    if stats['by_minute']:
        lines.extend(["", "⏱ **ПО МИНУТАМ:**"])
        for minute_range in sorted(stats['by_minute'].keys()):
            data = stats['by_minute'][minute_range]
            if data['total'] > 0:
                acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
                lines.append(f"  {minute_range} мин: {data['total']} шт, точность {acc:.1f}%")
    
    # Фильтрация сигналов
    if stats['filtered']['sent'] > 0 or stats['filtered']['filtered'] > 0:
        lines.extend([
            "",
            f"🎯 **ФИЛЬТРАЦИЯ (> {stats['filtered']['min_prob']*100:.0f}%):**",
            f"  • Отправлено: {stats['filtered']['sent']}",
            f"  • Отфильтровано: {stats['filtered']['filtered']}"
        ])
        if stats['filtered']['sent'] + stats['filtered']['filtered'] > 0:
            filter_rate = (stats['filtered']['filtered'] / (stats['filtered']['sent'] + stats['filtered']['filtered'])) * 100
            lines.append(f"  • Процент отсеивания: {filter_rate:.1f}%")
    
    # Последние 10 прогнозов
    if stats['recent']:
        lines.extend(["", "📋 **ПОСЛЕДНИЕ 10 ПРОГНОЗОВ:**"])
        for pred in stats['recent']:
            mark = "✅" if pred['correct'] else "❌"
            lines.append(f"  {mark} {pred['home']} vs {pred['away']} - {pred['prob']:.1f}% ({pred['confidence']})")
    
    lines.extend([
        "",
        f"📅 Отчет сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    ])
    
    return "\n".join(lines)

def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    try:
        bot = TelegramBot(TELEGRAM_TOKEN, CHANNEL_ID)
        
        # Отправляем сообщение
        bot.send_message_to_channel(message)
        
        # Даем время на отправку
        import time
        time.sleep(2)
        
        print("✅ Сообщение отправлено в Telegram")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("📊 РУЧНОЙ ЗАПУСК СТАТИСТИКИ")
    print("="*60)
    
    # Загружаем данные
    print("\n1. Загрузка данных...")
    data = load_predictions()
    if not data:
        return
    
    # Рассчитываем статистику
    print("2. Расчет статистики...")
    stats = calculate_stats(data)
    if not stats:
        return
    
    # Форматируем сообщение
    print("3. Форматирование отчета...")
    message = format_stats_message(stats)
    
    # Показываем отчет в консоли
    print("\n" + "="*60)
    print("📋 ОТЧЕТ:")
    print("="*60)
    print(message)
    print("="*60)
    
    # Спрашиваем, отправлять ли в Telegram
    print("\n4. Отправка в Telegram...")
    send = input("📨 Отправить отчет в Telegram канал? (y/n): ").lower()
    
    if send == 'y' or send == 'yes':
        if send_telegram_message(message):
            print("✅ Готово!")
        else:
            print("❌ Не удалось отправить")
    else:
        print("⏹ Отправка отменена")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()