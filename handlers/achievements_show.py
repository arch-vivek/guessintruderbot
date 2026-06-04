from telegram import Update
from telegram.ext import ContextTypes
from services.achievements import ACHIEVEMENTS_DEF
from utils.helpers import smart_reply

async def achievements_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data["db"]
    unlocked_rows = await db.fetchall("SELECT achievement_id FROM achievements WHERE user_id = ?", user.id)
    unlocked = {row["achievement_id"] for row in unlocked_rows}
    text = "🏆 **Achievements**\n\n"
    for ach_id, desc in ACHIEVEMENTS_DEF.items():
        if ach_id in unlocked:
            text += f"✅ {desc}\n"
        else:
            progress = await get_achievement_progress(user.id, ach_id, db)
            text += f"🔒 {desc} — {progress}\n" if progress else f"🔒 {desc}\n"
    await smart_reply(update, context, text, parse_mode="Markdown")

async def get_achievement_progress(user_id, ach_id, db):
    user = await db.fetchone("SELECT total_games, wins, streak, level FROM users WHERE user_id = ?", user_id)
    if not user:
        return ""
    if ach_id == "first_win":
        return f"{user['wins']}/1"
    elif ach_id == "win_10":
        return f"{user['wins']}/10"
    elif ach_id == "win_50":
        return f"{user['wins']}/50"
    elif ach_id == "streak_5":
        return f"{user['streak']}/5"
    elif ach_id == "streak_10":
        return f"{user['streak']}/10"
    elif ach_id == "level_10":
        return f"{user['level']}/10"
    elif ach_id == "level_50":
        return f"{user['level']}/50"
    elif ach_id == "level_75":
        return f"{user['level']}/75"
    elif ach_id == "level_100":
        return f"{user['level']}/100"
    elif ach_id == "daily_3":
        # could count distinct daily challenge completions, but skip for now
        return ""
    return ""