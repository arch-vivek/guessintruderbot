from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import smart_reply

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ *Guess The Intruder – Help*\n\n"
        "Find the item that doesn't belong in the group.\n\n"
        "⚡ *Quick Play* – Solo fast rounds.\n"
        "👥 *Group Battle* – Use /battle in a group.\n"
        "🏆 *Ranked* – Competitive MMR duels.\n"
        "🤺 *Duel* – Challenge someone directly with /duel.\n"
        "📅 *Daily Challenge* – Once per day puzzle.\n"
        "♾️ *Endless* – Survive as long as you can.\n"
        "🎮 *Inline* – Type @guessintruderbot in any chat.\n\n"
        "Commands: /profile, /leaderboard, /achievements, /reward"
    )
    await smart_reply(update, context, text, parse_mode="Markdown")