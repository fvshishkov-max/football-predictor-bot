# apply_all_fixes.py
"""
Применение всех оптимизаций:
1. Увеличение порога до 48-50%
2. Усиление фильтра по минутам
3. Добавление фактора формы
4. Включение signal_validator
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filename):
    """Создает резервную копию файла"""
    if os.path.exists(filename):
        backup = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(filename, backup)
        print(f"✅ Backup created: {backup}")
        return True
    return False

def update_config():
    """Обновляет config.py - увеличиваем порог до 48%"""
    print("\n" + "="*60)
    print("1. ОБНОВЛЕНИЕ CONFIG.PY")
    print("="*60)
    
    if not os.path.exists('config.py'):
        print("❌ config.py not found")
        return
    
    backup_file('config.py')
    
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Увеличиваем порог с 46% до 48%
    content = content.replace(
        "MIN_PROBABILITY_FOR_SIGNAL = float(os.getenv('MIN_PROBABILITY_FOR_SIGNAL', '0.46'))",
        "MIN_PROBABILITY_FOR_SIGNAL = float(os.getenv('MIN_PROBABILITY_FOR_SIGNAL', '0.48'))"
    )
    
    # Добавляем дополнительные настройки
    new_settings = """
# Дополнительные настройки фильтрации
MIN_SIGNAL_PROBABILITY_HIGH = float(os.getenv('MIN_SIGNAL_PROBABILITY_HIGH', '0.52'))  # Для MEDIUM и LOW уверенности
EXCLUDE_MINUTES = os.getenv('EXCLUDE_MINUTES', '0-10,85-90')  # Минуты для исключения
USE_FORM_FACTOR = os.getenv('USE_FORM_FACTOR', 'True').lower() == 'true'
"""
    
    if "MIN_SIGNAL_PROBABILITY_HIGH" not in content:
        content += new_settings
    
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ config.py updated: MIN_PROBABILITY_FOR_SIGNAL = 0.48")

def update_predictor_threshold():
    """Обновляет predictor.py - динамический порог"""
    print("\n" + "="*60)
    print("2. ОБНОВЛЕНИЕ ПОРОГОВ В PREDICTOR.PY")
    print("="*60)
    
    if not os.path.exists('predictor.py'):
        print("❌ predictor.py not found")
        return
    
    backup_file('predictor.py')
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем динамический порог в analyze_live_match
    new_send_logic = '''            if prob >= self.min_signal_probability:
                # Динамический порог для разных уровней уверенности
                conf = prediction.get('confidence_level', 'MEDIUM')
                should_send = False
                
                if conf in ['VERY_HIGH', 'HIGH']:
                    should_send = True
                elif conf == 'MEDIUM' and prob >= 0.50:
                    should_send = True
                elif conf == 'LOW' and prob >= 0.55:
                    should_send = True
                else:
                    should_send = False
                
                if should_send:
                    half = "1-й тайм" if match.minute and match.minute < 45 else "2-й тайм"
                    self.match_last_signal[match.id] = datetime.now()
                    self.match_signal_count[match.id] = self.match_signal_count.get(match.id, 0) + 1
                    self.accuracy_stats['signals_sent_46plus'] += 1
                    logger.info(f"СИГНАЛ ОТПРАВЛЕН! Матч {match.id} ({half}) - {prob*100:.1f}% ({conf})")
                    return prediction.get('signal')'''
    
    # Заменяем старый блок
    old_pattern = r'if prob >= self\.min_signal_probability:.*?return prediction\.get\(\'signal\'\)'
    content = re.sub(old_pattern, new_send_logic, content, flags=re.DOTALL)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Динамический порог добавлен: VERY_HIGH/HIGH - 48%, MEDIUM - 50%, LOW - 55%")

def update_match_analyzer_filters():
    """Обновляет match_analyzer.py - усиление фильтра по минутам"""
    print("\n" + "="*60)
    print("3. ОБНОВЛЕНИЕ ФИЛЬТРА ПО МИНУТАМ")
    print("="*60)
    
    if not os.path.exists('match_analyzer.py'):
        print("❌ match_analyzer.py not found")
        return
    
    backup_file('match_analyzer.py')
    
    with open('match_analyzer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Обновляем _calculate_time_factor с исключением плохих минут
    new_time_factor = '''    def _calculate_time_factor(self, minute: int) -> float:
        """Рассчитывает фактор времени с исключением плохих минут"""
        if not minute:
            return 1.0
        
        # Исключаем плохие минуты (0-10 и 85-90)
        if minute < 10:
            return 0.3   # Очень низкая вероятность
        elif minute < 15:
            return 0.7
        elif minute < 30:
            return 0.85
        elif minute < 45:
            return 0.9
        elif minute < 60:
            return 0.95
        elif minute < 75:
            return 1.0   # Пик активности
        elif minute < 85:
            return 1.1   # Концовка - высокая вероятность
        elif minute < 90:
            return 0.8   # Последние минуты - рискованно
        else:
            return 0.5   # Добавленное время - низкая вероятность'''
    
    # Находим старый метод
    pattern = r'def _calculate_time_factor\(self, minute: int\) -> float:.*?return [0-9.]+'
    content = re.sub(pattern, new_time_factor, content, flags=re.DOTALL)
    
    with open('match_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Фильтр по минутам усилен: исключены 0-10 и 85-90 минуты")

def add_form_factor():
    """Добавляет фактор формы команд в predictor.py"""
    print("\n" + "="*60)
    print("4. ДОБАВЛЕНИЕ ФАКТОРА ФОРМЫ")
    print("="*60)
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем получение формы в predict_match
    form_code = '''
            # Получаем форму команд
            home_form = None
            away_form = None
            if match.home_team and hasattr(match.home_team, 'id'):
                home_form = self.team_analyzer.get_team_form(match.home_team.id)
                if home_form:
                    base_prob += (home_form.get('weighted_form', 0.5) - 0.5) * 0.1
            if match.away_team and hasattr(match.away_team, 'id'):
                away_form = self.team_analyzer.get_team_form(match.away_team.id)
                if away_form:
                    base_prob += (away_form.get('weighted_form', 0.5) - 0.5) * 0.1'''
    
    # Находим место для вставки
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "base_prob = 0.35" in line:
            lines.insert(i+1, form_code)
            break
    
    content = '\n'.join(lines)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Фактор формы добавлен (±10% от формы команд)")

def enable_validator():
    """Включает signal_validator в predictor.py"""
    print("\n" + "="*60)
    print("5. ВКЛЮЧЕНИЕ SIGNAL_VALIDATOR")
    print("="*60)
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем импорт
    if 'from signal_validator import SignalValidator' not in content:
        lines = content.split('\n')
        lines.insert(10, 'from signal_validator import SignalValidator')
        content = '\n'.join(lines)
        print("✅ Импорт SignalValidator добавлен")
    
    # Добавляем инициализацию
    if 'self.signal_validator = SignalValidator()' not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'self.match_filter = MatchFilter()' in line:
                lines.insert(i+1, '        self.signal_validator = SignalValidator()')
                content = '\n'.join(lines)
                print("✅ Инициализация SignalValidator добавлена")
                break
    
    # Добавляем валидацию в analyze_live_match
    validation_code = '''
            # Валидация сигнала
            if hasattr(self, 'signal_validator'):
                valid, reason, score = self.signal_validator.validate_signal(prediction, match)
                if not valid:
                    logger.debug(f"Сигнал отклонен валидатором: {reason}")
                    return None'''
    
    # Находим место после расчета вероятности
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "if prob >= self.min_signal_probability:" in line:
            lines.insert(i, validation_code)
            break
    
    content = '\n'.join(lines)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ SignalValidator интегрирован")

def update_analyze_match():
    """Обновляет метод _should_analyze_match с новыми фильтрами"""
    print("\n" + "="*60)
    print("6. ОБНОВЛЕНИЕ МЕТОДА АНАЛИЗА МАТЧА")
    print("="*60)
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_analyze = '''    def _should_analyze_match(self, match: Match) -> bool:
        """Улучшенная проверка матча"""
        
        # 1. Базовые фильтры
        if match.minute and match.minute > 75:
            return False
        if abs((match.home_score or 0) - (match.away_score or 0)) >= 3:
            return False
        if (match.home_score or 0) >= 4 or (match.away_score or 0) >= 4:
            return False
        
        # 2. Исключаем начало матча (0-10 минут)
        if match.minute and match.minute < 10:
            return False
        
        # 3. Исключаем последние минуты (85-90)
        if match.minute and 85 <= match.minute <= 90:
            return False
        
        # 4. Проверка на слишком большой перевес
        score_diff = abs((match.home_score or 0) - (match.away_score or 0))
        if score_diff >= 2 and match.minute and match.minute > 70:
            return False
        
        # 5. Проверка на слишком много голов
        total_goals = (match.home_score or 0) + (match.away_score or 0)
        if total_goals >= 4:
            return False
        
        return True'''
    
    # Находим старый метод
    pattern = r'def _should_analyze_match\(self, match: Match\) -> bool:.*?return False'
    content = re.sub(pattern, new_analyze, content, flags=re.DOTALL)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Метод _should_analyze_match обновлен")
    print("   - Исключены 0-10 минуты")
    print("   - Исключены 85-90 минуты")
    print("   - Исключены матчи с перевесом 2+ после 70 минуты")
    print("   - Исключены матчи с 4+ голами")

def create_summary():
    """Создает файл с отчетом об изменениях"""
    print("\n" + "="*60)
    print("7. СОЗДАНИЕ ОТЧЕТА")
    print("="*60)
    
    report = f"""
========================================
ОТЧЕТ О ПРИМЕНЕННЫХ ИЗМЕНЕНИЯХ
========================================
Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. УВЕЛИЧЕНИЕ ПОРОГА
   - Минимальная вероятность: 46% -> 48%
   - MEDIUM: 50% (было 48%)
   - LOW: 55% (было 48%)

2. УСИЛЕНИЕ ФИЛЬТРА ПО МИНУТАМ
   - Исключены: 0-10 минуты (фактор 0.3)
   - Исключены: 85-90 минуты (фактор 0.8)
   - Оптимальное время: 60-85 минуты (фактор 1.0-1.1)

3. ДОБАВЛЕН ФАКТОР ФОРМЫ
   - Учитывается форма команд за последние матчи
   - Влияние: ±10% от базовой вероятности

4. ВКЛЮЧЕН SIGNAL_VALIDATOR
   - Исторический анализ точности
   - Динамическая корректировка порогов

5. ОБНОВЛЕН МЕТОД АНАЛИЗА МАТЧА
   - Исключены: начало матча (0-10')
   - Исключены: концовка (85-90')
   - Исключены: разгромы (4+ голов)
   - Исключены: большая разница после 70'

========================================
ОЖИДАЕМЫЙ ЭФФЕКТ:
- Снижение ложных сигналов на 30-40%
- Повышение точности прогнозов
- Более релевантные сигналы в концовке матчей
========================================
"""
    
    os.makedirs('data', exist_ok=True)
    with open('data/optimization_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ Отчет сохранен в data/optimization_report.txt")

def main():
    print("="*70)
    print("🔧 ПРИМЕНЕНИЕ ВСЕХ ОПТИМИЗАЦИЙ")
    print("="*70)
    
    # Создаем папку для бэкапов
    os.makedirs('data/backups', exist_ok=True)
    
    # Применяем все изменения
    update_config()
    update_predictor_threshold()
    update_match_analyzer_filters()
    add_form_factor()
    enable_validator()
    update_analyze_match()
    create_summary()
    
    print("\n" + "="*70)
    print("✅ ВСЕ ИЗМЕНЕНИЯ ПРИМЕНЕНЫ!")
    print("="*70)
    print("\n📋 ЧТО БЫЛО СДЕЛАНО:")
    print("  • Порог увеличен до 48% (MEDIUM:50%, LOW:55%)")
    print("  • Исключены минуты 0-10 и 85-90")
    print("  • Добавлен фактор формы команд")
    print("  • Включен SignalValidator")
    print("  • Обновлен метод анализа матчей")
    print("\n🚀 Запустите бота: python run_fixed.py")
    print("\n📊 Отчет сохранен в data/optimization_report.txt")

if __name__ == "__main__":
    main()