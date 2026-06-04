from datetime import date
from telegram import Update
from telegram.ext import ContextTypes
from services.xp_progression import award_xp

async def daily_reward_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data["db"]

    today = date.today().isoformat()
    user_data = await db.fetchone(
        "SELECT last_daily, daily_streak FROM users WHERE user_id = ?", user.id
    )
    if not user_data:
        await update.message.reply_text("Please /start first.")
        return

    last_daily = user_data["last_daily"]
    if last_daily == today:
        await update.message.reply_text("🎁 You've already claimed today's reward. Come back tomorrow!")
        return

    # Calculate streak
    if last_daily:
        last_date = date.fromisoformat(last_daily)
        expected_date = date.today() - date.resolution
        if last_date == expected_date:
            new_streak = user_data["daily_streak"] + 1
        else:
            new_streak = 1
    else:
        new_streak = 1

    # XP reward: base 50 XP + streak bonus
    xp_reward = 50 + new_streak * 20   # 50, 70, 90, ...

    await db.execute(
        "UPDATE users SET last_daily = ?, daily_streak = ? WHERE user_id = ?",
        today, new_streak, user.id
    )

    # Award the XP
    await award_xp(user.id, xp_reward, db, combo=1)

    msg = (
        f"🎩 **Daily Reward**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💠 +{xp_reward} XP\n"
        f"🔥 Streak: {new_streak} days\n"
    )
    if new_streak == 7:
        msg += "🌟 **Weekly streak bonus!** +100 extra XP"
        await award_xp(user.id, 100, db, combo=1)

    await update.message.reply_text(msg, parse_mode="Markdown")