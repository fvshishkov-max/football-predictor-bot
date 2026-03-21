# fix_save_trigger.py
"""
Добавляет сохранение в predictor.py после каждого прогноза
"""

def add_save_calls():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, есть ли вызов save_predictions
    if 'self.save_predictions()' not in content:
        print("❌ save_predictions() не найден в predictor.py")
        return
    
    # Добавляем сохранение в analyze_live_match
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # После сигнала добавляем сохранение
        if 'self.accuracy_stats["signals_sent_46plus"] += 1' in line:
            new_lines.append('                    self.save_predictions()')
            print(f"✅ Добавлено сохранение после сигнала на строке {i+1}")
        
        # После предсказания добавляем сохранение
        if 'self._add_to_history(result)' in line:
            new_lines.append('            self.save_predictions()')
            print(f"✅ Добавлено сохранение после предсказания на строке {i+1}")
    
    new_content = '\n'.join(new_lines)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("\n✅ Изменения применены")

if __name__ == "__main__":
    add_save_calls()