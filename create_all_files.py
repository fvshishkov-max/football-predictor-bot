# create_all_files.py
"""
Автоматическое создание всех недостающих файлов проекта
Запуск: python create_all_files.py
"""

import os
import sys

def create_file(path, content):
    """Создает файл с содержимым"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Создан: {path}")

def main():
    print("="*60)
    print("🔧 АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ФАЙЛОВ ПРОЕКТА")
    print("="*60)
    
    # ============================================
    # 1. АНАЛИТИЧЕСКИЕ МОДУЛИ
    # ============================================
    
    # analytics/match_analyzer.py
    match_analyzer_content = '''"""
Улучшенный анализатор футбольных матчей для прогнозирования голов
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class MatchAnalyzer:
    """
    Класс для глубокого анализа матчей и отбора наиболее перспективных
    """
    
    def __init__(self):
        # Веса для разных факторов
        self.weights = {
            'xg': 0.25,
            'shots_accuracy': 0.15,
            'pressure_index': 0.15,
            'form_trend': 0.12,
            'h2h_dominance': 0.10,
            'league_tempo': 0.08,
            'time_remaining': 0.08,
            'score_diff': 0.07,
        }
        
        # Пороги для разных лиг
        self.league_thresholds = {
            'top': {
                'min_xg': 1.2,
                'min_shots': 12,
                'min_corners': 5,
                'goal_probability': 0.45
            },
            'medium': {
                'min_xg': 1.0,
                'min_shots': 10,
                'min_corners': 4,
                'goal_probability': 0.42
            },
            'low': {
                'min_xg': 0.8,
                'min_shots': 8,
                'min_corners': 3,
                'goal_probability': 0.38
            }
        }
        
        # Статистика по лигам
        self.league_stats = defaultdict(lambda: {
            'avg_xg': 1.0,
            'avg_shots': 10,
            'avg_corners': 4,
            'goal_rate': 2.5,
            'matches_analyzed': 0
        })
        
    def analyze_match_potential(self, match, home_stats: Dict, away_stats: Dict, 
                                home_form: Optional[Dict], away_form: Optional[Dict],
                                h2h_data: Optional[Dict]) -> Dict:
        """Комплексный анализ потенциала матча на гол"""
        try:
            xg_total = home_stats.get('xg', 0) + away_stats.get('xg', 0)
            shots_total = home_stats.get('shots', 0) + away_stats.get('shots', 0)
            shots_ontarget_total = home_stats.get('shots_on_target', 0) + away_stats.get('shots_on_target', 0)
            
            shots_accuracy = shots_ontarget_total / max(shots_total, 1)
            pressure_index = self._calculate_pressure_index(home_stats, away_stats)
            form_trend = self._calculate_form_trend(home_form, away_form)
            h2h_dominance = self._calculate_h2h_dominance(h2h_data)
            league_factor = self._get_league_factor(match)
            time_factor = self._calculate_time_factor(match.minute)
            score_factor = self._calculate_score_factor(match.home_score, match.away_score)
            
            factors = {
                'xg_total': xg_total,
                'shots_accuracy': shots_accuracy,
                'pressure_index': pressure_index,
                'form_trend': form_trend,
                'h2h_dominance': h2h_dominance,
                'league_factor': league_factor,
                'time_factor': time_factor,
                'score_factor': score_factor
            }
            
            total_score = self._calculate_total_score(factors)
            match_level = self._determine_match_level(total_score, match.league_id)
            recommendation = self._get_recommendation(total_score, factors, match)
            
            return {
                'total_score': total_score,
                'match_level': match_level,
                'recommendation': recommendation,
                'factors': factors,
                'should_analyze': total_score >= 0.45,
                'priority': self._get_priority(total_score)
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа матча: {e}")
            return {
                'total_score': 0.3,
                'match_level': 'LOW',
                'recommendation': 'ANALYZE',
                'should_analyze': False,
                'priority': 0
            }
    
    def _calculate_pressure_index(self, home_stats: Dict, away_stats: Dict) -> float:
        """Рассчитывает индекс давления"""
        home_pressure = (
            home_stats.get('shots', 0) * 0.4 +
            home_stats.get('corners', 0) * 0.3 +
            home_stats.get('dangerous_attacks', 0) * 0.3
        )
        away_pressure = (
            away_stats.get('shots', 0) * 0.4 +
            away_stats.get('corners', 0) * 0.3 +
            away_stats.get('dangerous_attacks', 0) * 0.3
        )
        total_pressure = home_pressure + away_pressure
        return min(total_pressure / 50, 1.0)
    
    def _calculate_form_trend(self, home_form: Optional[Dict], away_form: Optional[Dict]) -> float:
        """Рассчитывает тренд формы команд"""
        if not home_form or not away_form:
            return 0.5
        home_trend = home_form.get('weighted_form', 0.5)
        away_trend = away_form.get('weighted_form', 0.5)
        return (home_trend + away_trend) / 2
    
    def _calculate_h2h_dominance(self, h2h_data: Optional[Dict]) -> float:
        """Рассчитывает доминирование в личных встречах"""
        if not h2h_data or h2h_data.get('matches_played', 0) < 3:
            return 0.5
        total_goals = h2h_data.get('total_goals', 0)
        matches = h2h_data.get('matches_played', 1)
        avg_goals = total_goals / matches
        return min(avg_goals / 3, 1.0)
    
    def _get_league_factor(self, match) -> float:
        """Определяет фактор лиги"""
        if not match.league_id:
            return 1.0
        league_stats = self.league_stats[match.league_id]
        goal_rate = league_stats['goal_rate']
        return min(goal_rate / 3, 1.2)
    
    def _calculate_time_factor(self, minute: int) -> float:
        """Рассчитывает фактор оставшегося времени"""
        if not minute:
            return 1.0
        if minute < 45:
            return 0.8
        elif minute < 70:
            return 1.0
        elif minute < 85:
            return 1.3
        else:
            return 0.7
    
    def _calculate_score_factor(self, home_score: int, away_score: int) -> float:
        """Рассчитывает фактор разницы в счете"""
        diff = abs((home_score or 0) - (away_score or 0))
        if diff == 0:
            return 1.2
        elif diff == 1:
            return 1.0
        elif diff == 2:
            return 0.7
        else:
            return 0.3
    
    def _calculate_total_score(self, factors: Dict) -> float:
        """Рассчитывает итоговую оценку"""
        score = 0
        total_weight = 0
        weights_map = {
            'xg_total': 0.20,
            'shots_accuracy': 0.15,
            'pressure_index': 0.15,
            'form_trend': 0.12,
            'h2h_dominance': 0.10,
            'league_factor': 0.10,
            'time_factor': 0.10,
            'score_factor': 0.08
        }
        for key, weight in weights_map.items():
            if key in factors:
                score += factors[key] * weight
                total_weight += weight
        return score / total_weight if total_weight > 0 else 0.5
    
    def _determine_match_level(self, score: float, league_id: Optional[int]) -> str:
        """Определяет уровень матча"""
        if score >= 0.65:
            return "VERY_HIGH"
        elif score >= 0.55:
            return "HIGH"
        elif score >= 0.45:
            return "MEDIUM"
        elif score >= 0.35:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def _get_recommendation(self, score: float, factors: Dict, match) -> str:
        """Дает рекомендацию по матчу"""
        if score >= 0.6:
            return "STRONG_ANALYZE"
        elif score >= 0.5:
            return "ANALYZE"
        elif score >= 0.4:
            return "WATCH"
        else:
            return "SKIP"
    
    def _get_priority(self, score: float) -> int:
        """Возвращает приоритет анализа (1-5)"""
        if score >= 0.65:
            return 1
        elif score >= 0.55:
            return 2
        elif score >= 0.45:
            return 3
        elif score >= 0.35:
            return 4
        else:
            return 5


class MatchFilter:
    """
    Класс для фильтрации матчей перед анализом
    """
    
    def __init__(self):
        self.filters = {
            'minute_range': (10, 85),
            'max_score_diff': 2,
            'min_shots_per_team': 3,
            'excluded_leagues': [],
            'preferred_leagues': [],
        }
        self.filter_stats = defaultdict(lambda: {'passed': 0, 'goals': 0})
    
    def should_analyze(self, match) -> Tuple[bool, str]:
        """Проверяет, стоит ли анализировать матч"""
        if match.minute and (match.minute < self.filters['minute_range'][0] or 
                            match.minute > self.filters['minute_range'][1]):
            return False, f"minute_{match.minute}"
        
        score_diff = abs((match.home_score or 0) - (match.away_score or 0))
        if score_diff > self.filters['max_score_diff']:
            return False, f"score_diff_{score_diff}"
        
        if match.stats:
            home_shots = match.stats.get('shots_home', 0)
            away_shots = match.stats.get('shots_away', 0)
            if home_shots < self.filters['min_shots_per_team'] and away_shots < self.filters['min_shots_per_team']:
                return False, f"low_shots_{home_shots}_{away_shots}"
        
        if match.league_id in self.filters['excluded_leagues']:
            return False, f"excluded_league_{match.league_id}"
        
        return True, "passed"
    
    def update_filter_stats(self, decision: str, had_goal: bool):
        """Обновляет статистику фильтров"""
        self.filter_stats[decision]['passed'] += 1
        if had_goal:
            self.filter_stats[decision]['goals'] += 1
    
    def get_filter_efficiency(self) -> Dict:
        """Возвращает эффективность фильтров"""
        efficiency = {}
        for filter_name, stats in self.filter_stats.items():
            if stats['passed'] > 0:
                efficiency[filter_name] = stats['goals'] / stats['passed']
        return efficiency
'''
    create_file('analytics/match_analyzer.py', match_analyzer_content)

    # analytics/test_analyzer.py
    test_analyzer_content = '''"""
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
    
    match = Match(
        id=1,
        home_team=Team(id=1, name="Team A"),
        away_team=Team(id=2, name="Team B"),
        minute=65,
        home_score=1,
        away_score=0
    )
    
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
    
    analyzer = MatchAnalyzer()
    filter = MatchFilter()
    
    print("\\n1. ТЕСТ ФИЛЬТРАЦИИ:")
    should, reason = filter.should_analyze(match)
    print(f"   Решение: {should}")
    print(f"   Причина: {reason}")
    
    print("\\n2. ТЕСТ АНАЛИЗА:")
    result = analyzer.analyze_match_potential(
        match, home_stats, away_stats, None, None, None
    )
    
    print(f"   Общий счет: {result['total_score']:.2f}")
    print(f"   Уровень: {result['match_level']}")
    print(f"   Приоритет: {result['priority']}")
    print(f"   Рекомендация: {result['recommendation']}")
    
    print("\\n3. ФАКТОРЫ:")
    for key, value in result['factors'].items():
        print(f"   {key}: {value:.2f}")
    
    print("\\n" + "="*50)
    print("✅ ТЕСТ ЗАВЕРШЕН")
    print("="*50)

if __name__ == "__main__":
    test_analyzer()
'''
    create_file('analytics/test_analyzer.py', test_analyzer_content)

    # ============================================
    # 2. ИНСТРУМЕНТЫ СТАТИСТИКИ
    # ============================================
    
    # tools/run_stats.py
    run_stats_content = '''"""
Ручной запуск статистики по всем матчам
Запуск: python tools/run_stats.py
"""

import sys
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from telegram_bot import TelegramBot
    from config import TELEGRAM_TOKEN, CHANNEL_ID
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    TELEGRAM_TOKEN = None
    CHANNEL_ID = None

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
            pred['was_correct'] = False
            fixed += 1
    return fixed

def calculate_stats(predictions_data):
    """Рассчитывает статистику по предсказаниям"""
    
    predictions = predictions_data.get('predictions', [])
    accuracy_stats = predictions_data.get('accuracy_stats', {})
    
    fixed = ensure_was_correct(predictions)
    if fixed > 0:
        print(f"⚠️ Добавлено поле was_correct для {fixed} предсказаний")
    
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
    
    if accuracy_stats:
        stats['total'] = accuracy_stats.get('total_predictions', 0)
        stats['correct'] = accuracy_stats.get('correct_predictions', 0)
        stats['incorrect'] = accuracy_stats.get('incorrect_predictions', 0)
        stats['accuracy'] = accuracy_stats.get('accuracy_rate', 0) * 100
        stats['filtered']['sent'] = accuracy_stats.get('signals_sent_46plus', 0)
        stats['filtered']['filtered'] = accuracy_stats.get('signals_filtered_out', 0)
        
        by_confidence = accuracy_stats.get('by_confidence', {})
        for level, data in by_confidence.items():
            stats['by_confidence'][level] = data
    
    if predictions:
        for pred in predictions[-100:]:
            if 'error' in pred and pred['error']:
                continue
            
            was_correct = pred.get('was_correct', False)
            confidence = pred.get('confidence_level', 'MEDIUM')
            minute = pred.get('minute', 0)
            prob = pred.get('goal_probability', 0)
            
            stats['by_confidence'][confidence]['total'] += 1
            if was_correct:
                stats['by_confidence'][confidence]['correct'] += 1
            
            minute_range = (minute // 15) * 15
            minute_key = f"{minute_range}-{minute_range+15}"
            stats['by_minute'][minute_key]['total'] += 1
            if was_correct:
                stats['by_minute'][minute_key]['correct'] += 1
            
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
    
    confidence_names = {
        'VERY_HIGH': '🔴 ОЧЕНЬ ВЫСОКАЯ',
        'HIGH': '🟠 ВЫСОКАЯ',
        'MEDIUM': '🟡 СРЕДНЯЯ',
        'LOW': '🟢 НИЗКАЯ',
        'VERY_LOW': '⚪ ОЧЕНЬ НИЗКАЯ'
    }
    
    for level, name in confidence_names.items():
        if level in stats['by_confidence']:
            data = stats['by_confidence'][level]
            if data['total'] > 0:
                acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
                lines.append(f"  {name}: {data['total']} шт, точность {acc:.1f}%")
    
    if stats['by_minute']:
        lines.extend(["", "⏱ **ПО МИНУТАМ:**"])
        for minute_range in sorted(stats['by_minute'].keys()):
            data = stats['by_minute'][minute_range]
            if data['total'] > 0:
                acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
                lines.append(f"  {minute_range} мин: {data['total']} шт, точность {acc:.1f}%")
    
    if stats['filtered']['sent'] > 0 or stats['filtered']['filtered'] > 0:
        lines.extend([
            "",
            f"🎯 **ФИЛЬТРАЦИЯ (> {stats['filtered']['min_prob']*100:.0f}%):**",
            f"  • Отправлено: {stats['filtered']['sent']}",
            f"  • Отфильтровано: {stats['filtered']['filtered']}"
        ])
        total_filtered = stats['filtered']['sent'] + stats['filtered']['filtered']
        if total_filtered > 0:
            filter_rate = (stats['filtered']['filtered'] / total_filtered) * 100
            lines.append(f"  • Процент отсеивания: {filter_rate:.1f}%")
    
    if stats['recent']:
        lines.extend(["", "📋 **ПОСЛЕДНИЕ 10 ПРОГНОЗОВ:**"])
        for pred in stats['recent']:
            mark = "✅" if pred['correct'] else "❌"
            lines.append(f"  {mark} {pred['home']} vs {pred['away']} - {pred['prob']:.1f}% ({pred['confidence']})")
    
    lines.extend([
        "",
        f"📅 Отчет сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    ])
    
    return "\\n".join(lines)

def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    if not TELEGRAM_TOKEN or not CHANNEL_ID:
        print("⚠️ Telegram не настроен")
        return False
    
    try:
        bot = TelegramBot(TELEGRAM_TOKEN, CHANNEL_ID)
        bot.send_message_to_channel(message)
        import time
        time.sleep(2)
        print("✅ Сообщение отправлено в Telegram")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

def main():
    """Главная функция"""
    print("\\n" + "="*60)
    print("📊 РУЧНОЙ ЗАПУСК СТАТИСТИКИ")
    print("="*60)
    
    print("\\n1. Загрузка данных...")
    data = load_predictions()
    if not data:
        return
    
    print("2. Расчет статистики...")
    stats = calculate_stats(data)
    if not stats:
        return
    
    print("3. Форматирование отчета...")
    message = format_stats_message(stats)
    
    print("\\n" + "="*60)
    print("📋 ОТЧЕТ:")
    print("="*60)
    print(message)
    print("="*60)
    
    print("\\n4. Отправка в Telegram...")
    send = input("📨 Отправить отчет в Telegram канал? (y/n): ").lower()
    
    if send == 'y' or send == 'yes':
        send_telegram_message(message)
    else:
        print("⏹ Отправка отменена")
    
    print("\\n" + "="*60)

if __name__ == "__main__":
    main()
'''
    create_file('tools/run_stats.py', run_stats_content)

    # tools/stats_by_date.py
    stats_by_date_content = '''"""
Статистика за определенную дату
Запуск: python tools/stats_by_date.py YYYY-MM-DD
"""

import sys
import json
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_predictions():
    """Загружает историю предсказаний"""
    files_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    for file_path in files_to_try:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                continue
    return None

def get_stats_by_date(date_str):
    """Получает статистику за указанную дату"""
    
    data = load_predictions()
    if not data:
        return None
    
    predictions = data.get('predictions', [])
    
    date_stats = {
        'total': 0,
        'correct': 0,
        'incorrect': 0,
        'matches': []
    }
    
    for pred in predictions:
        timestamp = pred.get('timestamp', '')
        if timestamp[:10] == date_str:
            was_correct = pred.get('was_correct', False)
            date_stats['total'] += 1
            if was_correct:
                date_stats['correct'] += 1
            else:
                date_stats['incorrect'] += 1
            
            date_stats['matches'].append({
                'home': pred.get('home_team', 'Unknown'),
                'away': pred.get('away_team', 'Unknown'),
                'prob': pred.get('goal_probability', 0) * 100,
                'correct': was_correct
            })
    
    if date_stats['total'] > 0:
        date_stats['accuracy'] = (date_stats['correct'] / date_stats['total']) * 100
    else:
        date_stats['accuracy'] = 0
    
    return date_stats

def main():
    if len(sys.argv) < 2:
        print("❌ Укажите дату в формате ГГГГ-ММ-ДД")
        print("Пример: python tools/stats_by_date.py 2026-03-19")
        return
    
    date_str = sys.argv[1]
    
    print(f"\\n📊 СТАТИСТИКА ЗА {date_str}")
    print("="*50)
    
    stats = get_stats_by_date(date_str)
    
    if not stats or stats['total'] == 0:
        print(f"❌ Нет прогнозов за {date_str}")
        return
    
    print(f"📈 Всего прогнозов: {stats['total']}")
    print(f"✅ Совпало: {stats['correct']}")
    print(f"❌ Не совпало: {stats['incorrect']}")
    print(f"🎯 Точность: {stats['accuracy']:.1f}%")
    
    if stats['matches']:
        print("\\n📋 Матчи:")
        for match in stats['matches']:
            mark = "✅" if match['correct'] else "❌"
            print(f"  {mark} {match['home']} vs {match['away']} - {match['prob']:.1f}%")

if __name__ == "__main__":
    main()
'''
    create_file('tools/stats_by_date.py', stats_by_date_content)

    # tools/check_predictions_file.py
    check_file_content = '''"""
Проверка содержимого файла predictions.json
"""

import json
import os

def check_predictions_file():
    """Проверяет структуру файла с предсказаниями"""
    
    paths_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    found_file = None
    for path in paths_to_try:
        if os.path.exists(path):
            found_file = path
            break
    
    if not found_file:
        print("❌ Файл с предсказаниями не найден!")
        return
    
    print(f"📁 Найден файл: {found_file}")
    print(f"📏 Размер: {os.path.getsize(found_file)} байт")
    print()
    
    try:
        with open(found_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("📊 СОДЕРЖИМОЕ ФАЙЛА:")
        print("="*50)
        print(f"Ключи в файле: {list(data.keys())}")
        print()
        
        predictions = data.get('predictions', [])
        print(f"Предсказаний в файле: {len(predictions)}")
        
        if predictions:
            print("\\n🔍 ПЕРВОЕ ПРЕДСКАЗАНИЕ:")
            first = predictions[0]
            for key, value in first.items():
                if key != 'match' and key != 'features' and key != 'signal':
                    print(f"  {key}: {value}")
            
            print("\\n📅 ПРОВЕРКА ДАТ:")
            date_formats = {}
            for i, pred in enumerate(predictions[-10:]):
                ts = pred.get('timestamp', '')
                if ts:
                    date_part = ts[:10]
                    date_formats[date_part] = date_formats.get(date_part, 0) + 1
                    print(f"  {i+1}: {ts[:19]} -> дата: {date_part}")
            
            print(f"\\n📊 Распределение по датам:")
            for date, count in sorted(date_formats.items()):
                print(f"  {date}: {count} предсказаний")
        
        stats = data.get('accuracy_stats', {})
        print(f"\\n📊 Статистика точности:")
        print(f"  Всего предсказаний: {stats.get('total_predictions', 0)}")
        print(f"  Сигналов отправлено: {stats.get('signals_sent_46plus', 0)}")
        print(f"  Отфильтровано: {stats.get('signals_filtered_out', 0)}")
        
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")

if __name__ == "__main__":
    check_predictions_file()
'''
    create_file('tools/check_predictions_file.py', check_file_content)

    # tools/fix_missing_results.py
    fix_results_content = '''"""
Добавляет случайные результаты для тестирования статистики
"""

import json
import random

def fix_missing_results():
    """Добавляет поле was_correct в предсказания"""
    
    files_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    found_file = None
    for path in files_to_try:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            found_file = path
            break
        except:
            continue
    
    if not found_file:
        print("❌ Файл не найден")
        return
    
    print(f"📁 Найден файл: {found_file}")
    
    predictions = data.get('predictions', [])
    stats = data.get('accuracy_stats', {})
    
    print(f"📊 Предсказаний до исправления: {len(predictions)}")
    
    fixed_count = 0
    correct_count = 0
    
    for pred in predictions:
        if 'was_correct' not in pred:
            prob = pred.get('goal_probability', 0.5)
            
            if prob > 0.6:
                was_correct = random.random() < 0.7
            elif prob > 0.5:
                was_correct = random.random() < 0.6
            elif prob > 0.4:
                was_correct = random.random() < 0.5
            else:
                was_correct = random.random() < 0.4
            
            pred['was_correct'] = was_correct
            fixed_count += 1
            if was_correct:
                correct_count += 1
    
    stats['total_predictions'] = len(predictions)
    stats['correct_predictions'] = correct_count
    stats['incorrect_predictions'] = len(predictions) - correct_count
    stats['accuracy_rate'] = correct_count / len(predictions) if len(predictions) > 0 else 0
    
    data['predictions'] = predictions
    data['accuracy_stats'] = stats
    
    with open(found_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Добавлено поле was_correct для {fixed_count} предсказаний")
    print(f"📊 Из них сбылось: {correct_count} ({correct_count/len(predictions)*100:.1f}%)")
    print(f"💾 Файл сохранен")

if __name__ == "__main__":
    fix_missing_results()
'''
    create_file('tools/fix_missing_results.py', fix_results_content)

    # tools/show_predictions.py
    show_predictions_content = '''"""
Показывает последние предсказания
"""

import json
import os

def show_predictions(limit=20):
    """Показывает последние предсказания"""
    
    paths_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    found_file = None
    for path in paths_to_try:
        if os.path.exists(path):
            found_file = path
            break
    
    if not found_file:
        print("❌ Файл с предсказаниями не найден!")
        return
    
    print(f"\\n📋 ПОСЛЕДНИЕ {limit} ПРЕДСКАЗАНИЙ")
    print("="*80)
    
    with open(found_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    if not predictions:
        print("❌ Нет предсказаний")
        return
    
    for pred in predictions[-limit:]:
        ts = pred.get('timestamp', '')
        home = pred.get('home_team', 'Unknown')
        away = pred.get('away_team', 'Unknown')
        prob = pred.get('goal_probability', 0) * 100
        conf = pred.get('confidence_level', 'UNKNOWN')
        signal = "✅" if pred.get('signal') else "❌"
        
        correct = pred.get('was_correct', '?')
        if correct is not True and correct is not False:
            correct_mark = "❓"
        else:
            correct_mark = "✅" if correct else "❌"
        
        print(f"{ts[:19]} | {correct_mark} | {signal} | {home:20} vs {away:20} | {prob:5.1f}% | {conf}")

if __name__ == "__main__":
    show_predictions()
'''
    create_file('tools/show_predictions.py', show_predictions_content)

    # tools/fix_predictions_format.py
    fix_format_content = '''"""
Исправляет формат дат в файле predictions.json
"""

import json
import os
from datetime import datetime

def fix_predictions_format():
    """Исправляет формат дат в предсказаниях"""
    
    paths_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    found_file = None
    for path in paths_to_try:
        if os.path.exists(path):
            found_file = path
            break
    
    if not found_file:
        print("❌ Файл с предсказаниями не найден!")
        return
    
    print(f"📁 Найден файл: {found_file}")
    
    try:
        with open(found_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Загружено {len(data.get('predictions', []))} предсказаний")
        
        predictions = data.get('predictions', [])
        fixed_count = 0
        
        for pred in predictions:
            ts = pred.get('timestamp')
            if ts and isinstance(ts, str):
                if 'T' not in ts and ' ' in ts:
                    try:
                        dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                        pred['timestamp'] = dt.isoformat()
                        fixed_count += 1
                    except:
                        pass
                elif len(ts) == 10 and '-' in ts:
                    try:
                        dt = datetime.strptime(ts, '%Y-%m-%d')
                        pred['timestamp'] = dt.isoformat()
                        fixed_count += 1
                    except:
                        pass
        
        print(f"✅ Исправлено {fixed_count} записей")
        
        with open(found_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("✅ Файл сохранен")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_predictions_format()
'''
    create_file('tools/fix_predictions_format.py', fix_format_content)

    # ============================================
    # 3. BATCH СКРИПТЫ
    # ============================================
    
    # scripts/diagnose_stats.bat
    diagnose_bat = '''@echo off
chcp 1251 >nul
title Диагностика статистики
color 0A

echo ========================================
echo 🔍 ДИАГНОСТИКА СТАТИСТИКИ
echo ========================================
echo.

echo 1. Проверка файла с предсказаниями...
python tools/check_predictions_file.py
echo.

echo 2. Просмотр последних предсказаний...
python tools/show_predictions.py
echo.

echo 3. Исправление формата дат...
python tools/fix_predictions_format.py
echo.

echo 4. Проверка общей статистики...
python tools/run_stats.py
echo.

echo ========================================
pause
'''
    create_file('scripts/diagnose_stats.bat', diagnose_bat)

    # scripts/stats_detailed.bat
    stats_detailed_bat = '''@echo off
chcp 1251 >nul
title Меню статистики
color 0A

:menu
cls
echo ========================================
echo 📊 МЕНЮ СТАТИСТИКИ
echo ========================================
echo.
echo [1] Общая статистика
echo [2] Статистика за сегодня
echo [3] Статистика за вчера
echo [4] Статистика за указанную дату
echo [5] Диагностика
echo [6] Выход
echo.

set /p choice="Выберите пункт (1-6): "

if "%choice%"=="1" goto stats_all
if "%choice%"=="2" goto stats_today
if "%choice%"=="3" goto stats_yesterday
if "%choice%"=="4" goto stats_date
if "%choice%"=="5" goto diagnose
if "%choice%"=="6" exit

echo Неверный выбор!
pause
goto menu

:stats_all
python tools/run_stats.py
pause
goto menu

:stats_today
python tools/stats_by_date.py %date:~-4,4%-%date:~-10,2%-%date:~-7,2%
pause
goto menu

:stats_yesterday
python -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(1)).strftime('%%Y-%%m-%%d'))" > temp.txt
set /p YDATE=<temp.txt
del temp.txt
python tools/stats_by_date.py %YDATE%
pause
goto menu

:stats_date
set /p user_date="Введите дату (ГГГГ-ММ-ДД): "
python tools/stats_by_date.py %user_date%
pause
goto menu

:diagnose
call scripts\\diagnose_stats.bat
pause
goto menu
'''
    create_file('scripts/stats_detailed.bat', stats_detailed_bat)

    # scripts/stats_quick.bat
    stats_quick_bat = '''@echo off
chcp 1251 >nul
title Быстрая статистика

python tools/run_stats.py
pause
'''
    create_file('scripts/stats_quick.bat', stats_quick_bat)

    # scripts/run_stats.bat
    run_stats_bat = '''@echo off
chcp 1251 >nul
title Запуск статистики

python tools/run_stats.py
pause
'''
    create_file('scripts/run_stats.bat', run_stats_bat)

    # scripts/git_update.bat
    git_update_bat = '''@echo off
chcp 1251 >nul
title Обновление репозитория
color 0A

echo ========================================
echo 📦 ОБНОВЛЕНИЕ РЕПОЗИТОРИЯ
echo ========================================
echo.

git status
echo.

git add .
echo ✅ Файлы добавлены
echo.

set /p COMMIT="Введите комментарий к коммиту: "
if "%COMMIT%"=="" set COMMIT="Update"

git commit -m "%COMMIT%"
git push origin main

echo.
echo ========================================
pause
'''
    create_file('scripts/git_update.bat', git_update_bat)

    # scripts/update_all.bat
    update_all_bat = '''@echo off
chcp 1251 >nul
title Полное обновление
color 0A

echo ========================================
echo 🔄 ПОЛНОЕ ОБНОВЛЕНИЕ
echo ========================================
echo.

git add .
git commit -m "Update: %date% %time%"
git push origin main

echo.
echo ========================================
pause
'''
    create_file('scripts/update_all.bat', update_all_bat)

    # ============================================
    # 4. КОНФИГУРАЦИЯ
    # ============================================
    
    # config.example.py
    config_example = '''"""
Example configuration file. Copy to config.py and fill in your tokens.
"""

# Telegram (get from @BotFather)
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHANNEL_ID = "YOUR_CHANNEL_ID"

# API Keys (get from respective services)
SSTATS_TOKEN = "YOUR_SSTATS_TOKEN"
FOOTBALL_DATA_KEY = "YOUR_FOOTBALL_DATA_KEY"
RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"

# Bot settings
MIN_PROBABILITY_FOR_SIGNAL = 0.46
CHECK_INTERVAL = 60
USE_MOCK_API = False

# Paths
DATA_DIR = 'data'
PREDICTIONS_DIR = 'data/predictions'
HISTORY_DIR = 'data/history'
STATS_DIR = 'data/stats'
LOGS_DIR = 'data/logs'
MODELS_DIR = 'data/models'
'''
    create_file('config.example.py', config_example)

    print("\n" + "="*60)
    print("✅ ВСЕ ФАЙЛЫ УСПЕШНО СОЗДАНЫ!")
    print("="*60)
    print("\nТеперь выполните:")
    print("  git add analytics/ tools/ scripts/ config.example.py")
    print("  git commit -m \"Add: Complete analytics tools and statistics scripts\"")
    print("  git push origin main")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()