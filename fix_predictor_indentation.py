# fix_predictor_indentation.py
"""
Исправляет отступы в predictor.py
"""

import re

def fix_predictor():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим проблемный метод
    pattern = r'def _should_send_signal\(self, prediction: Dict, match=None\) -> bool:.*?return False'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        print("Найден метод _should_send_signal")
        
        # Правильная версия метода с отступами
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
        
        # Заменяем
        new_content = content.replace(match.group(0), new_method)
        
        with open('predictor.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ predictor.py исправлен!")
    else:
        print("❌ Метод не найден")
        
        # Альтернативный поиск
        alt_pattern = r'def _should_send_signal\(self, prediction\).*?return False'
        match = re.search(alt_pattern, content, re.DOTALL)
        if match:
            print("Найден альтернативный метод")
            new_content = content.replace(match.group(0), new_method)
            with open('predictor.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✅ predictor.py исправлен!")

if __name__ == "__main__":
    fix_predictor()