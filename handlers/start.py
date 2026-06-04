from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.xp_progression import create_user_if_not_exists
from handlers.help import help_command

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data["db"]
    await create_user_if_not_exists(user.id, user.username, user.first_name, db)

    keyboard = [
        [InlineKeyboardButton("⚡ Quick Play", callback_data="mode_quickplay"),
         InlineKeyboardButton("👥 Group Battle", callback_data="mode_groupbattle")],
        [InlineKeyboardButton("🏆 Ranked", callback_data="mode_ranked"),
         InlineKeyboardButton("📅 Daily Challenge", callback_data="mode_daily")],
        [InlineKeyboardButton("♾️ Endless Mode", callback_data="mode_endless")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile"),
         InlineKeyboardButton("🏅 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]

    await update.message.reply_text(
        "🤖 *Guess The Intruder*\n\n"
        "Find the one that doesn't belong!\n"
        "━━━━━━━━━━━━━━━\n"
        "⚡ Fast rounds • 🔥 Combos • 🏆 Leagues\n"
        "━━━━━━━━━━━━━━━\n\n"
        "Choose a mode:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def menu_redirect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    mode = query.data
    if mode == "mode_quickplay":
        from handlers.quick_play import start_quick_play
        await start_quick_play(update, context)
    elif mode == "mode_groupbattle":
        await query.edit_message_text("Use /battle in a group to start a group battle!")
    elif mode == "mode_ranked":
        from handlers.ranked import ranked_start
        await ranked_start(update, context)
    elif mode == "mode_daily":
        from handlers.daily_challenge import start_daily
        await start_daily(update, context)
    elif mode == "mode_endless":
        from handlers.endless import start_endless
        await start_endless(update, context)
    elif mode == "profile":
        from handlers.profile import profile_command
        await profile_command(update, context)
    elif mode == "leaderboard":
        from handlers.leaderboard import leaderboard_global
        await leaderboard_global(update, context)
    elif mode == "help":
        from handlers.help import help_command
        await help_command(update, context)
    else:
        await query.edit_message_text("Unknown option.")