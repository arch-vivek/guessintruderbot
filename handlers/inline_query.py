import time, uuid, random, asyncio
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from core.game_engine import generate_puzzle
from services.xp_progression import award_xp

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Try to get a puzzle from the pre‑warmed pool
    pool = context.bot_data.get("inline_pool", [])
    if pool:
        puzzle = pool.pop(0)   # take the first one
    else:
        puzzle = generate_puzzle(difficulty=random.randint(1,2))
        # in background, ask the warm‑up task to refill (already running in main)

    puzzle_id = uuid.uuid4().hex[:8]
    context.bot_data.setdefault("inline_puzzles", {})[puzzle_id] = {
        "puzzle": puzzle,
        "expires": time.time() + 600,
        "answered_users": set()
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(opt, callback_data=f"inline_answer_{puzzle_id}_{i}")] for i, opt in enumerate(puzzle["options"])
    ])

    results = []
    results.append(
        InlineQueryResultArticle(
            id=puzzle_id,
            title="⚡ Quick Intruder Challenge",
            description="Find the one that doesn't belong!",
            input_message_content=InputTextMessageContent(
                f"🎮 *Guess the Intruder!*\n\n" + "\n".join(puzzle["options"]),
                parse_mode="Markdown"
            ),
            reply_markup=keyboard,
            thumbnail_url="https://via.placeholder.com/100/00ffcc/000?text=GIT"
        )
    )
    results.append(
        InlineQueryResultArticle(
            id="challenge_friend",
            title="🤺 Challenge a Friend",
            description="Send a duel request",
            input_message_content=InputTextMessageContent(
                "🎯 *Duel Request!* I challenge you to Guess the Intruder! Use /duel to accept.",
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ Accept Duel", callback_data="challenge_general")]])
        )
    )
    await update.inline_query.answer(results, cache_time=0, is_personal=False)

async def inline_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    db = context.bot_data["db"]
    data = query.data.split("_")
    if len(data) < 3 or data[0] != "inline" or data[1] != "answer":
        return
    puzzle_id = data[2]
    chosen_idx = int(data[3])
    stored = context.bot_data.get("inline_puzzles", {}).get(puzzle_id)
    if not stored or stored["expires"] < time.time():
        await query.answer("Challenge expired.", show_alert=True)
        return
    if user.id in stored.get("answered_users", set()):
        await query.answer("You already answered this puzzle!", show_alert=True)
        return
    stored.setdefault("answered_users", set()).add(user.id)

    puzzle = stored["puzzle"]
    correct = (chosen_idx == puzzle["intruder_index"])
    if correct:
        await award_xp(user.id, 10, db, combo=1)
        await query.answer("✅ Correct! +10 XP", show_alert=True)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
    else:
        await query.answer("❌ Wrong intruder!", show_alert=True)