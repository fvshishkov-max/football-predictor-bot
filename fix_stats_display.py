# fix_stats_display.py
"""
Исправление отображения статистики - показываем то, что есть
"""

def fix_predictor_stats():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем блок отображения статистики
    new_stats_block = '''        # Получаем статистику (показываем только то, что есть)
        home_shots = home_stats.get('shots', 0)
        away_shots = away_stats.get('shots', 0)
        home_shots_ontarget = home_stats.get('shots_on_target', 0)
        away_shots_ontarget = away_stats.get('shots_on_target', 0)
        home_xg = home_stats.get('xg', 0.5)
        away_xg = away_stats.get('xg', 0.5)
        home_possession = home_stats.get('possession', 50)
        away_possession = away_stats.get('possession', 50)
        home_corners = home_stats.get('corners', 0)
        away_corners = away_stats.get('corners', 0)
        
        # Проверяем, какая статистика есть
        has_shots = home_shots > 0 or away_shots > 0
        has_shots_ontarget = home_shots_ontarget > 0 or away_shots_ontarget > 0
        has_xg = home_xg != 0.5 or away_xg != 0.5
        has_possession = home_possession != 50 or away_possession != 50
        has_corners = home_corners > 0 or away_corners > 0
        
        has_any_stats = has_shots or has_shots_ontarget or has_xg or has_possession or has_corners
        
        message_lines = [
            f"{emoji} ⚽ ПОТЕНЦИАЛЬНЫЙ ГОЛ!",
            "━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"🏟 {home_name}  vs  {away_name}{location_str}",
            f"📊 Счет: {current_score}",
            f"⏱ Минута: {match.minute or 0}' {period}",
            "",
            f"📈 Вероятность гола: {goal_prob*100:.1f}%",
            f"🎯 Уверенность: {conf_text}",
        ]
        
        if has_any_stats:
            stats_lines = ["", "📊 СТАТИСТИКА:"]
            if has_shots:
                stats_lines.append(f"  • Удары: {home_shots} : {away_shots}")
            if has_shots_ontarget:
                stats_lines.append(f"  • В створ: {home_shots_ontarget} : {away_shots_ontarget}")
            if has_xg:
                stats_lines.append(f"  • xG: {home_xg:.2f} : {away_xg:.2f}")
            if has_possession:
                stats_lines.append(f"  • Владение: {home_possession:.0f}% : {away_possession:.0f}%")
            if has_corners:
                stats_lines.append(f"  • Угловые: {home_corners} : {away_corners}")
            message_lines.extend(stats_lines)'''
    
    # Заменяем старый блок
    import re
    pattern = r'# Получаем статистику.*?message_lines\.extend\(\[.*?\]\)'
    content = re.sub(pattern, new_stats_block, content, flags=re.DOTALL)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ predictor.py обновлен")
    print("   • Теперь показывается только доступная статистика")
    print("   • Если есть xG - покажем xG")
    print("   • Если есть удары - покажем удары")
    print("   • И т.д.")

if __name__ == "__main__":
    fix_predictor_stats()
    print("\nПерезапустите бота: python run_fixed.py")