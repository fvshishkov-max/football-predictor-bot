# fix_predictor_logging_fixed.py
"""
Исправление логирования в predictor.py
Запуск: python fix_predictor_logging_fixed.py
"""

import re

def fix_logging():
    """Добавляет логирование в predictor.py"""
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("="*60)
    print("🔧 ДОБАВЛЕНИЕ ЛОГИРОВАНИЯ В PREDICTOR.PY")
    print("="*60)
    
    # 1. Проверяем наличие импорта logging
    if 'import logging' not in content:
        lines = content.split('\n')
        lines.insert(1, 'import logging')
        content = '\n'.join(lines)
        print("✅ Добавлен импорт logging")
    
    # 2. Добавляем настройку logger
    if 'logger = logging.getLogger' not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'import config' in line:
                lines.insert(i+2, '\nlogger = logging.getLogger(__name__)')
                content = '\n'.join(lines)
                print("✅ Добавлен logger")
                break
    
    # 3. Обновляем метод save_predictions с логированием
    # Находим старый метод и заменяем
    save_method_pattern = r'def save_predictions\(self, filename: str = .*?\):.*?return'
    match = re.search(save_method_pattern, content, re.DOTALL)
    
    if match:
        old_method = match.group(0)
        
        new_method = '''def save_predictions(self, filename: str = 'data/predictions/predictions.json'):
        """Сохраняет предсказания"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            logger.info(f"💾 Сохранение предсказаний в {filename}")
            
            # Подготавливаем данные для сериализации
            predictions_serializable = []
            for p in self.predictions_history[-100:]:
                p_copy = {}
                for key, value in p.items():
                    if key == 'match':
                        continue
                    elif isinstance(value, datetime):
                        p_copy[key] = value.isoformat()
                    elif hasattr(value, 'isoformat'):
                        p_copy[key] = value.isoformat()
                    else:
                        p_copy[key] = value
                predictions_serializable.append(p_copy)
            
            # Подготавливаем accuracy_stats
            accuracy_stats_serializable = {}
            for key, value in self.accuracy_stats.items():
                if key == 'by_minute' or key == 'by_league':
                    accuracy_stats_serializable[key] = dict(value)
                elif isinstance(value, datetime):
                    accuracy_stats_serializable[key] = value.isoformat()
                else:
                    accuracy_stats_serializable[key] = value
            
            data = {
                'predictions': predictions_serializable,
                'accuracy_stats': accuracy_stats_serializable,
                'thresholds': self.thresholds,
                'half_goals': dict(self.half_goals),
                'match_signal_count': dict(self.match_signal_count),
                'min_signal_probability': self.min_signal_probability
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ Сохранено {len(predictions_serializable)} предсказаний")
            
            # Сохраняем XGBoost модель
            if self.xgb_model and hasattr(self.xgb_model, 'get_booster'):
                try:
                    _ = self.xgb_model.get_booster()
                    joblib.dump(self.xgb_model, self.model_path)
                    if self.feature_names:
                        with open(self.model_path.replace('.pkl', '_features.json'), 'w', encoding='utf-8') as f:
                            json.dump(self.feature_names, f)
                except Exception as e:
                    logger.error(f"Ошибка сохранения XGBoost: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            try:
                with open(filename + '.backup', 'w', encoding='utf-8') as f:
                    json.dump({"error": str(e), "timestamp": datetime.now().isoformat()}, f, default=str)
                logger.info("💾 Сохранена резервная копия")
            except:
                pass'''
        
        content = content.replace(old_method, new_method)
        print("✅ Метод save_predictions обновлен")
    else:
        print("⚠️ Метод save_predictions не найден, ищем альтернативу...")
    
    # 4. Сохраняем изменения
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ predictor.py обновлен с логированием")

if __name__ == "__main__":
    fix_logging()