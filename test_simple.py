# test_simple.py
import requests

def test_api_simple():
    """Простой тест API с использованием requests"""
    api_key = "k0f69qjmqx4gs8a8"
    url = "https://sstats.net/api/matches/live"
    params = {"key": api_key}
    headers = {"Accept": "application/json"}
    
    print(f"Тестируем API: {url}")
    response = requests.get(url, params=params, headers=headers)
    
    print(f"Статус: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Первые 500 символов ответа:\n{response.text[:500]}")
    
    # Пробуем распарсить JSON
    try:
        data = response.json()
        print("JSON успешно распарсен!")
        print(f"Тип данных: {type(data)}")
        if isinstance(data, list):
            print(f"Количество элементов: {len(data)}")
        elif isinstance(data, dict):
            print(f"Ключи: {list(data.keys())}")
    except:
        print("Не удалось распарсить JSON")

if __name__ == "__main__":
    test_api_simple()