# fix_all_files.py
"""
Исправляет все файлы с проблемами кодировки
"""

# Исправляем signal_validator.py
signal_content = '''"""
signal_validator.py - Жесткий валидатор сигналов для отсеивания ложных срабатываний
"""

import json
import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SignalValidator:
    """
    Класс для жесткой валидации сигналов на основе исторических данных
    """
    
    def __init__(self, stats_file='data/stats/signal_stats.json'):
        self.stats_file = stats_file
        self.signal_stats = self._load_stats()
        
        # Пороги для валидации
        self.thresholds = {
            'min_accuracy': 0.55,
            'max_false_rate': 0.45,
            'min_samples': 10,
            'confidence_weights': {
                'VERY_HIGH': 1.2,
                'HIGH': 1.0,
                'MEDIUM': 0.8,
                'LOW': 0.5,
                'VERY_LOW': 0.3
            }
        }
        
        # Статистика по лигам
        self.league_stats = defaultdict(lambda: {
            'total': 0,
            'correct': 0,
            'false': 0,
            'accuracy': 0.0
        })
        
        # Статистика по минутам
        self.minute_stats = defaultdict(lambda: {
            'total': 0,
            'correct': 0,
            'accuracy': 0.0
        })
        
        # Статистика по вероятности
        self.probability_bins = {
            '0.40-0.45': {'min': 0.40, 'max': 0.45, 'total': 0, 'correct': 0},
            '0.45-0.50': {'min': 0.45, 'max': 0.50, 'total': 0, 'correct': 0},
            '0.50-0.55': {'min': 0.50, 'max': 0.55, 'total': 0, 'correct': 0},
            '0.55-0.60': {'min': 0.55, 'max': 0.60, 'total': 0, 'correct': 0},
            '0.60-0.65': {'min': 0.60, 'max': 0.65, 'total': 0, 'correct': 0},
            '0.65-0.70': {'min': 0.65, 'max': 0.70, 'total': 0, 'correct': 0},
            '0.70+': {'min': 0.70, 'max': 1.0, 'total': 0, 'correct': 0},
        }
        
        self._update_from_history()
    
    def _load_stats(self):
        """Загружает статистику сигналов"""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                'total_signals': 0,
                'correct_signals': 0,
                'false_signals': 0,
                'accuracy': 0.0,
                'by_confidence': {},
                'by_league': {},
                'by_minute': {},
                'by_probability': {},
                'recent_false': []
            }
    
    def _save_stats(self):
        """Сохраняет статистику сигналов"""
        import os
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.signal_stats, f, indent=2, ensure_ascii=False)
    
    def _update_from_history(self):
        """Обновляет статистику из истории предсказаний"""
        try:
            with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            predictions = data.get('predictions', [])
            
            for pred in predictions[-500:]:
                if not pred.get('signal'):
                    continue
                
                prob = pred.get('goal_probability', 0)
                confidence = pred.get('confidence_level', 'MEDIUM')
                minute = pred.get('minute', 0)
                league = pred.get('league_id')
                was_correct = pred.get('was_correct', False)
                
                if league:
                    self.league_stats[league]['total'] += 1
                    if was_correct:
                        self.league_stats[league]['correct'] += 1
                    else:
                        self.league_stats[league]['false'] += 1
                
                minute_bin = (minute // 10) * 10
                self.minute_stats[minute_bin]['total'] += 1
                if was_correct:
                    self.minute_stats[minute_bin]['correct'] += 1
                
                for bin_name, bin_data in self.probability_bins.items():
                    if bin_data['min'] <= prob < bin_data['max']:
                        bin_data['total'] += 1
                        if was_correct:
                            bin_data['correct'] += 1
                        break
            
            for stats in [self.league_stats, self.minute_stats]:
                for key in stats:
                    if stats[key]['total'] > 0:
                        stats[key]['accuracy'] = stats[key]['correct'] / stats[key]['total']
            
            for bin_data in self.probability_bins.values():
                if bin_data['total'] > 0:
                    bin_data['accuracy'] = bin_data['correct'] / bin_data['total']
                    
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
    
    def validate_signal(self, prediction: Dict, match) -> Tuple[bool, str, float]:
        """
        Жесткая валидация сигнала
        Возвращает: (пропустить, причина, confidence_score)
        """
        prob = prediction.get('goal_probability', 0)
        confidence = prediction.get('confidence_level', 'MEDIUM')
        minute = match.minute or 0
        league = match.league_id
        
        reasons = []
        confidence_score = 1.0
        
        # 1. ПРОВЕРКА ПО ВЕРОЯТНОСТИ
        if prob < 0.48:
            return False, f"probability_too_low_{prob:.2f}", 0.0
        
        # 2. ПРОВЕРКА ПО УРОВНЮ УВЕРЕННОСТИ
        confidence_mult = self.thresholds['confidence_weights'].get(confidence, 0.5)
        if confidence_mult < 0.8 and prob < 0.55:
            return False, f"low_confidence_{confidence}", confidence_mult
        
        # 3. ПРОВЕРКА ПО МИНУТЕ
        minute_acc = self.minute_stats.get((minute // 10) * 10, {}).get('accuracy', 0.5)
        if minute_acc < 0.4:
            reasons.append(f"bad_minute_{minute}")
            confidence_score *= 0.7
        elif minute_acc < 0.5:
            confidence_score *= 0.9
        
        # 4. ПРОВЕРКА ПО ЛИГЕ
        league_acc = self.league_stats.get(league, {}).get('accuracy', 0.5)
        if league_acc < 0.4:
            reasons.append("bad_league")
            confidence_score *= 0.6
        elif league_acc < 0.5:
            confidence_score *= 0.8
        
        # 5. ПРОВЕРКА ПО ИСТОРИЧЕСКОЙ ТОЧНОСТИ
        prob_acc = 0.5
        for bin_data in self.probability_bins.values():
            if bin_data['min'] <= prob < bin_data['max']:
                prob_acc = bin_data.get('accuracy', 0.5)
                if bin_data['total'] > 10 and prob_acc < 0.45:
                    return False, f"bad_prob_range_{bin_data['min']:.2f}-{bin_data['max']:.2f}", 0.0
                break
        
        confidence_score *= prob_acc
        
        # 6. ИТОГОВОЕ РЕШЕНИЕ
        if confidence_score < 0.5:
            return False, f"low_confidence_score_{confidence_score:.2f}", confidence_score
        
        if len(reasons) > 2:
            return False, f"multiple_issues_{'_'.join(reasons)}", confidence_score
        
        return True, "passed", confidence_score
    
    def record_signal_result(self, prediction: Dict, match, was_correct: bool):
        """Записывает результат сигнала для улучшения валидации"""
        
        prob = prediction.get('goal_probability', 0)
        confidence = prediction.get('confidence_level', 'MEDIUM')
        minute = match.minute or 0
        league = match.league_id
        
        self.signal_stats['total_signals'] += 1
        if was_correct:
            self.signal_stats['correct_signals'] += 1
        else:
            self.signal_stats['false_signals'] += 1
            
            self.signal_stats['recent_false'].append({
                'timestamp': datetime.now().isoformat(),
                'match_id': match.id,
                'home': match.home_team.name if match.home_team else 'Unknown',
                'away': match.away_team.name if match.away_team else 'Unknown',
                'probability': prob,
                'confidence': confidence,
                'minute': minute
            })
            
            if len(self.signal_stats['recent_false']) > 50:
                self.signal_stats['recent_false'] = self.signal_stats['recent_false'][-50:]
        
        total = self.signal_stats['correct_signals'] + self.signal_stats['false_signals']
        if total > 0:
            self.signal_stats['accuracy'] = self.signal_stats['correct_signals'] / total
        
        if confidence not in self.signal_stats['by_confidence']:
            self.signal_stats['by_confidence'][confidence] = {'total': 0, 'correct': 0}
        
        self.signal_stats['by_confidence'][confidence]['total'] += 1
        if was_correct:
            self.signal_stats['by_confidence'][confidence]['correct'] += 1
        
        self._save_stats()
    
    def get_validation_stats(self) -> Dict:
        """Возвращает статистику валидации"""
        return {
            'total_signals': self.signal_stats['total_signals'],
            'correct': self.signal_stats['correct_signals'],
            'false': self.signal_stats['false_signals'],
            'accuracy': self.signal_stats['accuracy'],
            'recent_false': self.signal_stats['recent_false'][-10:],
            'league_stats': dict(self.league_stats),
            'minute_stats': dict(self.minute_stats),
            'probability_stats': self.probability_bins
        }
    
    def get_false_signals_report(self) -> str:
        """Возвращает отчет по ложным сигналам"""
        report = "📊 **ОТЧЕТ ПО ЛОЖНЫМ СИГНАЛАМ**\n"
        report += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        report += f"Всего сигналов: {self.signal_stats['total_signals']}\n"
        report += f"✅ Совпало: {self.signal_stats['correct_signals']}\n"
        report += f"❌ Ложных: {self.signal_stats['false_signals']}\n"
        report += f"🎯 Точность: {self.signal_stats['accuracy']*100:.1f}%\n\n"
        
        if self.signal_stats['recent_false']:
            report += "📋 **Последние ложные сигналы:**\n"
            for false in self.signal_stats['recent_false'][-5:]:
                report += f"  • {false['home']} vs {false['away']} - {false['probability']*100:.1f}% ({false['confidence']})\n"
        
        return report
'''

with open('signal_validator.py', 'w', encoding='utf-8') as f:
    f.write(signal_content)
print("✅ signal_validator.py исправлен")

# Исправляем analyze_false_signals.py
analyze_content = '''# -*- coding: utf-8 -*-
from signal_validator import SignalValidator

def analyze_false_signals():
    validator = SignalValidator()
    stats = validator.get_validation_stats()

    print("=" * 60)
    print("🔍 АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ")
    print("=" * 60)

    print("\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Всего сигналов: {stats['total_signals']}")
    print(f"  ✅ Правильных: {stats['correct']}")
    print(f"  ❌ Ложных: {stats['false']}")
    print(f"  🎯 Точность: {stats['accuracy'] * 100:.1f}%")

    if stats['recent_false']:
        print("\n📋 ПОСЛЕДНИЕ ЛОЖНЫЕ СИГНАЛЫ:")
        for false in stats['recent_false'][-5:]:
            print(f"  • {false['home']} vs {false['away']} - {false['probability']*100:.1f}% ({false['confidence']}) на {false['minute']}'")

if __name__ == "__main__":
    analyze_false_signals()
'''

with open('analyze_false_signals.py', 'w', encoding='utf-8') as f:
    f.write(analyze_content)
print("✅ analyze_false_signals.py исправлен")

# Создаем простой тестовый файл
simple_content = '''# -*- coding: utf-8 -*-
from signal_validator import SignalValidator

v = SignalValidator()
s = v.get_validation_stats()

print("=" * 50)
print("СТАТИСТИКА СИГНАЛОВ")
print("=" * 50)
print(f"Всего сигналов: {s['total_signals']}")
print(f"Правильных: {s['correct']}")
print(f"Ложных: {s['false']}")
print(f"Точность: {s['accuracy']*100:.1f}%")
'''

with open('simple_analyze.py', 'w', encoding='utf-8') as f:
    f.write(simple_content)
print("✅ simple_analyze.py создан")

print("\n" + "=" * 60)
print("✅ ВСЕ ФАЙЛЫ ИСПРАВЛЕНЫ!")
print("=" * 60)
print("\nТеперь запустите:")
print("  python simple_analyze.py")
print("  или")
print("  python analyze_false_signals.py")