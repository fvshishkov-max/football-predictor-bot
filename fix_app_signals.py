# fix_app_signals.py
"""
Исправление отправки сигналов в app.py
"""

import re

def fix_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим блок отправки сигнала и исправляем
    new_signal_block = '''
                    signal = self.predictor.analyze_live_match(match)
                    
                    if signal:
                        self.last_predictions[match.id] = signal
                        self.stats_reporter.register_prediction(match.id, signal, match)
                        
                        # Получаем сообщение
                        message = signal.get('message')
                        if message:
                            # Отправляем в Telegram
                            self.telegram_bot.send_message(message)
                            self.stats['signals_sent'] += 1
                            logger.info(f"📨 Сигнал отправлен: {match.home_team.name} vs {match.away_team.name}")
                        else:
                            logger.warning(f"⚠️ Сигнал без сообщения для матча {match.id}")'''
    
    # Заменяем старый блок
    pattern = r'signal = self\.predictor\.analyze_live_match\(match\).*?logger\.info\(f"📨 Сигнал:.*?"\)'
    content = re.sub(pattern, new_signal_block, content, flags=re.DOTALL)
    
    # Добавляем логирование в начало _fast_check
    if 'logger.info(f"[{datetime.now().strftime' not in content:
        import datetime
        content = content.replace(
            'async def _fast_check(self):',
            '''async def _fast_check(self):
        logger.info(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Проверка live матчей...")'''
        )
        print("✅ Добавлено логирование времени")
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ app.py исправлен")
    print("   • Улучшена отправка сигналов")
    print("   • Добавлено логирование времени")

def fix_telegram_send():
    with open('telegram_bot_ultimate.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Убеждаемся, что send_message работает
    if 'def send_message' not in content:
        send_method = '''
    def send_message(self, text: str):
        """Отправляет сообщение в канал"""
        self.message_queue.put((self.channel_id, text))
        logger.info(f"📨 Сообщение добавлено в очередь (очередь: {self.message_queue.qsize()})")
        return True'''
        
        # Добавляем метод
        content += send_method
        print("✅ Добавлен метод send_message")
    
    with open('telegram_bot_ultimate.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ telegram_bot_ultimate.py исправлен")

if __name__ == "__main__":
    fix_app()
    fix_telegram_send()
    print("\n" + "="*60)
    print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
    print("="*60)
    print("\nПерезапустите бота: python run_fixed.py")