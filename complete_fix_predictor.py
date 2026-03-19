# complete_fix_predictor.py
"""
Полное исправление predictor.py - перезапись проблемных методов
"""

import re

def complete_fix():
    """Полностью перезаписывает проблемные методы"""
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 ПОЛНОЕ ИСПРАВЛЕНИЕ PREDICTOR.PY")
    print("="*50)
    
    # 1. Исправляем метод _should_analyze_match
    old_pattern = r'def _should_analyze_match\(self, match: Match\) -> bool:.*?return False(?=\n\s*def|\Z)'
    new_method = '''def _should_analyze_match(self, match: Match) -> bool:
    """Улучшенная проверка с использованием MatchFilter"""
    
    # Быстрая фильтрация (старая)
    if match.minute and match.minute > 75:
        return False
    if abs((match.home_score or 0) - (match.away_score or 0)) >= 3:
        return False
    if (match.home_score or 0) >= 4 or (match.away_score or 0) >= 4:
        return False
    
    # Новая, более умная фильтрация
    should, reason = self.match_filter.should_analyze(match)
    
    if should:
        # Дополнительный анализ потенциала
        if hasattr(self, 'match_analyzer'):
            home_stats = self._extract_team_stats(match, True)
            away_stats = self._extract_team_stats(match, False)
            analysis = self.match_analyzer.analyze_match_potential(
                match, home_stats, away_stats, None, None, None
            )
            
            # Обновляем статистику фильтра после матча
            if hasattr(match, 'total_goals'):
                self.match_filter.update_filter_stats(reason, match.total_goals > 0)
            
            return analysis['should_analyze']
    
    return False'''
    
    # Ищем и заменяем
    match = re.search(old_pattern, content, re.DOTALL)
    if match:
        content = content.replace(match.group(0), new_method)
        print("✅ Исправлен метод _should_analyze_match")
    else:
        print("⚠️ Метод _should_analyze_match не найден, добавляем...")
        # Добавляем в конец класса (приблизительно)
        content = content.replace('    def _get_default_prediction', 
                                  new_method + '\n\n    def _get_default_prediction')
    
    # 2. Исправляем метод _extract_team_stats
    old_extract = '''    def _extract_team_stats(self, match: Match, is_home: bool) -> Dict:
        """Извлекает статистику команды"""
        stats = {
            'shots': 0, 'shots_on_target': 0,
            'possession': 50, 'xg': 0.5,
            'has_real_stats': False
        }
        
        if not match.stats or not isinstance(match.stats, dict):
            return stats
        
        prefix = 'home' if is_home else 'away'
        stats['shots'] = match.stats.get(f'shots_{prefix}', 0)
        stats['shots_on_target'] = match.stats.get(f'shots_ontarget_{prefix}', 0)
        stats['possession'] = match.stats.get(f'possession_{prefix}', 50)
        stats['xg'] = match.stats.get(f'xg_{prefix}', 0.5)
        stats['has_real_stats'] = match.stats.get('has_real_stats', False)
        
        return stats'''
    
    # Проверяем, не склеен ли метод
    if 'return Falsedef' in content:
        content = content.replace('return Falsedef', 'return False\n\n    def')
    
    # Сохраняем
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Файл сохранен")
    
    # Проверяем синтаксис
    import py_compile
    try:
        py_compile.compile('predictor.py', doraise=True)
        print("✅ Синтаксис в порядке!")
    except py_compile.PyCompileError as e:
        print(f"❌ Ошибка: {e}")
        
        # Показываем проблемную строку
        error_str = str(e)
        line_match = re.search(r'line (\d+)', error_str)
        if line_match:
            line_num = int(line_match.group(1))
            with open('predictor.py', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"\nПроблема вокруг строки {line_num}:")
            start = max(0, line_num - 5)
            end = min(len(lines), line_num + 5)
            for i in range(start, end):
                prefix = '>>> ' if i+1 == line_num else '    '
                print(f"{prefix}{i+1:4d}: {lines[i].rstrip()}")

if __name__ == "__main__":
    complete_fix()