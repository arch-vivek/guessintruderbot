from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# /admin_broadcast <message>
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /admin_broadcast <message>")
        return
    text = " ".join(context.args)
    db = context.bot_data["db"]
    users = await db.fetchall("SELECT user_id FROM users")
    count = 0
    for u in users:
        try:
            await context.bot.send_message(u["user_id"], text)
            count += 1
        except:
            pass
    await update.message.reply_text(f"Broadcast sent to {count} users.")

# /admin_give <user_id> <xp_amount>
async def admin_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin_give <user_id> <xp_amount>")
        return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid numbers.")
        return

    from services.xp_progression import award_xp
    db = context.bot_data["db"]
    await award_xp(target_id, amount, db, combo=1)
    await update.message.reply_text(f"✅ Gave {amount} XP to user {target_id}.")

# /admin_setprofile <user_id> <field> <value>
# /admin_setprofile <user_id> <field> <value>
# Allowed: xp, level, mmr, rank_tier, wins, losses, streak, max_streak
async def admin_setprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /admin_setprofile <user_id> <field> <value>\n"
            "Fields: xp, level, mmr, rank_tier, wins, losses, streak, max_streak"
        )
        return
    try:
        target_id = int(context.args[0])
        field = context.args[1].lower()
        if field == "rank_tier":
            value = context.args[2]
        else:
            value = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Invalid input.")
        return

    allowed = {"xp", "level", "mmr", "rank_tier", "wins", "losses", "streak", "max_streak"}
    if field not in allowed:
        await update.message.reply_text(f"Unknown field. Allowed: {', '.join(allowed)}")
        return

    db = context.bot_data["db"]
    await db.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", value, target_id)
    await update.message.reply_text(f"✅ Updated {field} for user {target_id} to {value}.")

# /admin_info <user_id>
async def admin_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /admin_info <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return
    db = context.bot_data["db"]
    user = await db.fetchone("SELECT * FROM users WHERE user_id = ?", target_id)
    if not user:
        await update.message.reply_text("User not found.")
        return
    text = "\n".join([f"**{k}**: {v}" for k, v in user.items()])
    await update.message.reply_text(text, parse_mode="Markdown")