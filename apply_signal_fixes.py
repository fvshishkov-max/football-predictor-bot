# apply_signal_fixes.py
"""
Автоматическое применение всех исправлений для улучшения отбора сигналов
Запуск: python apply_signal_fixes.py
"""

import os
import sys
import shutil
from datetime import datetime

def create_file(path, content):
    """Создает файл с содержимым (упрощенная версия)"""
    # Создаем папку только если есть путь
    dirname = os.path.dirname(path)
    if dirname:  # Проверяем, что путь не пустой
        os.makedirs(dirname, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Создан: {path}")

def create_backup():
    """Создает резервную копию важных файлов"""
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = ['predictor.py', 'stats_reporter.py']
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"✅ Резервная копия: {file} -> {backup_dir}/")
    
    return backup_dir

def update_predictor():
    """Обновляет predictor.py с новым валидатором"""
    
    if not os.path.exists('predictor.py'):
        print("❌ predictor.py не найден!")
        return False
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Добавить импорт
    if 'from signal_validator import SignalValidator' not in content:
        # Находим место для импорта
        lines = content.split('\n')
        import_pos = -1
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_pos = i
        
        if import_pos >= 0:
            lines.insert(import_pos + 1, 'from signal_validator import SignalValidator')
        else:
            # Если импортов нет, добавляем в начало
            lines.insert(0, 'from signal_validator import SignalValidator')
        
        content = '\n'.join(lines)
        print("✅ Добавлен импорт SignalValidator")
    
    # 2. Добавить инициализацию в __init__
    if 'self.signal_validator = SignalValidator()' not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'self.match_filter = MatchFilter()' in line:
                lines.insert(i + 1, '        self.signal_validator = SignalValidator()')
                content = '\n'.join(lines)
                print("✅ Добавлена инициализация SignalValidator")
                break
    
    # 3. Заменить метод _should_send_signal
    new_method = '''    def _should_send_signal(self, prediction: Dict, match=None) -> bool:
        """Улучшенная проверка с валидатором"""
        if prediction.get('error', False):
            return False
        
        prob = prediction.get('goal_probability', 0)
        
        # 1. БАЗОВЫЙ ФИЛЬТР (46%)
        if prob < self.min_signal_probability:
            logger.debug(f"⏳ Сигнал: {prob*100:.1f}% - НИЖЕ ПОРОГА")
            self.accuracy_stats['signals_filtered_out'] += 1
            return False
        
        # 2. ЖЕСТКАЯ ВАЛИДАЦИЯ
        if hasattr(self, 'signal_validator'):
            valid, reason, score = self.signal_validator.validate_signal(prediction, match)
            
            if not valid:
                logger.debug(f"⏳ Сигнал отклонен валидатором: {reason} (score: {score:.2f})")
                self.accuracy_stats['signals_filtered_out'] += 1
                return False
            
            # Динамический порог на основе confidence score
            if score < 0.6 and prob < 0.52:
                logger.debug(f"⏳ Сигнал: низкий confidence score ({score:.2f}) при {prob*100:.1f}%")
                self.accuracy_stats['signals_filtered_out'] += 1
                return False
        
        # 3. ПРОВЕРКА ПО ИСТОРИИ (если есть данные)
        if hasattr(self, 'accuracy_stats') and self.accuracy_stats['total_predictions'] > 50:
            conf = prediction.get('confidence_level', 'MEDIUM')
            conf_stats = self.accuracy_stats['by_confidence'].get(conf, {'total': 0, 'correct': 0})
            
            # Если по данному уровню уверенности статистика плохая
            if conf_stats['total'] > 10:
                conf_accuracy = conf_stats['correct'] / conf_stats['total']
                if conf_accuracy < 0.4 and prob < 0.55:
                    logger.debug(f"⏳ Сигнал: низкая точность для {conf} ({conf_accuracy*100:.1f}%)")
                    self.accuracy_stats['signals_filtered_out'] += 1
                    return False
        
        logger.debug(f"✅ Сигнал: {prob*100:.1f}% - ПРОШЕЛ ВСЕ ПРОВЕРКИ")
        return True'''
    
    import re
    # Ищем старый метод
    old_pattern = r'def _should_send_signal\(self, prediction: Dict\).*?return False'
    match = re.search(old_pattern, content, re.DOTALL)
    
    if match:
        content = content.replace(match.group(0), new_method)
        print("✅ Заменен метод _should_send_signal")
    else:
        print("⚠️ Метод _should_send_signal не найден, ищем альтернативу...")
        # Пробуем найти без типа
        old_pattern2 = r'def _should_send_signal\(self, prediction\).*?return False'
        match2 = re.search(old_pattern2, content, re.DOTALL)
        if match2:
            content = content.replace(match2.group(0), new_method)
            print("✅ Заменен метод _should_send_signal (альтернативный вариант)")
    
    # 4. Обновить вызов в analyze_live_match
    content = content.replace(
        'if self._should_send_signal(prediction):',
        'if self._should_send_signal(prediction, match):'
    )
    
    # 5. Добавить запись результатов в update_accuracy
    update_code = '''            if pred.get('signal') and hasattr(self, 'signal_validator'):
                self.signal_validator.record_signal_result(pred, match, had_goal)'''
    
    if 'self.signal_validator.record_signal_result' not in content:
        # Находим место после обновления статистики
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'self.accuracy_stats[' in line and 'correct_predictions' in line:
                # Ищем конец блока
                for j in range(i, min(i+30, len(lines))):
                    if lines[j].strip() == '' and j+1 < len(lines):
                        lines.insert(j+1, update_code)
                        content = '\n'.join(lines)
                        print("✅ Добавлена запись результатов валидации")
                        break
                break
    
    # Сохраняем изменения
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ predictor.py обновлен")
    return True

def create_signal_validator():
    """Создает файл signal_validator.py"""
    
    content = '''"""
signal_validator.py - Жесткий валидатор сигналов для отсеивания ложных срабатываний
"""

import json
import logging
from datetime import datetime, timedelta
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
            with open(self.stats_file, 'r') as f:
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
        with open(self.stats_file, 'w') as f:
            json.dump(self.signal_stats, f, indent=2)
    
    def _update_from_history(self):
        """Обновляет статистику из истории предсказаний"""
        try:
            with open('data/predictions/predictions.json', 'r') as f:
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
            reasons.append(f"bad_league")
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
    create_file('signal_validator.py', content)

def create_analyze_false():
    """Создает файл analyze_false_signals.py"""
    
    content = '''"""
analyze_false_signals.py - Анализ ложных сигналов для улучшения фильтрации
"""

import json
from signal_validator import SignalValidator

def analyze_false_signals():
    """Анализирует ложные сигналы и предлагает улучшения"""
    
    validator = SignalValidator()
    stats = validator.get_validation_stats()
    
    print("="*60)
    print("🔍 АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ")
    print("="*60)
    
    print(f"\\n📊 Общая статистика:")
    print(f"  Всего сигналов: {stats['total_signals']}")
    print(f"  ✅ Правильных: {stats['correct']}")
    print(f"  ❌ Ложных: {stats['false']}")
    print(f"  🎯 Точность: {stats['accuracy']*100:.1f}%")
    
    if stats['recent_false']:
        print(f"\\n📋 Последние ложные сигналы:")
        for false in stats['recent_false'][-5:]:
            print(f"  • {false['home']} vs {false['away']} - {false['probability']*100:.1f}% ({false['confidence']}) на {false['minute']}'")
    
    print(f"\\n📊 Статистика по вероятности:")
    for bin_name, bin_data in stats['probability_stats'].items():
        if bin_data['total'] > 0:
            acc = bin_data.get('accuracy', 0) * 100
            print(f"  {bin_name}: {bin_data['total']} сигналов, точность {acc:.1f}%")
    
    print(f"\\n📊 Статистика по минутам:")
    for minute, minute_stats in sorted(stats['minute_stats'].items()):
        if minute_stats['total'] > 0:
            acc = minute_stats['accuracy'] * 100
            print(f"  {minute}-{minute+9} мин: {minute_stats['total']} сигналов, точность {acc:.1f}%")
    
    print("\\n" + "="*60)
    print("💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
    print("="*60)
    
    for bin_name, bin_data in stats['probability_stats'].items():
        if bin_data['total'] > 5 and bin_data.get('accuracy', 0) < 0.4:
            print(f"  • Повысить порог для диапазона {bin_name} (сейчас {bin_data['accuracy']*100:.1f}%)")
    
    for minute, minute_stats in sorted(stats['minute_stats'].items()):
        if minute_stats['total'] > 5 and minute_stats['accuracy'] < 0.35:
            print(f"  • Исключить минуты {minute}-{minute+9} (точность {minute_stats['accuracy']*100:.1f}%)")
    
    if stats['accuracy'] < 0.5:
        print(f"  • Общая точность низкая ({stats['accuracy']*100:.1f}%) - увеличьте порог до 48-50%")

if __name__ == "__main__":
    analyze_false_signals()
'''
    create_file('analyze_false_signals.py', content)

def create_batch_scripts():
    """Создает batch скрипты"""
    
    # Создаем папку scripts если её нет
    os.makedirs('scripts', exist_ok=True)
    
    # analyze_false.bat
    analyze_bat = '''@echo off
chcp 1251 >nul
title Анализ ложных сигналов
color 0C

echo ========================================
echo 🔍 АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ
echo ========================================
echo.

python analyze_false_signals.py

echo.
pause
'''
    create_file('scripts/analyze_false.bat', analyze_bat)
    
    # optimize_thresholds.bat
    optimize_bat = '''@echo off
chcp 1251 >nul
title Оптимизация порогов
color 0A

echo ========================================
echo 🔧 ОПТИМИЗАЦИЯ ПОРОГОВ
echo ========================================
echo.

python -c "
from signal_validator import SignalValidator
import json

v = SignalValidator()
stats = v.get_validation_stats()

print('📊 ТЕКУЩИЕ ПОРОГИ:')
print('  • Минимальная вероятность: 46%')
print('  • VERY_HIGH вес: 1.2')
print('  • HIGH вес: 1.0')
print('  • MEDIUM вес: 0.8')
print()

print('📈 РЕКОМЕНДАЦИИ:')
if stats['accuracy'] < 0.5:
    new_threshold = 48 + (50 - stats['accuracy']*100) / 10
    print(f'  • Увеличить порог до {new_threshold:.0f}%')
    
for bin_name, bin_data in stats['probability_stats'].items():
    if bin_data['total'] > 5 and bin_data.get('accuracy', 0) < 0.4:
        min_val = bin_data['min']
        print(f'  • Исключить сигналы ниже {min_val*100:.0f}% (точность {bin_data.get("accuracy",0)*100:.1f}%)')
"

echo.
pause
'''
    create_file('scripts/optimize_thresholds.bat', optimize_bat)
    
    print("✅ Batch скрипты созданы")

def update_gitignore():
    """Обновляет .gitignore"""
    gitignore_path = '.gitignore'
    new_lines = [
        '',
        '# Signal validator stats',
        'data/stats/signal_stats.json'
    ]
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for line in new_lines:
            if line not in content:
                content += line + '\n'
        
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ .gitignore обновлен")
    else:
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print("✅ .gitignore создан")

def main():
    """Главная функция"""
    print("="*60)
    print("🔧 АВТОМАТИЧЕСКОЕ ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ")
    print("="*60)
    
    # 1. Создаем резервную копию
    print("\n1. СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ")
    backup_dir = create_backup()
    print(f"   📁 Резервная копия в: {backup_dir}")
    
    # 2. Создаем signal_validator.py
    print("\n2. СОЗДАНИЕ ВАЛИДАТОРА")
    create_signal_validator()
    
    # 3. Создаем analyze_false_signals.py
    print("\n3. СОЗДАНИЕ АНАЛИЗАТОРА")
    create_analyze_false()
    
    # 4. Обновляем predictor.py
    print("\n4. ОБНОВЛЕНИЕ PREDICTOR.PY")
    if update_predictor():
        print("   ✅ predictor.py успешно обновлен")
    
    # 5. Создаем batch скрипты
    print("\n5. СОЗДАНИЕ BATCH СКРИПТОВ")
    create_batch_scripts()
    
    # 6. Обновляем .gitignore
    print("\n6. ОБНОВЛЕНИЕ .GITIGNORE")
    update_gitignore()
    
    # 7. Итог
    print("\n" + "="*60)
    print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
    print("="*60)
    print("\n📋 ЧТО БЫЛО СДЕЛАНО:")
    print("  • Создан signal_validator.py - жесткий валидатор сигналов")
    print("  • Создан analyze_false_signals.py - анализ ложных срабатываний")
    print("  • Обновлен predictor.py - добавлена жесткая валидация")
    print("  • Созданы batch скрипты для анализа")
    print("  • Обновлен .gitignore")
    print("\n📁 Резервная копия сохранена в:", backup_dir)
    print("\n🚀 ЗАПУСТИТЕ:")
    print("  • scripts\\analyze_false.bat - для анализа ложных сигналов")
    print("  • scripts\\optimize_thresholds.bat - для оптимизации порогов")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()