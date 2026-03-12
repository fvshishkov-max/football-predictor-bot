# test_endpoints.py
import requests

def test_all_endpoints():
    """Тестирует все возможные эндпоинты"""
    api_key = "k0f69qjmqx4gs8a8"
    base_url = "https://sstats.net/api"
    
    endpoints = [
        "/matches/live",
        "/matches/today",
        "/live",
        "/today",
        "/v1/matches/live",
        "/v1/matches/today",
        "/api/matches/live",
        "/api/matches/today"
    ]
    
    headers = {"Accept": "application/json"}
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        params = {"key": api_key}
        
        print(f"\nТестируем: {url}")
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            print(f"  Статус: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  ✅ JSON успешно получен!")
                    if isinstance(data, list):
                        print(f"  Количество элементов: {len(data)}")
                    elif isinstance(data, dict):
                        print(f"  Ключи: {list(data.keys())}")
                except:
                    print(f"  ❌ Не JSON: {response.text[:100]}")
            else:
                print(f"  ❌ Ошибка: {response.text[:100]}")
        except Exception as e:
            print(f"  ❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    test_all_endpoints()