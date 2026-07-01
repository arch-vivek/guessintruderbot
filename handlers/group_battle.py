import asyncio, time, json, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup 
from telegram.ext import ContextTypes
from core.game_engine import generate_puzzle
from services.xp_progression import award_xp
from utils.rate_limiter import RateLimiter
from log import logger

LOBBIES_KEY = "gb_lobbies"
ROUNDS_KEY = "gb_rounds"

battle_limiter = RateLimiter(max_calls=2, period=60)  # max 2 battles per minute per user

async def group_battle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Group only guard
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("⚔️ Group battles are only available in groups. Invite me to a group and try again!")
        return

    # Rate limit
    if not await battle_limiter.is_allowed(user.id):
        await update.message.reply_text("⏳ Please wait before starting another battle.")
        return

    db = context.bot_data["db"]
    lobbies = context.bot_data.setdefault(LOBBIES_KEY, {})
    if chat.id in lobbies and lobbies[chat.id].get("active"):
        await update.message.reply_text("A battle is already in progress!")
        return

    lobby = {
        "players": set(),
        "status": "lobby",
        "message_id": None,
        "chat_id": chat.id,
        "start_time": time.time() + 30,
        "round": 0,
        "scores": {},
        "alive": set(),
        "creator": user.id
    }
    lobbies[chat.id] = lobby

    msg = await update.message.reply_text(
        "⚔️ *GROUP BATTLE starting in 30s!*\n\n"
        "Players: 0\n"
        "Type /join to participate.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Join", callback_data="gb_join")]])
    )
    lobby["message_id"] = msg.message_id

    await asyncio.sleep(30)
    lobby = lobbies.get(chat.id)
    if not lobby or lobby["status"] != "lobby":
        return
    if len(lobby["players"]) < 2:
        await context.bot.edit_message_text(
            chat_id=chat.id,
            message_id=lobby["message_id"],
            text="Not enough players. Battle cancelled."
        )
        del lobbies[chat.id]
        return

    lobby["status"] = "active"
    lobby["alive"] = set(lobby["players"])
    lobby["scores"] = {p: 0 for p in lobby["players"]}
    await context.bot.send_message(chat.id, "⚔️ Battle begins! Check your private messages.")
    await run_battle_rounds(chat.id, context)
    logger.info(f"Group battle started in chat {chat.id} by user {user.id}")

async def join_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("This command is only for joining a group battle. Use it inside a group where a battle is active.")
        return
    user = update.effective_user
    lobbies = context.bot_data.get(LOBBIES_KEY, {})
    lobby = lobbies.get(chat.id)
    if not lobby or lobby["status"] != "lobby":
        await update.message.reply_text("No lobby to join.")
        return
    lobby["players"].add(user.id)
    await update.message.reply_text(f"{user.first_name} joined! ({len(lobby['players'])} players)")

async def handle_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    user = query.from_user
    chat_id = query.message.chat_id
    lobbies = context.bot_data.get(LOBBIES_KEY, {})
    lobby = lobbies.get(chat_id)

    if not lobby or lobby["status"] != "lobby":
        try:
            await query.edit_message_text("This lobby is no longer available.")
        except:
            pass
        return

    lobby["players"].add(user.id)

    try:
        await query.edit_message_text(
            f"⚔️ *GROUP BATTLE starting soon!*\n\nPlayers: {len(lobby['players'])}\n\n/join to participate.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Join", callback_data="gb_join")]])
        )
    except Exception:
        await context.bot.send_message(
            chat_id,
            f"Player joined! ({len(lobby['players'])} total). Use /join to enter."
        )

async def run_battle_rounds(chat_id, context):
    lobbies = context.bot_data.get(LOBBIES_KEY, {})
    lobby = lobbies.get(chat_id)
    if not lobby:
        return
    rounds = 5
    for r in range(rounds):
        lobby["round"] = r + 1
        puzzle = generate_puzzle(difficulty=2)
        alive_players = list(lobby["alive"])
        if len(alive_players) <= 1:
            break

        round_id = f"{chat_id}_{r}"
        round_data = {
            "puzzle": puzzle,
            "answers": {},
            "start_time": time.monotonic(),
            "deadline": time.monotonic() + 8,
            "alive": alive_players
        }
        context.bot_data.setdefault(ROUNDS_KEY, {})[round_id] = round_data

        for uid in alive_players:
            try:
                await context.bot.send_message(
                    uid,
                    f"⚔️ *Round {lobby['round']}*\n\nFind the intruder:\n\n" + "\n".join(puzzle["options"]),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(opt, callback_data=f"gb_answer_{round_id}_{i}")]
                        for i, opt in enumerate(puzzle["options"])
                    ]),
                    parse_mode="Markdown"
                )
            except Exception:
                lobby["alive"].discard(uid)

        await asyncio.sleep(8)

        round_data = context.bot_data.get(ROUNDS_KEY, {}).get(round_id)
        if not round_data:
            continue
        correct_idx = puzzle["intruder_index"]
        for uid, (chosen, elapsed) in round_data["answers"].items():
            if uid in lobby["alive"]:
                if chosen == correct_idx:
                    lobby["scores"][uid] += 100 + max(0, int(80 - elapsed * 10))
                else:
                    lobby["alive"].discard(uid)
                    try:
                        await context.bot.send_message(uid, "❌ Wrong answer! Eliminated.")
                    except:
                        pass
        if round_id in context.bot_data.get(ROUNDS_KEY, {}):
            del context.bot_data[ROUNDS_KEY][round_id]

        score_text = "\n".join([f"• `{uid}`: {score}" for uid, score in lobby["scores"].items()])
        await context.bot.send_message(
            chat_id,
            f"⚔️ *Round {lobby['round']} Results*\n\nEliminated: {len(lobby['players']) - len(lobby['alive'])}\nScores:\n{score_text}",
            parse_mode="Markdown"
        )
        await asyncio.sleep(2)

    winner = max(lobby["scores"], key=lobby["scores"].get) if lobby["scores"] else None
    if winner:
        await award_xp(winner, 200, context.bot_data["db"], combo=2)
        await context.bot.send_message(chat_id, f"🏆 *Winner: {winner}* with {lobby['scores'][winner]} points!")
    del lobbies[chat_id]
    logger.info(f"Group battle winner: {winner} in chat {chat_id}")

async def gb_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    user = query.from_user
    data = query.data.split("_")
    if len(data) < 5:
        return
    round_id = f"{data[2]}_{data[3]}"
    chosen_idx = int(data[4])
    rounds = context.bot_data.get(ROUNDS_KEY, {})
    round_data = rounds.get(round_id)
    if not round_data:
        try:
            await query.edit_message_text("No active round.")
        except:
            pass
        return
    if user.id not in round_data["alive"]:
        return
    if user.id in round_data["answers"]:
        return
    elapsed = time.monotonic() - round_data["start_time"]
    round_data["answers"][user.id] = (chosen_idx, elapsed)
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except:
        pass
    