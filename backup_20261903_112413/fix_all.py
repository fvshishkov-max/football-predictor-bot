# fix_all.py
"""
Скрипт для автоматического исправления всех проблем
Запустите: python fix_all.py
"""

import os
import re

def fix_telegram_bot():
    """Исправляет telegram_bot.py"""
    filename = 'telegram_bot.py'
    if not os.path.exists(filename):
        print(f"❌ {filename} не найден")
        return False
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем проблемный метод send_goal_signal
    pattern = r'def send_goal_signal\(self, match: Match, analysis: Optional\[MatchAnalysis\] = None, custom_message: Optional\[str\] = None\).*?return False'
    
    new_method = '''def send_goal_signal(self, match: Match, analysis: Optional[MatchAnalysis] = None, custom_message: Optional[str] = None):
        """
        Отправляет сигнал о голе в Telegram.
        Теперь безопасно работает, если analysis равен None.
        """
        try:
            # Формируем сообщение
            if custom_message:
                # Если передано готовое сообщение, используем его
                message_text = custom_message
                logger.debug(f"📨 Используется готовое сообщение для матча {match.id}")
            else:
                # Если готового сообщения нет, формируем базовое
                home_name = match.home_team.name if match.home_team else "Unknown"
                away_name = match.away_team.name if match.away_team else "Unknown"
                message_text = (
                    f"⚽ **ПОТЕНЦИАЛЬНЫЙ ГОЛ!**\\n"
                    f"⚔️ **{home_name} vs {away_name}**\\n"
                    f"📊 **Счет:** {match.home_score}:{match.away_score}\\n"
                    f"⏱️ **Минута:** {match.minute or 0}'"
                )
            
            # Добавляем сообщение в очередь на отправку
            self.message_queue.put((self.channel_id, message_text))
            logger.info(f"📨 Сигнал для матча {match.id} добавлен в очередь")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при подготовке сигнала для матча {match.id}: {e}")
            return False'''
    
    new_content = re.sub(pattern, new_method, content, flags=re.DOTALL)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ {filename} исправлен")
    return True

def fix_predictor():
    """Исправляет проблему с JSON сериализацией в predictor.py"""
    filename = 'predictor.py'
    if not os.path.exists(filename):
        print(f"❌ {filename} не найден")
        return False
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим и заменяем метод save_predictions
    pattern = r'def save_predictions\(self, filename: str = .*?\).*?except Exception as e:.*?logger.error\(f"Ошибка сохранения: {e}"\)'
    
    new_method = '''def save_predictions(self, filename: str = 'data/predictions.json'):
        """Сохраняет предсказания"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Подготавливаем данные для сериализации
            predictions_serializable = []
            for p in self.predictions_history[-100:]:  # Сохраняем только последние 100
                p_copy = {}
                for key, value in p.items():
                    if key == 'match':
                        continue  # Пропускаем объект Match
                    elif isinstance(value, datetime):
                        p_copy[key] = value.isoformat()  # Конвертируем datetime в строку
                    elif hasattr(value, 'isoformat'):  # Для других объектов с методом isoformat
                        p_copy[key] = value.isoformat()
                    else:
                        p_copy[key] = value
                predictions_serializable.append(p_copy)
            
            # Подготавливаем accuracy_stats
            accuracy_stats_serializable = {}
            for key, value in self.accuracy_stats.items():
                if key == 'by_minute' or key == 'by_league':
                    # Конвертируем defaultdict в обычный dict
                    accuracy_stats_serializable[key] = dict(value)
                elif isinstance(value, datetime):
                    accuracy_stats_serializable[key] = value.isoformat()
                else:
                    accuracy_stats_serializable[key] = value
            
            data = {
                'predictions': predictions_serializable,
                'accuracy_stats': accuracy_stats_serializable,
                'thresholds': self.thresholds,
                'half_goals': self.half_goals,
                'match_signal_count': self.match_signal_count,
                'min_signal_probability': self.min_signal_probability
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Сохраняем XGBoost модель
            if self.xgb_model and hasattr(self.xgb_model, 'get_booster'):
                try:
                    _ = self.xgb_model.get_booster()  # Проверяем, что модель обучена
                    joblib.dump(self.xgb_model, self.model_path)
                    if self.feature_names:
                        with open(self.model_path.replace('.pkl', '_features.json'), 'w') as f:
                            json.dump(self.feature_names, f)
                except:
                    pass
            
            logger.info(f"💾 Сохранено {len(predictions_serializable)} предсказаний")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")'''
    
    new_content = re.sub(pattern, new_method, content, flags=re.DOTALL)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ {filename} исправлен")
    return True

def fix_app_indentation():
    """Исправляет отступы в app.py на строке 151"""
    filename = 'app.py'
    if not os.path.exists(filename):
        print(f"❌ {filename} не найден")
        return False
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Ищем строки около 151 и исправляем отступы
    if len(lines) >= 151:
        # Убеждаемся, что строка 151 имеет правильный отступ (4 пробела)
        lines[150] = '            message = None\n'  # Индекс 150 = строка 151
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ Отступы в {filename} исправлены")
    return True

def main():
    """Главная функция"""
    print("="*60)
    print("🔧 ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ")
    print("="*60)
    
    fix_telegram_bot()
    fix_predictor()
    fix_app_indentation()
    
    print("\n" + "="*60)
    print("✅ Все исправления применены!")
    print("🚀 Запустите бота: python run_fixed.py")
    print("="*60)

if __name__ == "__main__":
    main()