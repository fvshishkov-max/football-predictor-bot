# force_api_loop.py
"""
Добавляет принудительное обновление даже при ошибках API
"""

def fix_app_loop():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем принудительный сброс при ошибках
    new_loop_code = '''
    async def _fast_check(self):
        """Быстрая асинхронная проверка матчей с принудительным обновлением"""
        try:
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Проверка live матчей...")
            
            # Принудительно очищаем кэш API каждые 5 циклов
            if self.stats['api_calls'] % 5 == 0 and self.stats['api_calls'] > 0:
                logger.info("🔄 Принудительное обновление кэша API")
                if hasattr(self.api_client, 'sstats'):
                    self.api_client.sstats.cache = {}
            
            matches = await self.api_client.get_live_matches()
            
            if not matches:
                logger.warning("📭 Нет live матчей, повторная попытка через 10 секунд")
                await asyncio.sleep(10)
                return
            
            logger.info(f"📊 Получено {len(matches)} матчей")
            
            filtered = [m for m in matches if self._quick_filter(m)]
            
            if filtered:
                logger.info(f"📊 Анализ {len(filtered)} матчей из {len(matches)}")
            
            for match in filtered:
                try:
                    signal = self.predictor.analyze_live_match(match)
                    
                    if signal:
                        self.last_predictions[match.id] = signal
                        self.stats_reporter.register_prediction(match.id, signal, match)
                        
                        message = signal.get('message')
                        if message:
                            self.telegram_bot.send_message(message)
                            self.stats['signals_sent'] += 1
                            logger.info(f"📨 Сигнал: {match.home_team.name} vs {match.away_team.name}")
                    
                    self.stats['matches_analyzed'] += 1
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    self.stats['errors_count'] += 1
                    logger.error(f"❌ Ошибка матча {getattr(match, 'id', 'unknown')}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки: {e}")
            # При ошибке ждем 10 секунд
            await asyncio.sleep(10)'''
    
    # Находим старый метод и заменяем
    import re
    pattern = r'async def _fast_check\(self\):.*?except Exception as e:.*?logger\.error\(f"❌ Ошибка проверки: {e}"\)'
    content = re.sub(pattern, new_loop_code, content, flags=re.DOTALL)
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ app.py обновлен с принудительным циклом")

def fix_api_timeout():
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Уменьшаем задержки rate limit
    content = content.replace('await asyncio.sleep(30)', 'await asyncio.sleep(5)')
    content = content.replace('waiting 30 seconds', 'waiting 5 seconds')
    
    # Добавляем fallback при ошибках
    fallback_code = '''
            except Exception as e:
                logger.debug(f"Ошибка API: {e}")
                # Возвращаем пустой ответ вместо None
                return {"data": []}'''
    
    content = content.replace('except Exception as e:', fallback_code)
    
    with open('api_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ api_client.py обновлен с уменьшенными задержками")

def add_health_check():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем health check
    health_code = '''
    async def _health_check(self):
        """Проверка здоровья API"""
        try:
            test_matches = await self.api_client.get_live_matches()
            if test_matches:
                logger.info(f"✅ API здоров: {len(test_matches)} live матчей")
                return True
            else:
                logger.warning("⚠️ API вернул 0 матчей")
                return False
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False'''
    
    # Добавляем метод
    content += health_code
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Добавлен health check")

if __name__ == "__main__":
    fix_app_loop()
    fix_api_timeout()
    add_health_check()
    print("\nПерезапустите бота: python run_fixed.py")