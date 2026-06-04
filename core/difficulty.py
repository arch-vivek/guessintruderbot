async def get_player_difficulty(user_id: int, db) -> int:
    user = await db.fetchone("SELECT mmr, level FROM users WHERE user_id = ?", user_id)
    if not user:
        return 1
    mmr = user["mmr"]
    if mmr < 1100:
        return 1
    elif mmr < 1300:
        return 2
    elif mmr < 1500:
        return 3
    elif mmr < 1700:
        return 4
    else:
        return 5