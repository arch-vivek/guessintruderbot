import asyncio, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.game_engine import generate_puzzle
from services.xp_progression import award_xp, get_user, create_user_if_not_exists
from utils.rate_limiter import RateLimiter

RANKED_QUEUE = []
queue_lock = asyncio.Lock()
matchmaker_running = False

duel_limiter = RateLimiter(max_calls=3, period=60)   # 3 duels per minute
ranked_limiter = RateLimiter(max_calls=5, period=60) # 5 ranked queue joins per minute

RANK_TIERS = {
    (0, 1199): "bronze",
    (1200, 1399): "silver",
    (1400, 1599): "gold",
    (1600, 1799): "platinum",
    (1800, 1999): "diamond",
    (2000, 2199): "master",
    (2200, float("inf")): "mythic"
}

def get_rank_tier(mmr: int) -> str:
    for (lo, hi), tier in RANK_TIERS.items():
        if lo <= mmr <= hi:
            return tier
    return "bronze"

async def update_rank_tier(user_id: int, db):
    user = await db.fetchone("SELECT mmr, rank_tier FROM users WHERE user_id = ?", user_id)
    if not user:
        return None
    old_tier = user["rank_tier"]
    new_tier = get_rank_tier(user["mmr"])
    if new_tier != old_tier:
        await db.execute("UPDATE users SET rank_tier = ? WHERE user_id = ?", new_tier, user_id)
        return new_tier
    return None

# ---------- Ranked Matchmaking ----------
async def ranked_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data["db"]

    # Rate limit check
    if not await ranked_limiter.is_allowed(user.id):
        msg = "⏳ Please wait before joining ranked again."
        if update.callback_query:
            await update.callback_query.answer(msg, show_alert=True)
        else:
            await update.message.reply_text(msg)
        return

    await create_user_if_not_exists(user.id, user.username, user.first_name, db)

    async with queue_lock:
        if user.id in RANKED_QUEUE:
            msg = "Already in queue."
            if update.callback_query:
                await update.callback_query.answer(msg, show_alert=True)
            else:
                await update.message.reply_text(msg)
            return
        RANKED_QUEUE.append(user.id)

    text = "⏳ Searching for opponent..."
    if update.callback_query:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)

    global matchmaker_running
    if not matchmaker_running:
        matchmaker_running = True
        asyncio.create_task(matchmaker(context))

async def matchmaker(context):
    global matchmaker_running
    db = context.bot_data["db"]
    try:
        while True:
            await asyncio.sleep(3)
            async with queue_lock:
                if len(RANKED_QUEUE) >= 2:
                    p1 = RANKED_QUEUE.pop(0)
                    p2 = RANKED_QUEUE.pop(0)
                    asyncio.create_task(start_duel(p1, p2, context, db, is_ranked=True, group_chat_id=None))
    except asyncio.CancelledError:
        matchmaker_running = False

# ---------- Direct Duel Command ----------
async def duel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    challenger = update.effective_user
    db = context.bot_data["db"]

    # Rate limit check
    if not await duel_limiter.is_allowed(challenger.id):
        await update.message.reply_text("⏳ Please wait before starting another duel.")
        return

    group_chat_id = update.effective_chat.id

    target_user = None
    target_id = None
    target_username = None
    target_first_name = None

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id
        target_username = target_user.username
        target_first_name = target_user.first_name
    elif context.args:
        username = context.args[0].lstrip("@").lower()
        row = await db.fetchone("SELECT user_id, username, first_name FROM users WHERE LOWER(username) = ?", username)
        if row:
            target_id = row["user_id"]
            target_username = row["username"]
            target_first_name = row["first_name"]
        else:
            await update.message.reply_text(
                "❌ User not found. They must have started the bot at least once.\n"
                "Tip: reply to their message with /duel instead – that works even if they're new!"
            )
            return
    else:
        await update.message.reply_text("Usage: reply to a message with /duel, or /duel @username")
        return

    if target_id == challenger.id:
        await update.message.reply_text("You can't duel yourself.")
        return

    await create_user_if_not_exists(target_id, target_username, target_first_name, db)

    pending_key = f"duel_challenge_{challenger.id}_{target_id}"
    if pending_key in context.bot_data:
        await update.message.reply_text("You already have a pending challenge against this user.")
        return

    challenge_data = {
        "challenger_id": challenger.id,
        "target_id": target_id,
        "expires": time.time() + 60,
        "challenger_name": challenger.first_name or challenger.username or str(challenger.id),
        "group_chat_id": group_chat_id
    }
    context.bot_data[pending_key] = challenge_data

    target_display = target_first_name or target_username or "user"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Accept Duel", callback_data=f"duel_accept_{challenger.id}_{target_id}_{int(challenge_data['expires'])}")]
    ])
    await update.message.reply_text(
        f"🤺 {challenge_data['challenger_name']} challenges {target_display} to a duel!\n\n"
        "Tap the button to accept (60 seconds).",
        reply_markup=keyboard
    )

async def duel_accept_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    db = context.bot_data["db"]

    data = query.data.split("_")
    if len(data) < 4:
        await query.answer("Invalid challenge.", show_alert=True)
        return

    challenger_id = int(data[2])
    target_id = int(data[3])

    if user.id != target_id:
        await query.answer("This challenge is not for you.", show_alert=True)
        return

    pending_key = f"duel_challenge_{challenger_id}_{target_id}"
    challenge = context.bot_data.pop(pending_key, None)
    if not challenge or challenge["expires"] < time.time():
        await query.answer("Challenge expired.", show_alert=True)
        await query.edit_message_text("Challenge expired.")
        return

    await create_user_if_not_exists(user.id, user.username, user.first_name, db)

    group_chat_id = challenge["group_chat_id"]
    await query.edit_message_text("⚔️ Duel accepted! Prepare...")
    await start_duel(challenger_id, target_id, context, db, is_ranked=False, group_chat_id=group_chat_id)

# ---------- Core Duel Engine ----------
async def start_duel(uid1, uid2, context, db, is_ranked=True, group_chat_id=None):
    for uid in (uid1, uid2):
        user = await db.fetchone("SELECT user_id FROM users WHERE user_id = ?", uid)
        if not user:
            await create_user_if_not_exists(uid, None, f"Player{str(uid)[-4:]}", db)

    def get_display_name(row, uid):
        if row:
            name = row["first_name"] or row["username"]
            if name:
                return name
        return f"Player{str(uid)[-4:]}"

    u1 = await db.fetchone("SELECT first_name, username FROM users WHERE user_id = ?", uid1)
    u2 = await db.fetchone("SELECT first_name, username FROM users WHERE user_id = ?", uid2)
    name1 = get_display_name(u1, uid1)
    name2 = get_display_name(u2, uid2)

    puzzles = [generate_puzzle(2) for _ in range(5)]
    duel_id = f"{uid1}_{uid2}_{int(time.time())}"
    duel_data = {
        "players": [uid1, uid2],
        "names": {uid1: name1, uid2: name2},
        "puzzles": puzzles,
        "current_round": 0,
        "answers": {uid1: [], uid2: []},
        "message_ids": {},
        "start_time": time.monotonic(),
        "is_ranked": is_ranked,
        "group_chat_id": group_chat_id,
        "round_timeout": 10,
        "processed": False,
        "db": db,
        "timeout_task": None
    }
    context.bot_data[duel_id] = duel_data

    await show_round(duel_id, context)
    duel_data["timeout_task"] = asyncio.create_task(round_timeout_task(duel_id, context))

async def show_round(duel_id, context):
    duel = context.bot_data.get(duel_id)
    if not duel or duel["current_round"] >= len(duel["puzzles"]):
        return

    round_idx = duel["current_round"]
    puzzle = duel["puzzles"][round_idx]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(opt, callback_data=f"duel_{duel_id}_{i}")] for i, opt in enumerate(puzzle["options"])
    ])
    text = f"⚔️ {'Ranked' if duel['is_ranked'] else 'Casual'} Duel – Round {round_idx+1}/5\n\n" + "\n".join(puzzle["options"])

    if duel["group_chat_id"]:
        if "group" in duel["message_ids"]:
            chat_id, msg_id = duel["message_ids"]["group"]
            try:
                msg = await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text, reply_markup=keyboard, parse_mode="Markdown")
                duel["message_ids"]["group"] = (chat_id, msg.message_id)
            except:
                try:
                    msg = await context.bot.send_message(duel["group_chat_id"], text, reply_markup=keyboard, parse_mode="Markdown")
                    duel["message_ids"]["group"] = (duel["group_chat_id"], msg.message_id)
                except:
                    pass
        else:
            try:
                msg = await context.bot.send_message(duel["group_chat_id"], text, reply_markup=keyboard, parse_mode="Markdown")
                duel["message_ids"]["group"] = (duel["group_chat_id"], msg.message_id)
            except:
                pass
    else:
        for uid in duel["players"]:
            if uid in duel["message_ids"]:
                chat_id, msg_id = duel["message_ids"][uid]
                try:
                    msg = await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text, reply_markup=keyboard, parse_mode="Markdown")
                    duel["message_ids"][uid] = (chat_id, msg.message_id)
                except:
                    try:
                        msg = await context.bot.send_message(uid, text, reply_markup=keyboard, parse_mode="Markdown")
                        duel["message_ids"][uid] = (uid, msg.message_id)
                    except:
                        pass
            else:
                try:
                    msg = await context.bot.send_message(uid, text, reply_markup=keyboard, parse_mode="Markdown")
                    duel["message_ids"][uid] = (uid, msg.message_id)
                except:
                    pass

    if duel.get("timeout_task"):
        duel["timeout_task"].cancel()
    duel["start_time"] = time.monotonic()
    duel["processed"] = False
    duel["timeout_task"] = asyncio.create_task(round_timeout_task(duel_id, context))

async def round_timeout_task(duel_id, context):
    try:
        await asyncio.sleep(10)
        duel = context.bot_data.get(duel_id)
        if not duel or duel["processed"]:
            return
        for uid in duel["players"]:
            if len(duel["answers"][uid]) <= duel["current_round"]:
                duel["answers"][uid].append((False, 10.0))
        duel["processed"] = True
        await process_duel_round(duel_id, context)
    except asyncio.CancelledError:
        pass

async def duel_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data

    if not data.startswith("duel_"):
        return

    try:
        prefix, chosen_str = data.rsplit("_", 1)
    except ValueError:
        return

    if not prefix.startswith("duel_"):
        return
    duel_id = prefix[5:]

    if not any(ch.isdigit() for ch in duel_id):
        return

    try:
        chosen_idx = int(chosen_str)
    except ValueError:
        await query.answer("Invalid option.", show_alert=True)
        return

    duel = context.bot_data.get(duel_id)
    if not duel:
        await query.answer("Duel expired.", show_alert=True)
        return
    if user.id not in duel["players"]:
        await query.answer("Not your duel.", show_alert=True)
        return

    round_idx = duel["current_round"]
    if len(duel["answers"][user.id]) > round_idx:
        await query.answer("Already answered.", show_alert=True)
        return

    elapsed = time.monotonic() - duel["start_time"]
    correct = (chosen_idx == duel["puzzles"][round_idx]["intruder_index"])
    duel["answers"][user.id].append((correct, elapsed))
    await query.answer("Answer recorded!")

    if (len(duel["answers"][duel["players"][0]]) > round_idx and
        len(duel["answers"][duel["players"][1]]) > round_idx):
        if not duel["processed"]:
            duel["processed"] = True
            if duel.get("timeout_task"):
                duel["timeout_task"].cancel()
            await process_duel_round(duel_id, context)

async def process_duel_round(duel_id, context):
    duel = context.bot_data.get(duel_id)
    if not duel:
        return

    round_idx = duel["current_round"]
    puzzle = duel["puzzles"][round_idx]
    p1, p2 = duel["players"]
    a1 = duel["answers"][p1][round_idx][0]
    a2 = duel["answers"][p2][round_idx][0]
    intruder_text = puzzle["options"][puzzle["intruder_index"]]

    if duel["group_chat_id"]:
        feedback = (
            f"⚔️ Round {round_idx+1} results:\n"
            f"✅ {duel['names'][p1]} was {'correct' if a1 else 'wrong'}\n"
            f"✅ {duel['names'][p2]} was {'correct' if a2 else 'wrong'}\n"
            f"Intruder: {intruder_text}"
        )
    else:
        feedback_p1 = f"⚔️ Round {round_idx+1} result:\n{'✅ Correct!' if a1 else '❌ Wrong!'}\nIntruder: {intruder_text}"
        feedback_p2 = f"⚔️ Round {round_idx+1} result:\n{'✅ Correct!' if a2 else '❌ Wrong!'}\nIntruder: {intruder_text}"

    if duel["group_chat_id"] and "group" in duel["message_ids"]:
        chat_id, msg_id = duel["message_ids"]["group"]
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=feedback, parse_mode="Markdown")
        except:
            pass
    else:
        for uid, fb in [(p1, feedback_p1), (p2, feedback_p2)]:
            if uid in duel["message_ids"]:
                chat_id, msg_id = duel["message_ids"][uid]
                try:
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=fb, parse_mode="Markdown")
                except:
                    pass

    await asyncio.sleep(2)

    duel["current_round"] += 1
    if duel["current_round"] < len(duel["puzzles"]):
        await show_round(duel_id, context)
    else:
        await finish_duel(duel_id, context)

async def handle_duel_forfeit(duel_id, uid, context):
    duel = context.bot_data.get(duel_id)
    if not duel:
        return
    winner = duel["players"][0] if duel["players"][1] == uid else duel["players"][1]
    await finish_duel(duel_id, context, forfeit_winner=winner)

async def finish_duel(duel_id, context, forfeit_winner=None):
    duel = context.bot_data.pop(duel_id, None)
    if not duel:
        return
    db = duel.get("db") or context.bot_data["db"]
    p1, p2 = duel["players"]
    name1 = duel["names"][p1]
    name2 = duel["names"][p2]

    p1_correct = sum(1 for a in duel["answers"][p1] if a[0])
    p2_correct = sum(1 for a in duel["answers"][p2] if a[0])

    if forfeit_winner:
        winner_id = forfeit_winner
        loser_id = p1 if p2 == forfeit_winner else p2
    else:
        if p1_correct > p2_correct:
            winner_id, loser_id = p1, p2
        elif p2_correct > p1_correct:
            winner_id, loser_id = p2, p1
        else:
            w_mmr = await db.fetchone("SELECT mmr FROM users WHERE user_id = ?", p1)
            l_mmr = await db.fetchone("SELECT mmr FROM users WHERE user_id = ?", p2)
            if w_mmr and l_mmr:
                if w_mmr["mmr"] >= l_mmr["mmr"]:
                    winner_id, loser_id = p1, p2
                else:
                    winner_id, loser_id = p2, p1
            else:
                winner_id, loser_id = p1, p2

    winner_name = duel["names"][winner_id]
    loser_name = duel["names"][loser_id]

    await award_xp(winner_id, 100, db, combo=1)
    await award_xp(loser_id, 30, db, combo=1)

    delta = 0
    rank_msg = ""
    if duel.get("is_ranked", True):
        w_user = await db.fetchone("SELECT mmr FROM users WHERE user_id = ?", winner_id)
        l_user = await db.fetchone("SELECT mmr FROM users WHERE user_id = ?", loser_id)
        if w_user and l_user:
            k = 32
            expected = 1 / (1 + 10 ** ((l_user["mmr"] - w_user["mmr"]) / 400))
            delta = int(k * (1 - expected))
            await db.execute("UPDATE users SET mmr = mmr + ?, wins = wins + 1 WHERE user_id = ?", delta, winner_id)
            await db.execute("UPDATE users SET mmr = mmr - ?, losses = losses + 1 WHERE user_id = ?", delta, loser_id)
            new_rank = await update_rank_tier(winner_id, db)
            if new_rank:
                rank_msg = f"\n🎉 Congratulations! You've reached **{new_rank.capitalize()}** rank!"

    result = (
        f"🏆 Duel finished!\n\n"
        f"{name1}: {p1_correct}/5 correct\n"
        f"{name2}: {p2_correct}/5 correct\n\n"
        f"Winner: **{winner_name}**\n"
    )
    if duel.get("is_ranked"):
        result += f"MMR change: +{delta} ({winner_name}), -{delta} ({loser_name})"

    if duel["group_chat_id"] and "group" in duel["message_ids"]:
        chat_id, msg_id = duel["message_ids"]["group"]
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=result, parse_mode="Markdown")
        except:
            await context.bot.send_message(duel["group_chat_id"], result, parse_mode="Markdown")
    else:
        for uid in [winner_id, loser_id]:
            personal = result
            if uid == winner_id and rank_msg:
                personal += rank_msg
            if uid in duel["message_ids"]:
                chat_id, msg_id = duel["message_ids"][uid]
                try:
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=personal, parse_mode="Markdown")
                except:
                    try:
                        await context.bot.send_message(uid, personal, parse_mode="Markdown")
                    except:
                        pass
            else:
                try:
                    await context.bot.send_message(uid, personal, parse_mode="Markdown")
                except:
                    pass