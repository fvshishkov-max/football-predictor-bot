# fix_predictor_stability.py
"""
Исправление нестабильности predictor.py
"""

import re

def fix_stability():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Убираем random вариацию, которая делает результаты нестабильными
    # Ищем блок с random.uniform
    pattern = r'variation = random\.uniform\(0\.95, 1\.05\).*?goal_probability = min\(0\.95, max\(0\.1, goal_probability \* variation\)\)'
    
    replacement = '        # Убираем random вариацию для стабильности\n        # variation = random.uniform(0.95, 1.05)\n        # goal_probability = min(0.95, max(0.1, goal_probability * variation))\n        # Используем только калиброванную вероятность\n        goal_probability = goal_probability'
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Removed random variation from predictor")
    print("   Results should now be stable")

def fix_analyze_method():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем кэширование результатов для одного матча
    if 'self._prediction_cache = {}' not in content:
        # Добавляем кэш в __init__
        content = content.replace(
            'self.match_signal_count = {}',
            'self.match_signal_count = {}\n        self._prediction_cache = {}'
        )
        print("✅ Added prediction cache")
    
    # Добавляем использование кэша в predict_match
    cache_code = '''
        # Проверяем кэш
        cache_key = f"{match.id}_{match.minute}"
        if cache_key in self._prediction_cache:
            logger.debug(f"Using cached prediction for {cache_key}")
            return self._prediction_cache[cache_key]
        
        # ... существующий код ...
        
        # Сохраняем в кэш
        self._prediction_cache[cache_key] = result
        # Очищаем старые записи (оставляем последние 100)
        if len(self._prediction_cache) > 100:
            oldest = min(self._prediction_cache.keys(), key=lambda x: int(x.split('_')[0]))
            del self._prediction_cache[oldest]
'''
    
    # Находим начало метода predict_match
    if 'def predict_match(self, match: Match) -> Dict:' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'def predict_match' in line:
                # Вставляем кэш после начала метода
                lines.insert(i+2, '        # Проверяем кэш')
                lines.insert(i+3, '        cache_key = f"{match.id}_{match.minute}"')
                lines.insert(i+4, '        if cache_key in self._prediction_cache:')
                lines.insert(i+5, '            logger.debug(f"Using cached prediction for {cache_key}")')
                lines.insert(i+6, '            return self._prediction_cache[cache_key]')
                lines.insert(i+7, '')
                break
        
        # Находим место для сохранения в кэш
        for i, line in enumerate(lines):
            if 'result = {' in line:
                # После result вставляем сохранение в кэш
                lines.insert(i+15, '        # Сохраняем в кэш')
                lines.insert(i+16, '        self._prediction_cache[cache_key] = result')
                lines.insert(i+17, '        # Очищаем старые записи')
                lines.insert(i+18, '        if len(self._prediction_cache) > 100:')
                lines.insert(i+19, '            oldest = min(self._prediction_cache.keys(), key=lambda x: int(x.split("_")[0]))')
                lines.insert(i+20, '            del self._prediction_cache[oldest]')
                break
        
        content = '\n'.join(lines)
        print("✅ Added caching to predict_match")
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_stability()
    fix_analyze_method()
    print("\nRestart bot: python run_fixed.py")