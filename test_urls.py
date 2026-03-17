# test_urls.py
from models import Match, Team

def test_url_generation():
    """Тестирует генерацию URL для разных команд"""
    
    # Создаем тестовые команды
    test_cases = [
        ("Manchester City", "Liverpool", 12345),
        ("Реал Мадрид", "Барселона", 12346),
        ("Bayern München", "Borussia Dortmund", 12347),
        ("Paris Saint-Germain", "Olympique Marseille", 12348),
        ("Juventus", "AC Milan", 12349),
        ("Зенит", "Спартак", 12350),
        ("Dynamo Kyiv", "Shakhtar Donetsk", 12351),
    ]
    
    from predictor import Predictor
    predictor = Predictor()
    
    print("=" * 60)
    print("Тестирование генерации URL для матчей")
    print("=" * 60)
    
    for home, away, match_id in test_cases:
        match = Match(
            id=match_id,
            home_team=Team(id=1, name=home),
            away_team=Team(id=2, name=away),
            minute=30,
            home_score=1,
            away_score=0
        )
        
        url = predictor._generate_match_url(match)
        print(f"\n📊 {home} vs {away}")
        print(f"🔗 {url}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_url_generation()