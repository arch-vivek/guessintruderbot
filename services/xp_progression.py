from core.events import DOUBLE_XP

async def get_user(user_id, db):
    return await db.fetchone("SELECT * FROM users WHERE user_id = ?", user_id)

async def create_user_if_not_exists(user_id, username, first_name, db):
    user = await db.fetchone("SELECT user_id FROM users WHERE user_id = ?", user_id)
    if not user:
        await db.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            user_id, username, first_name
        )

def xp_for_level(level: int) -> int:
    return 100 * level * level

async def award_xp(user_id, base_xp, db, combo=1, bonus_multiplier=1.0):
    user = await db.fetchone("SELECT xp, level FROM users WHERE user_id = ?", user_id)
    if not user:
        return None
    gained = int(base_xp * combo * bonus_multiplier)
    if DOUBLE_XP:
        gained *= 2
    new_xp = user["xp"] + gained
    new_level = user["level"]
    while new_xp >= xp_for_level(new_level + 1):
        new_level += 1
        # Check level achievements
        from services.achievements import check_level_achievements
        await check_level_achievements(user_id, new_level, db)

    await db.execute(
        "UPDATE users SET xp = ?, level = ?, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?",
        new_xp, new_level, user_id
    )
    return gained, new_level, new_xp, user["level"]