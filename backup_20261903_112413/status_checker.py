# status_checker.py
import time
import os
import json
from datetime import datetime
import glob
import sys
import io

# Настраиваем вывод для поддержки UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_status():
    """Проверяет статус бота с подробной информацией"""
    status_file = 'data/bot_status.json'
    last_signal_time = None
    last_signal_text = ""
    
    print("="*60)
    print("📊 МОНИТОРИНГ СТАТУСА БОТА")
    print("="*60)
    
    while True:
        try:
            # Очищаем экран
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("="*60)
            print(f"🕒 {datetime.now().strftime('%H:%M:%S')} - МОНИТОРИНГ АКТИВЕН")
            print("="*60)
            
            # Проверяем время последнего обновления predictions.json
            if os.path.exists('data/predictions.json'):
                mod_time = os.path.getmtime('data/predictions.json')
                last_update = datetime.fromtimestamp(mod_time)
                time_since = (datetime.now() - last_update).total_seconds()
                
                # Статус бота
                if time_since < 300:  # 5 минут
                    status_emoji = "✅"
                    status_text = "АКТИВЕН"
                elif time_since < 900:  # 15 минут
                    status_emoji = "⚠️"
                    status_text = "ЗАМЕДЛЕНИЕ"
                else:
                    status_emoji = "❌"
                    status_text = "ЗАВИС"
                
                print(f"{status_emoji} СТАТУС: {status_text}")
                print(f"📅 Последнее обновление: {last_update.strftime('%H:%M:%S')}")
                print(f"⏱ Прошло: {time_since:.0f} секунд")
                print(f"📊 Размер файла: {os.path.getsize('data/predictions.json')} bytes")
            
            # Проверяем наличие новых сигналов в логах (с поддержкой UTF-8)
            if os.path.exists('app.log'):
                try:
                    # Читаем файл с UTF-8 кодировкой
                    with open('app.log', 'r', encoding='utf-8', errors='ignore') as f:
                        # Читаем последние 50 строк
                        lines = f.readlines()[-50:]
                        
                        signal_count = 0
                        goal_count = 0
                        error_count = 0
                        
                        for line in reversed(lines):
                            if 'СИГНАЛ ОТПРАВЛЕН' in line:
                                signal_count += 1
                                if last_signal_time != line[:19]:
                                    last_signal_time = line[:19]
                                    last_signal_text = line.strip()
                            elif '⚽ ГОЛ' in line:
                                goal_count += 1
                            elif 'ERROR' in line or 'Ошибка' in line:
                                error_count += 1
                        
                        print(f"\n📊 СТАТИСТИКА (последние 50 строк):")
                        print(f"  • Сигналов: {signal_count}")
                        print(f"  • Голов: {goal_count}")
                        print(f"  • Ошибок: {error_count}")
                        
                        if last_signal_time:
                            print(f"\n📨 Последний сигнал: {last_signal_time}")
                            # Обрезаем длинные строки
                            short_text = last_signal_text[:80] + "..." if len(last_signal_text) > 80 else last_signal_text
                            print(f"   {short_text}")
                            
                except Exception as e:
                    print(f"\n⚠️ Ошибка чтения лога: {e}")
            
            # Проверяем процессы Python
            print(f"\n🔄 ПРОЦЕССЫ:")
            try:
                import psutil
                python_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    if 'python' in proc.info['name'].lower():
                        python_processes.append(proc.info)
                
                if python_processes:
                    for proc in python_processes:
                        print(f"  • PID {proc['pid']}: CPU {proc['cpu_percent']:.1f}%, RAM {proc['memory_percent']:.1f}%")
                else:
                    print("  • Нет активных Python процессов")
            except ImportError:
                print("  • psutil не установлен (pip install psutil)")
            except Exception as e:
                print(f"  • Ошибка: {e}")
            
            # Проверяем очередь Telegram
            queue_file = 'telegram_queue.log'
            if os.path.exists(queue_file):
                queue_size = os.path.getsize(queue_file)
                print(f"\n📦 Очередь Telegram: {queue_size} bytes")
                if queue_size > 1024:
                    print(f"  ⚠️ Большая очередь! {queue_size/1024:.1f} KB")
            
            # Проверяем свободное место на диске
            try:
                import shutil
                total, used, free = shutil.disk_usage(".")
                free_mb = free / (1024*1024)
                print(f"\n💾 Свободно места: {free_mb:.1f} MB")
                if free_mb < 100:
                    print("  ⚠️ Мало места на диске!")
            except:
                pass
            
            print("\n" + "="*60)
            print(f"🔄 Следующая проверка через 10 секунд...")
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n👋 Мониторинг остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Устанавливаем кодировку для Windows
    if sys.platform == 'win32':
        import locale
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    
    check_status()