# fix_indentation.py
"""
Автоматическое исправление отступов в predictor.py
"""

import re

def fix_indentation():
    """Исправляет отступы в проблемном методе"""
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем метод _should_analyze_match
    pattern = r'(def _should_analyze_match\(self, match: Match\) -> bool:.*?)(?=def|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        old_method = match.group(1)
        print("✅ Найден метод _should_analyze_match")
        print(f"Длина: {len(old_method)} символов")
        
        # Правильная версия метода
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
        
        # Заменяем в файле
        new_content = content.replace(old_method, new_method)
        
        with open('predictor.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Файл исправлен!")
        return True
    else:
        print("❌ Метод не найден!")
        return False

if __name__ == "__main__":
    fix_indentation()