from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import smart_reply

async def leaderboard_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data["db"]
    top = await db.fetchall(
        "SELECT user_id, username, first_name, level, mmr FROM users ORDER BY mmr DESC LIMIT 10"
    )
    text = "🌐 *GLOBAL LEADERBOARD (MMR)*\n━━━━━━━━━━━━━━━\n"
    for i, row in enumerate(top):
        name = row["first_name"] or row["username"] or str(row["user_id"])
        text += f"{i+1}. `{name}` — Lv.{row['level']} | {row['mmr']} MMR\n"
    await smart_reply(update, context, text, parse_mode="Markdown")