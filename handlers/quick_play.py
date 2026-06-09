import asyncio, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from core.game_engine import generate_puzzle
from core.difficulty import get_player_difficulty
from services.xp_progression import award_xp
from services.achievements import check_achievement, check_streak_achievements, check_win_achievements
from core.anti_cheat import is_suspicious_speed
from utils.rate_limiter import game_start_limiter

active_games = {}
active_games_lock = asyncio.Lock()

async def start_quick_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    db = context.bot_data["db"]
    chat_id = query.message.chat_id

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(0.2)

    if not await game_start_limiter.is_allowed(user.id):
        await query.answer("⏳ Please wait before starting another game.")
        return

    async with active_games_lock:
        # If there's an existing game for this user, cancel its timeout task and remove it
        old_game = active_games.pop(user.id, None)
        if old_game and "timeout_task" in old_game:
            old_game["timeout_task"].cancel()

    difficulty = await get_player_difficulty(user.id, db)
    puzzle = generate_puzzle(difficulty)
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"qp_answer_{i}")] for i, opt in enumerate(puzzle["options"])]
    keyboard.append([InlineKeyboardButton("❌ Quit", callback_data="qp_quit")])

    msg = await query.edit_message_text(
        f"🕹️ *Quick Play* — Level {difficulty}\n\nFind the intruder!\n\n" + "\n".join(puzzle["options"]),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    game_state = {
        "puzzle": puzzle,
        "message_id": msg.message_id,
        "chat_id": chat_id,
        "difficulty": difficulty,
        "start_time": time.monotonic(),
        "user_id": user.id,
        "timeout_task": None
    }

    # Create the timeout task and store it
    timeout_task = asyncio.create_task(auto_timeout(user.id, context, game_state))
    game_state["timeout_task"] = timeout_task

    async with active_games_lock:
        active_games[user.id] = game_state

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    db = context.bot_data["db"]

    async with active_games_lock:
        game = active_games.pop(user.id, None)

    if not game:
        await query.answer("No active game.", show_alert=True)
        return

    # Cancel the timeout task immediately
    if game.get("timeout_task"):
        game["timeout_task"].cancel()

    if query.data == "qp_quit":
        await query.edit_message_text("Game cancelled.")
        return

    try:
        chosen_idx = int(query.data.split("_")[2])
    except:
        await query.answer("Invalid choice.")
        return

    puzzle = game["puzzle"]
    correct = (chosen_idx == puzzle["intruder_index"])
    elapsed = time.monotonic() - game["start_time"]

    if correct and is_suspicious_speed(user.id, game["difficulty"], elapsed):
        await query.answer("⚠️ Suspicious speed detected.", show_alert=True)
        return

    user_data = await db.fetchone("SELECT total_games, wins, streak, max_streak FROM users WHERE user_id = ?", user.id)
    if user_data:
        new_streak = user_data["streak"] + 1 if correct else 0
        max_streak = max(user_data["max_streak"], new_streak)
        await db.execute(
            "UPDATE users SET total_games = total_games + 1, wins = wins + ?, streak = ?, max_streak = ?, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?",
            1 if correct else 0, new_streak, max_streak, user.id
        )
    else:
        new_streak = 1 if correct else 0

    if correct:
        combo = min(new_streak, 10)
        gained_info = await award_xp(user.id, base_xp=50, db=db, combo=combo)
        total_wins = (user_data["wins"] if user_data else 0) + 1
        await check_win_achievements(user.id, total_wins, db)
        await check_streak_achievements(user.id, new_streak, db)
        if elapsed < 2:
            await check_achievement(user.id, "perfect_round", db)

        try:
            await query.edit_message_text("✅")
            await asyncio.sleep(0.3)
            await query.edit_message_text("✨")
            await asyncio.sleep(0.3)
            await query.edit_message_text("💎")
            await asyncio.sleep(0.3)
        except:
            pass

        text = (
            "✅ *CORRECT!*\n\n"
            f"🎯 Intruder: {puzzle['options'][puzzle['intruder_index']]}\n"
            f"⚡ Time: {elapsed:.1f}s\n"
        )
        if gained_info:
            text += f"🔥 Combo x{combo}\n💠 +{gained_info[0]} XP\n"
            if gained_info[1] != gained_info[3]:
                text += f"⬆️ Level Up! {gained_info[3]} → {gained_info[1]}\n"

        await query.edit_message_text(text, parse_mode="Markdown")

        if new_streak > 0 and new_streak % 5 == 0:
            bonus_xp = 50
            await award_xp(user.id, bonus_xp, db, combo=1)
            try:
                await context.bot.send_message(game["chat_id"], f"🔥 **STREAK x{new_streak}!** +{bonus_xp} bonus XP!")
            except:
                pass
    else:
        text = f"❌ *WRONG!*\n\nThe intruder was: {puzzle['options'][puzzle['intruder_index']]}\n"
        await query.edit_message_text(text, parse_mode="Markdown")

async def auto_timeout(user_id: int, context: ContextTypes.DEFAULT_TYPE, game_state: dict):
    """Task that expires the game after 10 seconds, if not already answered."""
    try:
        await asyncio.sleep(10)
        # After sleeping, check if this game is still the active one (not already popped)
        async with active_games_lock:
            current_game = active_games.get(user_id)
            if current_game is game_state:   # same object, meaning it wasn't replaced
                active_games.pop(user_id, None)
            else:
                return  # Game already handled, nothing to do
        # Edit the message to show timeout
        try:
            await context.bot.edit_message_text(
                chat_id=game_state["chat_id"],
                message_id=game_state["message_id"],
                text="⌛ Time's up! Game expired."
            )
        except:
            pass
    except asyncio.CancelledError:
        # Task was cancelled because the player answered – that's fine
        pass