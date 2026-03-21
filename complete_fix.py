# complete_fix.py
"""
Полное исправление predictor.py с русским языком
"""

import re

def complete_fix():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Полностью заменяем метод _generate_signal
    new_generate_signal = '''    def _generate_signal(self, match: Match, goal_prob: float, confidence: str,
                        home_stats: Dict, away_stats: Dict) -> Dict:
        from translations import get_country_info, get_league_icon
        
        confidence_emojis = {"VERY_HIGH": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "VERY_LOW": "⚪"}
        confidence_text = {"VERY_HIGH": "ОЧЕНЬ ВЫСОКАЯ", "HIGH": "ВЫСОКАЯ", "MEDIUM": "СРЕДНЯЯ", "LOW": "НИЗКАЯ", "VERY_LOW": "ОЧЕНЬ НИЗКАЯ"}
        
        emoji = confidence_emojis.get(confidence, "⚪")
        conf_text = confidence_text.get(confidence, confidence)
        
        home_name = match.home_team.name if match.home_team else "Хозяева"
        away_name = match.away_team.name if match.away_team else "Гости"
        
        country_info = {'flag': '🌍', 'name': ''}
        if match.home_team and match.home_team.country_code:
            country_info = get_country_info(match.home_team.country_code)
        elif match.away_team and match.away_team.country_code:
            country_info = get_country_info(match.away_team.country_code)
        
        league_icon = get_league_icon(match.league_name) if match.league_name else '🏆'
        league_display = match.league_name if match.league_name else ""
        
        location_parts = []
        if country_info['name']:
            location_parts.append(f"{country_info['flag']} {country_info['name']}")
        if league_display:
            location_parts.append(f"{league_icon} {league_display}")
        
        location_str = f" | {' | '.join(location_parts)}" if location_parts else ""
        
        current_score = f"{match.home_score or 0}:{match.away_score or 0}"
        
        period = ""
        if match.minute:
            if match.minute < 45:
                period = "1-й тайм"
            elif match.minute < 90:
                period = "2-й тайм"
            else:
                period = "Доп. время"
        
        has_stats = any([
            home_stats.get('shots', 0) > 0,
            away_stats.get('shots', 0) > 0,
            home_stats.get('shots_on_target', 0) > 0,
            away_stats.get('shots_on_target', 0) > 0
        ])
        
        message_lines = [
            f"{emoji} ⚽ ПОТЕНЦИАЛЬНЫЙ ГОЛ!",
            f"━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"🏟 {home_name}  vs  {away_name}{location_str}",
            f"📊 Счет: {current_score}",
            f"⏱ Минута: {match.minute or 0}' {period}",
            f"",
            f"📈 Вероятность гола: {goal_prob*100:.1f}%",
            f"🎯 Уверенность: {conf_text}",
        ]
        
        if has_stats:
            message_lines.extend([
                f"",
                f"📊 Статистика матча:",
                f"  • Удары: {home_stats.get('shots', 0)} : {away_stats.get('shots', 0)}",
                f"  • В створ: {home_stats.get('shots_on_target', 0)} : {away_stats.get('shots_on_target', 0)}",
                f"  • xG: {home_stats.get('xg', 0):.2f} : {away_stats.get('xg', 0):.2f}",
            ])
        
        return {
            'emoji': emoji,
            'message': "\\n".join(message_lines),
            'confidence': confidence,
            'probability': goal_prob,
            'match_id': match.id,
            'current_score': current_score,
            'timestamp': datetime.now()
        }'''
    
    # Находим старый метод и заменяем
    pattern = r'def _generate_signal\(self, match: Match, goal_prob: float, confidence: str,.*?return \{[^}]+\}'
    content = re.sub(pattern, new_generate_signal, content, flags=re.DOTALL)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed _generate_signal method with Russian language")
    print("\nRestart bot: python run_fixed.py")

if __name__ == "__main__":
    complete_fix()