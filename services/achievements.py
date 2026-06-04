ACHIEVEMENTS_DEF = {
    "first_win": "First Victory – Win your first game",
    "win_10": "10 Wins – Win 10 games total",
    "win_50": "50 Wins – Win 50 games total",
    "streak_5": "Hot Streak – 5 consecutive wins",
    "streak_10": "On Fire – 10 consecutive wins",
    "perfect_round": "Perfect Round – Answer correctly in under 2 sec",
    "daily_3": "Daily Devotion – Complete 3 daily challenges",
    "level_10": "Level 10 – Reach level 10",
    "level_50": "Level 50 – Reach level 50",
    "referral_1": "Recruiter – Refer a friend",
}

async def check_achievement(user_id: int, key: str, db):
    existing = await db.fetchone("SELECT 1 FROM achievements WHERE user_id = ? AND achievement_id = ?", user_id, key)
    if not existing:
        await db.execute("INSERT INTO achievements (user_id, achievement_id) VALUES (?, ?)", user_id, key)
        return True
    return False

async def check_win_achievements(user_id, total_wins, db):
    if total_wins >= 1:
        await check_achievement(user_id, "first_win", db)
    if total_wins >= 10:
        await check_achievement(user_id, "win_10", db)
    if total_wins >= 50:
        await check_achievement(user_id, "win_50", db)

async def check_streak_achievements(user_id, streak, db):
    if streak >= 5:
        await check_achievement(user_id, "streak_5", db)
    if streak >= 10:
        await check_achievement(user_id, "streak_10", db)

async def check_level_achievements(user_id, new_level, db):
    achievements_map = {10: "level_10", 50: "level_50"}
    if new_level in achievements_map:
        await check_achievement(user_id, achievements_map[new_level], db)