@echo off
echo ========================================
echo 🔥 ЗАПУСК БОТА ЧЕРЕЗ TOR
echo ========================================
echo.
echo 1. Убедитесь что Tor Browser запущен
echo 2. Tor создает прокси на localhost:9050
echo.

REM Проверяем доступность Tor
echo Проверка Tor...
python -c "import socks; s = socks.socksocket(); s.set_proxy(socks.SOCKS5, '127.0.0.1', 9050); s.connect(('api.telegram.org', 443)); print('✅ Tor работает')" 2>nul

if %errorlevel% neq 0 (
    echo ❌ Tor не найден! Запустите Tor Browser
    echo.
    echo Нажмите любую клавишу для выхода...
    pause > nul
    exit
)

echo.
echo 🚀 Запуск бота...
python run_fixed.py

pause