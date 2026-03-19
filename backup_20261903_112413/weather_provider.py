# weather_provider.py
import aiohttp
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class WeatherProvider:
    """Провайдер погодных условий для матчей"""
    
    # Бесплатный API OpenWeatherMap (нужно зарегистрироваться)
    API_KEY = "your_openweather_api_key"  # Замените на реальный ключ
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    @staticmethod
    def get_weather_factor(weather_data: Dict) -> float:
        """
        Возвращает коэффициент влияния погоды на результативность
        1.0 - оптимально, меньше - хуже для голов
        """
        weather_main = weather_data.get('weather', [{}])[0].get('main', '').lower()
        
        factors = {
            'clear': 1.0,      # Ясно - оптимально
            'clouds': 0.95,     # Облачно - немного меньше голов
            'rain': 0.8,        # Дождь - меньше голов
            'snow': 0.6,        # Снег - очень мало голов
            'storm': 0.5,       # Шторм - минимальная результативность
            'fog': 0.7,         # Туман - меньше голов
            'mist': 0.75,       # Дымка - меньше голов
            'drizzle': 0.85,    # Морось - немного меньше
        }
        
        # Учитываем температуру (холод - меньше голов)
        temp = weather_data.get('main', {}).get('temp', 20)
        temp_factor = 1.0
        if temp < 5:
            temp_factor = 0.8
        elif temp < 10:
            temp_factor = 0.9
        
        base_factor = factors.get(weather_main, 0.9)
        return base_factor * temp_factor
    
    async def get_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """Получает погоду по координатам"""
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Ошибка погодного API: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка получения погоды: {e}")
        
        return None