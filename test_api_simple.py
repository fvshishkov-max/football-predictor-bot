# test_api_simple.py
import requests
import json

def test_api_simple():
    """Простой тест API с использованием requests"""
    
    api_key = "k0f69qjmqx4gs8a8"
    base_url = "https://sstats.net/api"
    
    print("🔍 Тестирование SStats API...")
    
    # Пробуем разные эндпоинты
    endpoints = [
        "/matches/live",
        "/matches/today",
        "/live",
        "/today"
    ]
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        params = {"key": api_key}
        
        print(f"\n📡 Тестируем: {url}")
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            print(f"   Статус: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            
            if response.status_code == 200:
                # Пробуем распарсить JSON
                try:
                    data = response.json()
                    print(f"   ✅ JSON успешно получен!")
                    
                    if isinstance(data, list):
                        print(f"   📊 Получен список из {len(data)} элементов")
                        if len(data) > 0:
                            print(f"   Пример первого элемента: {json.dumps(data[0], indent=2)[:200]}")
                    elif isinstance(data, dict):
                        print(f"   📊 Ключи в ответе: {list(data.keys())}")
                        if 'data' in data:
                            print(f"   В поле 'data' - {len(data['data'])} элементов")
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ Ошибка парсинга JSON: {e}")
                    print(f"   Первые 200 символов ответа: {response.text[:200]}")
            else:
                print(f"   ❌ Ошибка: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")
    
    print("\n✅ Тестирование завершено")

if __name__ == "__main__":
    test_api_simple()