import json
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.game_engine import generate_puzzle
from services.xp_progression import award_xp
from utils.helpers import smart_reply
from utils.rate_limiter import RateLimiter

daily_limiter = RateLimiter(max_calls=1, period=60)

async def get_today_challenge(db):
    today_str = str(date.today())
    challenge = await db.fetchone("SELECT * FROM daily_challenges WHERE date = ?", today_str)
    if not challenge:
        puzzle = generate_puzzle(difficulty=2)
        await db.execute("INSERT INTO daily_challenges (date, puzzle_data) VALUES (?, ?)", today_str, json.dumps(puzzle))
        challenge = await db.fetchone("SELECT * FROM daily_challenges WHERE date = ?", today_str)
    return challenge

async def start_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data["db"]

    if not await daily_limiter.is_allowed(user.id):
        await smart_reply(update, context, "⏳ Please wait before attempting the daily challenge again.")
        return

    today_str = str(date.today())
    user_data = await db.fetchone("SELECT last_daily FROM users WHERE user_id = ?", user.id)
    if user_data and user_data["last_daily"] == today_str:
        await smart_reply(update, context, "You already attempted today's challenge! Come back tomorrow.")
        return

    challenge = await get_today_challenge(db)
    puzzle = json.loads(challenge["puzzle_data"])
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"daily_answer_{i}")] for i, opt in enumerate(puzzle["options"])]
    keyboard.append([InlineKeyboardButton("« Back to Menu", callback_data="start_menu")])

    if update.callback_query:
        msg = await update.callback_query.edit_message_text(
            f"📅 *Daily Challenge*\n\nFind the intruder:\n\n" + "\n".join(puzzle["options"]),
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
        chat_id = update.callback_query.message.chat_id
    else:
        msg = await update.message.reply_text(
            f"📅 *Daily Challenge*\n\nFind the intruder:\n\n" + "\n".join(puzzle["options"]),
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
        chat_id = update.message.chat_id

    context.user_data["daily_game"] = {
        "puzzle": puzzle,
        "message_id": msg.message_id,
        "chat_id": chat_id
    }

async def daily_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    db = context.bot_data["db"]
    game = context.user_data.get("daily_game")
    if not game:
        await query.answer("Game expired.", show_alert=True)
        return
    chosen_idx = int(query.data.split("_")[2])
    puzzle = game["puzzle"]
    correct = (chosen_idx == puzzle["intruder_index"])
    if correct:
        await award_xp(user.id, 150, db, combo=2)
        await db.execute("UPDATE daily_challenges SET attempts = attempts + 1 WHERE date = ?", str(date.today()))
        await query.edit_message_text("✅ Correct! +150 XP\nYou completed the daily challenge!")
    else:
        await query.edit_message_text(f"❌ Wrong! The intruder was {puzzle['options'][puzzle['intruder_index']]}")
    await db.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", str(date.today()), user.id)
    context.user_data.pop("daily_game", None)